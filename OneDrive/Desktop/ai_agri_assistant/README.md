# AI Agriculture Assistant (Unified)

A premium AI-powered assistant for farmers, featuring a unified FastAPI backend and a React/Vite frontend.

## 🚀 Architecture

The project has been unified into a simplified, modular structure for easy deployment on free platforms like **Render** and **Vercel**.

- **Frontend**: React + Vite + TailwindCSS (Optimized for Vercel/Netlify)
- **Backend**: FastAPI (Unified app with NLU, RAG, and LLM Orchestration)
- **Database**: SQLite (Local file-based knowledge base)
- **LLM**: Groq (Llama 3) for fast response generation

## 📂 Folder Structure

```
ai_agri_assistant/
├── backend/
│   ├── app/
│   │   ├── main.py          # Entry point & Routes
│   │   ├── config.py        # Environment settings
│   │   ├── services/        # Modular service logic
│   │   │   ├── orchestrator.py
│   │   │   ├── nlu.py
│   │   │   ├── rag.py
│   │   │   └── llm.py
│   │   └── utils/           # Formatting utilities
│   ├── data/
│   │   └── agri_knowledge.db # SQLite KB
│   └── requirements.txt
├── frontend/
│   ├── src/                 # React source code
│   └── package.json
└── .env                     # Groq API Key
```

## 🛠️ Local Setup

### Backend
1. `cd backend`
2. `pip install -r requirements.txt`
3. Create `.env` in the root with `GROQ_API_KEY=your_key_here`
4. `uvicorn app.main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## 🌍 Deployment

### Backend (Render - Free Tier)
1. Push this project to GitHub.
2. Create a new **Web Service** on Render.
3. Root Directory: `backend`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables:
   - `GROQ_API_KEY`: Your Groq API Key
   - `PYTHON_VERSION`: 3.10 or higher

### Frontend (Vercel)
1. Push to GitHub.
2. Link the `frontend` directory to a new Vercel project.
3. Framework Preset: `Vite`
4. Root Directory: `frontend`

---
Made with ❤️ for Indian Farmers.
