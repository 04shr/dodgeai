# AI Layer

## LLM Router
Routes requests based on use-case:
- `nl_query` → Gemini (best at dialogue)
- `root_cause` → OpenRouter/Claude (best at reasoning)
- `insights_summary` → Groq/LLaMA (fastest, cheapest)

## Fallback chain
Each use-case has an ordered fallback list. If provider fails (rate limit, timeout), next provider is tried automatically.

## Prompt templates
See `app/ai/prompts.py` for all templates.
