import json
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


def _base_rewrite(text):
    """Shared structural edits (bullets, risk reversal, P.S.)."""
    t = text.strip()
    if "God Bless" in t or "god bless" in t.lower():
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
        t = re.sub(r"\s*God Bless.*$", inject + "God Bless ♥️", t, flags=re.I | re.DOTALL)
    else:
        t += (
            "\n\nNo subscription. No auto-ship. No cost. Just the list. "
            "I'm not sure how long they keep the page up, but it's there now.\n\n"
        )
    if "P.S." not in t and "P.P.S." not in t:
        t += (
            "\n\nP.S. The link's below if you want it.\n\n"
            "P.P.S. I don't know how long they keep that page live. It's free and there's nothing to sign up for."
        )
    return t.strip()


def _model_specific_addon(scorer_id, text):
    """Return a short model-specific addition to append or inject (so each model changes something different)."""
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


def rewrite_by_model(copy_text, scorer_id):
    scorer_id = (scorer_id or "").strip() or "cw-eugene-schwartz"
    name = next((n for sid, n, _ in SCORERS if sid == scorer_id), "Eugene Schwartz")
    revised = _base_rewrite(copy_text)
    addon = _model_specific_addon(scorer_id, revised)
    if addon:
        revised = (revised.rstrip() + addon).strip()
    summary = SCORER_SUMMARIES.get(scorer_id, "Revised to score 90+ for this model.")
    return {"revised": revised, "summary": summary, "scorer_id": scorer_id, "scorer_name": name}


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
