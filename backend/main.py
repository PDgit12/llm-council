"""FastAPI backend for LLM Council."""

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio
import os
import shutil

import storage
from council import run_full_council, generate_conversation_title, stage1_collect_responses, stage2_collect_rankings, stage3_synthesize_final, calculate_aggregate_rankings

app = FastAPI(title="LLM Council API")

# Ensure upload directory exists
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount uploads for serving
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Enable CORS for local development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://llm-council-alpha-pied.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to the server."""
    file_id = str(uuid.uuid4())
    # Keep original extension if possible
    ext = os.path.splitext(file.filename)[1]
    if not ext:
        ext = ""
    
    filename = f"{file_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {
        "id": file_id,
        "filename": file.filename,
        "path": f"/uploads/{filename}",
        "full_path": os.path.abspath(file_path),
        "content_type": file.content_type
    }


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str
    attachments: Optional[List[Dict[str, Any]]] = None


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class TestCase(BaseModel):
    """A test case for prompt optimization."""
    id: Optional[str] = None
    input: str
    expected: str


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]
    test_cases: List[TestCase] = []


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a specific conversation."""
    success = storage.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "ok"}


@app.post("/api/conversations/{conversation_id}/test-cases", response_model=TestCase)
async def add_test_case(conversation_id: str, test_case: TestCase):
    """Add a test case to a conversation."""
    try:
        new_test_case = storage.add_test_case(conversation_id, test_case.input, test_case.expected)
        return new_test_case
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/conversations/{conversation_id}/test-cases/{test_case_id}")
async def delete_test_case(conversation_id: str, test_case_id: str):
    """Delete a test case from a conversation."""
    success = storage.delete_test_case(conversation_id, test_case_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test case or conversation not found")
    return {"status": "ok"}


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get history (previous messages)
    history = conversation["messages"]

    # Check if this is the first message
    is_first_message = len(history) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content, attachments=request.attachments)

    # If this is the first message, generate a title
    if is_first_message:
        try:
            # Don't let title generation fail the request
            title = await generate_conversation_title(request.content)
            storage.update_conversation_title(conversation_id, title)
        except Exception as e:
            print(f"Title generation failed: {e}")

    # Run the 3-stage council process with history and test cases
    test_cases = conversation.get("test_cases", [])
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content, history=history, attachments=request.attachments, test_cases=test_cases
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            # Get history (previous messages) before adding the new one
            history = conversation["messages"]
            
            # Add user message
            storage.add_user_message(conversation_id, request.content, attachments=request.attachments)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Stage 1: Collect responses
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            test_cases = conversation.get("test_cases", [])
            is_lab_mode = len(test_cases) > 0
            
            stage1_results = await stage1_collect_responses(
                request.content, 
                history=history, 
                attachments=request.attachments,
                is_lab_mode=is_lab_mode
            )
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(
                request.content, 
                stage1_results, 
                history=history,
                test_cases=test_cases
            )
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(
                request.content, 
                stage1_results, 
                stage2_results, 
                history=history,
                is_lab_mode=is_lab_mode
            )
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )



@app.get("/debug/openrouter")
async def debug_openrouter():
    """Test OpenRouter connection and return result."""
    import os
    import sys
    
    try:
        from openai import AsyncOpenAI
    except ImportError as e:
        import subprocess
        try:
            installed_packages = subprocess.check_output([sys.executable, "-m", "pip", "list"]).decode()
        except Exception as pip_err:
            installed_packages = f"Failed to list packages: {str(pip_err)}"
            
        try:
            current_files = os.listdir(".")
        except Exception as fs_err:
            current_files = f"Failed to list files: {str(fs_err)}"
            
        return {
            "status": "error", 
            "message": f"Failed to import openai: {str(e)}",
            "debug_info": {
                "sys_path": sys.path,
                "sys_executable": sys.executable,
                "current_working_directory": os.getcwd(),
                "directory_contents": current_files,
                "installed_packages": installed_packages
            }
        }

    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        # Check if key exists and has content
        if not api_key:
            return {
                "status": "error", 
                "message": "OPENROUTER_API_KEY is missing or empty",
                "env_vars_present": list(os.environ.keys())
            }
        
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        completion = await client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://llm-council.vercel.app",
                "X-Title": "LLM Council Debug",
            },
            model="google/gemini-2.0-flash-lite-preview-02-05:free",
            messages=[{"role": "user", "content": "Say hello"}]
        )
        return {
            "status": "success", 
            "response": completion.choices[0].message.content,
            "key_length": len(api_key),
            "key_prefix": api_key[:5] if len(api_key) > 5 else "SHORT",
            "python_version": sys.version
        }
    except Exception as e:
        import traceback
        return {
            "status": "error", 
            "message": str(e), 
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
