"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Council members - list of model identifiers
# Using high-quality preview models available to the user
# Council members - list of model identifiers
# Using ONLY verified working models (others hit 429 Quota limits)
COUNCIL_MODELS = [
    "gemini-3-flash-preview", 
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemma-3-27b-it",
]

# Models specifically for Stage 2 (Peer Ranking) - we use fast models
STAGE2_MODELS = [
    "gemini-2.5-flash-lite",
]

# Chairman model - synthesizes final response (Using 3-flash as 3-pro hit quota limit)
CHAIRMAN_MODEL = "gemini-3-flash-preview"

# Model for fast title generation
TITLE_MODEL = "gemini-2.5-flash-lite"

# Global timeout for any single model request (seconds)
MODEL_TIMEOUT = 20.0

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
