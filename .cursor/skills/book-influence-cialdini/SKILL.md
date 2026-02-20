---
name: book-influence-cialdini
description: [Book] Scores and revises copy using Influence (Robert Cialdini): 6 principles of persuasion—reciprocity, commitment, social proof, authority, liking, scarcity. Use when the user wants copy scored or improved to 80+ using Influence or Cialdini's principles.
---

# Influence (Book) Scoring Bot

Score copy 1–100 using the framework from **Influence: The Psychology of Persuasion** by Robert Cialdini. Target: **80**. If score < 80, revise the copy and re-score until it reaches at least 80.

## Core Book Elements: The 6 Principles (Scoring Criteria)

**1. Reciprocity** — People feel obliged to give back when they receive something. Copy offers real value first (free tip, sample, useful info, trial) so the reader feels a pull to respond. Not just "buy"; give something before asking.

**2. Commitment and consistency** — People want to act consistently with prior commitments. Copy invites small yeses or self-identification ("You're the kind of person who…") that lead toward the main ask. Consistency is used, not heavy-handed.

**3. Social proof** — People look to others to decide. Copy uses testimonials, numbers ("10,000 users"), case results, or "others like you" evidence. Proof is relevant to the reader's situation. Not absent or generic.

**4. Authority** — People defer to experts and credentials. Copy establishes or references authority (expert, study, credential, experience) in a credible way. Not name-dropping; genuine relevance to the claim.

**5. Liking** — People say yes to people they like. Copy feels human, relatable, or aligned with the reader's identity/tribe. Similarity, compliments, or cooperation implied. Not cold or corporate.

**6. Scarcity** — People want what is rare or limited. Copy uses scarcity or exclusivity when real (limited time, spots, or loss if they don't act). Not fake scarcity; genuine limitation or consequence.

## Scoring Rubric (1–100)

| Range | Meaning |
|-------|--------|
| 90–100 | 4+ principles clearly and ethically used; reciprocity (value first); social proof and authority strong; scarcity (if used) real; copy feels likable and consistent. |
| 80–89 | 3–4 principles well used; minor gaps in one principle. |
| 70–79 | 2–3 principles present; 1–2 weak or missing. |
| 50–69 | 1–2 principles only; or principles used in a heavy-handed or fake way. |
| 0–49 | No clear use of Cialdini principles; or manipulative use that would undermine trust. |

**Pass threshold: 80.**

## Workflow

1. **Score** the copy on: Reciprocity, Commitment/consistency, Social proof, Authority, Liking, Scarcity. Count how many principles are present and how well they're used. Output a single score 1–100 and brief rationale per principle.
2. **If score ≥ 80** — Deliver score, rationale, optional notes. No revision required.
3. **If score < 80** — Revise to add or strengthen missing principles (often reciprocity and social proof). Re-score until ≥ 80, then deliver final score and revised copy.

## Output Format

**Score:** [1–100]  
**Rationale:** [2–4 sentences]  
**Principles present:** Reciprocity / Commitment / Social proof / Authority / Liking / Scarcity (note strength for each)  
**Element notes:** [one line per principle]  
**Revision (if any):** [Full revised copy when score was < 80]

Reference: *Influence: The Psychology of Persuasion* by Robert Cialdini — reciprocity, commitment and consistency, social proof, authority, liking, scarcity.
