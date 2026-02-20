# Plan: Connect Rewrite to Claude (LLM)

**Goal:** Use Claude to rewrite copy so each revision is driven by that scorer’s real framework (Schwartz, Ogilvy, Cashvertising, etc.) and aimed at a 90+ score from that perspective. When the user picks “Eugene Schwartz,” the rewrite follows Schwartz’s awareness, mechanism, and economy rules—not a fixed template.

**Decisions (Option B for both):**
- **Framework source:** Option B — Use the skill files at runtime. Framework text is loaded from `api/skills/{scorer_id}.md` (shipped with the API deploy). Single source of truth; update the skill file and both grading context and rewrite stay in sync.
- **Claude response:** Option B — Structured output. We ask Claude for JSON `{"revised": "...", "summary": "..."}`. Parse and return; if parsing fails, fall back to treating the full response as `revised` and use a generic summary.

---

## 1. Overview

| Current | After |
|--------|--------|
| Rewrite = hardcoded per-model text blocks | Rewrite = Claude API call with that model’s framework as the “brief” |
| Same structure every time for a given model | Real edits: tighten, add mechanism, adjust bullets, etc. |
| No link to skill docs | System prompt built from (or aligned with) each scorer’s SKILL.md |

**Flow:** User selects a model → clicks “Rewrite to 90+” → backend sends the copy + that model’s rewrite instructions to Claude → Claude returns revised copy (+ short summary) → app shows diff and “Revised by [model].”

---

## 2. Where Claude Gets Called

- **Vercel:** `api/rewrite.py` — serverless function. Call Anthropic’s API from here (with `ANTHROPIC_API_KEY` in Vercel env).
- **Local:** `web/server.py` — same logic: if `ANTHROPIC_API_KEY` is set, call Claude; otherwise fall back to current mock so the app still works without a key.

Both endpoints already accept `copy` + `scorer_id` and return `revised`, `summary`, `scorer_name`. We only change *how* `revised` and `summary` are produced (Claude vs templates).

---

## 3. Rewrite Prompts: Using the Frameworks

Each of the 16 scorers needs a **rewrite system prompt** that tells Claude:

- You are rewriting as [Eugene Schwartz / Ogilvy / Cashvertising / …].
- Here are the criteria this framework uses (awareness, mechanism, bullets, etc.).
- Goal: revise the copy so it would score **90+** by this framework. Preserve the core offer and message; improve structure, clarity, and alignment with the criteria.
- Output format: revised copy only, or structured (e.g. JSON with `revised` and `summary`) so we can show “Revised by [name]” and a one-line summary.

**Where the framework text comes from (Option B — implemented):**

- **16 scorers** — Framework text is loaded at runtime from `api/skills/{scorer_id}.md`. The repo ships a copy of each scorer’s content in `api/skills/` (15 from `.cursor/skills/` plus `meta-score.md` as a synthetic prompt). The rewrite handler reads the matching `.md` file and uses it as the “Framework” section of the system prompt. Single source of truth: update `api/skills/` when you update a framework.
- **Meta Scorer (16th)** — `api/skills/meta-score.md` contains the synthetic prompt for Meta’s ad delivery (clear CTA, no aggressive caps, policy-safe, first 125 characters strong, no engagement bait).

**Shared instructions in every prompt:**

- Preserve the core offer and key claims; don’t invent new facts.
- Output only the revised copy (and if we use structured output, a one-sentence summary).
- Follow the Natural Language Doc and Anti AI Module (conversational, no banned patterns, 3rd–5th grade reading level) so the rewrite doesn’t sound like generic AI.

---

## 4. API Key and Environment

- **Variable:** `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` if we use an OpenAI-compatible gateway for Claude; for native Anthropic we use `ANTHROPIC_API_KEY`).
- **Vercel:** Project → Settings → Environment Variables → add `ANTHROPIC_API_KEY` (secret). No key in code.
- **Local:** `.env` in project root or in `web/` with `ANTHROPIC_API_KEY=sk-ant-...`. Add `.env` to `.gitignore` if not already.
- **Behavior:** If the key is missing or invalid, the rewrite endpoint falls back to the current **template-based rewrite** and optionally returns a flag like `"llm_used": false` so the UI can show “Revised (template)” vs “Revised by [model] (Claude).”

---

## 5. Request / Response Shape

**Backend → Anthropic:**

- **Model:** e.g. `claude-sonnet-4-20250514` or `claude-3-5-haiku-20241022` (faster/cheaper). Prefer a single model for all rewrites so behavior is consistent.
- **System message:** The scorer-specific rewrite prompt (framework + output rules).
- **User message:** The copy to rewrite, e.g. “Rewrite the following copy to score 90+ by your criteria. Preserve the offer and message.\n\n[COPY]”
- **Max tokens:** Cap output (e.g. 2048) so we don’t get runaway length. If the copy is long, we may need to allow more.

**Claude → Backend (Option B — implemented):**

- We ask Claude for JSON only: `{"revised": "...", "summary": "One sentence."}`. The system prompt specifies this format. We parse the response (stripping markdown code fences if present). If parsing fails or `revised` is empty, we fall back to the **template-based rewrite** and do not set `llm_used`.

**Backend → Frontend:** Unchanged. Response still has `revised`, `summary`, `scorer_id`, `scorer_name`. Optional: add `llm_used: true/false` so the UI can distinguish Claude vs template.

---

## 6. Fallback and Errors

- **No API key:** Use current template rewrite; set `llm_used: false`.
- **API error (rate limit, timeout, 5xx):** Catch, log, and fall back to template rewrite; optionally return a message like “Rewrite used backup method (no LLM).”
- **Vercel timeout:** Serverless default is often 10s; Claude may take 5–15s for long copy. Consider increasing timeout (e.g. 30s) or trimming copy sent to Claude (e.g. first N characters) if needed.
- **Content policy / refusals:** Rare for ad copy; if Claude refuses, fall back to template and optionally surface “Could not use Claude for this rewrite.”

---

## 7. Files to Add or Change

| Item | Action |
|------|--------|
| **Rewrite prompts** | Add `api/rewrite_prompts/` (or one JSON/dict in code) with 16 prompts: 15 from skill content + 1 for meta. Each prompt = “You are rewriting as [X]. Criteria: … Goal: 90+. Output: revised copy only (or JSON).” |
| **`api/rewrite.py`** | 1) Read `scorer_id` and load that scorer’s prompt. 2) If `ANTHROPIC_API_KEY` set, call Anthropic API with system + user message; parse response → `revised`, `summary`. 3) Else (or on error) use existing template logic. 4) Return same JSON shape; optional `llm_used`. |
| **`web/server.py`** | Mirror the same logic: env check, Claude call with scorer prompt, fallback to current `_rewrite_body_by_model` / `MODEL_BLOCKS`. |
| **Dependencies** | Add `anthropic` (or `openai` if using OpenAI-compatible endpoint) to the environment that runs the rewrite. For Vercel serverless, add `anthropic` to `package.json` if the API is in a Node serverless, or use a serverless function that runs Python and list `anthropic` in `requirements.txt` in the same directory as the function. (Current `api/` is Python-style HTTP handler—confirm how Vercel runs it and add the dependency there.) |
| **Env / docs** | Document `ANTHROPIC_API_KEY` in `HOSTING.md` or `COPY SCORER - FULL SETUP GUIDE.txt`. Add `.env` to `.gitignore` if not already. |

---

## 8. Optional: Limits and Cost

- **Token limits:** Set `max_tokens` on the Claude request (e.g. 2048). Input = system prompt + user (copy). Long copy may require a higher limit or truncation.
- **Timeouts:** Vercel serverless timeout (e.g. 30s) so the request doesn’t die mid-Claude-call.
- **Cost:** Per-request cost depends on model and length. Haiku is cheaper; Sonnet higher quality. You can start with one model and switch later.
- **Rate limits:** Anthropic has per-key limits. If you expect many concurrent rewrites, consider queuing or a “Revised (template)” fallback when over limit.

---

## 9. Implementation Order (Done)

1. **Skills in repo** — Added `api/skills/` with 16 `.md` files (15 from `.cursor/skills/`, 1 `meta-score.md` synthetic). Framework text is read at runtime.
2. **Claude call** — In `api/rewrite.py`: `_load_skill_prompt(scorer_id)`, `_rewrite_via_claude(copy_text, scorer_id, scorer_name)` loads framework, calls Anthropic, parses JSON with fallback. Uses `ANTHROPIC_API_KEY` from env.
3. **Integration** — POST handler tries Claude when key is set; on success returns Claude output with `llm_used: true`; on missing key or error uses template and `llm_used: false`.
4. **Local server** — Same logic in `web/server.py`; skills path is `api/skills/` relative to project root. `web/requirements.txt` includes `anthropic`.
5. **Frontend (optional)** — Response includes `llm_used`. UI can show a “Claude” vs “Template” badge next to “Revised by [name]” if desired.
6. **Docs and env** — Plan updated. Set `ANTHROPIC_API_KEY` in Vercel (Environment Variables) and in local `.env` (add `.env` to `.gitignore` if not already).

---

## 10. Summary

- **What:** Rewrite endpoint calls Claude with a per-scorer system prompt derived from the copywriting frameworks (skills + meta).
- **Why:** So rewrites actually follow each framework and aim for 90+, not generic templates.
- **Where:** `api/rewrite.py` (Vercel) and `web/server.py` (local); same request/response shape.
- **How:** 16 prompts in repo; Anthropic API key in env; fallback to current templates when no key or on error.
- **Next step:** Create the 16 rewrite prompts, then implement the Claude call and fallback in `api/rewrite.py`.
