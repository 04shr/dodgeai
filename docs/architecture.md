# System Architecture

```
Frontend (HTML/CSS/JS)  ←→  FastAPI Backend  ←→  Firebase Firestore
                                    ↕
                          AI Layer (LLM Router)
                         Gemini / OpenRouter / Groq
                                    ↕
                          Data Pipeline (Pandas)
                          SAP JSONL → Unified CSV
```

## Request flow
1. Browser loads `index.html`, hash-based router renders pages
2. Pages fetch static JSON/CSV for instant load (no backend required in static mode)
3. AI features and write operations go through FastAPI
4. FastAPI reads from local CSV + Firestore, routes AI calls through fallback chain
