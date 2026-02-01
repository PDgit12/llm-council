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
    """Query Google Gemini API directly using the SDK."""
    try:
        # Extract name after 'google/' if present
        if model_name.startswith("google/"):
            model_name = model_name.replace("google/", "")
        
        # Strip ':free' suffix if present (used for OpenRouter)
        if model_name.endswith(":free"):
            model_name = model_name.replace(":free", "")
        
        # Convert messages to Gemini format
        # For multi-turn, we can use the chat session if we want, but for now
        # let's just pass the messages list if the SDK supports it, or format as string.
        # Actually, the genai SDK has a ChatSession.
        model = genai.GenerativeModel(model_name)
        
        # Simple conversion for generating content from history
        # Gemini SDK takes a list of {'role': 'user'|'model', 'parts': [str]}
        gemini_history = []
        for msg in messages[:-1]:
            role = 'user' if msg['role'] == 'user' else 'model'
            gemini_history.append({'role': role, 'parts': [msg['content']]})
        
        import asyncio
        chat = model.start_chat(history=gemini_history)
        # Apply timeout to the async call
        response = await asyncio.wait_for(chat.send_message_async(messages[-1]['content']), timeout=timeout)
        
        return {
            'content': response.text,
            'reasoning_details': None
        }
    except Exception as e:
        print(f"Error querying Google model {model_name} directly: {e}")
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
    if GOOGLE_API_KEY and (model.startswith("google/gemini") or model.startswith("google/gemma")):
        result = await query_model_direct_google(model, messages, timeout=timeout)
        if result:
            return result
        # Fallback to OpenRouter if direct fails (maybe the key is invalid or model not supported)

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
    """Query multiple models in parallel."""
    import asyncio
    tasks = [query_model(model, messages) for model in models]
    responses = await asyncio.gather(*tasks)
    return {model: response for model, response in zip(models, responses)}
