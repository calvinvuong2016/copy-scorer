"""
Copy scoring & rewrite API. Serves the UI and provides /api/grade and /api/rewrite.
Run: uvicorn server:app --reload --app-dir web
"""
from __future__ import annotations

import os
import re
import hashlib
from pathlib import Path

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

SUMMARY_TEMPLATES = {
    "cw-eugene-schwartz": "Copy aligns with problem-aware to solution-aware. Mass desire is present; mechanism could be sharper. Headline and length fit the stage.",
    "cw-david-ogilvy": "Headline does strong work. Good use of specifics and credibility. Benefit-led and clear.",
    "cw-gary-halbert": "Strong borrowed interest and one-reader voice. Story is specific. P.S. underused.",
    "cw-joe-sugarman": "First sentence pulls; flow and triggers are strong. Multiple psychological triggers present.",
    "cw-gary-bencivenga": "Proof present; bullets and risk reversal would strengthen. Narrative does the work.",
    "cw-dan-kennedy": "Personality and objection handling good. CTA and urgency could be stronger.",
    "cw-john-carlton": "Selling style and story are strong. Control and big promise delivered.",
    "cw-clayton-makepeace": "Benefit and mechanism in prose; bullet structure would improve score.",
    "cw-bob-bly": "Facts and headline strong. CTA could be sharper.",
    "cw-claude-hopkins": "Specifics and preemptive angle present. Offer clarity could improve.",
    "book-cashvertising": "Life-Force 8 and sensory language strong. Headline works. Scarcity absent.",
    "book-breakthrough-advertising": "One mass desire; headline believable. Techniques and journey present.",
    "book-scientific-advertising": "Specific over general; offer clarity could be stronger.",
    "book-influence-cialdini": "Social proof and authority strong. Scarcity missing.",
    "book-ogilvy-on-advertising": "Headline and credibility strong. Research-driven feel.",
    "meta-score": "Good engagement potential; first impression strong. Some caps and pattern fatigue. Policy in monitored category.",
}

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
        summary = SUMMARY_TEMPLATES.get(sid, "Scored against framework criteria.")
        results.append(
            ScorerResult(id=sid, name=name, type=stype, score=score, summary=summary)
        )
    return results


# -----------------------------------------------------------------------------
# API: rewrite (mock: add structure so diff is visible; per-scorer addons)
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


def _model_addon(scorer_id: str, text: str) -> str:
    already_has_ps = "P.S." in text or "P.P.S." in text
    addons = {
        "cw-eugene-schwartz": "\n\nThe five brands use the same ingredients the dermatology office actually recommends—that's the mechanism that makes this work.",
        "cw-david-ogilvy": "\n\nHeadline does the work; the rest is proof and clarity. What you get: the 5 brands, what each does, and where to get them—no signup.",
        "cw-gary-halbert": "\n\nP.S. Nina's sent this to a dozen women. Every one has thanked her. The link's below if you want it." if not already_has_ps else "",
        "cw-joe-sugarman": "\n\nThe first sentence pulls you in; the rest keeps you reading. No subscription. No cost. Just the list.",
        "cw-gary-bencivenga": "\n\nNo subscription. No auto-ship. No cost. Just the list. (Risk reversed.)",
        "cw-dan-kennedy": "\n\nI'm not sure how long they keep the page up—so if you want the list, the link's below. No fluff.",
        "cw-john-carlton": "\n\nBig promise: see the 5 brands that actually smooth lines, firm skin, and fade spots. Control: one link below. No commitment.",
        "cw-clayton-makepeace": "\n\n• The 5 brands (benefit)\n• Why the dermatology office stands behind them (mechanism)\n• The one ingredient in four of the five (intrigue)\n\nNo subscription. No cost. Just the list.",
        "cw-bob-bly": "\n\nFacts: 5 brands, what each does, where to get them. No signup. No cost. Clear CTA: link below.",
        "cw-claude-hopkins": "\n\nSpecific offer: the 5 brand names, what each does for skin over 45, and where to get them. Free. No signup. Test-ready.",
        "book-cashvertising": "\n\nLife-Force 8: social approval and comfort. What you get: the 5 brands, sensory results, no cost. Link below.",
        "book-breakthrough-advertising": "\n\nOne mass desire (looking like yourself again). Headline doesn't mention product. What you get: the 5 brands, clear. Link below.",
        "book-scientific-advertising": "\n\nSpecific offer: 5 brands, what each does, where to get them. Free. No signup. Preemptive: what the doctors give their wives.",
        "book-influence-cialdini": "\n\nSocial proof: Nina, dozen women. Authority: dermatology office. What you get: the list. No cost. Link below.",
        "book-ogilvy-on-advertising": "\n\nHeadline does the work. What you get: the 5 brands, what each does, where to get them. No signup. Credibility: same list the office uses.",
        "meta-score": "\n\nAlgorithm-friendly: clear CTA, no aggressive caps. What you get: the 5 brands, free. Link below. No engagement bait.",
    }
    return addons.get(scorer_id, "")


def _mock_rewrite(copy_text: str, scorer_id: str | None = None) -> tuple[str, str, str]:
    """Add 90+ structural elements; optional model-specific addon. Returns (revised, summary, scorer_name)."""
    text = copy_text.strip()
    if "God Bless" in text or "god bless" in text.lower():
        inject = (
            "\n\nHere's what you get when you click the link below... nothing fancy. Just a free page that shows:\n\n"
            "• The 5 brands and why the dermatology office stands behind them\n"
            "• What each one does for fine lines, sagging, and dark spots\n"
            "• Where to get them without the markup\n"
            "• Why the doctors give these to their wives\n"
            "• The one ingredient that showed up in four of the five\n\n"
            "No subscription. No auto-ship. No cost. Just the list. "
            "I'm not sure how long they keep the page up, but it's there now.\n\n"
        )
        text = re.sub(r"\s*God Bless.*$", inject + "God Bless ♥️", text, flags=re.I | re.DOTALL)
    else:
        text += (
            "\n\nNo subscription. No auto-ship. No cost. Just the list. "
            "I'm not sure how long they keep the page up, but it's there now.\n\n"
        )
    if "P.S." not in text and "P.P.S." not in text:
        text += (
            "\n\nP.S. The link's below if you want it.\n\n"
            "P.P.S. I don't know how long they keep that page live. It's free and there's nothing to sign up for."
        )
    text = text.strip()
    sid = (scorer_id or "").strip() or "cw-eugene-schwartz"
    name = next((n for s_id, n, _ in SCORERS if s_id == sid), "Eugene Schwartz")
    addon = _model_addon(sid, text)
    if addon:
        text = (text.rstrip() + addon).strip()
    summary = REWRITE_SUMMARIES.get(sid, "Revised to score 90+ for this model.")
    return text, summary, name


class RewriteRequest(BaseModel):
    copy: str
    scorer_id: str | None = None


class RewriteResponse(BaseModel):
    revised: str
    summary: str
    scorer_id: str | None = None
    scorer_name: str | None = None


@app.post("/api/rewrite", response_model=RewriteResponse)
def rewrite(req: RewriteRequest):
    if not (req.copy or "").strip():
        raise HTTPException(status_code=400, detail="Copy is required")
    revised, summary, scorer_name = _mock_rewrite(req.copy, req.scorer_id)
    return RewriteResponse(
        revised=revised,
        summary=summary,
        scorer_id=(req.scorer_id or "cw-eugene-schwartz").strip() or "cw-eugene-schwartz",
        scorer_name=scorer_name,
    )
