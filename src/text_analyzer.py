"""
Text Analyzer Module

Provides rule-based text preprocessing, keyword extraction,
and semantic pattern matching for story classification.
"""

import re
from typing import Optional

try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class TextAnalyzer:
    """
    Rule-based text analyzer for extracting semantic signals from story content.
    
    Uses keyword patterns and phrase matching to identify genre indicators.
    """
    
    def __init__(self):
        self._init_nltk()
        self._build_pattern_rules()
    
    def _init_nltk(self) -> None:
        """Initialize NLTK resources if available."""
        self.lemmatizer = None
        self.stop_words = set()
        
        if NLTK_AVAILABLE:
            try:
                self.stop_words = set(stopwords.words('english'))
                self.lemmatizer = WordNetLemmatizer()
            except LookupError:
                pass
    
    def _build_pattern_rules(self) -> None:
        """
        Define semantic patterns that map to taxonomy subcategories.
        
        Each pattern is a dict with:
        - keywords: list of terms that indicate this category
        - phrases: list of multi-word patterns
        - negative: terms that reduce confidence
        - weight: base importance of this category
        """
        self.category_patterns = {
            'enemies-to-lovers': {
                'keywords': ['hate', 'hated', 'enemy', 'enemies', 'rival', 'rivalry', 
                            'despise', 'loathe', 'antagonist', 'compete', 'competition'],
                'phrases': [
                    r'hated\s+each\s+other',
                    r'couldn\'t\s+stand',
                    r'worst\s+enemy',
                    r'changed\s+everything',
                    r'fell\s+in\s+love',
                    r'unexpected\s+(love|feelings)',
                ],
                'context_requires': ['love', 'romance', 'relationship', 'together', 'feelings'],
                'weight': 1.0
            },
            'slow-burn': {
                'keywords': ['years', 'slowly', 'gradual', 'time', 'patience', 'waiting',
                            'friendship', 'friends', 'eventually'],
                'phrases': [
                    r'over\s+the\s+years',
                    r'slowly\s+(fell|developed|grew)',
                    r'friends\s+first',
                    r'took\s+time',
                ],
                'context_requires': ['love', 'romance', 'feelings'],
                'weight': 0.8
            },
            'second chance': {
                'keywords': ['again', 'reunion', 'reunite', 'return', 'years', 'past',
                            'memory', 'memories', 'regret', 'wonder', 'gray-haired', 'older'],
                'phrases': [
                    r'met\s+again',
                    r'years\s+(later|after)',
                    r'what\s+could\s+have\s+been',
                    r'second\s+chance',
                    r'came\s+back',
                    r'after\s+the\s+war',
                ],
                'context_requires': ['love', 'romance', 'relationship', 'together'],
                'weight': 1.0
            },
            'espionage': {
                'keywords': ['spy', 'spies', 'agent', 'mission', 'secret', 'covert',
                            'intelligence', 'cia', 'mi6', 'kremlin', 'kgb', 'undercover',
                            'operative', 'classified', 'infiltrate'],
                'phrases': [
                    r'secret\s+mission',
                    r'without\s+being\s+detected',
                    r'stolen\s+(drive|documents|files|intel)',
                    r'double\s+agent',
                    r'enemy\s+territory',
                ],
                'context_requires': [],
                'weight': 1.0
            },
            'psychological': {
                'keywords': ['mind', 'mental', 'paranoia', 'paranoid', 'obsession', 
                            'obsessed', 'sanity', 'insane', 'delusion', 'perception',
                            'reality', 'manipulation', 'gaslight'],
                'phrases': [
                    r'losing\s+(his|her|their)\s+mind',
                    r'can\'t\s+trust',
                    r'what\s+is\s+real',
                    r'playing\s+mind\s+games',
                ],
                'context_requires': [],
                'weight': 0.9
            },
            'legal thriller': {
                'keywords': ['lawyer', 'attorney', 'judge', 'court', 'trial', 'verdict',
                            'jury', 'prosecution', 'defense', 'witness', 'testimony',
                            'cross-examination', 'courtroom', 'legal', 'law'],
                'phrases': [
                    r'before\s+the\s+judge',
                    r'cross[\-\s]examination',
                    r'opening\s+statement',
                    r'the\s+jury',
                    r'your\s+honor',
                    r'fate\s+of',
                ],
                'context_requires': [],
                'weight': 1.2
            },
            'hard sci-fi': {
                'keywords': ['physics', 'science', 'ftl', 'light-speed', 'quantum',
                            'stasis', 'cryogenic', 'metabolic', 'propulsion', 'orbit',
                            'trajectory', 'radiation', 'gravity', 'engineering'],
                'phrases': [
                    r'ftl\s+travel',
                    r'faster\s+than\s+light',
                    r'deep\s+dive\s+into',
                    r'the\s+physics\s+of',
                    r'long[\-\s]term\s+stasis',
                    r'scientific\s+(accuracy|detail)',
                ],
                'context_requires': [],
                'weight': 1.0
            },
            'space opera': {
                'keywords': ['empire', 'galactic', 'fleet', 'starship', 'interstellar',
                            'rebellion', 'planets', 'alien', 'aliens', 'federation',
                            'captain', 'crew', 'space', 'battle'],
                'phrases': [
                    r'galactic\s+(empire|war|federation)',
                    r'across\s+the\s+(galaxy|stars)',
                    r'space\s+battle',
                    r'alien\s+(race|species)',
                ],
                'context_requires': [],
                'weight': 0.9
            },
            'cyberpunk': {
                'keywords': ['neon', 'cyber', 'hack', 'hacker', 'corporate', 'dystopia',
                            'augment', 'implant', 'virtual', 'ai', 'android', 'tokyo',
                            'megacity', 'tech', 'futuristic', 'digital'],
                'phrases': [
                    r'neon[\-\s]drenched',
                    r'neon[\-\s]lit',
                    r'ai\s+operating\s+system',
                    r'virtual\s+reality',
                    r'corporate\s+(control|dystopia)',
                    r'high[\-\s]tech.*low[\-\s]life',
                ],
                'context_requires': [],
                'weight': 1.0
            },
            'psychological horror': {
                'keywords': ['dread', 'terror', 'fear', 'paranoia', 'nightmare',
                            'hallucination', 'disturbing', 'unsettling', 'creeping'],
                'phrases': [
                    r'losing\s+(his|her|their)\s+grip',
                    r'can\'t\s+escape',
                    r'in\s+(his|her|their)\s+mind',
                ],
                'context_requires': ['horror', 'scary', 'fear', 'terror'],
                'weight': 0.9
            },
            'gothic': {
                'keywords': ['mansion', 'victorian', 'old', 'ancient', 'estate', 'manor',
                            'corridors', 'whisper', 'whispers', 'secrets', 'dark', 'past',
                            'family', 'curse', 'haunted', 'atmosphere', 'brooding', 'decay'],
                'phrases': [
                    r'old\s+(victorian|mansion|manor|estate)',
                    r'victorian\s+mansion',
                    r'seemed\s+to\s+breathe',
                    r'dark\s+past',
                    r'family\'?s?\s+(dark\s+)?secret',
                    r'whispering\s+secrets',
                    r'corridors\s+whisper',
                ],
                'context_requires': [],
                'weight': 1.0
            },
            'slasher': {
                'keywords': ['killer', 'murder', 'stalk', 'stalks', 'masked', 'mask',
                            'victim', 'victims', 'teenagers', 'teens', 'camp', 'cabin',
                            'woods', 'knife', 'blood', 'chase', 'survive', 'survival'],
                'phrases': [
                    r'masked\s+killer',
                    r'stalks\s+(a\s+group|the|them)',
                    r'group\s+of\s+teenagers',
                    r'summer\s+camp',
                    r'one\s+by\s+one',
                    r'pick\s+them\s+off',
                ],
                'context_requires': [],
                'weight': 1.0
            }
        }
        
        self.unmapped_indicators = {
            'keywords': ['recipe', 'cook', 'bake', 'ingredient', 'ingredients',
                        'instructions', 'how-to', 'tutorial', 'guide', 'diy',
                        'build', 'construct', 'steps', 'degrees', 'cups', 'flour',
                        'sugar', 'mix', 'stir', 'household', 'items', 'backyard'],
            'phrases': [
                r'how\s+to\s+(build|make|cook|bake)',
                r'step[\-\s]by[\-\s]step',
                r'cups?\s+of\s+\w+',
                r'bake\s+at\s+\d+\s+degrees',
                r'mix\s+(with|together)',
                r'using\s+(basic\s+)?household\s+items',
            ]
        }
    
    def preprocess(self, text: str) -> str:
        """
        Clean and normalize text for analysis.
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned lowercase text
        """
        text = text.lower()
        text = re.sub(r'[^\w\s\'-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_tokens(self, text: str) -> list:
        """
        Extract meaningful tokens from text.
        
        Args:
            text: Preprocessed text
            
        Returns:
            List of tokens with stopwords removed
        """
        text = self.preprocess(text)
        
        if NLTK_AVAILABLE:
            try:
                tokens = word_tokenize(text)
            except LookupError:
                tokens = text.split()
        else:
            tokens = text.split()
        
        tokens = [t for t in tokens if t not in self.stop_words and len(t) > 2]
        
        if self.lemmatizer:
            tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
        
        return tokens
    
    def calculate_category_scores(self, text: str, tags: list) -> dict:
        """
        Calculate match scores for each taxonomy category.
        
        Args:
            text: The story snippet/blurb
            tags: User-provided tags
            
        Returns:
            Dict mapping category names to score dicts with score and matched terms
        """
        processed_text = self.preprocess(text)
        processed_tags = [t.lower() for t in tags]
        combined_text = processed_text + ' ' + ' '.join(processed_tags)
        
        scores = {}
        
        for category, patterns in self.category_patterns.items():
            score = 0.0
            matched_keywords = []
            matched_phrases = []
            
            for keyword in patterns['keywords']:
                if keyword in processed_text:
                    score += 1.0
                    matched_keywords.append(keyword)
            
            for phrase_pattern in patterns['phrases']:
                if re.search(phrase_pattern, processed_text):
                    score += 2.0
                    matched_phrases.append(phrase_pattern)
            
            context_required = patterns.get('context_requires', [])
            if context_required:
                context_found = any(ctx in combined_text for ctx in context_required)
                if not context_found:
                    score *= 0.3
            
            score *= patterns.get('weight', 1.0)
            
            if score > 0:
                scores[category] = {
                    'score': score,
                    'matched_keywords': matched_keywords,
                    'matched_phrases': matched_phrases
                }
        
        return scores
    
    def check_unmapped(self, text: str, tags: list) -> dict:
        """
        Check if content matches unmapped (non-fiction) patterns.
        
        Args:
            text: The story snippet
            tags: User-provided tags
            
        Returns:
            Dict with is_unmapped boolean and matched indicators
        """
        processed_text = self.preprocess(text)
        processed_tags = [t.lower() for t in tags]
        
        matched_keywords = []
        matched_phrases = []
        
        for keyword in self.unmapped_indicators['keywords']:
            if keyword in processed_text or keyword in processed_tags:
                matched_keywords.append(keyword)
        
        for phrase_pattern in self.unmapped_indicators['phrases']:
            if re.search(phrase_pattern, processed_text):
                matched_phrases.append(phrase_pattern)
        
        keyword_count = len(matched_keywords)
        phrase_count = len(matched_phrases)
        
        is_unmapped = (keyword_count >= 3) or (phrase_count >= 1 and keyword_count >= 1)
        
        return {
            'is_unmapped': is_unmapped,
            'matched_keywords': matched_keywords,
            'matched_phrases': matched_phrases,
            'confidence': min((keyword_count + phrase_count * 2) / 5.0, 1.0)
        }
    
    def get_tag_hints(self, tags: list) -> list:
        """
        Extract potential category hints from user tags.
        
        Maps common tag words to possible categories.
        
        Args:
            tags: User-provided tags
            
        Returns:
            List of (tag, suggested_category) tuples
        """
        tag_mappings = {
            'love': ['romance', 'enemies-to-lovers', 'slow-burn', 'second chance'],
            'romance': ['romance', 'slow-burn', 'enemies-to-lovers'],
            'scary': ['horror', 'psychological horror', 'gothic', 'slasher'],
            'horror': ['horror', 'psychological horror', 'gothic', 'slasher'],
            'ghost': ['gothic', 'psychological horror'],
            'action': ['thriller', 'espionage'],
            'spies': ['espionage'],
            'spy': ['espionage'],
            'space': ['sci-fi', 'space opera', 'hard sci-fi'],
            'future': ['sci-fi', 'cyberpunk', 'space opera'],
            'robots': ['sci-fi', 'hard sci-fi', 'cyberpunk'],
            'sad': ['second chance', 'slow-burn'],
            'house': ['gothic'],
        }
        
        hints = []
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in tag_mappings:
                hints.append((tag, tag_mappings[tag_lower]))
        
        return hints
