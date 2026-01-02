"""
Taxonomy manager for logistics status classification.
Handles loading, querying, and validation of the classification tree.
"""
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SubStatus:
    """A sub-status in the taxonomy."""
    code: str
    eng_meaning: str
    chn_meaning: str
    is_default: bool


@dataclass
class MainStatus:
    """A main status category."""
    name: str
    sub_statuses: Dict[str, SubStatus]
    
    def get_default_sub_status(self) -> Optional[SubStatus]:
        """Get the default sub-status for this main status."""
        for sub in self.sub_statuses.values():
            if sub.is_default:
                return sub
        return None
    
    def get_sub_status_codes(self) -> List[str]:
        """Get all sub-status codes."""
        return list(self.sub_statuses.keys())


class TaxonomyManager:
    """Manages the logistics status taxonomy."""
    
    def __init__(self, taxonomy_path: str):
        self.taxonomy_path = taxonomy_path
        self.main_statuses: Dict[str, MainStatus] = {}
        self.sub_to_main: Dict[str, str] = {}  # sub_status_code -> main_status_name
        self._load_taxonomy()
    
    def _load_taxonomy(self):
        """Load taxonomy from JSON file."""
        with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for main_name, subs in data.items():
            sub_statuses = {}
            for sub_code, sub_data in subs.items():
                sub_status = SubStatus(
                    code=sub_code,
                    eng_meaning=sub_data.get('eng_meaning', ''),
                    chn_meaning=sub_data.get('chn_meaning', ''),
                    is_default=sub_data.get('is_default', False)
                )
                sub_statuses[sub_code] = sub_status
                self.sub_to_main[sub_code] = main_name
            
            self.main_statuses[main_name] = MainStatus(
                name=main_name,
                sub_statuses=sub_statuses
            )
    
    def get_all_main_statuses(self) -> List[str]:
        """Get all main status names."""
        return list(self.main_statuses.keys())
    
    def get_all_sub_statuses(self) -> List[str]:
        """Get all sub-status codes."""
        return list(self.sub_to_main.keys())
    
    def get_main_status(self, main_name: str) -> Optional[MainStatus]:
        """Get a main status by name."""
        return self.main_statuses.get(main_name)
    
    def get_sub_status(self, sub_code: str) -> Optional[SubStatus]:
        """Get a sub-status by code."""
        main_name = self.sub_to_main.get(sub_code)
        if main_name:
            return self.main_statuses[main_name].sub_statuses.get(sub_code)
        return None
    
    def get_main_for_sub(self, sub_code: str) -> Optional[str]:
        """Get the main status name for a sub-status code."""
        return self.sub_to_main.get(sub_code)
    
    def is_valid_sub_status(self, sub_code: str) -> bool:
        """Check if a sub-status code is valid."""
        return sub_code in self.sub_to_main
    
    def get_sub_statuses_for_main(self, main_name: str) -> List[SubStatus]:
        """Get all sub-statuses for a main status."""
        main = self.main_statuses.get(main_name)
        if main:
            return list(main.sub_statuses.values())
        return []
    
    def build_taxonomy_prompt(self) -> str:
        """Build a prompt-friendly representation of the taxonomy."""
        lines = ["# 物流状态分类树 (Logistics Status Taxonomy)\n"]
        
        for main_name, main_status in self.main_statuses.items():
            lines.append(f"## {main_name}")
            for sub_code, sub in main_status.sub_statuses.items():
                default_mark = " [默认/Default]" if sub.is_default else ""
                lines.append(f"- **{sub_code}**: {sub.chn_meaning}{default_mark}")
                if sub.eng_meaning:
                    lines.append(f"  - English: {sub.eng_meaning}")
            lines.append("")
        
        return "\n".join(lines)
    
    def build_enum_list(self) -> str:
        """Build a simple enum list of all valid sub-status codes."""
        return ", ".join(sorted(self.sub_to_main.keys()))
    
    def validate_prediction(self, main_status: str, sub_status: str) -> Tuple[bool, str]:
        """
        Validate a prediction.
        Returns (is_valid, error_message).
        """
        if main_status not in self.main_statuses:
            return False, f"Invalid main status: {main_status}"
        
        if sub_status not in self.sub_to_main:
            return False, f"Invalid sub status: {sub_status}"
        
        expected_main = self.sub_to_main[sub_status]
        if expected_main != main_status:
            return False, f"Sub status {sub_status} belongs to {expected_main}, not {main_status}"
        
        return True, ""
