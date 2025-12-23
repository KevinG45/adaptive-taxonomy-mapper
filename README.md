# Adaptive Taxonomy Mapper

A rule-based inference engine that maps user-generated content tags to a structured internal taxonomy.

## Overview

This prototype prioritizes deterministic, explainable logic over probabilistic LLM outputs to ensure taxonomy integrity and prevent hallucinations.

## Features

- Context-aware mapping: Story content overrides misleading user tags
- Hierarchy compliance: Outputs follow the defined taxonomy structure
- Unmapped detection: Flags content that does not fit the taxonomy
- Reasoning logs: Each mapping includes an explanation

## Requirements

- Python 3.10+
- nltk

## Installation

```bash
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

## Usage

```bash
python main.py
```

Output is written to both console and `output/results.json`.

## Project Structure

```
adaptive-taxonomy-mapper/
├── data/
│   ├── taxonomy.json      # Internal category hierarchy
│   └── test_cases.json    # Golden set of 10 test cases
├── src/
│   ├── taxonomy_loader.py # Taxonomy parsing and lookup
│   ├── text_analyzer.py   # Text preprocessing and keyword extraction
│   ├── inference_engine.py# Core mapping logic
│   └── output_handler.py  # Result formatting
├── output/                # Generated results
├── main.py               # Entry point
├── requirements.txt
└── SYSTEM_DESIGN.md      # Architecture decisions
```

## License

For evaluation purposes only.
