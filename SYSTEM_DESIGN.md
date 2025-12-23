# System Design Document

## What This Document Covers

There are three practical questions that come up when thinking about taking this prototype to production. I have addressed each below.

---

## 1. What if the taxonomy grows to 5,000 categories?

The current prompt includes all 12 subcategories directly in the context. With 5,000 categories, that would blow past token limits and make the model less accurate.

Here is how I would handle it:

**Stage 1: Narrow down candidates first**

Before calling the LLM, run a lightweight filter to reduce 5,000 categories to maybe 20-50 candidates. This could be:
- Keyword matching between the snippet and category names/descriptions
- Embedding similarity (vectorize the snippet, compare against pre-computed category embeddings)
- A fast classifier that predicts the parent genre (Romance, Horror, Sci-Fi, etc.)

**Stage 2: LLM picks from the shortlist**

The prompt now only includes the 20-50 candidate categories. The model has enough context to make a good decision without being overwhelmed.

**Stage 3: Validate and fallback**

If the LLM picks something not in the candidate list (unlikely but possible), either reject it or run a second pass with a broader candidate set.

This two-stage approach keeps the LLM focused while scaling to large taxonomies.

---

## 2. How do you keep costs down at 1 million stories per month?

LLM API calls add up fast. At 1 million stories, even cheap models become expensive.

**Strategy 1: Cache aggressively**

Hash each story snippet and check if we have seen it before. Duplicate or near-duplicate content gets the cached result. In a platform with user-generated content, duplicates are common.

**Strategy 2: Batch by similarity**

Group similar stories together using embeddings or simple text hashing. Process one representative story from each cluster, apply the result to the whole cluster. This can cut API calls by 50-70% for repetitive content.

**Strategy 3: Use a tiered model approach**

- Tier 1: Run a small, cheap model first (like Llama 3.3 8B or a fine-tuned classifier)
- Tier 2: Only escalate to the larger model (70B) for ambiguous cases where Tier 1 confidence is low

For this prototype I used Llama 3.3 70B through Groq, which has generous free tier limits. In production, you could run smaller models locally or use a mix of providers.

**Strategy 4: Async batch processing**

Instead of processing stories in real-time, queue them and process in batches during off-peak hours. This allows for better rate limit management and lets you take advantage of batch pricing.

---

## 3. How do you prevent the system from inventing categories?

This is the hallucination problem. The LLM might confidently output "Paranormal Romance" even though that category does not exist in the taxonomy.

**How I handled it in this prototype:**

The `_validate_category` function checks every LLM output against a whitelist built from taxonomy.json. If the output does not match any valid subcategory, it gets rejected.

```
LLM says "Paranormal Romance"
    |
    v
Check: is "Paranormal Romance" in valid_categories?
    |
    v
No -> Mark as error, do not use this output
```

**Additional safeguards for production:**

1. **Constrained output format**: The prompt explicitly lists valid categories and asks the model to pick from that list only. This reduces (but does not eliminate) hallucination.

2. **Temperature control**: I set temperature to 0.1 to make outputs more deterministic and less creative.

3. **Fuzzy matching fallback**: If the model outputs something close but not exact (like "Gothic Horror" instead of "Gothic"), the validator can fuzzy-match to the closest valid category.

4. **Logging and alerts**: Track cases where validation fails. If a pattern emerges (model keeps inventing the same category), that is a signal to either add that category or adjust the prompt.

The key insight is: never trust LLM output directly. Always validate against the source of truth (the taxonomy JSON).

---

## How the pieces fit together

```
Story comes in (tags + snippet)
       |
       v
Build prompt with taxonomy categories and rules
       |
       v
Call LLM (Groq/Llama 3.3 70B)
       |
       v
Parse response to extract category and reasoning
       |
       v
Validate category against taxonomy whitelist
       |
       v
Result goes out (full path like Fiction > Horror > Gothic, or [UNMAPPED])
```

---

## Prompt Design

The prompt follows a structured format:

1. **Role definition**: "You are a story classifier for a fiction platform"
2. **Rules section**: Three explicit rules (Context Wins, Honesty, Pick From List)
3. **Valid categories**: Listed explicitly to constrain output
4. **Input section**: User tags and story snippet clearly labeled
5. **Output format**: Exact format specified to make parsing reliable

This structure gives the model clear constraints while allowing it to reason about the content.

---

## Why I made these choices

| Choice | Reason |
|--------|--------|
| Groq + Llama 3.3 70B | Free tier, fast inference, good reasoning ability |
| Low temperature (0.1) | More deterministic outputs, less hallucination |
| Explicit output format | Makes response parsing reliable |
| Whitelist validation | Catches any hallucinated categories before they reach production |
| Separate reasoning field | Provides transparency into model decisions |
