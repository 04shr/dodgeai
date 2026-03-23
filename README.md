# O2C Intelligence System

AI-powered Order-to-Cash analytics platform.

## Stack
- **Frontend**: Vanilla HTML/CSS/JS — dark UI, no framework
- **Backend**: FastAPI + Python
- **Database**: Firebase Firestore
- **AI**: Multi-LLM (Gemini / OpenRouter / Groq) with fallback routing
- **Pipeline**: Pandas-based ETL

## Quick start
```bash
# 1. Run pipeline
cd pipeline && python o2c_pipeline.py

# 2. Start backend
cd backend && uvicorn main:app --reload

# 3. Serve frontend
cd frontend && python -m http.server 5173
```
