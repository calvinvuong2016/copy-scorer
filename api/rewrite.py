import json
import os
import re
from http.server import BaseHTTPRequestHandler

# Same order as grade.py — all models can rewrite individually
SCORERS = [
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
    ("book-cashvertising", "Cashvertising", "book"),
    ("book-breakthrough-advertising", "Breakthrough Advertising", "book"),
    ("book-scientific-advertising", "Scientific Advertising", "book"),
    ("book-influence-cialdini", "Influence (Cialdini)", "book"),
    ("book-ogilvy-on-advertising", "Ogilvy on Advertising", "book"),
    ("meta-score", "Meta Scorer", "meta"),
]

SCORER_SUMMARIES = {
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


# Per-model injected block: (intro_line, bullet_block, closer_line, ps_line, pps_line)
# Each model gets a visibly different middle section so rewrites don't all look the same.
_MODEL_BLOCKS = {
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


def _rewrite_by_model(text, scorer_id):
    """Build revised copy using this model's intro, bullets, closer, and P.S. (template fallback)."""
    t = text.strip()
    block = _MODEL_BLOCKS.get(scorer_id, _MODEL_BLOCKS["cw-eugene-schwartz"])
    intro, bullets, closer, ps, pps = block
    if "God Bless" in t or "god bless" in t.lower():
        inject = "\n\n" + intro + bullets + closer + "God Bless ♥️\n\n"
        t = re.sub(r"\s*God Bless.*$", inject, t, flags=re.I | re.DOTALL)
    else:
        t += "\n\n" + intro + bullets + closer
    if "P.S." not in t and "P.P.S." not in t:
        t += "\n\n" + ps + "\n\n" + pps
    return t.strip()


def _skills_dir():
    """Directory containing scorer framework .md files (api/skills)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")


def _load_skill_prompt(scorer_id):
    """Load framework content from api/skills/{scorer_id}.md. Try __file__ path then cwd/api/skills (Vercel)."""
    filename = scorer_id + ".md"
    for base in [_skills_dir(), os.path.join(os.getcwd(), "api", "skills")]:
        if not base:
            continue
        path = os.path.join(base, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            continue
    return None


# Injected when loading framework for REWRITE so the model does full replacement, not "revise weak spots".
_REWRITE_MODE_OVERRIDE = """
--- REWRITE TASK (override any "revision" workflow in the framework below) ---
You are doing a FULL REPLACEMENT, not a patch. Do not "revise by fixing the lowest-scoring elements" or "add a revision at the end." Write the entire ad from scratch in your voice. Same offer and key facts; every sentence rewritten. The document below is for your voice and 90+ criteria only.
"""

_REWRITE_SYSTEM_PREFIX = """You ARE the copywriter (or book framework) described below. The document is YOUR methodology and what 90+ means on your rubric. Your job: write a COMPLETE REPLACEMENT of the ad as you would write it, so it would score 90+.

--- CRITICAL: COMPLETE REPLACEMENT ONLY ---
- Your output must be a NEW ad. Same offer, same product, same audience—but YOU write every sentence. Opening = your first sentence (not the original's). Body = your phrasing and structure. Close = your closing (e.g. your P.S.), not the original's close.
- FAILURE (forbidden): Returning the original ad with the same or nearly same opening and body, then adding a new block (e.g. "Here's what you get...", bullets, "P.S. The link below..."). That is a tacked-on ending. Reject that approach.
- SUCCESS: A standalone ad that starts with YOUR opening line, flows in YOUR voice, and ends with YOUR close. Total length in the same ballpark as the original; no long add-on at the end.
- Before returning, check: (1) Is my first sentence different from the original's first sentence? (2) Is my ending my own close, not the original's last paragraph plus new lines? If either is no, rewrite.

--- STAY IN CHARACTER ---
- Use your rubric's 90–100 row. Satisfy every element you score (awareness, mechanism, one-reader voice, headline, proof, etc.). No methodology jargon in the ad—no "awareness", "mechanism", "borrowed interest", copywriter or book names. Only selling copy.

--- OUTPUT ---
- Natural language, 3rd–5th grade level. No AI patterns (no triplets, no "not just X but Y").
- Valid JSON only: {"revised": "<full revised copy>", "summary": "<one short sentence>"}. Newlines as \\n in "revised".

Your framework (how YOU score and what 90+ means):
"""


def _rewrite_via_claude(copy_text, scorer_id, scorer_name):
    """Call Claude to rewrite copy. Returns (revised, summary, True) on success, or (None, reason, False) on failure."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not api_key.strip():
        return None, "ANTHROPIC_API_KEY is not set. Add it in Vercel: Project → Settings → Environment Variables (Production + Preview), then redeploy.", False
    framework = _load_skill_prompt(scorer_id)
    if not framework:
        return None, "Writer framework file not found on server. Ensure api/skills/ is deployed with your project.", False
    try:
        import anthropic
    except ImportError:
        return None, "anthropic package missing. Add anthropic to api/requirements.txt and redeploy.", False
    system = _REWRITE_SYSTEM_PREFIX + _REWRITE_MODE_OVERRIDE + framework
    user = f"""You are {scorer_name}. Output a COMPLETE REPLACEMENT of the ad below: your opening sentence, your body, your close. Do not keep the original and add a new block at the end—that is invalid. Same offer and facts; every line in your voice so it would score 90+ on your rubric. No jargon or your name in the ad.

Return only this JSON: {{"revised": "<full revised ad>", "summary": "<one short sentence>"}}.

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
        # Strip markdown code fence if present
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        revised = (data.get("revised") or "").strip()
        summary = (data.get("summary") or "").strip() or SCORER_SUMMARIES.get(scorer_id, "Revised to score 90+ for this model.")
        if not revised:
            return None, None, False
        # If opening unchanged, retry once with stricter instruction
        def first_line(s):
            return (s or "").strip().split("\n")[0].strip()[:120]
        if first_line(revised) == first_line(copy_text):
            retry_user = f"""Your previous response was invalid: the opening was unchanged. You MUST output a COMPLETE REPLACEMENT. Your first sentence must be DIFFERENT from the original. Rewrite the entire ad from the top in your voice. Return only JSON: {{"revised": "<full revised ad>", "summary": "<one short sentence>"}}.

ORIGINAL COPY:
{copy_text}"""
            try:
                msg2 = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=system,
                    messages=[{"role": "user", "content": retry_user}],
                )
                text2 = ""
                for block in getattr(msg2, "content", []):
                    if getattr(block, "type", None) == "text":
                        text2 += getattr(block, "text", "") or ""
                text2 = text2.strip()
                if text2.startswith("```"):
                    text2 = re.sub(r"^```(?:json)?\s*", "", text2)
                    text2 = re.sub(r"\s*```$", "", text2)
                data2 = json.loads(text2)
                revised2 = (data2.get("revised") or "").strip()
                if revised2 and first_line(revised2) != first_line(copy_text):
                    revised, summary = revised2, (data2.get("summary") or summary or "").strip()
            except Exception:
                pass
        return revised, summary, True
    except Exception as e:
        err = str(e).strip() or "Unknown error"
        if len(err) > 200:
            err = err[:197] + "..."
        return None, "Claude API error: " + err + ". Check ANTHROPIC_API_KEY and redeploy.", False


def rewrite_by_model(copy_text, scorer_id):
    scorer_id = (scorer_id or "").strip() or "cw-eugene-schwartz"
    name = next((n for sid, n, _ in SCORERS if sid == scorer_id), "Eugene Schwartz")
    revised, summary, llm_used = _rewrite_via_claude(copy_text, scorer_id, name)
    if not llm_used:
        revised = copy_text
        # summary already has the specific reason from _rewrite_via_claude
    return {
        "revised": revised,
        "summary": summary,
        "scorer_id": scorer_id,
        "scorer_name": name,
        "llm_used": llm_used,
    }


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            data = json.loads(body) if body.strip() else {}
            copy_text = (data.get("copy") or "").strip()
            scorer_id = (data.get("scorer_id") or "").strip() or "cw-eugene-schwartz"
            if not copy_text:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "Copy is required"}).encode("utf-8"))
                return
            result = rewrite_by_model(copy_text, scorer_id)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"detail": str(e)}).encode("utf-8"))

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
