"""
Inference Engine Module

Core mapping logic that combines taxonomy lookup with text analysis
to determine the best category mapping for user content.
"""

from typing import Optional
from src.taxonomy_loader import TaxonomyLoader
from src.text_analyzer import TextAnalyzer


class MappingResult:
    """Represents the result of a taxonomy mapping operation."""
    
    def __init__(
        self,
        case_id: int,
        user_tags: list,
        snippet: str,
        mapped_category: Optional[str],
        full_path: Optional[str],
        reasoning: str,
        is_unmapped: bool = False,
        is_error: bool = False,
        confidence_score: float = 0.0
    ):
        self.case_id = case_id
        self.user_tags = user_tags
        self.snippet = snippet
        self.mapped_category = mapped_category
        self.full_path = full_path
        self.reasoning = reasoning
        self.is_unmapped = is_unmapped
        self.is_error = is_error
        self.confidence_score = confidence_score
    
    def to_dict(self) -> dict:
        """Convert result to dictionary for JSON serialization."""
        return {
            'id': self.case_id,
            'user_tags': self.user_tags,
            'snippet': self.snippet,
            'mapped_category': self.mapped_category if not self.is_unmapped else '[UNMAPPED]',
            'full_path': self.full_path if not self.is_unmapped else None,
            'reasoning': self.reasoning,
            'is_unmapped': self.is_unmapped,
            'is_error': self.is_error,
            'confidence_score': round(self.confidence_score, 2)
        }


class InferenceEngine:
    """
    Maps user-tagged content to the internal taxonomy using rule-based inference.
    
    Implements three core rules:
    1. Context Wins: Story content overrides misleading user tags
    2. Honesty: Content outside taxonomy scope is marked [UNMAPPED]
    3. Hierarchy: Mappings follow the defined taxonomy structure
    """
    
    def __init__(self, taxonomy_loader: TaxonomyLoader):
        self.taxonomy = taxonomy_loader
        self.analyzer = TextAnalyzer()
    
    def map_single(self, case_id: int, user_tags: list, snippet: str) -> MappingResult:
        """
        Map a single piece of content to the taxonomy.
        
        Args:
            case_id: Unique identifier for the case
            user_tags: List of user-provided tags
            snippet: Story description/blurb
            
        Returns:
            MappingResult with category assignment and reasoning
        """
        try:
            unmapped_check = self.analyzer.check_unmapped(snippet, user_tags)
            if unmapped_check['is_unmapped']:
                reasoning = self._build_unmapped_reasoning(unmapped_check)
                return MappingResult(
                    case_id=case_id,
                    user_tags=user_tags,
                    snippet=snippet,
                    mapped_category=None,
                    full_path=None,
                    reasoning=reasoning,
                    is_unmapped=True,
                    confidence_score=unmapped_check['confidence']
                )
            
            category_scores = self.analyzer.calculate_category_scores(snippet, user_tags)
            
            if not category_scores:
                return MappingResult(
                    case_id=case_id,
                    user_tags=user_tags,
                    snippet=snippet,
                    mapped_category=None,
                    full_path=None,
                    reasoning='No matching patterns found in content or tags.',
                    is_unmapped=True,
                    confidence_score=0.0
                )
            
            best_category = self._select_best_category(category_scores, user_tags)
            full_path = self.taxonomy.get_full_path(best_category)
            reasoning = self._build_mapping_reasoning(
                best_category, 
                category_scores[best_category], 
                user_tags
            )
            
            max_score = category_scores[best_category]['score']
            confidence = min(max_score / 5.0, 1.0)
            
            return MappingResult(
                case_id=case_id,
                user_tags=user_tags,
                snippet=snippet,
                mapped_category=best_category,
                full_path=full_path,
                reasoning=reasoning,
                is_unmapped=False,
                confidence_score=confidence
            )
            
        except Exception as e:
            return MappingResult(
                case_id=case_id,
                user_tags=user_tags,
                snippet=snippet,
                mapped_category=None,
                full_path=None,
                reasoning=f'Processing error: {str(e)}',
                is_error=True,
                confidence_score=0.0
            )
    
    def _select_best_category(self, scores: dict, user_tags: list) -> str:
        """
        Select the best category from scored candidates.
        
        Context (snippet analysis) takes priority over user tags.
        
        Args:
            scores: Dict mapping category names to score info
            user_tags: Original user tags (for reference only)
            
        Returns:
            Name of the best matching category
        """
        sorted_categories = sorted(
            scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        return sorted_categories[0][0]
    
    def _build_mapping_reasoning(
        self, 
        category: str, 
        score_info: dict, 
        user_tags: list
    ) -> str:
        """
        Construct explanation for why a category was selected.
        
        Args:
            category: The selected category
            score_info: Scoring details including matched terms
            user_tags: Original user tags
            
        Returns:
            Human-readable reasoning string
        """
        parts = []
        
        tag_str = ', '.join(user_tags)
        parts.append(f'User tags: [{tag_str}].')
        
        if score_info['matched_keywords']:
            keywords = ', '.join(score_info['matched_keywords'][:5])
            parts.append(f'Content keywords matched: {keywords}.')
        
        if score_info['matched_phrases']:
            parts.append(f'Phrase patterns detected: {len(score_info["matched_phrases"])}.')
        
        hierarchy = self.taxonomy.get_hierarchy_info(category)
        if hierarchy:
            parts.append(
                f'Mapped to {hierarchy["subcategory"]} under {hierarchy["parent"]}.'
            )
        
        tag_lower = [t.lower() for t in user_tags]
        category_hints = self._get_category_parent(category)
        if category_hints and not any(category_hints.lower() in t for t in tag_lower):
            parts.append('Context analysis overrode user tags.')
        
        return ' '.join(parts)
    
    def _build_unmapped_reasoning(self, unmapped_info: dict) -> str:
        """
        Construct explanation for why content was marked unmapped.
        
        Args:
            unmapped_info: Detection info from text analyzer
            
        Returns:
            Human-readable reasoning string
        """
        parts = ['Content does not fit the fiction taxonomy.']
        
        if unmapped_info['matched_keywords']:
            keywords = ', '.join(unmapped_info['matched_keywords'][:5])
            parts.append(f'Non-fiction indicators: {keywords}.')
        
        if unmapped_info['matched_phrases']:
            parts.append('Instructional/recipe pattern detected.')
        
        parts.append('Marked as [UNMAPPED] to maintain taxonomy integrity.')
        
        return ' '.join(parts)
    
    def _get_category_parent(self, category: str) -> Optional[str]:
        """Get the parent category name for a subcategory."""
        info = self.taxonomy.get_hierarchy_info(category)
        if info:
            return info['parent']
        return None
    
    def map_batch(self, cases: list) -> list:
        """
        Process multiple cases in batch.
        
        Args:
            cases: List of dicts with id, user_tags, and snippet keys
            
        Returns:
            List of MappingResult objects
        """
        results = []
        for case in cases:
            result = self.map_single(
                case_id=case['id'],
                user_tags=case['user_tags'],
                snippet=case['snippet']
            )
            results.append(result)
        return results
