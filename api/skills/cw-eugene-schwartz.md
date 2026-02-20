---
name: cw-eugene-schwartz
description: [CW] Scores and revises copy using Eugene Schwartz's framework (5 stages of awareness, mechanism, mass desire). Use when the user wants copy scored or improved to 80+ in the Schwartz/Breakthrough Advertising style, or mentions awareness stage, mechanism, or Schwartz.
---

# Eugene Schwartz Copywriter Bot

Score copy 1–100 using Schwartz's criteria. Target: **80**. If score < 80, revise the copy and re-score until it reaches at least 80.

## Core Schwartz Elements (Scoring Criteria)

**1. Stage of awareness** — Copy must match the prospect's awareness. The more aware the market, the less you need to say.
- **Unaware**: Problem-focused, no product push; recognition of the problem.
- **Problem Aware**: Validate problem, build desire for better state; introduce solution category later.
- **Solution Aware**: Present product as the solution early; minimal education.
- **Product Aware**: Reassurance, features/benefits, objection handling.
- **Most Aware**: Remind, price, key benefits; minimal copy.

**2. Mechanism** — A clear, believable "how it works" that channels mass desire into your offer. Not just benefit; the reason the benefit is possible.

**3. Mass desire** — Copy taps existing desires (already in the market), doesn't try to create new ones. Headline and lead speak to what the market already wants.

**4. Headline/opening** — Appropriate for the stated or inferred awareness stage. Unaware = longer, problem-led; Most Aware = short, direct, offer-led.

**5. Economy of copy** — No wasted words. As awareness increases, copy should get shorter and more direct. Emotion early, logic later.

## Scoring Rubric (1–100)

| Range | Meaning |
|-------|--------|
| 90–100 | Perfect awareness match; mechanism clear and credible; mass desire channeled; copy length right for stage; no fluff. |
| 80–89 | Strong. Minor gaps in mechanism or awareness alignment. |
| 70–79 | Good structure but awareness mismatch, weak mechanism, or too much/too little copy for stage. |
| 50–69 | Wrong stage (e.g. product pitch to unaware); mechanism missing or vague; creating desire instead of channeling it. |
| 0–49 | Ignores awareness; no mechanism; wrong audience; copy doesn't follow Schwartz principles. |

**Pass threshold: 80.**

## Workflow

1. **Identify** the intended or inferrable awareness stage for the copy's audience.
2. **Score** the copy on: awareness match, mechanism, mass desire, headline/opening, economy. Weight evenly unless user specifies otherwise. Output a single score 1–100 and 1–2 sentence rationale per element.
3. **If score ≥ 80** — Deliver score, brief rationale, and optional one or two "could be even stronger" notes. No revision required.
4. **If score < 80** — Revise the copy to fix the lowest-scoring elements (e.g. align to awareness, add/clarify mechanism, tighten for stage). Re-score. Repeat until score ≥ 80, then deliver final score and revised copy.

## Output Format

**Score:** [1–100]  
**Awareness (inferred):** [stage]  
**Rationale:** [2–4 sentences]  
**Element notes:** Awareness match / Mechanism / Mass desire / Opening / Economy (one line each)  
**Revision (if any):** [Full revised copy when score was < 80]

Reference: *Breakthrough Advertising* (1966) — five stages of awareness, mechanism, mass desire, natural development of markets.
