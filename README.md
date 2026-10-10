# GovGuide AI — Working RAG Chatbot Starter

A Flask + Markdown OKF + TF-IDF retrieval + optional Ollama generation project for the KIET LE Cohort night project.

## What works
- Responsive browser chat UI, session history in SQLite, retrieval over eight OKF Markdown notes, source filenames and status badges.
- Offline **extractive RAG mode**: no LLM or API key required. Returns retrieved note excerpts.
- Optional **generative RAG mode** using a local Ollama model. Requires separately installing Ollama and downloading its model.
- Import local PDF/Markdown/TXT source documents using a CLI; reindex via restart.
- Automated Flask API tests and a 10-question retrieval/abstention benchmark.

## Windows PowerShell installation
```powershell
cd GovGuide_AI_RAG_Chatbot
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
```
Open http://127.0.0.1:5000

If activation is blocked, use `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.\.venv\Scripts\python.exe run.py` instead.

## Turn on real generative RAG (optional)
Install Ollama from https://ollama.com, then:
```powershell
ollama pull qwen2.5:0.5b
ollama serve
```
In a **separate** PowerShell terminal, before starting Flask:
```powershell
$env:RAG_MODE="ollama"
python run.py
```
If Ollama is already running, do not launch `ollama serve` again. The backend falls back to source excerpts if Ollama is unavailable.

## Add more government documents
Download the **actual official government PDF** manually and save it locally. Then run:
```powershell
python scripts/add_document.py "C:\path\to\guideline.pdf" --title "Scholarship guideline" --source-url "https://official-government-source.example/path"
python run.py
```
Replace the illustrative URL with the exact real official PDF URL. The imported document is `draft` until human verification. Do not mark as verified automatically.

## Benchmark and tests
```powershell
python scripts/benchmark.py
python -m pytest -q
```
Benchmark reports retrieval hit/abstention only, not answer faithfulness. For the cohort project, compare V1 keyword and V2 embeddings (not implemented in this starter) and record real results.

## Data warning
The supplied eight OKF notes are **project-authored teaching material**, not verified scheme-specific datasets. This app does NOT train or fine-tune an LLM. RAG indexes documents; that is the appropriate first step for frequently changing scheme information. No benefit amounts or deadlines are invented. For real-world deployment, add verified scheme PDFs and a verification workflow, authentication for admin routes, rate limiting, encrypted storage, logging controls, and an independent safety evaluation.

## API
- `GET /api/health`
- `POST /api/chat` JSON `{ "message": "...", "session_id": "optional UUID" }`
- `GET /api/history/<session_id>`
- `POST /api/reindex` local use only

## Notes
Chat history is stored in local SQLite; do not enter personal IDs or secrets. This is a functional development prototype, not an official government service.
