"""
Taxonomy Loader - handles loading and querying the category hierarchy.
"""

import json
from pathlib import Path
from typing import Optional


class TaxonomyLoader:
    """Loads taxonomy JSON and provides lookup methods for categories."""

    def __init__(self, taxonomy_path: str):
        self.taxonomy_path = Path(taxonomy_path)
        self.raw_taxonomy = {}
        self.subcategory_map = {}  # subcategory -> {root, parent, subcategory}
        self.parent_map = {}       # parent -> [subcategories]
        self.all_subcategories = set()
        self._load()

    def _load(self):
        """Load taxonomy from file and build lookup structures."""
        with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
            self.raw_taxonomy = json.load(f)
        self._build_maps()

    def _build_maps(self):
        """Build flattened lookup maps from nested taxonomy structure."""
        for root, genres in self.raw_taxonomy.items():
            for parent, subcategories in genres.items():
                self.parent_map[parent.lower()] = [s.lower() for s in subcategories]

                for subcategory in subcategories:
                    key = subcategory.lower()
                    self.subcategory_map[key] = {
                        'root': root,
                        'parent': parent,
                        'subcategory': subcategory
                    }
                    self.all_subcategories.add(key)

    def get_full_path(self, subcategory: str) -> Optional[str]:
        """Get full path like 'Fiction > Horror > Gothic' for a subcategory."""
        key = subcategory.lower()
        if key not in self.subcategory_map:
            return None

        info = self.subcategory_map[key]
        return f"{info['root']} > {info['parent']} > {info['subcategory']}"

    def get_hierarchy_info(self, subcategory: str) -> Optional[dict]:
        """Get dict with root, parent, subcategory for a given subcategory."""
        return self.subcategory_map.get(subcategory.lower())

    def is_valid_subcategory(self, name: str) -> bool:
        """Check if name is a valid subcategory."""
        return name.lower() in self.all_subcategories

    def get_all_subcategories(self) -> list:
        """Return all subcategory names."""
        return list(self.all_subcategories)
