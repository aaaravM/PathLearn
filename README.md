# PathLearn – Autonomous Learning Platform

A full-stack AI learning platform that combines a Flask backend (RAG + LLM + adaptive engines) with a static HTML/CSS/JS frontend. It delivers lessons, mixed-question practice, placement tests, and career resources inspired by Khan Academy.

## Table of Contents
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Folder Structure](#folder-structure)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Local Setup](#local-setup)
- [Frontend (Netlify)](#frontend-netlify)
- [Backend (Railway/Render/etc)](#backend-railwayrenderetc)
- [LLM/RAG Configuration](#llmrag-configuration)
- [Placement & Lessons](#placement--lessons)
- [Training the Student RNN](#training-the-student-rnn)
- [Developing & Testing](#developing--testing)
- [Known Caveats](#known-caveats)

## Architecture
- **Frontend**: Static HTML/CSS/JS in `frontend/` (templates + static assets). SPA behavior requires a redirect rule.
- **Backend**: Flask app in `backend/app.py` exposes pages and JSON APIs. RAG/LLM via Hugging Face router using an OpenAI-compatible client with fallbacks.
- **Models**: Student RNN (LSTM) in `backend/models/student_model.py`; DRL placeholder in `backend/models/drl_agent.py`; RAG/LLM in `backend/models/rag_engine.py`.
- **Data**: Courses catalog in `backend/data/courses.json`; careers/resources in `backend/data/careers.json`.
- **Deployment**: Frontend on Netlify (static). Backend on Railway/Render/Fly/etc. (Python).

## Key Features
- Course catalog with “View Units” grid; unit hover shows estimated questions/time/title.
- Placement test (LLM-generated) that auto-sets placement (ahead/average/behind) and auto-completes units.
- Lessons with theory (styled, evidence blocks) and mixed question types (MCQ/TF/short/essay) with fallbacks.
- Career resources page (Resources) with curated links by career/degree.
- Auth-ready UI (Firebase on the frontend if configured).

## Folder Structure
```
backend/         # Flask app, models, data
frontend/        # Static templates and assets
ml_training/     # Training scripts (user-provided)
docs/            # Supporting docs
Procfile         # For platform start (python backend/app.py)
railway.toml     # [start] cmd = "python backend/app.py"
requirements.txt # Runtime deps (light, no torch)
```

## Prerequisites
- Python 3.11+
- Git
- Hugging Face token (with access to your chosen model)
- (Optional) Node is NOT required for build; frontend is static.

## Configuration
Backend config in `backend/config.py`:
- `HF_API_KEY`: Hugging Face token (hardcoded here; can be overridden by `HF_TOKEN` env var in your host).
- `HF_MODEL`: `"katanemo/Arch-Router-1.5B:hf-inference"` (router model string). Swap to a model your token can access if needed.
- `SECRET_KEY`: Flask session key (set via env in production).
- Careers list: `backend/data/careers.json`.
- Courses: `backend/data/courses.json` (includes K-1 to College tracks).

Environment variables (recommended in deployment):
- `HF_TOKEN` (overrides HF_API_KEY)
- `FLASK_ENV=production`
- Any Firebase keys if you wire frontend auth.

## Local Setup
```bash
cd backend
pip install -r ../requirements.txt
python app.py
# visit http://127.0.0.1:5000
```
Frontend uses root-relative `/static/...` paths when served from `frontend` root by Flask. If opening files directly, serve `frontend/` so `/static` resolves.

## Frontend (Netlify)
- Set Publish directory: `frontend`
- Build command: leave blank (no build step)
- **SPA routing**: add `frontend/_redirects` with:
  ```
  /* /index.html 200
  ```
- If you have a backend, add an API proxy (optional):
  ```
  /api/* https://<your-backend>/api/:splat 200
  ```
Commit `_redirects` if you need routes beyond `/`.

## Backend (Railway/Render/etc)
1) Ensure root `requirements.txt` exists (light deps, no torch).
2) Start command: `python backend/app.py` (Procfile already set).
3) Set env vars: `HF_TOKEN=<your HF key>` (and `FLASK_ENV=production`).
4) Deploy from GitHub. If your platform uses Nixpacks, Python should be detected automatically by the root `requirements.txt`.

## LLM/RAG Configuration
- Primary client: OpenAI-compatible pointing to `https://router.huggingface.co/v1` with `HF_MODEL`.
- Fallback: `InferenceClient` using the same model for text generation.
- If you see “model not supported” or 410, your token likely lacks access. Change `HF_MODEL` to one your token can use or enable access on HF.

## Placement & Lessons
- Placement test: `/api/placement-test` generates mixed-type questions; placement is inferred and applied to the selected track.
- Lessons: `/api/lesson` pulls theory and practice. If LLM fails, theory and 5 MCQs are injected as fallback.
- Question types rendered one-by-one in `frontend/static/js/lesson-runtime.js`.

## Training the Student RNN
- Training scripts are user-provided (e.g., `ml_training/train_rnn.py`). A lightweight fallback is used if torch is unavailable.
- For real training: run your `train_rnn.py` to save `ml_training/models_saved/student_rnn.pt`. At runtime, `student_model.py` will load this file automatically if torch is installed and the file exists. A torchless fallback is used otherwise.
- If you need heavy deps (torch/pandas/sklearn), keep them out of production `requirements.txt`; use a separate training requirements file locally.

## Developing & Testing
- Lint/test placeholders: `tests/` folder contains stubs. Run your preferred test runner after adding real tests.
- To change styling/paths for Netlify, ensure templates use `/static/...` links and publish `frontend` root.

## Known Caveats
- SPA routing (deep links) requires `_redirects` on Netlify.
- LLM access depends on your HF token/model permissions; change `HF_MODEL` or token if you see “model not supported”/410.
- Torch is not included in production deps; RNN will fall back if no weights/torch are available.

## Quick Commands
- Local run: `cd backend && pip install -r ../requirements.txt && python app.py`
- Git push (from repo root) after changes: `git add . && git commit -m "Update" && git push`
- Netlify publish dir: `frontend` (no build)
- Backend start: `python backend/app.py` (Procfile/railway.toml already set)
