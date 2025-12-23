"""
Inference Engine - classifies stories using Groq LLM with prompt engineering.
"""

import os
import re
from typing import Optional
from dataclasses import dataclass

from groq import Groq
from dotenv import load_dotenv

from src.taxonomy_loader import TaxonomyLoader

load_dotenv()


@dataclass
class MappingResult:
    """Result of a taxonomy mapping operation."""
    case_id: int
    user_tags: list
    snippet: str
    mapped_category: Optional[str]
    full_path: Optional[str]
    reasoning: str
    is_unmapped: bool = False
    is_error: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            'id': self.case_id,
            'user_tags': self.user_tags,
            'snippet': self.snippet,
            'mapped_category': self.mapped_category if not self.is_unmapped else '[UNMAPPED]',
            'full_path': self.full_path,
            'reasoning': self.reasoning,
            'is_unmapped': self.is_unmapped,
            'is_error': self.is_error
        }


class InferenceEngine:
    """
    Classifies stories into taxonomy categories using Groq API.
    
    Two-stage approach:
    1. LLM classifies based on content (not just tags)
    2. Output validated against taxonomy whitelist
    """

    def __init__(self, taxonomy: TaxonomyLoader):
        self.taxonomy = taxonomy
        self.valid_categories = self._build_category_list()
        self._init_client()

    def _init_client(self):
        """Initialize Groq API client."""
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError('GROQ_API_KEY not found in environment')

        self.client = Groq(api_key=api_key)
        self.model = 'llama-3.3-70b-versatile'

    def _build_category_list(self) -> list:
        """Build formatted list of valid categories for the prompt."""
        categories = []
        for subcat in self.taxonomy.get_all_subcategories():
            info = self.taxonomy.get_hierarchy_info(subcat)
            if info:
                categories.append(f"{info['parent']} > {info['subcategory']}")
        return sorted(categories)

    def _build_prompt(self, user_tags: list, snippet: str) -> str:
        """
        Build the classification prompt.
        
        Embeds three core rules:
        - Context Wins: story content overrides misleading tags
        - Honesty: non-fiction gets [UNMAPPED]
        - Pick From List: only valid categories allowed
        """
        categories_str = '\n'.join(f'  - {cat}' for cat in self.valid_categories)
        tags_str = ', '.join(user_tags)

        return f"""You are a story classifier for a fiction platform. Map the story to exactly one category from the list below.

RULES:
1. CONTEXT WINS: The story snippet matters more than user tags. If tags say "Action" but the story is about a courtroom, pick "Legal Thriller".
2. HONESTY: If the content is NOT fiction (recipes, how-to guides, instructions), respond with UNMAPPED.
3. PICK FROM LIST ONLY: Only use categories from the list below. Never invent new ones.

VALID CATEGORIES:
{categories_str}

INPUT:
User Tags: [{tags_str}]
Story Snippet: "{snippet}"

OUTPUT FORMAT:
Category: [subcategory name only, like "Gothic" or "Espionage", or UNMAPPED]
Reasoning: [one sentence explanation]"""

    def _parse_response(self, response_text: str) -> tuple:
        """Extract category and reasoning from LLM response."""
        category = None
        reasoning = ''

        for line in response_text.strip().split('\n'):
            line = line.strip()
            if line.lower().startswith('category:'):
                category = line.split(':', 1)[1].strip()
            elif line.lower().startswith('reasoning:'):
                reasoning = line.split(':', 1)[1].strip()

        # Fallback: search for category name in response if parsing failed
        if category is None:
            all_subcats = [c.split(' > ')[-1] for c in self.valid_categories]
            pattern = r'\b(UNMAPPED|' + '|'.join(re.escape(s) for s in all_subcats) + r')\b'
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                category = match.group(1)

        return category, reasoning

    def _validate_category(self, category: str) -> Optional[str]:
        """Validate category exists in taxonomy. Returns None if invalid."""
        if category is None:
            return None

        category_clean = category.strip('[]').strip()

        if category_clean.upper() == 'UNMAPPED':
            return 'UNMAPPED'

        # Check against valid categories list
        for valid_cat in self.valid_categories:
            subcategory = valid_cat.split(' > ')[-1]
            if subcategory.lower() == category_clean.lower():
                return subcategory

        # Fallback check against taxonomy directly
        if self.taxonomy.is_valid_subcategory(category_clean):
            info = self.taxonomy.get_hierarchy_info(category_clean)
            if info:
                return info['subcategory']

        return None

    def map_single(self, case_id: int, user_tags: list, snippet: str) -> MappingResult:
        """Classify a single story using the LLM."""
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
            validated = self._validate_category(raw_category)

            # Validation failed
            if validated is None:
                return MappingResult(
                    case_id=case_id,
                    user_tags=user_tags,
                    snippet=snippet,
                    mapped_category=None,
                    full_path=None,
                    reasoning=f'Could not validate LLM output: {raw_category}',
                    is_unmapped=True,
                    is_error=True
                )

            # Content is not fiction
            if validated == 'UNMAPPED':
                return MappingResult(
                    case_id=case_id,
                    user_tags=user_tags,
                    snippet=snippet,
                    mapped_category=None,
                    full_path=None,
                    reasoning=reasoning or 'Content does not fit fiction taxonomy.',
                    is_unmapped=True
                )

            # Successfully classified
            return MappingResult(
                case_id=case_id,
                user_tags=user_tags,
                snippet=snippet,
                mapped_category=validated,
                full_path=self.taxonomy.get_full_path(validated),
                reasoning=reasoning or 'Classified based on story content.'
            )

        except Exception as e:
            return MappingResult(
                case_id=case_id,
                user_tags=user_tags,
                snippet=snippet,
                mapped_category=None,
                full_path=None,
                reasoning=f'Error: {str(e)}',
                is_unmapped=True,
                is_error=True
            )

    def map_batch(self, cases: list) -> list:
        """Process multiple cases sequentially."""
        results = []
        for case in cases:
            print(f"  Case {case['id']}...")
            result = self.map_single(case['id'], case['user_tags'], case['snippet'])
            results.append(result)
        return results
