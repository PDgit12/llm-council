"""OpenRouter API client for making LLM requests."""

import httpx
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL, GOOGLE_API_KEY, MODEL_TIMEOUT

# Configure Google SDK if key is present
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

async def query_model_direct_google(
    model_name: str,
    messages: List[Dict[str, str]],
    timeout: float = MODEL_TIMEOUT
) -> Optional[Dict[str, Any]]:
    """Query Google Gemini API directly using the SDK with retries."""
    import asyncio
    import PIL.Image
    import os
    
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
            # simple import check
            import google.generativeai as genai
            
            model = genai.GenerativeModel(model_name)
            
            # Convert messages to Gemini history format and handle images
            gemini_history = []
            
            # Helper to load image if path exists
            def load_image(path):
                # Remove leading /uploads/ or / if present to get relative path from root
                clean_path = path.lstrip('/')
                if clean_path.startswith('uploads/'):
                    clean_path = os.path.join('data', clean_path)
                elif not clean_path.startswith('data/'):
                    clean_path = os.path.join('data/uploads', os.path.basename(path))
                
                if os.path.exists(clean_path):
                    return PIL.Image.open(clean_path)
                return None

            # Process history (excluding last message)
            for msg in messages[:-1]:
                role = 'user' if msg['role'] == 'user' else 'model'
                parts = [msg['content']]
                
                # Check for attachments in history messages
                if 'attachments' in msg and msg['attachments']:
                    for att in msg['attachments']:
                        if att.get('content_type', '').startswith('image/'):
                            img = load_image(att['path'])
                            if img:
                                parts.append(img)
                                
                gemini_history.append({'role': role, 'parts': parts})
            
            # Process current message
            last_msg = messages[-1]
            current_parts = [last_msg['content']]
            if 'attachments' in last_msg and last_msg['attachments']:
                for att in last_msg['attachments']:
                    if att.get('content_type', '').startswith('image/'):
                        img = load_image(att['path'])
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
    messages: List[Dict[str, str]],
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
    }
    payload = {
        "model": model,
        "messages": messages,
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
            message = data['choices'][0]['message']
            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }
    except Exception as e:
        print(f"Error querying model {model} via OpenRouter: {e}")
        return None

async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """Query multiple models in parallel with staggered starts to avoid rate limits."""
    import asyncio
    import random
    
    async def delayed_query(model, msgs, delay):
        if delay > 0:
            await asyncio.sleep(delay)
        return await query_model(model, msgs)

    # Stagger requests by 0.5 to 1.5 seconds to avoid hitting "Requests per minute" burst limits
    tasks = []
    for i, model in enumerate(models):
        # First model runs immediately, others stagger
        delay = 0 if i == 0 else (i * 1.5) + random.uniform(0, 0.5)
        tasks.append(delayed_query(model, messages, delay))
    
    responses = await asyncio.gather(*tasks)
    return {model: response for model, response in zip(models, responses)}
