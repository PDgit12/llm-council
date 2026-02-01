"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Council members - list of model identifiers
# We use 'lite' versions and smaller models to minimize latency while maintaining quality.
COUNCIL_MODELS = [
    "google/gemini-2.0-flash-lite-preview-09-2025",
    "google/gemini-flash-lite-latest",
    "google/gemma-3-4b-it",
    "google/gemma-3-12b-it",
]

# Models specifically for Stage 2 (Peer Ranking) - we use only the fastest here
STAGE2_MODELS = [
    "google/gemini-2.0-flash-lite-preview-09-2025",
    "google/gemini-flash-lite-latest",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "google/gemini-2.0-flash"

# Model for fast title generation
TITLE_MODEL = "google/gemini-flash-lite-latest"

# Global timeout for any single model request (seconds)
MODEL_TIMEOUT = 20.0

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
