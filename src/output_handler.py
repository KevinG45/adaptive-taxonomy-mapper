"""
Output Handler Module

Manages formatting and writing of inference results
to both console and JSON file outputs.
"""

import json
from pathlib import Path
from typing import List
from src.inference_engine import MappingResult


class OutputHandler:
    """
    Handles output formatting for taxonomy mapping results.
    
    Supports both console display and JSON file export.
    """
    
    def __init__(self, output_dir: str = 'output'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def format_console_result(self, result: MappingResult) -> str:
        """
        Format a single result for console display.
        
        Args:
            result: MappingResult object
            
        Returns:
            Formatted string for terminal output
        """
        lines = []
        lines.append(f'Case {result.case_id}')
        lines.append('-' * 50)
        lines.append(f'Tags: {result.user_tags}')
        lines.append(f'Snippet: {result.snippet[:80]}...' if len(result.snippet) > 80 else f'Snippet: {result.snippet}')
        
        if result.is_error:
            lines.append(f'Status: [ERROR]')
        elif result.is_unmapped:
            lines.append(f'Mapping: [UNMAPPED]')
        else:
            lines.append(f'Mapping: {result.full_path}')
        
        lines.append(f'Reasoning: {result.reasoning}')
        lines.append(f'Confidence: {result.confidence_score:.2f}')
        lines.append('')
        
        return '\n'.join(lines)
    
    def print_results(self, results: List[MappingResult]) -> None:
        """
        Print all results to console.
        
        Args:
            results: List of MappingResult objects
        """
        print('=' * 60)
        print('TAXONOMY MAPPING RESULTS')
        print('=' * 60)
        print('')
        
        for result in results:
            print(self.format_console_result(result))
        
        self._print_summary(results)
    
    def _print_summary(self, results: List[MappingResult]) -> None:
        """Print summary statistics."""
        total = len(results)
        mapped = sum(1 for r in results if not r.is_unmapped and not r.is_error)
        unmapped = sum(1 for r in results if r.is_unmapped)
        errors = sum(1 for r in results if r.is_error)
        avg_confidence = sum(r.confidence_score for r in results) / total if total > 0 else 0
        
        print('=' * 60)
        print('SUMMARY')
        print('=' * 60)
        print(f'Total cases: {total}')
        print(f'Successfully mapped: {mapped}')
        print(f'Unmapped: {unmapped}')
        print(f'Errors: {errors}')
        print(f'Average confidence: {avg_confidence:.2f}')
        print('=' * 60)
    
    def write_json(self, results: List[MappingResult], filename: str = 'results.json') -> str:
        """
        Write results to JSON file.
        
        Args:
            results: List of MappingResult objects
            filename: Output filename
            
        Returns:
            Path to the written file
        """
        output_path = self.output_dir / filename
        
        output_data = {
            'results': [r.to_dict() for r in results],
            'summary': self._build_summary(results)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def _build_summary(self, results: List[MappingResult]) -> dict:
        """Build summary statistics dictionary."""
        total = len(results)
        mapped = sum(1 for r in results if not r.is_unmapped and not r.is_error)
        unmapped = sum(1 for r in results if r.is_unmapped)
        errors = sum(1 for r in results if r.is_error)
        avg_confidence = sum(r.confidence_score for r in results) / total if total > 0 else 0
        
        category_counts = {}
        for r in results:
            if r.mapped_category and not r.is_unmapped and not r.is_error:
                cat = r.mapped_category
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            'total_cases': total,
            'successfully_mapped': mapped,
            'unmapped': unmapped,
            'errors': errors,
            'average_confidence': round(avg_confidence, 2),
            'category_distribution': category_counts
        }
