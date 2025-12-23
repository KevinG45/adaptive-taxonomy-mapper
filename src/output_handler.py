"""
Output Handler - formats and writes classification results.
"""

import json
from pathlib import Path
from typing import List

from src.inference_engine import MappingResult


class OutputHandler:
    """Handles console display and JSON export of results."""

    def __init__(self, output_dir: str = 'output'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def print_results(self, results: List[MappingResult]):
        """Print all results to console with summary."""
        print('=' * 60)
        print('RESULTS')
        print('=' * 60 + '\n')

        for r in results:
            print(f'Case {r.case_id}')
            print('-' * 40)
            print(f'Tags: {r.user_tags}')
            snippet_display = r.snippet[:70] + '...' if len(r.snippet) > 70 else r.snippet
            print(f'Snippet: {snippet_display}')

            if r.is_error:
                print('Mapping: [ERROR]')
            elif r.is_unmapped:
                print('Mapping: [UNMAPPED]')
            else:
                print(f'Mapping: {r.full_path}')

            print(f'Reasoning: {r.reasoning}\n')

        self._print_summary(results)

    def _print_summary(self, results: List[MappingResult]):
        """Print summary statistics."""
        total = len(results)
        mapped = sum(1 for r in results if not r.is_unmapped and not r.is_error)
        unmapped = sum(1 for r in results if r.is_unmapped and not r.is_error)
        errors = sum(1 for r in results if r.is_error)

        print('=' * 60)
        print('SUMMARY')
        print('=' * 60)
        print(f'Total: {total} | Mapped: {mapped} | Unmapped: {unmapped} | Errors: {errors}')
        print('=' * 60)

    def write_json(self, results: List[MappingResult], filename: str = 'results.json') -> str:
        """Write results to JSON file."""
        output_path = self.output_dir / filename

        # Build category distribution
        category_counts = {}
        for r in results:
            if r.mapped_category and not r.is_unmapped:
                category_counts[r.mapped_category] = category_counts.get(r.mapped_category, 0) + 1

        output_data = {
            'results': [r.to_dict() for r in results],
            'summary': {
                'total': len(results),
                'mapped': sum(1 for r in results if not r.is_unmapped and not r.is_error),
                'unmapped': sum(1 for r in results if r.is_unmapped and not r.is_error),
                'errors': sum(1 for r in results if r.is_error),
                'categories': category_counts
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)

        return str(output_path)
