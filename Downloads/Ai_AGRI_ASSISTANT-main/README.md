# AI Agriculture Assistant 🌱

A production-ready, full-stack microservices-based system designed to assist farmers using state-of-the-art AI. The system leverages RAG (Retrieval-Augmented Generation) and Large Language Models (LLMs) to provide accurate, source-attributed agricultural advice.

---

## 📖 Description

The **AI Agriculture Assistant** is a comprehensive tool built to bridge the gap between complex agricultural knowledge and practical farming needs. By combining a verified Knowledge Base with advanced NLU (Natural Language Understanding), the assistant provides farmers with real-time insights into crop management, pest control, and soil health.

### Why it exists:
Farmers often face information overload or generic advice. This system provides **precise, context-aware answers** backed by a custom knowledge base, ensuring that the advice is both scientifically sound and practically applicable.

---

## ✨ Features

- **🧠 RAG + LLM Hybrid**: Combines the reasoning capabilities of Llama 3 with a private knowledge base (SQLite/Vector-like search).
- **🏗️ Microservices Architecture**: Decoupled services for NLU, RAG, LLM generation, and Chat Orchestration.
- **🔍 Source Attribution**: Clearly distinguishes between Knowledge Base facts and AI-generated insights.
- **🎨 Modern Dashboard**: A high-performance React dashboard styled with Tailwind CSS for a premium user experience.
- **🐳 Dockerized Deployment**: Easy setup using Docker Compose for consistent environments.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: React + Vite + Tailwind CSS
- **Database**: SQLite (Knowledge Base)
- **AI Model**: Llama 3 (via Groq API)
- **Containerization**: Docker & Docker Compose
- **Connectivity**: REST API Gateway

---

## 📐 Architecture Diagram

```ascii
      +-----------------+
      |   User Browser  |
      +--------+--------+
               | (HTTP/JSON)
      +--------v--------+
      |   API Gateway   | (Port 8000)
      +--------+--------+
               |
      +--------v------------+
      |  Chat Orchestrator  | (The "Brain")
      +--------+------------+
               |
    +----------+----------+----------------+
    |                     |                |
+---v---+           +-----v-----+    +-----v-----+
|  NLU  |           |    RAG    |    |    LLM    |
|Service|           |  Service  |    |  Service  |
+-------+           +-----------+    +-----------+
    |                     |                |
(Analyzes             (Queries DB)      (Generates
 Intent)                                Response)
```

---

## 🚀 Setup Instructions

Follow these steps to get the project running locally:

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-agriculture-assistant.git
cd ai-agriculture-assistant
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory based on `.env.example`:
```bash
cp .env.example .env
```
Add your **Groq API Key** to the `.env` file.

### 3. Run with Docker Compose
Ensure you have Docker and Docker Compose installed, then run:
```bash
docker-compose -f docker/docker-compose.yml up --build
```

### 4. Access the Dashboard
Once the services are up, open your browser and navigate to:
**[http://localhost:3000](http://localhost:3000)**

---

## 🧪 How RAG + LLM Works

1.  **Intent Analysis (NLU)**: The user's query is analyzed to understand the core agricultural question.
2.  **Knowledge Retrieval (RAG)**: The system searches the local SQLite database for relevant documents and facts.
3.  **Context Injection**: The retrieved facts are injected into the LLM prompt.
4.  **Generative Response**: The LLM (Llama 3) generates a natural language response using the provided facts, ensuring accuracy and reducing hallucinations.

---

## 🔮 Future Improvements

- 🎤 **Voice Input**: Multi-modal interaction for hands-free use in the field.
- 🌎 **Multi-language Support**: Localizing advice for different regional languages.
- 📸 **Image-based Detection**: Uploading leaf photos for instant disease diagnosis using vision models.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
