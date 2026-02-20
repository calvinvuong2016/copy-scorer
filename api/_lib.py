# Shared logic for Vercel serverless functions (grade + rewrite)
import re
import hashlib

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


def mock_score(scorer_id: str, copy_text: str) -> int:
    h = int(hashlib.sha256((scorer_id + copy_text[:500]).encode()).hexdigest(), 16)
    return 65 + (h % 28)


def run_grade(copy_text: str) -> list:
    results = []
    for sid, name, stype in SCORERS:
        score = mock_score(sid, copy_text)
        summary = SUMMARY_TEMPLATES.get(sid, "Scored against framework criteria.")
        results.append({"id": sid, "name": name, "type": stype, "score": score, "summary": summary})
    return results


def mock_rewrite(copy_text: str) -> str:
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


def run_rewrite(copy_text: str) -> dict:
    revised = mock_rewrite(copy_text)
    summary = (
        "Revised copy adds: clearer offer (what they get), 5 bullets (benefit + mechanism + intrigue), "
        "risk reversal (no subscription/auto-ship/cost), and P.S./P.P.S. for proof and light urgency. "
        "Goal: score 90+ across CW, Book, and Meta criteria."
    )
    return {"revised": revised, "summary": summary}
