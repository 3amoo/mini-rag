# mini-RAG

A minimal implementation of a RAG (Retrieval-Augmented Generation) pipeline for question answering, built as a REST API with FastAPI.

Upload documents, split them into chunks, embed them into a vector database, then ask questions and get answers grounded in your own data.

## Features

- **Document ingestion** — upload `.txt` and `.pdf` files per project, with size/type validation.
- **Processing / chunking** — recursive character splitting with configurable chunk size and overlap (LangChain).
- **Embedding + vector indexing** — push chunks into a local file-based Qdrant vector DB.
- **Semantic search** — query the collection by embedding similarity (cosine).
- **RAG answering** — retrieves relevant chunks, builds a prompt from templates, and generates an answer with an LLM.
- **Multi-provider LLM support** — OpenAI-compatible (incl. local models like Ollama via a custom API URL), Cohere, and Google Gemini; generation and embedding backends are configured independently.
- **Bilingual prompt templates** — Arabic (`ar`) and English (`en`) locales.
- **Metadata storage** — projects, assets, and chunks are persisted in MongoDB.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Hypercorn (ASGI) |
| Language | Python 3.14 |
| Database | MongoDB (via `motor`, async + `pydantic-mongo`) |
| Vector DB | Qdrant (local, file-based mode) |
| Text processing | LangChain (`RecursiveCharacterTextSplitter`, `PyMuPDFLoader`) |
| LLM providers | OpenAI-compatible, Cohere, Google Gemini |
| Config | `pydantic-settings` + `.env` files |

## Project Structure

```
mini-RAG/
├── docker/
│   ├── docker-compose.yml      # MongoDB service
│   └── .env.example
└── src/
    ├── main.py                # FastAPI app, startup/shutdown (DB, LLM, VectorDB clients)
    ├── requirements.txt
    ├── .env.example
    ├── helpers/
    │   └── config.py          # pydantic settings (reads .env)
    ├── routes/                # API endpoints + request schemes
    │   ├── base.py            # GET /api/v1
    │   ├── data.py            # upload & process endpoints
    │   └── nlp.py             # index, search & RAG answer endpoints
    ├── controllers/           # business logic (Data, Process, NLP, Project)
    ├── models/                # MongoDB models + enums (schemes, response signals)
    ├── stores/
    │   ├── llm/               # LLM providers (OpenAI, Cohere, Gemini) + factories
    │   │   └── templates/      # prompt templates (locales: ar, en)
    │   └── vectordb/           # Qdrant provider + factory
    └── assets/
        ├── files/<project>/   # uploaded files
        └── qdrant_db/          # local vector DB collections
```

## Getting Started

### Requirements

- Python 3.14.7
- Docker (for MongoDB)

### 1. Clone and create a virtual environment

```bash
git clone <repo-url> && cd mini-RAG
python -m venv venv
source venv/bin/activate
```

(Install Python on Void Linux: `sudo xbps-install -S python3`)

### 2. Install dependencies

```bash
pip install -r src/requirements.txt
```

### 3. Start MongoDB

```bash
cd docker
cp .env.example .env        # set MONGO_INITDB_ROOT_USERNAME / PASSWORD
docker compose up -d
```

### 4. Configure the app

```bash
cd ../src
cp .env.example .env
```

Fill in the values — see the [Configuration](#configuration) section below.

### 5. Run the server

```bash
hypercorn main:app --reload
```

The API is now available at `http://127.0.0.1:8000`, interactive docs at `/docs`.

## Configuration

All settings live in `src/.env` (see `src/.env.example`). Key options:

| Variable | Description | Example |
|---|---|---|
| `APP_NAME` / `APP_VERSION` | App identity | `mini-RAG` / `0.1` |
| `MONGODB_URL` | MongoDB connection string | `mongodb://admin:admin@localhost:27017/?authSource=admin` |
| `MONGODB_DATABASE` | Database name | `mini-rag` |
| `GENETATION_BACKEND` | LLM for generation: `OPENAI`, `COHERE`, or `GEMINI` | `OPENAI` |
| `EMBEDDING_BACKEND` | LLM for embeddings: `OPENAI`, `COHERE`, or `GEMINI` | `GEMINI` |
| `OPENAI_API_KEY` / `OPENAI_API_URL` | OpenAI-compatible credentials (point `OPENAI_API_URL` at Ollama/ngrok for local models) | |
| `COHERE_API_KEY` | Cohere API key | |
| `GEMINI_API_KEY` | Google Gemini API key | |
| `GENETATION_MODEL_ID` | Generation model | `gemma2:9b-instruct-q5_0` |
| `EMBEDDING_MODEL_ID` / `EMBEDDING_MODEL_SIZE` | Embedding model and vector size | `gemini-embedding-001` / `384` |
| `FILE_ALLOWED_TYPES` | Allowed MIME types | `["text/plain", "application/pdf"]` |
| `FILE_MAX_SIZE` | Max upload size (MB) | `10` |
| `FILE_DEFAULT_CHUNK_SIZE` | Upload stream chunk size (bytes) | `512000` |
| `VECTOR_DB_BACKEND` | Vector DB provider | `QDRANT` |
| `VECTOR_DB_PATH` | Local Qdrant storage path | `qdrant_db` |
| `VECTOR_DB_DISTANCE_METHOD` | Similarity metric | `cosine` |
| `PRIMARY_LANG` / `DEFAULT_LANG` | Prompt template languages | `ar` / `en` |

## API Endpoints

Base path: `/api/v1`

### Data

#### Upload a file

```http
POST /api/v1/data/upload/{project_id}
Content-Type: multipart/form-data
```

| Field | Type | Description |
|---|---|---|
| `file` | file | `.txt` or `.pdf` (max 10 MB) |

Response: `{"signal": "file_upload_success", "file_id": "<id>"}`

#### Process uploaded files (chunking)

```http
POST /api/v1/data/process/{project_id}
```

```json
{
  "file_id": "optional — process a single file, omit for all project files",
  "chunk_size": 100,
  "overlap_size": 20,
  "do_reset": 0
}
```

Response: `{"signal": "processing_success", "inserted_chunks": 42, "processed_files": 2}`

### NLP

#### Index chunks into the vector DB

```http
POST /api/v1/nlp/index/push/{project_id}
```

```json
{ "do_reset": 0 }
```

Response: `{"signal": "insert_into_vectordb_success", "insert_items_count": 42}`

#### Get collection info

```http
GET /api/v1/nlp/index/info/{project_id}
```

#### Semantic search

```http
POST /api/v1/nlp/index/search/{project_id}
```

```json
{ "text": "your query", "limit": 5 }
```

#### RAG question answering

```http
POST /api/v1/nlp/index/answer/{project_id}
```

```json
{ "text": "your question", "limit": 5 }
```

Response: `{"signal": "rag_answer_success", "answer": "...", "full_prompt": "...", "chat_history": [...]}`

### Example workflow

```bash
curl -F "file=@doc.pdf" http://127.0.0.1:8000/api/v1/data/upload/1
curl -X POST http://127.0.0.1:8000/api/v1/data/process/1 \
  -H "Content-Type: application/json" \
  -d '{"chunk_size": 100, "overlap_size": 20}'
curl -X POST http://127.0.0.1:8000/api/v1/nlp/index/push/1 \
  -H "Content-Type: application/json" -d '{}'
curl -X POST http://127.0.0.1:8000/api/v1/nlp/index/answer/1 \
  -H "Content-Type: application/json" \
  -d '{"text": "What is this document about?", "limit": 5}'
```

## Pipeline Overview

1. **Upload** — files are validated and stored under `src/assets/files/<project_id>/`; an asset record is created in MongoDB.
2. **Process** — files are loaded (`PyMuPDFLoader` for PDFs) and split into chunks with `RecursiveCharacterTextSplitter`; chunks are saved in MongoDB.
3. **Index** — chunk texts are embedded via the configured embedding backend and inserted into a per-project Qdrant collection (`collection_<project_id>`).
4. **Answer** — the question is embedded, the top-k similar chunks are retrieved, a bilingual RAG prompt is assembled from templates, and the generation LLM produces the answer.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
