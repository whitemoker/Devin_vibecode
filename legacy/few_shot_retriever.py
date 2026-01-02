"""
Few-shot example retriever for logistics status classification.
Supports both static and retrieval-based few-shot selection.
"""
import json
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class SampleCase:
    """A sample case for few-shot learning."""
    main_status: str
    sub_status: str
    trace: str
    reason: str
    embedding: Optional[np.ndarray] = None


class FewShotRetriever:
    """Retrieves relevant few-shot examples for classification."""
    
    def __init__(self, sample_cases_path: str):
        self.sample_cases_path = sample_cases_path
        self.cases: List[SampleCase] = []
        self.cases_by_main: Dict[str, List[SampleCase]] = {}
        self.cases_by_sub: Dict[str, List[SampleCase]] = {}
        self._load_cases()
    
    def _load_cases(self):
        """Load sample cases from JSON file."""
        with open(self.sample_cases_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            case = SampleCase(
                main_status=item['main_status'],
                sub_status=item['sub_status'],
                trace=item['trace'],
                reason=item['reason']
            )
            self.cases.append(case)
            
            # Index by main status
            if case.main_status not in self.cases_by_main:
                self.cases_by_main[case.main_status] = []
            self.cases_by_main[case.main_status].append(case)
            
            # Index by sub status
            if case.sub_status not in self.cases_by_sub:
                self.cases_by_sub[case.sub_status] = []
            self.cases_by_sub[case.sub_status].append(case)
    
    def get_random_examples(self, n: int = 3, exclude_sub_status: Optional[str] = None) -> List[SampleCase]:
        """Get random examples from different categories."""
        # Try to get examples from different main statuses
        selected = []
        main_statuses = list(self.cases_by_main.keys())
        random.shuffle(main_statuses)
        
        for main_status in main_statuses:
            if len(selected) >= n:
                break
            
            candidates = self.cases_by_main[main_status]
            if exclude_sub_status:
                candidates = [c for c in candidates if c.sub_status != exclude_sub_status]
            
            if candidates:
                selected.append(random.choice(candidates))
        
        # If we don't have enough, add more randomly
        while len(selected) < n and len(selected) < len(self.cases):
            remaining = [c for c in self.cases if c not in selected]
            if exclude_sub_status:
                remaining = [c for c in remaining if c.sub_status != exclude_sub_status]
            if remaining:
                selected.append(random.choice(remaining))
            else:
                break
        
        return selected
    
    def get_examples_by_keyword_similarity(
        self, 
        query_trace: str, 
        n: int = 3,
        exclude_sub_status: Optional[str] = None
    ) -> List[SampleCase]:
        """
        Get examples based on keyword overlap.
        This is a simple retrieval method that doesn't require embeddings.
        """
        # Extract keywords from query
        query_keywords = self._extract_keywords(query_trace)
        
        # Score each case by keyword overlap
        scored_cases = []
        for case in self.cases:
            if exclude_sub_status and case.sub_status == exclude_sub_status:
                continue
            
            case_keywords = self._extract_keywords(case.trace)
            overlap = len(query_keywords & case_keywords)
            scored_cases.append((case, overlap))
        
        # Sort by score (descending) and take top n
        scored_cases.sort(key=lambda x: x[1], reverse=True)
        
        # Try to get diverse examples (from different sub-statuses)
        selected = []
        seen_sub_statuses = set()
        
        for case, score in scored_cases:
            if len(selected) >= n:
                break
            if case.sub_status not in seen_sub_statuses:
                selected.append(case)
                seen_sub_statuses.add(case.sub_status)
        
        # If we don't have enough diverse examples, add more
        for case, score in scored_cases:
            if len(selected) >= n:
                break
            if case not in selected:
                selected.append(case)
        
        return selected
    
    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from text for similarity matching."""
        # Simple keyword extraction: split by whitespace and punctuation
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words and short words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'at', 'to', 'in', 'on', 'for', 'of', 'and', 'or', 'by',
            '的', '了', '在', '是', '有', '和', '与', '等', '已', '正在',
        }
        keywords = {w for w in words if len(w) > 2 and w not in stop_words}
        
        return keywords
    
    def get_examples_for_main_status(
        self, 
        main_status: str, 
        n: int = 3
    ) -> List[SampleCase]:
        """Get examples for a specific main status."""
        cases = self.cases_by_main.get(main_status, [])
        if len(cases) <= n:
            return cases
        return random.sample(cases, n)
    
    def get_one_example_per_sub_status(
        self, 
        main_status: Optional[str] = None
    ) -> List[SampleCase]:
        """Get one example for each sub-status."""
        selected = []
        
        if main_status:
            cases = self.cases_by_main.get(main_status, [])
            seen_sub = set()
            for case in cases:
                if case.sub_status not in seen_sub:
                    selected.append(case)
                    seen_sub.add(case.sub_status)
        else:
            for sub_status, cases in self.cases_by_sub.items():
                if cases:
                    selected.append(cases[0])
        
        return selected
    
    def format_examples_for_prompt(self, examples: List[SampleCase]) -> str:
        """Format examples for inclusion in a prompt."""
        lines = []
        
        for i, example in enumerate(examples, 1):
            lines.append(f"### Example {i}")
            lines.append(f"**Trace:**")
            lines.append("```")
            lines.append(example.trace.strip())
            lines.append("```")
            lines.append(f"**Classification:** {example.sub_status} ({example.main_status})")
            lines.append(f"**Reason:** {example.reason}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict:
        """Get statistics about the sample cases."""
        return {
            "total_cases": len(self.cases),
            "main_statuses": len(self.cases_by_main),
            "sub_statuses": len(self.cases_by_sub),
            "cases_per_main": {k: len(v) for k, v in self.cases_by_main.items()},
            "cases_per_sub": {k: len(v) for k, v in self.cases_by_sub.items()},
        }
