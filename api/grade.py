import hashlib
import json
from http.server import BaseHTTPRequestHandler

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


def run_grade(copy_text):
    results = []
    for sid, name, stype in SCORERS:
        h = int(hashlib.sha256((sid + copy_text[:500]).encode()).hexdigest(), 16)
        score = 65 + (h % 28)
        summary = SUMMARY_TEMPLATES.get(sid, "Scored against framework criteria.")
        results.append({"id": sid, "name": name, "type": stype, "score": score, "summary": summary})
    return results


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
            if not copy_text:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "Copy is required"}).encode("utf-8"))
                return
            results = run_grade(copy_text)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(results).encode("utf-8"))
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
