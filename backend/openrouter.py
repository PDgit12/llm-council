"""OpenRouter API client for making LLM requests."""

import os
import asyncio
import httpx
import PIL.Image
import google.generativeai as genai
import asyncio
import os
import PIL.Image
from typing import List, Dict, Any, Optional
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL, GOOGLE_API_KEY, MODEL_TIMEOUT

# Configure Google SDK if key is present
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def _load_local_image(path: str) -> Optional[PIL.Image.Image]:
    """Helper to load image if path exists."""
    # Remove leading /uploads/ or / if present to get relative path from root
    clean_path = path.lstrip('/')
    if clean_path.startswith('uploads/'):
        clean_path = os.path.join('data', clean_path)
    elif not clean_path.startswith('data/'):
        clean_path = os.path.join('data/uploads', os.path.basename(path))

    try:
        # Resolve absolute paths to prevent traversal
        abs_path = os.path.abspath(clean_path)
        data_dir = os.path.abspath('data')

        # Security check: Ensure path is within data directory
        if os.path.commonpath([data_dir, abs_path]) != data_dir:
            return None

        if os.path.exists(abs_path):
            return PIL.Image.open(abs_path)
    except Exception:
        pass

    return None

async def query_model_direct_google(
    model_name: str,
    messages: List[Dict[str, Any]],
    timeout: float = MODEL_TIMEOUT
) -> Optional[Dict[str, Any]]:
    """Query Google Gemini API directly using the SDK with retries."""
    
    # Extract name after 'google/' if present
    if model_name.startswith("google/"):
        model_name = model_name.replace("google/", "")
    
    # Strip ':free' suffix if present (used for OpenRouter)
    if model_name.endswith(":free"):
        model_name = model_name.replace(":free", "")
    
    # Retry configuration
    max_retries = 3
    base_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction
            )
            
            # Filter out system messages for the conversation history
            conv_messages = [m for m in messages if m.get('role') != 'system']
            
            # Convert messages to Gemini history format and handle images
            gemini_history = []

            # Convert messages to Gemini history format
            gemini_history = []

            # Process history (excluding last message)
            for msg in conv_messages[:-1]:
                role = 'user' if msg['role'] == 'user' else 'model'
                parts = [msg['content']]
                
                # Check for attachments in history messages
                if 'attachments' in msg and msg['attachments']:
                    for att in msg['attachments']:
                        if att.get('content_type', '').startswith('image/'):
                            img = _load_local_image(att['path'])
                            if img:
                                parts.append(img)
                                
                gemini_history.append({'role': role, 'parts': parts})
            
            # Process current message (last one)
            last_msg = conv_messages[-1]
            current_parts = [last_msg['content']]
            if 'attachments' in last_msg and last_msg['attachments']:
                for att in last_msg['attachments']:
                    if att.get('content_type', '').startswith('image/'):
                        img = _load_local_image(att['path'])
                        if img:
                            current_parts.append(img)
            
            # Generate
            chat = model.start_chat(history=gemini_history)
            response = await asyncio.wait_for(chat.send_message_async(current_parts), timeout=timeout)
            
            return {
                'content': response.text,
                'reasoning_details': None
            }
            
        except Exception as e:
            error_str = str(e).lower()
            # Check for rate limit / quota errors
            if "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # 2s, 4s, 8s
                    print(f"Rate limit hit for {model_name}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
            
            print(f"Error querying Google model {model_name} (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None
    return None

async def query_model(
    model: str,
    messages: List[Dict[str, Any]],
    timeout: float = MODEL_TIMEOUT
) -> Optional[Dict[str, Any]]:
    """
    Query a single model. Prioritizes direct Google API if applicable.
    """
    # Check if we should use direct Google integration
    is_google_model = (
        model.startswith("google/") or 
        model.startswith("gemini-") or 
        model.startswith("gemma-") or
        model.startswith("models/") or
        model.startswith("deep-research-")
    )
    
    if GOOGLE_API_KEY and is_google_model:
        result = await query_model_direct_google(model, messages, timeout=timeout)
        if result:
            return result

    # OpenRouter fallback
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://llm-council.local", # Optional, for including your app on openrouter.ai rankings.
        "X-Title": "LLM Council", # Optional. Shows in rankings on openrouter.ai.
    }

    # Clean messages for OpenRouter (remove attachments/images if not supported directly via URL or base64)
    # OpenRouter generally supports image URLs in content blocks for vision models.
    # For simplicity, we'll just extract text unless we implement full image handling for OpenRouter.
    clean_messages = []
    for m in messages:
        content = m.get('content', '')
        # If attachments exist but we aren't handling them for OpenRouter yet, warn or ignore.
        # Ideally, we'd upload them somewhere or convert to base64 data URLs.
        clean_messages.append({"role": m['role'], "content": content})

    payload = {
        "model": model,
        "messages": clean_messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                message = data['choices'][0]['message']
                return {
                    'content': message.get('content'),
                    'reasoning_details': message.get('reasoning_details') # Some models return reasoning
                }
            else:
                print(f"⚠️ Unexpected response structure from OpenRouter for {model}: {data}")
                return None

    except Exception as e:
        print(f"⚠️ Error querying {model}: {e}")
        
        # Check for defined fallback
        # Import inside function to avoid potential circular import issues if config imports this module (though currently it doesn't)
        from config import MODEL_FALLBACKS
        if model in MODEL_FALLBACKS:
            backup_model = MODEL_FALLBACKS[model]
            # Avoid infinite recursion if backup is same as primary
            if backup_model == model:
                print(f"⚠️ Backup model is same as primary ({model}). Skipping fallback.")
                return None

            print(f"🔄 Switching to BACKUP model: {backup_model}")
            try:
                # Recursive call with the backup model
                return await query_model(backup_model, messages, timeout=timeout)
            except Exception as backup_e:
                print(f"❌ Backup {backup_model} also failed: {backup_e}")
                
        return None

async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, Any]],
    model_messages: Dict[str, List[Dict[str, Any]]] = None
) -> Dict[str, Optional[Dict[str, Any]]]:
    """Query multiple models in parallel with staggered starts to avoid rate limits.
    
    Args:
        models: List of model identifiers
        messages: Default messages for all models (can be None if model_messages provided)
        model_messages: Optional dict mapping model -> custom messages (for lens personas)
    """
    import random
    
    async def delayed_query(model, msgs, delay):
        if delay > 0:
            await asyncio.sleep(delay)
        return await query_model(model, msgs)

    # Stagger requests slightly to avoid hitting strict "burst" limits, but keep it fast.
    tasks = []
    for i, model in enumerate(models):
        # Use per-model messages if available, otherwise default
        msgs = model_messages.get(model, messages) if model_messages else messages
        # First model runs immediately, others stagger slightly (200ms)
        delay = 0 if i == 0 else (i * 0.2) + random.uniform(0, 0.1)
        tasks.append(delayed_query(model, msgs, delay))
    
    responses = await asyncio.gather(*tasks)
    return {model: response for model, response in zip(models, responses)}
