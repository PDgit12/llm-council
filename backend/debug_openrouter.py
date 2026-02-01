
import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load env vars from .env file if present, otherwise use process env
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
print(f"API Key present: {bool(OPENROUTER_API_KEY)}")
if OPENROUTER_API_KEY:
    print(f"API Key length: {len(OPENROUTER_API_KEY)}")
    print(f"API Key first 5 chars: {OPENROUTER_API_KEY[:5]}")
    print(f"API Key last 5 chars: {OPENROUTER_API_KEY[-5:]}")

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

async def test_connection():
    print("\nAttempting to connect to OpenRouter...")
    try:
        completion = await client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://llm-council.vercel.app",
                "X-Title": "LLM Council Debug",
            },
            model="google/gemini-2.0-flash-lite-preview-02-05:free",
            messages=[
                {
                    "role": "user",
                    "content": "Say hello in one word."
                }
            ]
        )
        print(f"Success! Response: {completion.choices[0].message.content}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
