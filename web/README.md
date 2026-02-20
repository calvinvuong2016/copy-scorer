# Copy Scorer UI

Simple web UI to grade copy with all CW, Book, and Meta scorers, and optionally rewrite to 90+ with highlighted changes.

## Run locally

From the **project root** (`Claude - Test`):

```bash
pip install -r web/requirements.txt
uvicorn server:app --reload --app-dir web
```

Then open **http://127.0.0.1:8000** in your browser.

## Features

1. **Enter copy** in the text area and click **Grade**.
2. **Bubbles** show each scorer’s name and score (CW, Book, Meta). Click a bubble to open the right-hand panel with the full summary.
3. Turn on **Rewrite to 90+** and click **Rewrite to 90+** to get revised copy; original and revised appear side by side with **yellow highlight** on changed text.

Scores and rewrite are currently **mock** (deterministic from copy content). To plug in real scoring/rewriting (e.g. LLM), extend `server.py` and use your API keys via environment variables.
