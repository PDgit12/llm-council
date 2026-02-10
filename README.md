# LLM Council: Prompt Lab

**LLM Council** is a high-performance deliberation engine evolved into a **Prompt Lab**—a specialized environment for autonomous prompt optimization and test-driven validation. 

Instead of relying on single-model outputs or manual "vibe checks," Prompt Lab uses a multi-stage consensus algorithm to generate, benchmark, and synthesize the mathematically optimal prompt for any given task.

---

## 🏛️ The 3-Stage Deliberation Engine

The core of LLM Council is its unique **3-Stage Pipeline**, designed to eliminate hallucinations and model bias through peer-vetted research.

### **Stage 1: Parallel Strategy Ideation**
The "Council" (a diverse mix of state-of-the-art models like Gemini 2.0/Gema/Flash) generates divergent engineering strategies for your task simultaneously. This provides a wide range of creative and logical approaches in seconds.

### **Stage 2: Test-Driven Validation & Peer Review**
Generated prompt variations are programmatically benchmarked against your **Test Cases** (Input/Expected Output pairs). Models then perform a "Blind Critique" of each other's performance, ranking them based on reliability, format adherence, and edge-case robustness.

### **Stage 3: Autonomous Synthesis (The Chairman)**
A specialized "Chairman" model reviews the original requirements, the cross-model evaluations, and the benchmark data. It merges the strongest elements of every strategy into a final **Master Prompt**—optimized for immediate production use.

---

## 🛠️ Key Features

- **Prompt Optimization Mode**: Add ground-truth test cases to automatically evolve your instructions.
- **Lightning Consensus**: Optimized with parallel asynchrony for full deliberation in under 20 seconds.
- **Bias-Free Ranking**: Anonymized peer review prevents models from prioritizing their own brand patterns.
- **Hybrid Storage**: Portable JSON-based persistent storage for tasks, test cases, and council history.
- **Transparency**: Deep-dive into raw critiques to understand precisely why one strategy outperformed another.

---

## 🚀 Quick Start

### Backend
1. Create a `.env` file with your `OPENROUTER_API_KEY` and `GOOGLE_API_KEY`.
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Start the server: `python -m backend.main`

### Frontend
1. Install dependencies: `npm install`
2. Run development server: `npm run dev`

---

## 🏗️ Architecture

- **Engine**: FastAPI (Python 3.10+)
- **Logic**: Async Parallel Orchestration (LLM-in-the-loop)
- **Frontend**: React + Vite
- **Styling**: Vanilla CSS (Modern Premium Aesthetic)
- **Data**: Local JSON Storage

---

*Built for high-density, vetted responses. Developed by Piyush Dua.*
