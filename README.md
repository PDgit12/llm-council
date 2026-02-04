# Lightning LLM Council

**Lightning LLM Council** is a high-speed, 3-stage deliberation engine that uses a "Council of LLMs" to produce high-density, vetted responses. Instead of asking a single model, you get a consensus-driven answer that has been peer-reviewed and synthesized by multiple providers.

### Key Features
- **3-Stage Deliberation**: Collects responses, holds a peer-review ranking stage, and then synthesizes a final "collectively wise" answer.
- **Lightning Mode**: Optimized for speed (<20s deliberation) using Gemini Lite models and aggressive timeouts.
- **Multi-Turn Support**: Persistent conversation history so you can ask follow-up questions.
- **Conversation Management**: Easily delete and manage your councils from the sidebar.
- **Hybrid Deploy Ready**: Optimized configurations for Vercel (Frontend) and Render (Backend).



## Tech Stack
- **Backend:** FastAPI (Python 3.10+), Async Google SDK, OpenRouter
- **Frontend:** React + Vite, Vanilla CSS
- **Storage:** Local JSON storage (mirrored to Render Disk in production)
