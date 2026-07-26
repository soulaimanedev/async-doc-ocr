# async-doc-ocr

Upload a PDF, get the text out of it. The extraction runs in the background so the API doesn't block while Tesseract does its thing.

## How it works

```
POST /documents               → saves the file, queues a job, returns an ID
GET  /documents               → list all documents (paginated)
GET  /documents/{id}/status   → pending / running / success / failed
GET  /documents/{id}/result   → the extracted text once it's done
```

The API and the worker are separate processes. When you upload a document the API writes it to disk, creates a DB record, and drops the document ID onto a RabbitMQ queue. The worker picks it up, runs Tesseract on each page (via pdf2image), and writes the result back to Postgres. If OCR fails it retries up to 3 times before marking the job as failed with an error message.

## Stack

- **FastAPI** — async HTTP layer
- **SQLAlchemy (async) + asyncpg** — Postgres access
- **aio-pika** — async RabbitMQ client
- **pdf2image + pytesseract** — PDF → image → text
- **tenacity** — retry logic on OCR failures
- **Docker Compose** — wires everything together

## Running locally

You need Docker and Docker Compose. Copy `.env.example` to `.env` and fill in the four values:

```bash
cp .env.example .env
# then edit .env with your credentials
```

Then start everything:

```bash
docker compose up --build
```

This starts Postgres, RabbitMQ, the API on port `8000`, and the worker. The API is ready when Postgres and RabbitMQ pass their healthchecks. Database tables are created automatically on first startup — there is no separate migration step.

RabbitMQ management UI is available at `http://localhost:15672` (guest/guest by default).

FastAPI's interactive docs are at `http://localhost:8000/docs` — useful for trying out the endpoints without curl.

> **Note:** if the file upload fails in the Swagger UI with a "Failed to fetch" error, this is likely caused by browser extensions blocking local requests — Brave's Shields is a known culprit. Try Chrome/Firefox, or disable Shields for `localhost`, if you hit this. curl works regardless.
## Usage

List all documents (paginated):

```bash
curl "http://localhost:8000/documents?limit=20&offset=0"
# {"total": 5, "limit": 20, "offset": 0, "items": [...]}
```

Upload a PDF:

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@your-document.pdf"
# {"id": 1, "name": "your-document.pdf", "status": "pending"}
```

Check status:

```bash
curl http://localhost:8000/documents/1/status
# {"id": 1, "status": "running"}
```

Get the result:

```bash
curl http://localhost:8000/documents/1/result
# {"id": 1, "status": "success", "message": "Processing succeeded", "result": "...extracted text..."}
```

Only PDF files are accepted. Anything else gets a 400.

## Running tests

### Prerequisites

**1. Docker and Docker Compose**

Install Docker Desktop (includes Compose) for Mac or Windows. On Linux, install the Docker Engine and the Compose plugin:

```bash
# Linux (Debian/Ubuntu)
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
```

**2. uv**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**3. Environment file**

If you haven't done this already for running the app:

```bash
cp .env.example .env
# Edit .env and fill in POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, and QUEUE_NAME
```

### Running

Start the full stack in the background:

```bash
docker compose up -d --build
```

Wait until the API is healthy before running tests:

```bash
until curl -sf http://localhost:8000/health; do echo "waiting..."; sleep 2; done
```

Install test dependencies and run:

```bash
uv sync --group dev
uv run pytest
```

The tests hit the real API at `http://localhost:8000`, publish to the real RabbitMQ queue, and assert against the real Postgres database. The end-to-end tests upload actual PDF fixtures and poll until the worker finishes processing them — allow up to 30 seconds per test.

In CI, the stack is started automatically via `docker compose up --build` before tests run.

## Known limits

- **Local file storage only.** Uploaded PDFs are written to a directory on disk. The API and worker share it via a Docker volume, which works for a single-node setup but won't scale horizontally without switching to object storage (S3/MinIO).
- **No authentication.** Any caller can upload documents and read any result by ID. Adding an auth layer (API keys or JWT) would be the first production step.
- **No dead-letter queue.** After 3 failed OCR attempts the job is marked `failed` and the message is discarded. There is no DLQ to inspect or replay permanently failing messages.
- **Tesseract accuracy is layout-sensitive.** OCR quality degrades on scanned PDFs with complex layouts, tables, or non-Latin scripts. A more capable engine (PaddleOCR, a cloud API) would improve results at the cost of added dependency or spend.
- **Upload itself is still synchronous.** Only the OCR step is decoupled via RabbitMQ — the client still waits for the full file to be received and written to disk before getting a response, since that's inherent to how HTTP uploads work. For very large files, this wait is unavoidable in this architecture; a production system might instead use pre-signed direct-to-storage uploads (client uploads straight to S3/MinIO) so the API only ever handles a small "create record" request, removing even that wait.