# Lightning LLM Council

![llmcouncil](header.jpg)

**Lightning LLM Council** is a high-speed, 3-stage deliberation engine that uses a "Council of LLMs" to produce high-density, vetted responses. Instead of asking a single model, you get a consensus-driven answer that has been peer-reviewed and synthesized by multiple providers.

### Key Features
- **3-Stage Deliberation**: Collects responses, holds a peer-review ranking stage, and then synthesizes a final "collectively wise" answer.
- **Lightning Mode**: Optimized for speed (<20s deliberation) using Gemini Lite models and aggressive timeouts.
- **Multi-Turn Support**: Persistent conversation history so you can ask follow-up questions.
- **Conversation Management**: Easily delete and manage your councils from the sidebar.
- **Hybrid Deploy Ready**: Optimized configurations for Vercel (Frontend) and Render (Backend).

## Deployment Guide (One-Click Ready)

This project is designed for easy deployment using Vercel for the frontend and Render for the backend.

### 1. Backend (Render)
1.  Connect your repository to [Render.com](https://render.com).
2.  Set the **Root Directory** to `backend`.
3.  Add your API keys in the Render dashboard:
    - `GOOGLE_API_KEY`: Your Gemini API key.
    - `OPENROUTER_API_KEY`: Your OpenRouter key.
4.  Copy your Render service URL (e.g., `https://llm-council-backend.onrender.com`).

### 2. Frontend (Vercel)
1.  Import your repository into [Vercel.com](https://vercel.com).
2.  Set the **Root Directory** to `frontend`.
3.  Add an environment variable:
    - `VITE_API_URL`: Your Render URL from Step 1.
4.  Click **Deploy**!

## Local Development

### 1. Install Dependencies
**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Run Locally
```bash
./start.sh
```

## Tech Stack
- **Backend:** FastAPI (Python 3.10+), Async Google SDK, OpenRouter
- **Frontend:** React + Vite, Vanilla CSS
- **Storage:** Local JSON storage (mirrored to Render Disk in production)
