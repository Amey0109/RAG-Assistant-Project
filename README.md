# 📄 Local PDF RAG Assistant

A fully local, privacy-first AI assistant that lets users upload PDF documents and ask questions about them using Retrieval-Augmented Generation (RAG). Every user has their own isolated document space. No data ever leaves your machine.

---

## ✨ Features

- 🔐 JWT-based user authentication (register & login)
- 📁 Per-user document isolation — users cannot see each other's documents
- 📤 Upload PDF documents and embed them into a vector database
- 💬 Ask questions about your documents via a streaming chat interface
- 🤖 Powered by Ollama — runs AI models completely locally
- 🔍 Automatic source detection — detects which document your question is about
- 💡 Casual chat support — handles greetings and friendly conversation naturally
- 🐳 Docker support — easy to share and deploy anywhere
- 🌐 Clean web frontend — no framework required, just open in a browser

---

## 🏗️ Project Structure

```
rag-assistant/
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── auth_router.py          # POST /auth/register, POST /auth/login
│   │   └── dependencies.py         # JWT dependency injection
│   ├── database/
│   │   ├── chroma_client.py        # Per-user ChromaDB collections
│   │   └── user_db.py              # JSON-based user store
│   ├── middleware/
│   │   └── timing_middleware.py    # Request timing logs
│   ├── models/
│   │   └── request_models.py       # Pydantic request models
│   ├── routers/
│   │   ├── document_router.py      # Upload, list, delete documents
│   │   └── query_router.py         # RAG query and SSE streaming
│   └── services/
│       ├── auth_service.py         # Password hashing, JWT creation
│       ├── document_service.py     # ChromaDB document operations
│       ├── ollama_service.py       # Ollama API calls
│       ├── pdf_service.py          # PDF parsing and chunking
│       └── rag_service.py          # RAG pipeline logic
├── data/                           # Docker volume (persists data)
│   ├── chroma_db/                  # Per-user vector databases
│   │   ├── <user_id>/
│   │   └── <user_id>/
│   └── users.json                  # Registered users
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── main.py                         # FastAPI entry point
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| AI / LLM | Ollama (local, no cloud) |
| Default Model | `qwen2.5:1.5b` |
| Embeddings | `all-mpnet-base-v2` (sentence-transformers) |
| Vector DB | ChromaDB (persistent) |
| PDF Parsing | pypdf |
| Auth | JWT (python-jose + passlib) |
| Frontend | Vanilla HTML / CSS / JS |
| Container | Docker + Docker Compose (two containers) |

---

## 🚀 Running Locally (Without Docker)

### Prerequisites

- Python 3.11
- [Ollama](https://ollama.com) installed and running
- Git

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/rag-assistant.git
cd rag-assistant
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Pull the default Ollama model**
```bash
ollama pull qwen2.5:1.5b
```

**5. Start the server**
```bash
uvicorn main:app --reload
```

**6. Open the frontend**

Open `frontend/index.html` in your browser (or serve with Live Server).

API docs available at: `http://127.0.0.1:8000/docs`

---

## 🐳 Running with Docker

Docker runs two containers — one for the FastAPI app and one for Ollama. Both are managed together by Docker Compose.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- WSL 2 enabled (Windows only — run `wsl --install` in PowerShell as Administrator)

### Steps

**1. Build and start both containers**
```bash
docker-compose up --build
```

First run takes longer — the Ollama container pulls the model automatically. The model is cached in its own Docker volume and will not be re-downloaded on future restarts.

**2. Open the frontend**

Open `frontend/index.html` in your browser.

API runs at: `http://localhost:8000`

**3. Stop the containers**
```bash
docker-compose down
```

> Your data (documents, users, Ollama models) is stored in Docker volumes and persists across restarts.

---

## 🤖 Changing the Ollama Model

You can use any model available on [ollama.com/library](https://ollama.com/library) — no code changes needed.

### Without Docker

**1. Pull your preferred model**
```bash
ollama pull llama3.1:8b
```

**2. Pass the model name when starting the server**

Windows PowerShell:
```powershell
$env:OLLAMA_MODEL="llama3.1:8b"; uvicorn main:app --reload
```

Mac / Linux:
```bash
OLLAMA_MODEL=llama3.1:8b uvicorn main:app --reload
```

### With Docker

Pass the model name in the terminal when starting — no file editing needed:

**Windows PowerShell:**
```powershell
$env:OLLAMA_MODEL="llama3.1:8b"; docker-compose up --build
```

**Mac / Linux:**
```bash
OLLAMA_MODEL=llama3.1:8b docker-compose up --build
```

Or if you prefer to edit the file, open `docker-compose.yml` and change this line under `rag-app > environment`:
```yaml
- OLLAMA_MODEL=qwen2.5:1.5b
```

The Ollama container will pull the new model automatically on first use and cache it permanently in its volume.

### Popular Model Options

| Model | Size | Best For |
|---|---|---|
| `qwen2.5:1.5b` | ~1 GB | Default — fast, low RAM |
| `qwen2.5:7b` | ~4.5 GB | Better answers, needs 8 GB RAM |
| `llama3.1:8b` | ~4.9 GB | Great general purpose |
| `llama3.1:70b` | ~40 GB | Best quality, needs GPU |
| `mistral:7b` | ~4.1 GB | Good for document Q&A |
| `phi3:mini` | ~2.3 GB | Fast, lightweight |

> **GPU users:** Ollama automatically detects and uses your GPU. Simply pick a larger model for significantly better responses.

---

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create a new account |
| POST | `/auth/login` | Login and receive JWT token |

### Documents *(requires JWT)*
| Method | Endpoint | Description |
|---|---|---|
| POST | `/documents/upload` | Upload a PDF |
| GET | `/documents` | List your documents |
| GET | `/documents/check` | Check if a document exists |
| DELETE | `/documents` | Delete a document |

### Query *(requires JWT)*
| Method | Endpoint | Description |
|---|---|---|
| POST | `/query` | Ask a question (full JSON response) |
| GET | `/query/stream` | Ask a question (SSE streaming) |

### Info
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/info` | Server info and active model |
| GET | `/docs` | Swagger UI |

---

## 🔒 Security Notes

- Passwords are hashed using `bcrypt` — never stored in plain text
- JWT tokens expire after 24 hours
- Each user's ChromaDB collection is fully isolated
- Change `JWT_SECRET` in `docker-compose.yml` to a strong random value before sharing

**Generate a strong secret:**
```bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"

# PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## 📦 Sharing the Docker Image

### Option A — Docker Hub *(recommended)*
```bash
docker login
docker tag rag-assistant-rag-app yourusername/rag-assistant
docker push yourusername/rag-assistant
```

Others can run it with just the `docker-compose.yml` file:
```bash
docker-compose up
```

### Option B — Export as a file
```bash
# Export
docker save -o rag-assistant.tar rag-assistant-rag-app

# Import (on another machine)
docker load -i rag-assistant.tar
docker-compose up
```

> Note: The FastAPI image is ~2-3 GB. The Ollama model downloads separately into its own volume on first run.

---

## 🛠️ Requirements

### Local (without Docker)
- Python 3.11
- Ollama installed
- 8 GB RAM minimum (16 GB recommended for larger models)

### Docker
- Docker Desktop with WSL 2 (Windows) or Docker Engine (Mac/Linux)
- 8 GB RAM minimum
- 10 GB free disk space (for image + model)

---

## 📝 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `JWT_SECRET` | Secret key for signing JWT tokens | `fallback-secret-for-local-dev` |
| `OLLAMA_MODEL` | Ollama model to use | `qwen2.5:1.5b` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |

---

## 🐛 Common Issues

**`wsl: command not found` on Windows**
Run `wsl --install` in PowerShell as Administrator, restart your PC, then reopen Docker Desktop.

**`pydantic-core` build error**
You are using Python 3.14+. Use Python 3.11 instead — `py -3.11 -m venv venv`.

**`JSONDecodeError` on startup**
The `users.json` file is empty. This is handled automatically — just restart the server.

**`bcrypt` error with passlib**
Run `pip install bcrypt==4.0.1 --force-reinstall`.

**Ollama container not ready yet**
If FastAPI starts before Ollama is ready, wait 10 seconds and try again. The `depends_on` in docker-compose ensures Ollama starts first but doesn't wait for the model pull to finish.

**Model takes too long to respond**
Switch to a smaller model like `qwen2.5:1.5b` or `phi3:mini`.

---

## 📄 License

MIT License — free to use, modify, and distribute.
