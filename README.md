An AI-powered agriculture assistant designed for Indian farmers, built with a production-grade microservices architecture.
The system follows a RAG-first, LLM-fallback strategy to ensure reliable, cost-effective, and explainable answers.

🧠 “Database se jankari mile to wahi do, warna LLM se intelligent jawab lao.”

##🚀 Key Highlights

✅ RAG-first architecture (LLM sirf tab jab data na mile)

✅ Free cloud LLM (Groq) – no OpenAI cost

✅ Dockerized microservices

✅ Circuit breaker + weak response detection

✅ Hinglish farmer-friendly responses

✅ Session-based chat history

✅ Production-ready backend design

##🏗️ System Architecture

 Client (UI / API)
      │
      ▼
API Gateway
      │
      ▼
Chat Orchestrator
  ├── NLU Service (Intent + Crop detection)
  ├── RAG Service (SQLite knowledge base)
  └── LLM Service (Groq Cloud)
         ├── Circuit Breaker
         ├── Prompt Guardrails
         └── Weak Response Filter

##🧩 Microservices Overview
Service	Responsibility
API Gateway	Single entry point, routing & CORS
Chat Orchestrator	Controls full conversation flow
NLU Service	Rule-based intent & crop detection
RAG Service	Knowledge lookup from SQLite DB
LLM Service	Groq LLM calls with safety controls

##🔁 Request Flow (RAG-First Logic)

User sends message

NLU → Detect intent & crop

RAG → Search local knowledge base

If data found → return RAG answer

Else → call LLM (Groq)

If LLM weak/fails → safe fallback response

Save full chat history

##🛠️ Tech Stack

Backend: FastAPI, Python

LLM: Groq (llama-3.1-8b-instant)

Database: SQLite (RAG)

Containerization: Docker, Docker Compose

Monitoring: Prometheus metrics

Testing: Pytest, HTTPX

Language: Hinglish (Hindi + English)

##📦 Project Structure
 backend/
└── services/
    ├── api_gateway/
    ├── chat_orchestrator/
    ├── nlu_llm/
    ├── rag_services/
    ├── llm-services/
    ├── docker-compose.yml
    └── .env


##🐳 Run with Docker (Recommended)
docker compose build
docker compose up -d

##Services will be available on:

API Gateway → http://localhost:8000

Swagger Docs → http://localhost:8000/docs

##🌱 Future Enhancements

🎤 Voice input/output (STT + TTS)

🌐 Frontend (Streamlit / React)

📄 PDF & Govt advisory ingestion (advanced RAG)

📊 Grafana dashboards

🌍 Multi-language support

##🏆 What This Project Demonstrates

Production-grade AI backend design

Microservices orchestration

Practical RAG implementation

Real-world debugging & cloud LLM usage

Scalable, interview-ready system

##👨‍💻 Author

Harsh Tripathi
AI / Backend / Applied LLM Systems
