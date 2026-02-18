"""FastAPI backend for Parallels — Cross-Domain Analogy Engine."""

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from typing import List, Dict, Any, Optional
from collections import defaultdict
import asyncio
import uuid
import json
import time
import os

from council import (
    generate_conversation_title, run_analogy_pipeline, select_domains
)
import storage
from config import (
    RATE_LIMIT_GLOBAL, RATE_LIMIT_MESSAGE, RATE_LIMIT_UPLOAD,
    MAX_MESSAGE_LENGTH, MAX_UPLOAD_SIZE, ALLOWED_UPLOAD_TYPES,
    MAX_CONVERSATIONS, FIREBASE_PROJECT_ID
)
import re

app = FastAPI(title="Parallels API", description="Cross-Domain Analogy Engine")

# Serve uploaded files statically
os.makedirs("data/uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

# ── CORS CONFIGURATION ──
# We allow localhost for development and specific project subdomains for production/previews.
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

# Construct a restrictive regex for preview URLs.
# Avoid broad wildcards like '.*' on shared domains (web.app, onrender.com)
# to prevent cross-origin attacks from other users' sites.
cors_regex_parts = []
if FIREBASE_PROJECT_ID:
    safe_id = re.escape(FIREBASE_PROJECT_ID)
    cors_regex_parts.append(fr"https://{safe_id}(--.*)?\.web\.app")
    cors_regex_parts.append(fr"https://{safe_id}(--.*)?\.firebaseapp\.com")

# Allow specific Render project subdomains
cors_regex_parts.append(r"https://parallels-[a-z0-9-]+\.onrender\.com")

# Combine parts into a single regex string
allow_origin_regex = "|".join(cors_regex_parts) if cors_regex_parts else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


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


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def check_rate_limit(request: Request, category: str, limit: int):
    """Raise 429 if rate limit exceeded."""
    ip = get_client_ip(request)
    if not rate_limiter.is_allowed(ip, category, limit):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in a moment."
        )


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
    print(f"[ERROR] Unhandled exception: {exc}")
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

@app.post("/api/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
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
    with open(filepath, 'wb') as f:
        f.write(content)

    return {
        "filename": filename,
        "path": f"/uploads/{filename}",
        "content_type": file.content_type,
        "size": len(content)
    }


# ── Conversations ──

@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations(request: Request):
    """List all conversations (metadata only)."""
    check_rate_limit(request, "global", RATE_LIMIT_GLOBAL)
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: Request, body: CreateConversationRequest):
    """Create a new exploration."""
    check_rate_limit(request, "global", RATE_LIMIT_GLOBAL)

    existing = storage.list_conversations()
    if len(existing) >= MAX_CONVERSATIONS:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum of {MAX_CONVERSATIONS} explorations reached. Please delete old ones."
        )

    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(request: Request, conversation_id: str):
    """Get a specific exploration with all its messages."""
    check_rate_limit(request, "global", RATE_LIMIT_GLOBAL)
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Exploration not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(request: Request, conversation_id: str):
    """Delete a specific exploration."""
    check_rate_limit(request, "global", RATE_LIMIT_GLOBAL)
    success = storage.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Exploration not found")
    return {"status": "ok"}


# ── Message Sending — runs the 4-stage analogy pipeline ──

@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(request: Request, conversation_id: str, body: SendMessageRequest):
    """Send a message and stream the 4-stage analogy pipeline via SSE."""
    check_rate_limit(request, "message", RATE_LIMIT_MESSAGE)

    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Exploration not found")

    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            history = conversation["messages"]
            storage.add_user_message(conversation_id, body.content, attachments=body.attachments)

            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(body.content))

            # Yield start event
            yield f"data: {json.dumps({'type': 'council_start', 'message': 'The Council is convening...'})}\n\n"
            
            # Execute the full Council Flow
            # Note: This awaits the entire flow. Future improvement: stream internal orchestrator events.
            result = await run_analogy_pipeline(
                body.content, 
                history, 
                target_domain=body.target_domain,
                attachments=body.attachments
            )
            
            # Yield the final result
            yield f"data: {json.dumps({'type': 'council_complete', 'data': result})}\n\n"

            # Title detection (if needed)
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save to storage (Adapting to new format)
            # The 'result' contains 'stages' and 'final_answer'. 
            # We map this to the storage schema.
            # stage2_results -> result['stages']['stage2'] (Grounding)
            # stage3_results -> result['stages']['stage3'] (Technical)
            # final_answer -> result['final_answer']
            
            # Mocking the old structure for storage compatibility if needed, 
            # OR we should update storage.add_assistant_message to handle the new structure.
            # For now, let's pass empty lists for the old distinct stages and put everything in the content 
            # or rely on a new storage method. 
            # Let's assume storage can handle generic blobs or we just save the final answer.
            
            storage.add_assistant_message(
                conversation_id, 
                [], # Old explorations
                [], # Old evaluations
                result.get("final_answer", "")
            )
            
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            print(f"[ERROR] Stream failed for {conversation_id}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred while processing your request. Please try again.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
