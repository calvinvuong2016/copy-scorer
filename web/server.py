"""
Copy scoring & rewrite API. Serves the UI and provides /api/grade and /api/rewrite.
Run: uvicorn server:app --reload --app-dir web
"""
from __future__ import annotations

import json
import os
import re
import hashlib
from pathlib import Path

# Load .env from project root so ANTHROPIC_API_KEY is set for local runs
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    with open(_env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip('"').strip("'")
                if key and value:
                    os.environ.setdefault(key, value)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# Scorer definitions (id, display name, type)
# -----------------------------------------------------------------------------
SCORERS = [
    # CW
    ("cw-eugene-schwartz", "Eugene Schwartz", "cw"),
    ("cw-david-ogilvy", "David Ogilvy", "cw"),
    ("cw-gary-halbert", "Gary Halbert", "cw"),
    ("cw-joe-sugarman", "Joe Sugarman", "cw"),
    ("cw-gary-bencivenga", "Gary Bencivenga", "cw"),
    ("cw-dan-kennedy", "Dan Kennedy", "cw"),
    ("cw-john-carlton", "John Carlton", "cw"),
    ("cw-clayton-makepeace", "Clayton Makepeace", "cw"),
    ("cw-bob-bly", "Bob Bly", "cw"),
    ("cw-claude-hopkins", "Claude Hopkins", "cw"),
    # Book
    ("book-cashvertising", "Cashvertising", "book"),
    ("book-breakthrough-advertising", "Breakthrough Advertising", "book"),
    ("book-scientific-advertising", "Scientific Advertising", "book"),
    ("book-influence-cialdini", "Influence (Cialdini)", "book"),
    ("book-ogilvy-on-advertising", "Ogilvy on Advertising", "book"),
    # Meta
    ("meta-score", "Meta Scorer", "meta"),
]

def _summary_for(scorer_id: str, score: int) -> str:
    """In-depth rationale for why this scorer gave this score. Score-aware where useful."""
    if score >= 90:
        intro = "The copy scores in the top band because it strongly meets this framework's criteria. "
    elif score >= 80:
        intro = "The copy scores well; it aligns with this framework with only minor gaps. "
    elif score >= 70:
        intro = "The copy has solid elements but misses some of what this framework prioritizes. "
    else:
        intro = "The copy is out of alignment with this framework in several areas. "

    reasons = {
        "cw-eugene-schwartz": "Schwartz evaluates awareness match (does the copy speak to the prospect's stage?), mechanism (a clear 'how it works'), and mass desire (channeling existing wants). Economy of copy and headline fit for the stage also matter. " + intro + "To move the score up: sharpen the mechanism, match copy length to awareness, and ensure the headline leads with what the market already wants.",
        "cw-david-ogilvy": "Ogilvy weighs headline (does it do real work?), research and specifics, clarity, benefit over feature, credibility, and a strong opening that carries the headline forward. " + intro + "To improve: make the headline more specific and benefit-led, add concrete proof where possible, and keep the opening tight and direct.",
        "cw-gary-halbert": "Halbert looks for one-reader voice (feels like a letter to one person), borrowed interest (opening that hooks with story or curiosity before selling), story that earns the sell, and a P.S. that works as a closer. " + intro + "To strengthen: open with a stronger hook, make the P.S. sell, and keep the tone conversational and personal.",
        "cw-joe-sugarman": "Sugarman scores the first sentence (does it get the second read?), use of psychological triggers (curiosity, honesty, specificity, flow), and involvement. Flow and curiosity with payoff matter. " + intro + "To raise the score: strengthen the first sentence, stack triggers without forcing them, and keep the reader moving forward with no dead spots.",
        "cw-gary-bencivenga": "Bencivenga evaluates bullets that fascinate, proof over promise, risk reversal, reasons why, and headline–bullet alignment. Specificity and clarity matter. " + intro + "To improve: add or sharpen bullets with benefit and intrigue, back claims with proof, and make risk reversal (guarantee, trial, no downside) clear.",
        "cw-dan-kennedy": "Kennedy scores directness (no fluff), urgency or scarcity, personality, list/relationship tone, a single clear CTA and offer, and objection crushing. " + intro + "To strengthen: be more direct, add a real reason to act now, and address the main objections head-on.",
        "cw-john-carlton": "Carlton looks for selling style (every element serves the sale), story that earns the sell, control (reader is guided step by step), big promise, proof, and a strong hook. " + intro + "To improve: make the hook and promise bolder, tighten control so the reader always knows what's next, and ensure proof matches the promise.",
        "cw-clayton-makepeace": "Makepeace evaluates bullets for benefit + mechanism + intrigue, fascinations, headline from the strongest bullet, theming, and variety. " + intro + "To raise the score: give each bullet clear benefit, mechanism or specificity, and intrigue or credibility; vary length and structure.",
        "cw-bob-bly": "Bly scores facts over fluff, headline that does a clear job, benefits leading with features supporting, clear structure (e.g. AIDA), and a measurable response mechanism. " + intro + "To improve: add more specifics and proof, make the headline do more work, and keep the CTA and offer crystal clear.",
        "cw-claude-hopkins": "Hopkins weighs specificity over generality, preemptive claims where possible, offer clarity, test-ready focus, and a headline that does work. " + intro + "To strengthen: make claims more specific (numbers, names, outcomes), clarify the offer (what you get, what you give), and give a clear reason to act.",
        "book-cashvertising": "Cashvertising scores Life-Force 8 (which desires are tapped?), headline strength, sensory language, social proof, scarcity/USP, and fear (if used) with a clear solution. " + intro + "To improve: tie the offer to a core desire, use more concrete sensory language, and add proof or scarcity where it fits.",
        "book-breakthrough-advertising": "Breakthrough Advertising evaluates one mass desire, headline (stops and compels, no product in headline), awareness and sophistication match, use of the seven techniques, and the body journey (Attention to Conviction). " + intro + "To strengthen: focus on one desire, make the headline pull without naming the product, and align copy length and angle to the prospect's awareness.",
        "book-scientific-advertising": "Scientific Advertising scores specificity, preemptive claim, offer clarity, test-ready focus, and headline that does work. " + intro + "To improve: replace general claims with specific ones, clarify the offer, and keep one main idea so the copy can be tested.",
        "book-influence-cialdini": "Influence scores use of reciprocity, commitment/consistency, social proof, authority, liking, and scarcity. " + intro + "To raise the score: add or strengthen value-first (reciprocity), social proof, and authority; use scarcity only when it's real.",
        "book-ogilvy-on-advertising": "Ogilvy on Advertising weighs headline (5x read), research-driven copy, clarity, benefit over feature, credibility, and opening that carries the headline. " + intro + "To improve: make the headline more specific and benefit-led, add proof and specifics, and keep the opening direct.",
        "meta-score": "Meta's lens scores ad quality (no clickbait), engagement potential (meaningful vs. passive), policy compliance, negative-feedback risk, creative freshness, and first-impression density (first ~125 characters). " + intro + "To improve: strengthen the first 125 characters, avoid aggressive caps and engagement bait, and keep the CTA clear and policy-safe.",
    }
    return reasons.get(scorer_id, intro + "Scored against this framework's criteria. Review the framework to see what would raise the score.")


# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = FastAPI(title="Copy Scorer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = Path(__file__).resolve().parent


def _mock_score(scorer_id: str, copy_text: str) -> int:
    """Deterministic mock score 65–92 based on scorer and copy."""
    h = int(hashlib.sha256((scorer_id + copy_text[:500]).encode()).hexdigest(), 16)
    return 65 + (h % 28)


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


# -----------------------------------------------------------------------------
# API: grade
# -----------------------------------------------------------------------------
class GradeRequest(BaseModel):
    copy: str


class ScorerResult(BaseModel):
    id: str
    name: str
    type: str
    score: int
    summary: str


@app.post("/api/grade", response_model=list[ScorerResult])
def grade(req: GradeRequest):
    if not (req.copy or "").strip():
        raise HTTPException(status_code=400, detail="Copy is required")
    results = []
    for sid, name, stype in SCORERS:
        score = _mock_score(sid, req.copy)
        summary = _summary_for(sid, score)
        results.append(
            ScorerResult(id=sid, name=name, type=stype, score=score, summary=summary)
        )
    return results


# -----------------------------------------------------------------------------
# API: rewrite (per-model blocks so each scorer produces visibly different copy)
# -----------------------------------------------------------------------------
REWRITE_SUMMARIES = {
    "cw-eugene-schwartz": "Revised for awareness match, clearer mechanism, and economy of copy (Schwartz).",
    "cw-david-ogilvy": "Revised for stronger headline, research-backed specifics, and benefit-led clarity (Ogilvy).",
    "cw-gary-halbert": "Revised with borrowed interest, one-reader voice, and a selling P.S. (Halbert).",
    "cw-joe-sugarman": "Revised for first-sentence hook, flow, and psychological triggers (Sugarman).",
    "cw-gary-bencivenga": "Revised with bullets that fascinate, proof, and risk reversal (Bencivenga).",
    "cw-dan-kennedy": "Revised for direct CTA, urgency, and objection crushing (Kennedy).",
    "cw-john-carlton": "Revised for selling style, control, and big promise (Carlton).",
    "cw-clayton-makepeace": "Revised with benefit + mechanism + intrigue bullets (Makepeace).",
    "cw-bob-bly": "Revised with facts over fluff and clearer headline/CTA (Bly).",
    "cw-claude-hopkins": "Revised for specific claims, preemptive angle, and offer clarity (Hopkins).",
    "book-cashvertising": "Revised for Life-Force 8, sensory language, and USP (Cashvertising).",
    "book-breakthrough-advertising": "Revised for one mass desire, headline, and 7 techniques (Breakthrough Advertising).",
    "book-scientific-advertising": "Revised for specifics, preemptive claim, and test-ready offer (Scientific Advertising).",
    "book-influence-cialdini": "Revised using reciprocity, social proof, authority, scarcity (Influence).",
    "book-ogilvy-on-advertising": "Revised for headline power, research, and credibility (Ogilvy on Advertising).",
    "meta-score": "Revised for algorithm-friendly copy: fewer caps, clear CTA, engagement-safe (Meta).",
}

# Per-model: (intro_line, bullet_block, closer_line, ps_line, pps_line)
MODEL_BLOCKS = {
    "cw-eugene-schwartz": (
        "Here's what you get when you click the link below. Same mechanism the dermatology office uses:\n\n",
        "• The 5 brands and why the office stands behind them\n• What each does for fine lines, sagging, dark spots\n• Where to get them without the markup\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "No subscription. No auto-ship. No cost. Just the list. I'm not sure how long they keep the page up, but it's there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. It's free and there's nothing to sign up for.",
    ),
    "cw-david-ogilvy": (
        "Click the link below. You get one page—research-backed, no fluff:\n\n",
        "• The 5 brands by name\n• What each does (fine lines, sagging, dark spots)\n• Where to buy without the markup\n• Why the doctors give these to their wives\n• The ingredient that appears in four of the five\n\n",
        "No signup. No cost. No subscription. The page is live now.\n\n",
        "P.S. Link below.\n\n",
        "P.P.S. I don't know how long they keep it up.",
    ),
    "cw-gary-halbert": (
        "Nina sent this to a dozen women. Here's what they get when they click the link:\n\n",
        "• The 5 brands the dermatology office actually recommends\n• What each one does for lines, sagging, spots\n• Where to get them (no markup)\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "No subscription. No auto-ship. No cost. Just the list. It's there now.\n\n",
        "P.S. Nina's sent this to a dozen women. Every one thanked her. The link's below if you want it.\n\n",
        "P.P.S. Free. Nothing to sign up for.",
    ),
    "cw-joe-sugarman": (
        "Click the link. The first thing you see is what you get:\n\n",
        "• The 5 brands and why the office stands behind them\n• What each does for fine lines, sagging, and dark spots\n• Where to get them without the markup\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "No subscription. No cost. Just the list. Page is live now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. No signup.",
    ),
    "cw-gary-bencivenga": (
        "When you click the link you get a free page. No risk:\n\n",
        "• The 5 brands—and why the dermatology office stands behind them\n• What each one does for fine lines, sagging, dark spots\n• Where to get them without the markup\n• Why the doctors give these to their wives\n• The one ingredient that showed up in four of the five\n\n",
        "No subscription. No auto-ship. No cost. Just the list. (Risk reversed.) It's there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. Nothing to sign up for.",
    ),
    "cw-dan-kennedy": (
        "If you want the list, the link's below. Here's what you get:\n\n",
        "• The 5 brands and why the office stands behind them\n• What each does for lines, sagging, spots\n• Where to get them without the markup\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "No subscription. No auto-ship. No cost. I'm not sure how long they keep the page up—so if you want it, the link's below.\n\n",
        "P.S. Link below. No fluff.\n\n",
        "P.P.S. Free. No signup.",
    ),
    "cw-john-carlton": (
        "Big promise: the 5 brands that actually smooth lines, firm skin, fade spots. One link. Here's what's on the page:\n\n",
        "• The 5 brands and why the dermatology office stands behind them\n• What each one does for fine lines, sagging, and dark spots\n• Where to get them without the markup\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "No commitment. No subscription. No cost. Just the list. Control: one link below. It's there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. Nothing to sign up for.",
    ),
    "cw-clayton-makepeace": (
        "Click the link. You get benefit, mechanism, intrigue:\n\n",
        "• The 5 brands (benefit)\n• Why the dermatology office stands behind them (mechanism)\n• What each does for fine lines, sagging, dark spots\n• Where to get them without the markup\n• The one ingredient in four of the five (intrigue)\n\n",
        "No subscription. No cost. Just the list. It's there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. No signup.",
    ),
    "cw-bob-bly": (
        "Facts. Click the link and you get:\n\n",
        "• The 5 brands by name\n• What each does (fine lines, sagging, dark spots)\n• Where to get them (no markup)\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "No signup. No cost. No subscription. Clear CTA: link below. Page is live now.\n\n",
        "P.S. Link below.\n\n",
        "P.P.S. Free. Nothing to sign up for.",
    ),
    "cw-claude-hopkins": (
        "Specific offer. Click the link for:\n\n",
        "• The 5 brand names\n• What each does for skin over 45 (fine lines, sagging, dark spots)\n• Where to get them without the markup\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "Free. No signup. No subscription. Test-ready. Page is there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. No signup.",
    ),
    "book-cashvertising": (
        "Life-Force 8: what you get when you click (social approval, comfort):\n\n",
        "• The 5 brands—see what the dermatology office stands behind\n• What each does for fine lines, sagging, dark spots (sensory results)\n• Where to get them without the markup\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "No cost. No signup. Just the list. Link below. It's there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. No signup.",
    ),
    "book-breakthrough-advertising": (
        "One mass desire: look like yourself again. The page gives you:\n\n",
        "• The 5 brands (headline doesn't mention product)\n• Why the office stands behind them\n• What each does for fine lines, sagging, dark spots\n• Where to get them without the markup\n• The one ingredient in four of the five\n\n",
        "No subscription. No cost. Just the list. Link below. It's there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. No signup.",
    ),
    "book-scientific-advertising": (
        "Specific offer. Preemptive: what the doctors give their wives. Click the link for:\n\n",
        "• The 5 brands by name\n• What each does (fine lines, sagging, dark spots)\n• Where to get them without the markup\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "Free. No signup. No subscription. Test-ready. Page is there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. No signup.",
    ),
    "book-influence-cialdini": (
        "Social proof: Nina. Authority: dermatology office. What you get when you click:\n\n",
        "• The 5 brands and why the office stands behind them\n• What each does for fine lines, sagging, dark spots\n• Where to get them without the markup\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "No cost. No signup. Just the list. Link below. It's there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. No signup.",
    ),
    "book-ogilvy-on-advertising": (
        "Headline does the work. Credibility: same list the office uses. Click the link for:\n\n",
        "• The 5 brands and what each does (fine lines, sagging, dark spots)\n• Where to get them without the markup\n• Why the dermatology office stands behind them\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "No signup. No cost. Page is there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. No signup.",
    ),
    "meta-score": (
        "Clear CTA. No aggressive caps. What you get when you click:\n\n",
        "• The 5 brands and why the office stands behind them\n• What each does for fine lines, sagging, dark spots\n• Where to get them without the markup\n• Why the doctors give these to their wives\n• The one ingredient in four of the five\n\n",
        "No subscription. No cost. Just the list. Free. Link below. No engagement bait. It's there now.\n\n",
        "P.S. The link's below if you want it.\n\n",
        "P.P.S. Free. No signup.",
    ),
}


def _rewrite_body_by_model(text: str, scorer_id: str) -> str:
    t = text.strip()
    block = MODEL_BLOCKS.get(scorer_id, MODEL_BLOCKS["cw-eugene-schwartz"])
    intro, bullets, closer, ps, pps = block
    if "God Bless" in t or "god bless" in t.lower():
        inject = "\n\n" + intro + bullets + closer + "God Bless ♥️\n\n"
        t = re.sub(r"\s*God Bless.*$", inject, t, flags=re.I | re.DOTALL)
    else:
        t += "\n\n" + intro + bullets + closer
    if "P.S." not in t and "P.P.S." not in t:
        t += "\n\n" + ps + "\n\n" + pps
    return t.strip()


# -----------------------------------------------------------------------------
# Claude (LLM) rewrite: load skill from api/skills, call Anthropic, JSON fallback
# -----------------------------------------------------------------------------
def _skills_dir() -> Path:
    """Directory containing scorer framework .md files (api/skills)."""
    return Path(__file__).resolve().parent.parent / "api" / "skills"


def _load_skill_prompt(scorer_id: str) -> str | None:
    """Load framework content from api/skills/{scorer_id}.md. Return None if not found."""
    path = _skills_dir() / f"{scorer_id}.md"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


_REWRITE_SYSTEM_PREFIX = """You are rewriting ad copy in the style of the copywriter whose framework is described below. The framework is for YOUR use only to guide tone and structure. It must NEVER appear in the ad.

--- RULE 1: FULL REWRITE, TOP TO BOTTOM ---
- You must REWRITE the entire piece. The first sentence of your output must be DIFFERENT from the first sentence of the input. The opening paragraph must be rewritten. The body must be rephrased and restructured. The close must be a rewrite of the original close in this copywriter's style.
- FORBIDDEN: Leaving the original opening and middle mostly intact and then adding a new paragraph or block at the end. If your "revision" is mostly the original plus a tacked-on ending, you have failed. The revised copy should feel like one cohesive rewrite, not original + add-on.
- Length: Your revised copy should be similar in length to the original (or shorter). Do not add a long new block at the end.

--- RULE 2: NO FRAMEWORK OR COPYWRITING JARGON IN THE AD ---
The ad must read like a normal sales message. The reader must never see copywriting theory or methodology. You must NOT include in the revised copy:
- Any of these words or phrases: "awareness", "mechanism", "mass desire", "benefit + mechanism + intrigue", "borrowed interest", "risk reversal", "scoring", "criteria", "framework", "headline does the work", "P.S. as closer", "Life-Force 8", "psychological triggers", "one reader", "selling style", or similar copywriting-course language.
- The copywriter's name or the name of any book (e.g. Breakthrough Advertising, Cashvertising, Boron Letters).
- Any sentence that explains how copy works or what makes copy good. Only selling copy aimed at the prospect.

--- OTHER ---
- Apply this copywriter's style (opening hook, rhythm, bullets, P.S., tone) throughout — but without using the jargon above. You may add persuasive content that fits the offer.
- Natural, conversational language. 3rd–5th grade reading level. No AI patterns (no triplets, no "not just X but Y").
- Output valid JSON only: {"revised": "<full revised copy>", "summary": "<one sentence>"}. "revised" = complete rewrite, newlines as \\n. "summary" = one short sentence.

Framework (use for style and structure only; do not quote or echo in the ad):
"""


def _rewrite_via_claude(copy_text: str, scorer_id: str, scorer_name: str) -> tuple[str | None, str | None, bool]:
    """Call Claude to rewrite using the scorer's framework. Returns (revised, summary, True) on success, else (None, None, False)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not api_key.strip():
        return None, None, False
    framework = _load_skill_prompt(scorer_id)
    if not framework:
        return None, None, False
    try:
        import anthropic
    except ImportError:
        return None, None, False
    system = _REWRITE_SYSTEM_PREFIX + framework
    user = f"""Rewrite the following ad in {scorer_name}'s style. Requirements:
1) Change the FIRST sentence — do not keep the original first sentence. Rewrite the opening, then the middle, then the close. Do not output the original with a new paragraph tacked on at the end.
2) The revised ad must be normal selling copy only. Do not include any copywriting jargon (no "mechanism", "awareness", "benefit + intrigue", etc.), copywriter names, or book titles. If in doubt, leave it out.
Output only valid JSON: {{"revised": "<full revised ad>", "summary": "<one sentence>"}}.

ORIGINAL COPY:
{copy_text}"""
    try:
        client = anthropic.Anthropic(api_key=api_key.strip())
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = ""
        for block in getattr(msg, "content", []):
            if getattr(block, "type", None) == "text":
                text += getattr(block, "text", "") or ""
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        revised = (data.get("revised") or "").strip()
        summary = (data.get("summary") or "").strip() or REWRITE_SUMMARIES.get(scorer_id, "Revised to score 90+ for this model.")
        if not revised:
            return None, None, False
        return revised, summary, True
    except Exception:
        return None, None, False


def _mock_rewrite(copy_text: str, scorer_id: str | None = None) -> tuple[str, str, str]:
    """Per-model template rewrite. Returns (revised, summary, scorer_name)."""
    sid = (scorer_id or "").strip() or "cw-eugene-schwartz"
    name = next((n for s_id, n, _ in SCORERS if s_id == sid), "Eugene Schwartz")
    revised = _rewrite_body_by_model(copy_text, sid)
    summary = REWRITE_SUMMARIES.get(sid, "Revised to score 90+ for this model.")
    return revised, summary, name


class RewriteRequest(BaseModel):
    copy: str
    scorer_id: str | None = None


class RewriteResponse(BaseModel):
    revised: str
    summary: str
    scorer_id: str | None = None
    scorer_name: str | None = None
    llm_used: bool | None = None


@app.post("/api/rewrite", response_model=RewriteResponse)
def rewrite(req: RewriteRequest):
    if not (req.copy or "").strip():
        raise HTTPException(status_code=400, detail="Copy is required")
    sid = (req.scorer_id or "").strip() or "cw-eugene-schwartz"
    name = next((n for s_id, n, _ in SCORERS if s_id == sid), "Eugene Schwartz")
    revised, summary, llm_used = _rewrite_via_claude(req.copy, sid, name)
    if not llm_used:
        revised, summary, name = _mock_rewrite(req.copy, req.scorer_id)
    return RewriteResponse(
        revised=revised,
        summary=summary,
        scorer_id=sid,
        scorer_name=name,
        llm_used=llm_used,
    )
