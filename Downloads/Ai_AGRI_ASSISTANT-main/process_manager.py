import subprocess
import time
import os
import sys

SERVICES = [
    {
        "name": "NLU",
        "cwd": "services/nlu_llm",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--port", "8002"],
        "env": {}
    },
    {
        "name": "RAG",
        "cwd": "services/rag_services",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--port", "8003"],
        "env": {"DB_PATH": os.path.abspath("services/chat_orchestrator/data/agri_knowledge.db")}
    },
    {
        "name": "LLM",
        "cwd": "services/llm-services",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--port", "8004"],
        "env": {}
    },
    {
        "name": "Orchestrator",
        "cwd": "services/chat_orchestrator",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
        "env": {
            "NLU_SERVICE_URL": "http://localhost:8002/analyze",
            "RAG_SERVICE_URL": "http://localhost:8003/query",
            "LLM_SERVICE_URL": "http://localhost:8004/generate",
            "DB_PATH": os.path.abspath("services/chat_orchestrator/data/agri_knowledge.db")
        }
    },
    {
        "name": "Gateway",
        "cwd": "services/api_gateway",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
        "env": {"CHAT_ORCHESTRATOR_URL": "http://localhost:8001"}
    }
]

processes = []

def start_services():
    for s in SERVICES:
        print(f"🚀 Starting {s['name']}...")
        env = os.environ.copy()
        env.update(s['env'])
        p = subprocess.Popen(
            s['cmd'],
            cwd=s['cwd'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append((s['name'], p))
        time.sleep(2) # Give it a moment

    print("\n✅ All services initiated. Checking status...")
    time.sleep(5)

    for name, p in processes:
        if p.poll() is None:
            print(f"🟢 {name} is running.")
        else:
            stdout, stderr = p.communicate()
            print(f"🔴 {name} FAILED to start.")
            print(f"Error: {stderr}")

if __name__ == "__main__":
    try:
        start_services()
        print("\nPress Ctrl+C to stop services (or wait for timeout)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        for name, p in processes:
            p.terminate()
