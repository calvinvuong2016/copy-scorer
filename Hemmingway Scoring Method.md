# Hemingway Scoring Method — Reference Guide

## THE FORMULA

Use the **Automated Readability Index (ARI)**:

```
Reading Level = round(4.71 × (characters ÷ words) + 0.5 × (words ÷ sentences) − 21.43)
```

### How to Count

- **Characters**: Letters and numbers ONLY. No spaces, no punctuation, no special characters.
- **Words**: Split by spaces. Hyphenated words count as one word.
- **Sentences**: Split by `.` `?` `!` — Treat `...` (ellipses) as ONE sentence break. A sentence that ends with `...` counts as one sentence. `--` does NOT end a sentence.

---

## COLOR-CODED FLAGS

### Yellow Flag — Hard-to-Read Sentences
A sentence is **hard to read** if BOTH are true:
- 14 or more words
- Sentence-level ARI score between 10 and 13

### Red Flag — Very Hard-to-Read Sentences
A sentence is **very hard to read** if BOTH are true:
- 14 or more words
- Sentence-level ARI score of 14 or higher

### Blue Flag — Adverbs
- Any word ending in `-ly` that functions as an adverb
- **NOT adverbs** (skip these): family, friendly, lonely, lovely, ugly, costly, holy, likely, only, early, daily, rally, belly, bully, ally, jolly, silly, wooly, reply, apply, supply, multiply, Italy, July
- **Target**: No more than 1 adverb per 100 words
- Example: 200 word copy = max 2 adverbs

### Green Flag — Passive Voice
Look for these patterns:
- `was/were` + past participle (was broken, were told)
- `is/are` + past participle (is known, are made)
- `has been/have been` + past participle (has been shown)
- `being` + past participle (being handled)
- **Target**: No more than 1 instance per 100 words

### Purple Flag — Complex Words
Any word with **3+ syllables** that has a simpler alternative:
- connected → tied to, linked
- eligibility → ability to get it
- qualifying → who can get it
- coverage → plan
- exclusively → only
- immediately → right now, now
- approximately → about, around
- unfortunately → sadly
- situations → spots, cases
- arrangements → plans
- experienced → felt, seen, had
- emotional → upset, raw
- expensive → pricey, costly
- insurance → coverage, plan
- industry → business
- exaggerating → making it up
- everything → all of it
- perfecting → getting good at
- convinced → sold on, sure

---

## SCORING THRESHOLDS

| Reading Level | Assessment |
|---|---|
| 4-6 | PASS — Great for ad copy |
| 7-8 | NEEDS WORK — Too high for ads, fine for articles |
| 9-10 | POOR — Average adult reading level, too complex for ads |
| 11+ | FAIL — Academic level, way too complex |

---

## HOW TO GRADE A SENTENCE

For each sentence, calculate its own ARI score:

1. Count characters (letters/numbers only) in that sentence
2. Count words in that sentence
3. The sentence count = 1 (since it's one sentence)
4. Plug into: `4.71 × (chars ÷ words) + 0.5 × (words ÷ 1) − 21.43`
5. Round to nearest whole number

If the sentence is 14+ words AND scores 10-13 → Yellow flag
If the sentence is 14+ words AND scores 14+ → Red flag

---

## WHAT DRIVES THE SCORE UP

In order of impact:

1. **Long sentences** — The single biggest factor. More words per sentence = higher score.
2. **Long words** — Words with many characters raise the characters-per-word ratio.
3. **Few sentence breaks** — Not enough periods, question marks, or exclamation points.

## WHAT DRIVES THE SCORE DOWN

1. **Shorter sentences** — Break long sentences into two.
2. **Simpler words** — Swap multi-syllable words for shorter ones.
3. **More sentence breaks** — Add periods. Turn commas into periods where possible.
