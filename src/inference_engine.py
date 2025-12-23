"""
Inference Engine Module

Uses Groq API (Llama 3.3 70B) to classify stories into taxonomy categories.
Implements prompt design and output validation to prevent hallucination.
"""

import json
import re
import os
from typing import Optional

from groq import Groq
from dotenv import load_dotenv

from src.taxonomy_loader import TaxonomyLoader


load_dotenv()


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
        is_error: bool = False
    ):
        self.case_id = case_id
        self.user_tags = user_tags
        self.snippet = snippet
        self.mapped_category = mapped_category
        self.full_path = full_path
        self.reasoning = reasoning
        self.is_unmapped = is_unmapped
        self.is_error = is_error
    
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
            'is_error': self.is_error
        }


class InferenceEngine:
    """
    Maps user-tagged content to the internal taxonomy using Groq API.
    
    The engine uses a two-stage approach:
    1. Classification: LLM analyzes content and selects a category
    2. Validation: Output is checked against the taxonomy whitelist
    """
    
    def __init__(self, taxonomy_loader: TaxonomyLoader):
        self.taxonomy = taxonomy_loader
        self.valid_categories = self._build_category_list()
        self._init_groq()
    
    def _init_groq(self):
        """Initialize the Groq API client."""
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError('GROQ_API_KEY not found in environment variables')
        
        self.client = Groq(api_key=api_key)
        self.model = 'llama-3.3-70b-versatile'
    
    def _build_category_list(self) -> list:
        """Build a formatted list of valid categories for the prompt."""
        categories = []
        for subcategory in self.taxonomy.get_all_subcategories():
            info = self.taxonomy.get_hierarchy_info(subcategory)
            if info:
                categories.append(f"{info['parent']} > {info['subcategory']}")
        return sorted(categories)
    
    def _build_prompt(self, user_tags: list, snippet: str) -> str:
        """
        Construct the classification prompt.
        
        The prompt embeds the three core rules:
        - Context Wins: Story content overrides misleading tags
        - Honesty: Use [UNMAPPED] for content outside taxonomy
        - Hierarchy: Pick from the provided category list only
        """
        categories_str = '\n'.join(f'  - {cat}' for cat in self.valid_categories)
        tags_str = ', '.join(user_tags)
        
        prompt = f"""You are a story classifier for a fiction platform. Map the story to exactly one category from the list below.

RULES YOU MUST FOLLOW:
1. CONTEXT WINS: The story snippet matters more than user tags. If tags say "Action" but the story describes a courtroom, pick "Legal Thriller" not action-related categories.
2. HONESTY: If the content is NOT fiction (like recipes, how-to guides, instructions, non-fiction), you must respond with UNMAPPED.
3. PICK FROM LIST ONLY: You can only choose from the categories below. Never invent new categories.

VALID CATEGORIES:
{categories_str}

INPUT:
User Tags: [{tags_str}]
Story Snippet: "{snippet}"

OUTPUT FORMAT (follow exactly):
Category: [write the subcategory name only, like "Gothic" or "Espionage", or write UNMAPPED]
Reasoning: [one sentence why you picked this]"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> tuple:
        """
        Parse the LLM response to extract category and reasoning.
        
        Returns:
            Tuple of (category, reasoning)
        """
        category = None
        reasoning = ''
        
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith('category:'):
                category = line.split(':', 1)[1].strip()
            elif line.lower().startswith('reasoning:'):
                reasoning = line.split(':', 1)[1].strip()
        
        if category is None:
            all_subcats = [c.split(' > ')[-1] for c in self.valid_categories]
            pattern = r'\b(UNMAPPED|' + '|'.join(re.escape(s) for s in all_subcats) + r')\b'
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                category = match.group(1)
        
        return category, reasoning
    
    def _validate_category(self, category: str) -> Optional[str]:
        """
        Validate that the category exists in the taxonomy.
        
        Returns:
            The validated category name or None if invalid
        """
        if category is None:
            return None
        
        category_clean = category.strip('[]').strip()
        
        if category_clean.upper() == 'UNMAPPED':
            return 'UNMAPPED'
        
        for valid_cat in self.valid_categories:
            subcategory = valid_cat.split(' > ')[-1]
            if subcategory.lower() == category_clean.lower():
                return subcategory
        
        if self.taxonomy.is_valid_subcategory(category_clean):
            info = self.taxonomy.get_hierarchy_info(category_clean)
            if info:
                return info['subcategory']
        
        return None
    
    def map_single(self, case_id: int, user_tags: list, snippet: str) -> MappingResult:
        """
        Map a single piece of content to the taxonomy using the LLM.
        
        Args:
            case_id: Unique identifier for the case
            user_tags: List of user-provided tags
            snippet: Story description/blurb
            
        Returns:
            MappingResult with category assignment and reasoning
        """
        try:
            prompt = self._build_prompt(user_tags, snippet)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content
            
            raw_category, reasoning = self._parse_response(response_text)
            
            validated_category = self._validate_category(raw_category)
            
            if validated_category is None:
                return MappingResult(
                    case_id=case_id,
                    user_tags=user_tags,
                    snippet=snippet,
                    mapped_category=None,
                    full_path=None,
                    reasoning=f'LLM response could not be validated. Raw: {raw_category}',
                    is_unmapped=True,
                    is_error=True
                )
            
            if validated_category == 'UNMAPPED':
                return MappingResult(
                    case_id=case_id,
                    user_tags=user_tags,
                    snippet=snippet,
                    mapped_category=None,
                    full_path=None,
                    reasoning=reasoning if reasoning else 'Content does not fit the fiction taxonomy.',
                    is_unmapped=True,
                    is_error=False
                )
            
            full_path = self.taxonomy.get_full_path(validated_category)
            
            return MappingResult(
                case_id=case_id,
                user_tags=user_tags,
                snippet=snippet,
                mapped_category=validated_category,
                full_path=full_path,
                reasoning=reasoning if reasoning else 'Classified based on story content.',
                is_unmapped=False,
                is_error=False
            )
            
        except Exception as e:
            return MappingResult(
                case_id=case_id,
                user_tags=user_tags,
                snippet=snippet,
                mapped_category=None,
                full_path=None,
                reasoning=f'Error during classification: {str(e)}',
                is_unmapped=True,
                is_error=True
            )
    
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
            print(f"Processing case {case['id']}...")
            result = self.map_single(
                case_id=case['id'],
                user_tags=case['user_tags'],
                snippet=case['snippet']
            )
            results.append(result)
        return results
