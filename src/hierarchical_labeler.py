"""
Hierarchical (two-stage) labeler for logistics status classification.
Stage 1: Classify into 6 main statuses
Stage 2: Classify into sub-statuses within the selected main status

This approach reduces prompt length and improves accuracy by:
1. First stage uses only 6 categories with short descriptions
2. Second stage only considers sub-statuses within the predicted main status
3. Allows "UNKNOWN" output when confidence is low
"""
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from string import Template

from llm_client import BaseLLMClient


@dataclass
class HierarchicalResult:
    """Result from hierarchical labeling."""
    # Final results
    sub_status: str
    main_status: str
    confidence: float
    explanation: str
    is_valid: bool = True
    error: str = ""
    
    # Stage 1 results
    stage1_main_status: str = ""
    stage1_confidence: float = 0.0
    stage1_explanation: str = ""
    
    # Stage 2 results
    stage2_sub_status: str = ""
    stage2_confidence: float = 0.0
    stage2_explanation: str = ""
    
    # Flags
    is_uncertain: bool = False
    uncertain_stage: str = ""  # "stage1" or "stage2"


# Mapping from main_status code to taxonomy key
MAIN_STATUS_MAP = {
    "IN_TRANSIT": "In transit/运输途中",
    "OUT_FOR_DELIVERY": "Out for delivery/派送中",
    "DELIVERED": "Delivered/签收",
    "DELIVERY_FAILED": "Failed attempt/投递失败",
    "EXCEPTION": "Exception/可能异常",
    "INFO_RECEIVED": "Info received/等待揽收",
}

# Reverse mapping
TAXONOMY_TO_MAIN = {v: k for k, v in MAIN_STATUS_MAP.items()}

# Human-readable names for main statuses
MAIN_STATUS_NAMES = {
    "IN_TRANSIT": "运输途中",
    "OUT_FOR_DELIVERY": "派送中",
    "DELIVERED": "已签收",
    "DELIVERY_FAILED": "投递失败",
    "EXCEPTION": "可能异常",
    "INFO_RECEIVED": "等待揽收",
}


class HierarchicalLabeler:
    """
    Two-stage hierarchical labeler.
    
    Stage 1: Classify into 6 main statuses
    Stage 2: Classify into sub-statuses within the predicted main status
    
    Usage:
        labeler = HierarchicalLabeler(
            client=your_llm_client,
            taxonomy_path="resources/taxonomy/taxonomy.json",
            main_template_path="resources/prompts/main_stage.yaml",
            sub_template_path="resources/prompts/sub_stage.yaml",
            fewshot_path="resources/datasets/fewshot.json",
            main_threshold=0.6,  # Confidence threshold for stage 1
            sub_threshold=0.5,   # Confidence threshold for stage 2
        )
        result = labeler.label(trace_text)
    """
    
    def __init__(
        self,
        client: BaseLLMClient,
        taxonomy_path: str,
        main_template_path: str,
        sub_template_path: str,
        fewshot_path: str,
        main_threshold: float = 0.6,
        sub_threshold: float = 0.5,
        main_examples: int = 6,  # Number of examples for stage 1 (1 per main status)
        sub_examples: int = 3,   # Number of examples for stage 2
    ):
        self.client = client
        self.main_threshold = main_threshold
        self.sub_threshold = sub_threshold
        self.main_examples = main_examples
        self.sub_examples = sub_examples
        
        # Load taxonomy
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            self.taxonomy = json.load(f)
        
        # Load templates
        import yaml
        with open(main_template_path, 'r', encoding='utf-8') as f:
            self.main_template = yaml.safe_load(f)
        with open(sub_template_path, 'r', encoding='utf-8') as f:
            self.sub_template = yaml.safe_load(f)
        
        # Load few-shot examples
        with open(fewshot_path, 'r', encoding='utf-8') as f:
            self.fewshot_data = json.load(f)
        
        # Build mappings
        self.sub_to_main = {}
        self.main_to_subs = {}
        for main_key, subs in self.taxonomy.items():
            main_code = TAXONOMY_TO_MAIN.get(main_key, main_key)
            self.main_to_subs[main_code] = list(subs.keys())
            for sub_code in subs.keys():
                self.sub_to_main[sub_code] = main_code
        
        # Group few-shot examples by main status
        self.fewshot_by_main = {}
        for ex in self.fewshot_data:
            main_code = self.sub_to_main.get(ex['sub_status'], 'UNKNOWN')
            if main_code not in self.fewshot_by_main:
                self.fewshot_by_main[main_code] = []
            self.fewshot_by_main[main_code].append(ex)
    
    def _get_main_examples(self) -> List[Dict]:
        """Get one example per main status for stage 1."""
        examples = []
        for main_code in MAIN_STATUS_MAP.keys():
            if main_code in self.fewshot_by_main and self.fewshot_by_main[main_code]:
                ex = self.fewshot_by_main[main_code][0]
                examples.append({
                    'trace': ex['trace'],
                    'main_status': main_code,
                    'reason': ex.get('reason', '')
                })
        return examples
    
    def _get_sub_examples(self, main_status: str, n: int = 3) -> List[Dict]:
        """Get examples for stage 2 (only from the specified main status).
        
        Uses deterministic selection (first n examples) for reproducibility.
        """
        examples = self.fewshot_by_main.get(main_status, [])
        return examples[:min(n, len(examples))]
    
    def _build_main_examples_text(self, examples: List[Dict]) -> str:
        """Build examples text for stage 1."""
        lines = []
        for i, ex in enumerate(examples, 1):
            trace_lines = ex['trace'].split('\n')[:3]
            trace_short = '\n'.join(trace_lines)
            if len(trace_lines) < len(ex['trace'].split('\n')):
                trace_short += '\n...'
            
            lines.append(f"案例{i} ({MAIN_STATUS_NAMES.get(ex['main_status'], ex['main_status'])}):")
            lines.append(f"轨迹: {trace_short}")
            lines.append(f"主状态: {ex['main_status']}")
            lines.append("")
        return "\n".join(lines)
    
    def _build_sub_examples_text(self, examples: List[Dict]) -> str:
        """Build examples text for stage 2."""
        lines = []
        for i, ex in enumerate(examples, 1):
            trace_lines = ex['trace'].split('\n')[:4]
            trace_short = '\n'.join(trace_lines)
            if len(trace_lines) < len(ex['trace'].split('\n')):
                trace_short += '\n...'
            
            lines.append(f"案例{i}:")
            lines.append(f"轨迹: {trace_short}")
            lines.append(f"子状态: {ex['sub_status']}")
            lines.append(f"原因: {ex.get('reason', '')}")
            lines.append("")
        return "\n".join(lines)
    
    def _build_sub_taxonomy_text(self, main_status: str) -> str:
        """Build taxonomy text for stage 2 (only sub-statuses of the main status)."""
        main_key = MAIN_STATUS_MAP.get(main_status)
        if not main_key or main_key not in self.taxonomy:
            return ""
        
        lines = []
        subs = self.taxonomy[main_key]
        for code, info in subs.items():
            lines.append(f"- {code}: {info['chn_meaning']}")
        return "\n".join(lines)
    
    def _build_sub_enum_list(self, main_status: str) -> str:
        """Build enum list for stage 2."""
        return ", ".join(self.main_to_subs.get(main_status, []))
    
    def _build_stage1_prompt(self, trace: str) -> List[Dict[str, str]]:
        """Build prompt for stage 1 (main status classification)."""
        examples = self._get_main_examples()
        
        system_prompt = self.main_template["system_prompt"]
        
        user_template = Template(self.main_template["user_prompt"])
        user_prompt = user_template.safe_substitute(
            examples=self._build_main_examples_text(examples),
            trace=trace
        )
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _build_stage2_prompt(self, trace: str, main_status: str) -> List[Dict[str, str]]:
        """Build prompt for stage 2 (sub-status classification)."""
        examples = self._get_sub_examples(main_status, self.sub_examples)
        main_name = MAIN_STATUS_NAMES.get(main_status, main_status)
        
        system_template = Template(self.sub_template["system_prompt"])
        system_prompt = system_template.safe_substitute(
            main_status_name=main_name,
            sub_taxonomy=self._build_sub_taxonomy_text(main_status),
            sub_enum_list=self._build_sub_enum_list(main_status)
        )
        
        user_template = Template(self.sub_template["user_prompt"])
        user_prompt = user_template.safe_substitute(
            examples=self._build_sub_examples_text(examples),
            trace=trace,
            main_status_name=main_name
        )
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _parse_main_response(self, response_text: str) -> Tuple[str, float, str]:
        """Parse stage 1 response. Returns (main_status, confidence, explanation)."""
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            return "UNKNOWN", 0.0, "No JSON found"
        
        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return "UNKNOWN", 0.0, "Invalid JSON"
        
        main_status = data.get("main_status", "UNKNOWN")
        confidence = float(data.get("confidence", 0.0))
        explanation = data.get("explanation", "")
        
        # Validate main_status
        if main_status not in MAIN_STATUS_MAP and main_status != "UNKNOWN":
            main_status = "UNKNOWN"
            confidence = 0.0
        
        return main_status, confidence, explanation
    
    def _parse_sub_response(self, response_text: str, main_status: str) -> Tuple[str, float, str]:
        """Parse stage 2 response. Returns (sub_status, confidence, explanation)."""
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            return "UNKNOWN", 0.0, "No JSON found"
        
        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return "UNKNOWN", 0.0, "Invalid JSON"
        
        sub_status = data.get("sub_status", "UNKNOWN")
        confidence = float(data.get("confidence", 0.0))
        explanation = data.get("explanation", "")
        
        # Validate sub_status belongs to main_status
        valid_subs = self.main_to_subs.get(main_status, [])
        if sub_status not in valid_subs and sub_status != "UNKNOWN":
            # Try to find default sub-status for this main
            default_sub = self._get_default_sub(main_status)
            if default_sub:
                sub_status = default_sub
            else:
                sub_status = "UNKNOWN"
                confidence = 0.0
        
        return sub_status, confidence, explanation
    
    def _get_default_sub(self, main_status: str) -> Optional[str]:
        """Get default sub-status for a main status."""
        main_key = MAIN_STATUS_MAP.get(main_status)
        if not main_key or main_key not in self.taxonomy:
            return None
        
        for code, info in self.taxonomy[main_key].items():
            if info.get("is_default", False):
                return code
        return None
    
    def label(self, trace: str) -> HierarchicalResult:
        """
        Label a logistics trace using two-stage classification.
        
        Stage 1: Classify into 6 main statuses
        Stage 2: Classify into sub-statuses (if stage 1 is confident)
        """
        result = HierarchicalResult(
            sub_status="UNKNOWN",
            main_status="UNKNOWN",
            confidence=0.0,
            explanation=""
        )
        
        # Stage 1: Main status classification
        try:
            messages = self._build_stage1_prompt(trace)
            response = self.client.complete(messages, temperature=0.0, max_tokens=300)
            main_status, main_conf, main_expl = self._parse_main_response(response.content)
            
            result.stage1_main_status = main_status
            result.stage1_confidence = main_conf
            result.stage1_explanation = main_expl
            
        except Exception as e:
            result.error = f"Stage 1 error: {e}"
            result.is_valid = False
            return result
        
        # Check stage 1 confidence
        if main_status == "UNKNOWN" or main_conf < self.main_threshold:
            result.main_status = main_status if main_status != "UNKNOWN" else "UNKNOWN"
            result.sub_status = "UNKNOWN"
            result.confidence = main_conf
            result.explanation = main_expl
            result.is_uncertain = True
            result.uncertain_stage = "stage1"
            return result
        
        # Stage 2: Sub-status classification
        try:
            messages = self._build_stage2_prompt(trace, main_status)
            response = self.client.complete(messages, temperature=0.0, max_tokens=300)
            sub_status, sub_conf, sub_expl = self._parse_sub_response(response.content, main_status)
            
            result.stage2_sub_status = sub_status
            result.stage2_confidence = sub_conf
            result.stage2_explanation = sub_expl
            
        except Exception as e:
            result.error = f"Stage 2 error: {e}"
            result.main_status = main_status
            result.sub_status = self._get_default_sub(main_status) or "UNKNOWN"
            result.confidence = main_conf
            result.explanation = main_expl
            return result
        
        # Check stage 2 confidence
        if sub_status == "UNKNOWN" or sub_conf < self.sub_threshold:
            result.main_status = main_status
            result.sub_status = sub_status if sub_status != "UNKNOWN" else self._get_default_sub(main_status) or "UNKNOWN"
            result.confidence = sub_conf
            result.explanation = sub_expl
            result.is_uncertain = True
            result.uncertain_stage = "stage2"
            return result
        
        # Success
        result.main_status = main_status
        result.sub_status = sub_status
        result.confidence = sub_conf
        result.explanation = sub_expl
        result.is_valid = sub_status in self.sub_to_main
        
        return result
    
    def label_batch(self, traces: List[str]) -> List[HierarchicalResult]:
        """Label multiple traces."""
        return [self.label(trace) for trace in traces]


if __name__ == "__main__":
    # Example usage
    import os
    import sys
    
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from llm_client import MoonshotClient
    
    # Create client
    client = MoonshotClient(
        api_key="your-api-key",
        model="moonshot-v1-128k"
    )
    
    # Create labeler
    labeler = HierarchicalLabeler(
        client=client,
        taxonomy_path="../resources/taxonomy/taxonomy.json",
        main_template_path="../resources/prompts/main_stage.yaml",
        sub_template_path="../resources/prompts/sub_stage.yaml",
        fewshot_path="../resources/datasets/fewshot.json",
        main_threshold=0.6,
        sub_threshold=0.5,
    )
    
    # Test
    test_trace = """单号：YT2534601002506026
物流商：YunExpress
2025-12-15 15:43:00 Clearance processing completed - Import 
2025-12-15 08:05:00 International flight has arrived US"""
    
    result = labeler.label(test_trace)
    print(f"Main Status: {result.main_status}")
    print(f"Sub Status: {result.sub_status}")
    print(f"Confidence: {result.confidence}")
    print(f"Explanation: {result.explanation}")
    print(f"Is Uncertain: {result.is_uncertain}")
