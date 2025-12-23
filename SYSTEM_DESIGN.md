# System Design

Three questions about scaling this prototype to production.

---

## 1. Scaling to 5,000 categories

Current approach puts all 12 categories in the prompt. At 5,000 categories, that breaks token limits and hurts accuracy.

**Solution: Two-stage classification**

Stage 1: Filter candidates using keyword matching or embedding similarity. Reduce 5,000 to 20-50 relevant categories.

Stage 2: LLM picks from the shortlist. Smaller context, better accuracy.

Stage 3: Validate output. If LLM picks something not in the list, reject or re-run.

---

## 2. Cost at 1 million stories per month

LLM calls get expensive at scale.

**Caching:** Hash snippets, return cached results for duplicates. User content has lots of repetition.

**Batching by similarity:** Cluster similar stories, process one per cluster, apply result to all.

**Tiered models:** Use a small cheap model first. Only escalate to the expensive model for ambiguous cases.

**Async processing:** Queue stories and process in batches during off-peak hours. Better rate limit management.

---

## 3. Preventing hallucinated categories

LLM might invent categories that don't exist in the taxonomy.

**How it's handled:**

1. Prompt lists valid categories explicitly and says "pick from this list only"
2. Temperature set to 0.1 for deterministic output
3. Every LLM response is validated against a whitelist built from taxonomy.json
4. Invalid outputs are rejected, not used

The validation function checks if the category exists before accepting it. If the LLM says "Paranormal Romance" but that's not in the taxonomy, it gets flagged as an error.

---

## Architecture

```
Input (tags + snippet)
       |
       v
Build prompt with rules and category list
       |
       v
LLM call (Groq / Llama 3.3 70B)
       |
       v
Parse response
       |
       v
Validate against taxonomy whitelist
       |
       v
Output (full path or [UNMAPPED])
```

---

## Prompt Design

The prompt has three explicit rules:

1. **Context Wins:** Story content overrides misleading tags
2. **Honesty:** Non-fiction gets [UNMAPPED]
3. **Pick From List:** Only valid categories allowed

Output format is fixed to make parsing reliable:
```
Category: [name]
Reasoning: [one sentence]
```
