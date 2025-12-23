# System Design Document

## Overview

This document addresses three scaling and reliability challenges for the Adaptive Taxonomy Mapper when deployed in a production environment.

---

## 1. Handling a Taxonomy with 5,000 Categories

### Problem

The current implementation uses linear pattern matching against each category. With 5,000 categories, this approach becomes computationally expensive and difficult to maintain.

### Solution: Hierarchical Indexing with Inverted Lookup

**Data Structure Changes:**

```
taxonomy_index = {
    "keyword": ["category_1", "category_5", "category_89"],
    "phrase_pattern": ["category_12", "category_340"],
    ...
}
```

Instead of iterating through all 5,000 categories for each input, build an inverted index mapping keywords and patterns to their associated categories.

**Process:**

1. Extract tokens from input text
2. Query the inverted index to get candidate categories (typically 10-50)
3. Score only the candidate set against full pattern rules
4. Select the highest-scoring match

**Complexity Reduction:**

- Current: O(n) where n = number of categories
- Proposed: O(k) where k = number of matching candidates (k << n)

**Additional Measures:**

- Group categories by parent genre first (e.g., filter to "Horror" subcategories before detailed matching)
- Cache frequently matched patterns using an LRU cache
- Store patterns in a trie structure for prefix-based matching

---

## 2. Minimizing Costs at 1 Million Stories per Month

### Problem

Processing 1 million stories monthly requires optimization for both compute time and, if using external services, API costs.

### Solution: Tiered Processing Pipeline

**Tier 1: Rule-Based Fast Path (handles ~70% of cases)**

The current deterministic engine handles clear-cut cases with no external dependencies. Stories with high-confidence matches (score > threshold) are resolved here.

Cost: Near zero (CPU only)

**Tier 2: Batch Processing with Caching**

For the remaining 30%:

1. **Content Hashing:** Generate a hash of normalized text. Check cache for previously processed identical or near-identical content.

2. **Similarity Clustering:** Group similar stories and process representative samples. Apply results to cluster members.

3. **Batch Windows:** Accumulate low-confidence cases and process in scheduled batches during off-peak hours.

**Tier 3: Human Review Queue (edge cases only)**

Stories that fail both automated tiers go to a review queue. Human decisions feed back into the rule set.

**Cost Estimates (1M stories/month):**

| Tier | Volume | Cost |
|------|--------|------|
| Rule-based | 700,000 | Compute only |
| Cached/Batched | 280,000 | Minimal |
| Human Review | 20,000 | Labor cost |

**Infrastructure:**

- Use message queues (Redis, RabbitMQ) for async processing
- Horizontal scaling with stateless workers
- Store results in a lookup table to avoid reprocessing

---

## 3. Preventing Hallucinated Sub-Genres

### Problem

A system must never output a category that does not exist in the taxonomy. This is critical for downstream recommendation engines.

### Solution: Output Validation Layer

**Approach 1: Closed Vocabulary Enforcement**

The inference engine only outputs values from a pre-loaded whitelist:

```python
VALID_SUBCATEGORIES = taxonomy.get_all_subcategories()

def validate_output(category):
    if category.lower() not in VALID_SUBCATEGORIES:
        return "[UNMAPPED]"
    return category
```

Every output passes through this gate before being returned.

**Approach 2: Structured Output Schema**

Define the output as an enum rather than free text:

```python
from enum import Enum

class Subcategory(Enum):
    SLOW_BURN = "Slow-burn"
    ENEMIES_TO_LOVERS = "Enemies-to-Lovers"
    # ... all valid categories
```

The engine returns enum members, making invalid outputs impossible at the type level.

**Approach 3: Post-Processing Verification**

If using any probabilistic component in future:

1. Parse the output
2. Fuzzy-match against the taxonomy (handle minor variations)
3. Reject if similarity score below threshold
4. Log rejected outputs for pattern analysis

**Current Implementation:**

This prototype uses Approach 1. The `TaxonomyLoader` class maintains a set of valid subcategories, and `InferenceEngine.map_single()` only returns categories present in that set. Content that cannot be mapped is explicitly marked `[UNMAPPED]` rather than forced into an incorrect category.

---

## Architecture Summary

```
Input (tags + snippet)
        |
        v
+-------------------+
|  Text Analyzer    |  <- Keyword extraction, pattern matching
+-------------------+
        |
        v
+-------------------+
|  Inference Engine |  <- Scoring, category selection
+-------------------+
        |
        v
+-------------------+
|  Taxonomy Loader  |  <- Validation against whitelist
+-------------------+
        |
        v
Output (full path or [UNMAPPED])
```

---

## Trade-offs and Decisions

| Decision | Rationale |
|----------|-----------|
| Rule-based over LLM | Deterministic, no API costs, no hallucination risk |
| NLTK for tokenization | Lightweight, well-tested, no network dependency |
| Keyword + phrase patterns | Balances precision with maintainability |
| Explicit [UNMAPPED] | Preserves taxonomy integrity over forced mappings |

---

## Future Improvements

1. Add confidence thresholds to flag borderline cases for review
2. Implement pattern learning from human-corrected mappings
3. Support multi-label classification for ambiguous content
4. Add A/B testing framework to measure mapping quality
