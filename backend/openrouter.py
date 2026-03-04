import httpx
import asyncio
import random
import json
import os
import logging
from google import genai
from google.genai import types
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL, GOOGLE_API_KEY, MODEL_TIMEOUT
import pypdf

logger = logging.getLogger(__name__)

# Initialize Google Client if key is present
google_client = None
if GOOGLE_API_KEY:
    google_client = genai.Client(api_key=GOOGLE_API_KEY)

# Global cache to prevent redundant PDF extraction during parallel runs
_pdf_text_cache = {}

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using pypdf, with caching."""
    if pdf_path in _pdf_text_cache:
        return _pdf_text_cache[pdf_path]
        
    try:
        text = ""
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        extracted = text.strip()
        _pdf_text_cache[pdf_path] = extracted
        return extracted
    except Exception as e:
        print(f"⚠️ PDF Extraction failed: {e}")
        return ""

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
    """Query Google Gemini API directly using the new google-genai SDK."""
    import asyncio
    import os
    
    if not google_client:
        return None

    # Extract name after 'google/' if present
    if model_name.startswith("google/"):
        model_name = model_name.replace("google/", "")
    
    # Strip ':free' suffix if present (used for OpenRouter)
    if model_name.endswith(":free"):
        model_name = model_name.replace(":free", "")
    
    # Reduced retries for faster fallback
    max_retries = 2
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Separate system instruction from history
            system_instruction = next((m['content'] for m in messages if m.get('role') == 'system'), None)
            
            # Convert messages to Gemini Content types
            contents = []
            conv_messages = [m for m in messages if m.get('role') != 'system']
            
            for msg in conv_messages:
                role = 'user' if msg['role'] == 'user' else 'model'
                parts = [types.Part.from_text(text=msg['content'])]
                
                # Handle attachments if any
                if 'attachments' in msg and msg['attachments']:
                    for att in msg['attachments']:
                        if att.get('content_type', '').startswith('image/'):
                            # For the new SDK, we'll need to read the file
                            path = att['path'].lstrip('/')
                            if path.startswith('uploads/'):
                                path = os.path.join('data', path)
                            elif not path.startswith('data/'):
                                path = os.path.join('data/uploads', os.path.basename(att['path']))
                            
                            if os.path.exists(path):
                                with open(path, 'rb') as f:
                                    image_data = f.read()
                                    parts.append(types.Part.from_bytes(
                                        data=image_data,
                                        mime_type=att['content_type']
                                    ))
                        elif att.get('content_type') == 'application/pdf':
                            path = att['path'].lstrip('/')
                            if path.startswith('uploads/'):
                                path = os.path.join('data', path)
                            elif not path.startswith('data/'):
                                path = os.path.join('data/uploads', os.path.basename(att['path']))
                            
                            if os.path.exists(path):
                                with open(path, 'rb') as f:
                                    pdf_data = f.read()
                                    parts.append(types.Part.from_bytes(
                                        data=pdf_data,
                                        mime_type='application/pdf'
                                    ))
                
                contents.append(types.Content(role=role, parts=parts))

            # Generate
            # Note: The new SDK uses a synchronous-looking call that can be run in a thread or 
            # if using the async client, we'd use client.aio.models.generate_content
            
            response = await google_client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                )
            )
            
            return {
                'content': response.text,
                'reasoning_details': None # Some models might have this, but for now None
            }
            
        except Exception as e:
            error_str = str(e).lower()
            
            # IMMEDIATE FALLBACK: If API is disabled or forbidden, don't retry.
            if any(x in error_str for x in ["permission_denied", "forbidden", "api has not been used", "403"]):
                print(f"Direct Google API unavailable (Permission Denied/403). Falling back to OpenRouter.")
                return None

            # Check for rate limit / quota errors
            if any(x in error_str for x in ["429", "quota", "resource_exhausted"]):
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
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
    timeout: float = MODEL_TIMEOUT,
    _tried_models: set = None,
    on_activity: callable = None
) -> Optional[Dict[str, Any]]:
    """
    Query a single model with fallback support and activity hooks.
    """
    if on_activity:
        asyncio.create_task(on_activity(model, "started"))

    if _tried_models is None:
        _tried_models = set()
    
    if model in _tried_models:
        print(f"🛑 Cycle detected or model already failed: {model}. Aborting fallback chain.")
        return None
    
    _tried_models.add(model)

    # 1. Try Direct Google Integration if applicable
    is_google_model = any(model.startswith(prefix) for prefix in ["google/", "gemini-", "gemma-", "models/", "deep-research-"])
    
    if GOOGLE_API_KEY and is_google_model:
        try:
            result = await query_model_direct_google(model, messages, timeout=timeout)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ Direct Google API failed for {model}: {e}. Proceeding to OpenRouter.")

    # 2. Try OpenRouter
    import base64
    import os
    
    # Pre-process attachments: extract text from PDFs for OpenRouter grounding
    pdf_texts = []
    processed_attachments = []
    
    attachments = messages[0].get('attachments', []) if messages else []
    
    for att in attachments:
        if att.get('content_type') == 'application/pdf':
            path = att['path'].lstrip('/')
            if path.startswith('uploads/'):
                path = os.path.join('data', path)
            elif not path.startswith('data/'):
                path = os.path.join('data/uploads', os.path.basename(att['path']))
            
            if os.path.exists(path):
                text = extract_text_from_pdf(path)
                if text:
                    pdf_texts.append(f"--- ATTACHMENT: {att.get('name', 'PDF')} ---\n{text}\n")
        else:
            processed_attachments.append(att)

    formatted_messages = []
    for i, msg in enumerate(messages):
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        # Only use processed_attachments (images) for OpenRouter multi-modal
        # pdf_texts will be prepended to the FIRST user message
        msg_attachments = msg.get('attachments', [])
        
        # If it's the first user message and we have PDF text, prepend it
        if role == 'user' and pdf_texts and i == 0:
            grounding_context = "\n".join(pdf_texts)
            content = f"USE THE FOLLOWING DATA SOURCE FOR YOUR RESPONSE:\n\n{grounding_context}\n\nUSER QUESTION: {content}"

        current_attachments = [a for a in msg_attachments if a.get('content_type', '').startswith('image/')]
        
        if not current_attachments:
            formatted_messages.append({"role": role, "content": content})
        else:
            # Multi-modal content format for images
            content_list = [{"type": "text", "text": content}]
            for att in current_attachments:
                path = att['path'].lstrip('/')
                if path.startswith('uploads/'):
                    path = os.path.join('data', path)
                elif not path.startswith('data/'):
                    path = os.path.join('data/uploads', os.path.basename(att['path']))
                
                if os.path.exists(path):
                    try:
                        with open(path, 'rb') as f:
                            b64_data = base64.b64encode(f.read()).decode('utf-8')
                            content_list.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{att['content_type']};base64,{b64_data}"
                                }
                            })
                    except Exception as e:
                        print(f"⚠️ Failed to read image for OpenRouter: {e}")
            
            formatted_messages.append({"role": role, "content": content_list})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://llm-council.vercel.app",
        "X-Title": "LLM Council",
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
        "messages": formatted_messages,
    }

    # Exponential Backoff for OpenRouter 429s (Rate Limits)
    max_retries = 3
    base_delay = 1.0 # seconds
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload
                )
                
                # Check for rate limit (429) - Retry with backoff
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        import random
                        # Jittered exponential backoff: (base * 2^attempt) + small random jitter
                        delay = (base_delay * (2 ** attempt)) + (random.random() * 0.5)
                        print(f"🚫 OpenRouter 429 hit for {model}. Retry {attempt+1}/{max_retries} in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"🛑 Max retries reached for {model} (Rate Limit).")
                        raise httpx.HTTPStatusError("Max retries for rate limit", request=response.request, response=response)
                
                response.raise_for_status()
                data = response.json()
                
                if 'choices' not in data or not data['choices']:
                    raise ValueError(f"Unexpected response format for {model}")
                    
                message = data['choices'][0]['message']
                res = {
                    'content': message.get('content'),
                    'reasoning_details': message.get('reasoning_details'),
                    'usage': data.get('usage'),
                    'finish_reason': data['choices'][0].get('finish_reason')
                }
                
                if on_activity:
                    asyncio.create_task(on_activity(model, "completed"))
                return res
                
        except httpx.HTTPStatusError as e:
            # Catch 402/403/400 explicitly to trigger immediate fallback without retries
            status_code = e.response.status_code if e.response else 0
            print(f"⚠️ API Error {status_code} for {model}: {e}")
            
            if status_code in [400, 402, 403]:
                # 400: Bad Request (often model specific)
                # 402: Payment Required (Free tier exhausted)
                # 403: Forbidden (Geo-block or key issue)
                print(f"⛔ Blocking error {status_code} for {model}. Triggering fallback immediately.")
                break # Break retry loop to go to tier fallback
            
            # For 429 or 5xx, we might retry (handled by loop), else break
            if attempt < max_retries - 1 and status_code not in [404]:
                await asyncio.sleep(0.5)
                continue
            break
            
        except httpx.RequestError as e:
            print(f"⚠️ Network error for {model} (Attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
                continue
            break
        except Exception as e:
            print(f"❌ Critical error querying {model}: {e}")
            break
        
        print(f"⚠️ Error querying {model}: {e}")
        
        # 3. ADVANCED FALLBACK: Try another model in the same TIER
        from .config import MODEL_TIER_MAP, MODELS_GENERAL, MODELS_TECHNICAL, MODELS_RESEARCH
        
        tier_name = MODEL_TIER_MAP.get(model)
        if tier_name:
            tier_list = []
            if tier_name == "general": tier_list = MODELS_GENERAL
            elif tier_name == "technical": tier_list = MODELS_TECHNICAL
            elif tier_name == "research": tier_list = MODELS_RESEARCH
            
            # Find the next available model in the tier that hasn't been tried
            for next_model in tier_list:
                if next_model not in _tried_models:
                    print(f"🔄 Tier Fallback ({tier_name}): Trying {next_model} next...")
                    return await query_model(next_model, messages, timeout=timeout, _tried_models=_tried_models, on_activity=on_activity)
        
        # 4. LEGACY FALLBACK: Check if there's a specific hardcoded backup
        from .config import MODEL_FALLBACKS
        if model in MODEL_FALLBACKS:
            backup_model = MODEL_FALLBACKS[model]
            if backup_model not in _tried_models:
                print(f"🔄 Hardcoded Fallback: Trying {backup_model}")
                return await query_model(backup_model, messages, timeout=timeout, _tried_models=_tried_models, on_activity=on_activity)
                
        return None

async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    model_messages: Dict[str, List[Dict[str, str]]] = None,
    yield_results: bool = False,
    on_activity: callable = None
) -> Any:
    """Query multiple models in parallel with staggered starts and timeouts."""
    
    # Pre-extract PDF text once for the entire batch
    attachments = (messages[0].get('attachments') or []) if messages else []
    for att in attachments:
        if att.get('content_type') == 'application/pdf':
            path = att['path'].lstrip('/')
            if path.startswith('uploads/'):
                path = os.path.join('data', path)
            elif not path.startswith('data/'):
                path = os.path.join('data/uploads', os.path.basename(att['path']))
            
            if os.path.exists(path):
                extract_text_from_pdf(path)

    async def protected_query(model, msgs, delay):
        if delay > 0:
            await asyncio.sleep(delay)
        
        if on_activity:
            await on_activity(model, "started")
            
        try:
            # 25s timeout for individual model queries in parallel stages
            # This prevents one stuck model from holding up the entire stage (e.g. Stage 2)
            res = await asyncio.wait_for(query_model(model, msgs, on_activity=on_activity), timeout=25.0)
            
            if on_activity:
                status = "completed" if res else "failed"
                await on_activity(model, status)
            return model, res
            
        except asyncio.TimeoutError:
            logger.warning(f"TIMEOUT: Model {model} took too long (>25s) in parallel phase.")
            if on_activity:
                await on_activity(model, "failed")
            return model, None
        except Exception as e:
            logger.error(f"ERROR: Model {model} failed in parallel phase: {e}")
            if on_activity:
                await on_activity(model, "failed")
            return model, None

    tasks = []
    for i, model in enumerate(models):
        msgs = model_messages.get(model, messages) if model_messages else messages
        delay = 0 if i == 0 else (i * 0.2) + random.uniform(0, 0.1)
        tasks.append(protected_query(model, msgs, delay))
    
    if yield_results:
        async def result_generator():
            if not tasks:
                return
            # as_completed yields futures as they finish
            for task in asyncio.as_completed(tasks):
                try:
                    yield await task
                except Exception as e:
                    logger.error(f"Error yielding parallel task: {e}")
                    yield None, None
        return result_generator()
    else:
        responses = await asyncio.gather(*tasks)
        # Filter out None results from timeouts/errors
        return {model: response for model, response in responses if response is not None}
