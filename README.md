# Adaptive Taxonomy Mapper

Maps messy user-generated tags to a structured internal taxonomy using LLM-based classification.

## The Problem

Users tag stories with vague terms like "Love" or "Scary". The recommendation engine needs precise categories like "Enemies-to-Lovers" or "Gothic Horror".

## How It Works

1. Story snippet and user tags go into a prompt with explicit classification rules
2. LLM (Llama 3.3 70B via Groq) picks the best category
3. Output is validated against the taxonomy to prevent hallucination
4. Non-fiction content gets flagged as [UNMAPPED]

## Three Core Rules

- **Context Wins**: Story content overrides misleading tags
- **Honesty**: Content outside the taxonomy is not force-fitted
- **Hierarchy**: Only categories from taxonomy.json are allowed

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file with your Groq API key:
```
GROQ_API_KEY=your_key_here
```

## Run

```bash
python main.py
```

Results go to console and `output/results.json`.

## Project Structure

```
├── data/
│   ├── taxonomy.json       # Category hierarchy
│   └── test_cases.json     # 10 test cases
├── src/
│   ├── taxonomy_loader.py  # Loads and queries taxonomy
│   ├── inference_engine.py # LLM classification + validation
│   └── output_handler.py   # Result formatting
├── main.py                 # Entry point
├── SYSTEM_DESIGN.md        # Scaling questions answered
└── REASONING_LOG.md        # Why each case was mapped that way
```
