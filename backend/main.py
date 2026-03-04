"""FastAPI backend for Parallels — Cross-Domain Analogy Engine."""

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from typing import List, Dict, Any, Optional
from collections import defaultdict
import asyncio
import logging
import uuid
import json
import time
import os
import sys

# Ensure backend directory is in python path for imports to work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Ensure data directory exists before imports that might rely on it
os.makedirs("data/uploads", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("parallels_api")

from .council import (
    generate_conversation_title, run_analogy_pipeline
)
from . import storage
from .config import (
    RATE_LIMIT_GLOBAL, RATE_LIMIT_MESSAGE, RATE_LIMIT_UPLOAD,
    MAX_MESSAGE_LENGTH, MAX_UPLOAD_SIZE, ALLOWED_UPLOAD_TYPES,
    MAX_CONVERSATIONS, FIREBASE_PROJECT_ID
)
import re

# ═══════════════════════════════════════════
#  CORS CONFIGURATION
# ═══════════════════════════════════════════

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Construct regex for allowed origins (localhost, Firebase, Render)
origin_regex_list = [
    r"http://localhost:\d+",
    r"http://127\.0\.0\.1:\d+",
    r"https://parallels-.*\.onrender\.com",
]

if FIREBASE_PROJECT_ID:
    origin_regex_list.append(rf"https://.*{re.escape(FIREBASE_PROJECT_ID)}.*\.web\.app")
    origin_regex_list.append(rf"https://.*{re.escape(FIREBASE_PROJECT_ID)}.*\.firebaseapp\.com")

allow_origin_regex = "|".join(origin_regex_list)

app = FastAPI(title="Parallels API", description="Cross-Domain Analogy Engine")

# Serve uploaded files statically
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    # Allow specific origins
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        os.getenv("PRODUCTION_FRONTEND_URL", "https://llm-council.vercel.app")
    ],
    # ALSO allow any Netlify/Vercel/Firebase preview URL using regex
    allow_origin_regex=r"https://.*\.web\.app|https://.*\.firebaseapp\.com|https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════
#  SECURITY HEADERS MIDDLEWARE
# ═══════════════════════════════════════════

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add industry-standard security headers to every response."""
    response = await call_next(request)
    
    # Force HTTPS (HSTS) - only if not localhost
    if "localhost" not in str(request.url) and "127.0.0.1" not in str(request.url):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevent MIME-type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Cross-Site Scripting protection (legacy but still useful)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy (Strict baseline)
    # Allows scripts from self and styles from self + fonts. Adjust as needed for specific CDNs.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: http://localhost:* https://*; " # Allow local and remote images
        "connect-src 'self' https://api.openrouter.ai https://*.firebaseio.com https://*.googleapis.com http://localhost:*;"
    )
    
    return response


# ═══════════════════════════════════════════
#  RATE LIMITING MIDDLEWARE
# ═══════════════════════════════════════════

class RateLimiter:
    """In-memory per-IP rate limiter with sliding window."""
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)

    def _clean_old(self, key: str, window: int = 60):
        cutoff = time.time() - window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def is_allowed(self, ip: str, category: str, limit: int) -> bool:
        key = f"{ip}:{category}"
        self._clean_old(key)
        if len(self._requests[key]) >= limit:
            return False
        self._requests[key].append(time.time())
        return True

    def remaining(self, ip: str, category: str, limit: int) -> int:
        key = f"{ip}:{category}"
        self._clean_old(key)
        return max(0, limit - len(self._requests[key]))


rate_limiter = RateLimiter()
security = HTTPBearer()

async def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)):
    """Authenticate the user via Firebase ID token."""
    decoded_token = storage.verify_id_token(auth.credentials)
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decoded_token

def get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def check_rate_limit(request: Request, category: str, limit: int):
    """Raise 429 if rate limit exceeded. Otherwise, provide remaining headers."""
    ip = get_client_ip(request)
    remaining = rate_limiter.remaining(ip, category, limit)
    
    # We want to attach headers. Since check_rate_limit is called inside the endpoint,
    # we can't easily modify the response here without returning a custom response.
    # Instead, we'll raise an exception with custom details, or let the caller handle headers.
    if not rate_limiter.is_allowed(ip, category, limit):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for {category}. Try again in a moment.",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0"
            }
        )
    return remaining


def validate_uuid(value: str):
    """Validate that the string is a valid UUID."""
    try:
        uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")


# ═══════════════════════════════════════════
#  REQUEST MODELS
# ═══════════════════════════════════════════

class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    content: str
    target_domain: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"Message too long (max {MAX_MESSAGE_LENGTH} chars)")
        return v


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


# ═══════════════════════════════════════════
#  GLOBAL ERROR HANDLER
# ═══════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions — never leak internals to the client."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    from starlette.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."}
    )


# ═══════════════════════════════════════════
#  ENDPOINTS
# ═══════════════════════════════════════════

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "product": "parallels", "version": "1.0.0"}


# ── File Upload (rate-limited, size-limited, type-restricted) ──

def _save_upload_file(filepath: str, content: bytes):
    """Helper to save file content synchronously in a thread pool."""
    with open(filepath, 'wb') as f:
        f.write(content)

@app.post("/api/upload")
async def upload_file(request: Request, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload an image file (max 5 MB, images only)."""
    check_rate_limit(request, "upload", RATE_LIMIT_UPLOAD)

    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only images are allowed."
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024*1024)}MB."
        )

    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename or '.png')[1]}"
    filepath = f"data/uploads/{filename}"

    # Run synchronous file I/O in a thread pool to avoid blocking the event loop
    await asyncio.to_thread(_save_upload_file, filepath, content)

    return {
        "filename": filename,
        "path": f"/uploads/{filename}",
        "content_type": file.content_type,
        "size": len(content)
    }


# ── Conversations ──

@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations(request: Request, user: dict = Depends(get_current_user)):
    """List all conversations for the authenticated user."""
    check_rate_limit(request, "global", RATE_LIMIT_GLOBAL)
    return storage.list_conversations(user_id=user["uid"])


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: Request, body: CreateConversationRequest, user: dict = Depends(get_current_user)):
    """Create a new exploration for the authenticated user."""
    check_rate_limit(request, "global", RATE_LIMIT_GLOBAL)

    existing = storage.list_conversations(user_id=user["uid"])
    if len(existing) >= MAX_CONVERSATIONS:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum of {MAX_CONVERSATIONS} explorations reached. Please delete old ones."
        )

    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id, user_id=user["uid"])
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(request: Request, conversation_id: str, user: dict = Depends(get_current_user)):
    """Get a specific exploration with all its messages."""
    check_rate_limit(request, "global", RATE_LIMIT_GLOBAL)
    validate_uuid(conversation_id)
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Exploration not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(request: Request, conversation_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific exploration."""
    check_rate_limit(request, "global", RATE_LIMIT_GLOBAL)
    validate_uuid(conversation_id)
    success = storage.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Exploration not found")
    return {"status": "ok"}


# ── Message Sending — runs the 4-stage analogy pipeline ──

@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(request: Request, conversation_id: str, body: SendMessageRequest, user: dict = Depends(get_current_user)):
    """Send a message and stream the 4-stage analogy pipeline via SSE."""
    check_rate_limit(request, "message", RATE_LIMIT_MESSAGE)
    validate_uuid(conversation_id)

    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Exploration not found")

    is_first_message = len(conversation.get("messages", [])) == 0

    async def event_generator():
        queue = asyncio.Queue()

        async def on_event(event_type, message=None, data=None):
            await queue.put({
                'type': event_type,
                'message': message,
                'data': data
            })

        try:
            conversation = storage.get_conversation(conversation_id)
            history = conversation["messages"]
            storage.add_user_message(conversation_id, body.content, attachments=body.attachments)

            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(body.content))

            # Start the pipeline in a separate task so we can yield events
            pipeline_task = asyncio.create_task(run_analogy_pipeline(
                body.content, 
                history, 
                target_domain=body.target_domain,
                attachments=body.attachments,
                on_event=on_event
            ))

            # Initial start event
            yield f"data: {json.dumps({'type': 'council_start', 'message': 'The Council is convening...'})}\n\n"
            
            # Consume events from the queue until the pipeline finishes
            while not pipeline_task.done() or not queue.empty():
                try:
                    # Wait for an event or check if pipeline is done
                    event = await asyncio.wait_for(queue.get(), timeout=0.1)
                    # logger.info(f"[STREAM] Yielding event: {event.get('type')}")
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    continue

            # Get the final result
            logger.info("[STREAM] Awaiting pipeline_task...")
            result = await pipeline_task
            logger.info(f"[STREAM] pipeline_task result: {type(result)}")
            
            # Yield the final result
            yield f"data: {json.dumps({'type': 'council_complete', 'data': result})}\n\n"

            # Title detection (if needed)
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            storage.add_assistant_message(
                conversation_id, 
                result.get("stage1", []),
                result.get("stage2", []),
                result
            )
            
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Stream failed for {conversation_id}: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
