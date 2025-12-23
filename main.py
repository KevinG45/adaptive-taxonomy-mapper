"""
Entry point for the Adaptive Taxonomy Mapper.
Loads test cases, runs classification, and outputs results.
"""

import json
import sys
from pathlib import Path

from src.taxonomy_loader import TaxonomyLoader
from src.inference_engine import InferenceEngine
from src.output_handler import OutputHandler


def load_test_cases(filepath: str) -> list:
    """Load test cases from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    base_dir = Path(__file__).parent
    taxonomy_path = base_dir / 'data' / 'taxonomy.json'
    test_cases_path = base_dir / 'data' / 'test_cases.json'
    output_dir = base_dir / 'output'

    # Validate required files exist
    if not taxonomy_path.exists():
        print(f'Error: Taxonomy file not found at {taxonomy_path}')
        sys.exit(1)

    if not test_cases_path.exists():
        print(f'Error: Test cases file not found at {test_cases_path}')
        sys.exit(1)

    # Load taxonomy and build lookup maps
    print('Loading taxonomy...')
    taxonomy = TaxonomyLoader(str(taxonomy_path))
    print(f'Loaded {len(taxonomy.get_all_subcategories())} subcategories')

    # Initialize the LLM-based inference engine
    print('Initializing inference engine...')
    engine = InferenceEngine(taxonomy)

    # Load and process test cases
    print('Loading test cases...')
    test_cases = load_test_cases(str(test_cases_path))
    print(f'Loaded {len(test_cases)} test cases\n')

    print('Processing...')
    results = engine.map_batch(test_cases)

    # Output results to console and JSON file
    output_handler = OutputHandler(str(output_dir))
    print('')
    output_handler.print_results(results)

    output_file = output_handler.write_json(results)
    print(f'\nResults written to: {output_file}')


if __name__ == '__main__':
    main()
