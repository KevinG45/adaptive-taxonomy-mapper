"""
Adaptive Taxonomy Mapper

Main entry point for processing test cases and generating
taxonomy mappings with reasoning logs.
"""

import json
import sys
from pathlib import Path

from src.taxonomy_loader import TaxonomyLoader
from src.inference_engine import InferenceEngine
from src.output_handler import OutputHandler


def load_test_cases(filepath: str) -> list:
    """
    Load test cases from JSON file.
    
    Args:
        filepath: Path to test_cases.json
        
    Returns:
        List of test case dictionaries
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Main execution function."""
    base_dir = Path(__file__).parent
    taxonomy_path = base_dir / 'data' / 'taxonomy.json'
    test_cases_path = base_dir / 'data' / 'test_cases.json'
    output_dir = base_dir / 'output'
    
    if not taxonomy_path.exists():
        print(f'Error: Taxonomy file not found at {taxonomy_path}')
        sys.exit(1)
    
    if not test_cases_path.exists():
        print(f'Error: Test cases file not found at {test_cases_path}')
        sys.exit(1)
    
    print('Loading taxonomy...')
    taxonomy = TaxonomyLoader(str(taxonomy_path))
    print(f'Loaded {len(taxonomy.get_all_subcategories())} subcategories')
    
    print('Initializing inference engine...')
    engine = InferenceEngine(taxonomy)
    
    print('Loading test cases...')
    test_cases = load_test_cases(str(test_cases_path))
    print(f'Loaded {len(test_cases)} test cases')
    
    print('')
    print('Processing cases...')
    results = engine.map_batch(test_cases)
    
    output_handler = OutputHandler(str(output_dir))
    
    print('')
    output_handler.print_results(results)
    
    output_file = output_handler.write_json(results)
    print('')
    print(f'Results written to: {output_file}')


if __name__ == '__main__':
    main()
