import json
import re
from http.server import BaseHTTPRequestHandler


def mock_rewrite(copy_text):
    text = copy_text.strip()
    if "God Bless" in text or "god bless" in text.lower():
        inject_before = (
            "\n\nHere's what you get when you click the link below... nothing fancy. Just a free page that shows:\n\n"
            "• The 5 brands and why the dermatology office stands behind them\n"
            "• What each one does for fine lines, sagging, and dark spots\n"
            "• Where to get them without the markup\n"
            "• Why the doctors give these to their wives\n"
            "• The one ingredient that showed up in four of the five\n\n"
            "No subscription. No auto-ship. No cost. Just the list. "
            "I'm not sure how long they keep the page up, but it's there now.\n\n"
        )
        text = re.sub(r"\s*God Bless.*$", inject_before + "God Bless ♥️", text, flags=re.I | re.DOTALL)
    else:
        inject_before = (
            "\n\nNo subscription. No auto-ship. No cost. Just the list. "
            "I'm not sure how long they keep the page up, but it's there now.\n\n"
        )
        text = text + inject_before
    if "P.S." not in text and "P.P.S." not in text:
        text += (
            "\n\nP.S. The link's below if you want it.\n\n"
            "P.P.S. I don't know how long they keep that page live. It's free and there's nothing to sign up for."
        )
    return text.strip()


def run_rewrite(copy_text):
    revised = mock_rewrite(copy_text)
    summary = (
        "Revised copy adds: clearer offer (what they get), 5 bullets (benefit + mechanism + intrigue), "
        "risk reversal (no subscription/auto-ship/cost), and P.S./P.P.S. for proof and light urgency. "
        "Goal: score 90+ across CW, Book, and Meta criteria."
    )
    return {"revised": revised, "summary": summary}


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
            result = run_rewrite(copy_text)
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
