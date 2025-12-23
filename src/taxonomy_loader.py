"""
Taxonomy Loader Module

Handles loading the taxonomy JSON and building lookup structures
for efficient category resolution.
"""

import json
from pathlib import Path
from typing import Optional


class TaxonomyLoader:
    """Loads and manages the internal taxonomy hierarchy."""
    
    def __init__(self, taxonomy_path: str):
        self.taxonomy_path = Path(taxonomy_path)
        self.raw_taxonomy: dict = {}
        self.subcategory_map: dict = {}
        self.parent_map: dict = {}
        self.all_subcategories: set = set()
        self._load()
    
    def _load(self) -> None:
        """Load taxonomy from JSON file and build lookup structures."""
        with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
            self.raw_taxonomy = json.load(f)
        self._build_maps()
    
    def _build_maps(self) -> None:
        """
        Build flattened lookup maps from the nested taxonomy.
        
        Creates:
        - subcategory_map: subcategory -> (root, parent, subcategory)
        - parent_map: parent -> list of subcategories
        - all_subcategories: set of all valid subcategory names
        """
        for root_category, genres in self.raw_taxonomy.items():
            for parent_category, subcategories in genres.items():
                self.parent_map[parent_category.lower()] = [s.lower() for s in subcategories]
                for subcategory in subcategories:
                    key = subcategory.lower()
                    self.subcategory_map[key] = {
                        'root': root_category,
                        'parent': parent_category,
                        'subcategory': subcategory
                    }
                    self.all_subcategories.add(key)
    
    def get_full_path(self, subcategory: str) -> Optional[str]:
        """
        Get the full taxonomy path for a subcategory.
        
        Args:
            subcategory: The subcategory name (case-insensitive)
            
        Returns:
            Full path string like 'Fiction > Horror > Gothic' or None if not found
        """
        key = subcategory.lower()
        if key not in self.subcategory_map:
            return None
        
        info = self.subcategory_map[key]
        return f"{info['root']} > {info['parent']} > {info['subcategory']}"
    
    def get_hierarchy_info(self, subcategory: str) -> Optional[dict]:
        """
        Get structured hierarchy information for a subcategory.
        
        Args:
            subcategory: The subcategory name (case-insensitive)
            
        Returns:
            Dict with root, parent, subcategory keys or None if not found
        """
        key = subcategory.lower()
        return self.subcategory_map.get(key)
    
    def is_valid_subcategory(self, name: str) -> bool:
        """Check if a name is a valid subcategory in the taxonomy."""
        return name.lower() in self.all_subcategories
    
    def get_subcategories_for_parent(self, parent: str) -> list:
        """Get all subcategories under a parent category."""
        return self.parent_map.get(parent.lower(), [])
    
    def get_all_parents(self) -> list:
        """Get all parent category names."""
        return list(self.parent_map.keys())
    
    def get_all_subcategories(self) -> list:
        """Get all subcategory names."""
        return list(self.all_subcategories)
