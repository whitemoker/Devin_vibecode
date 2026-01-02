"""
Simplified labeler for logistics status classification.
Uses a single prompt template file for easy customization.
Supports optional name anonymization before sending to LLM.
"""
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from llm_client import BaseLLMClient


@dataclass
class LabelResult:
    """Labeling result."""
    sub_status: str
    main_status: str
    confidence: float
    evidence: List[str]
    explanation: str
    is_valid: bool = True
    error: str = ""
    # Anonymization info
    original_trace: str = ""
    anonymized_trace: str = ""
    detected_names: List[Dict] = field(default_factory=list)


class SimpleLabeler:
    """
    Simple labeler that uses a template file for prompts.
    Supports optional name anonymization before sending to LLM.
    
    Usage:
        labeler = SimpleLabeler(
            client=your_llm_client,
            taxonomy_path="taxonomy.json",
            template_path="prompt_template.json",
            anonymize=True  # Enable name anonymization
        )
        result = labeler.label(trace_text)
    """
    
    def __init__(
        self,
        client: BaseLLMClient,
        taxonomy_path: str = "taxonomy.json",
        template_path: str = "prompt_template.json",
        sample_cases_path: str = "sample_cases.json",
        num_examples: int = 3,
        anonymize: bool = False,
    ):
        self.client = client
        self.num_examples = num_examples
        self.anonymize = anonymize
        self.anonymizer = None
        
        # Initialize anonymizer if enabled
        if self.anonymize:
            from anonymizer import NameAnonymizer
            self.anonymizer = NameAnonymizer()
        
        # Load taxonomy
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            self.taxonomy = json.load(f)
        
        # Load prompt template (supports both YAML and JSON)
        with open(template_path, 'r', encoding='utf-8') as f:
            if template_path.endswith('.yaml') or template_path.endswith('.yml'):
                import yaml
                self.template = yaml.safe_load(f)
            else:
                self.template = json.load(f)
        
        # Load sample cases
        with open(sample_cases_path, 'r', encoding='utf-8') as f:
            self.sample_cases = json.load(f)
        
        # Build sub_status to main_status mapping
        self.sub_to_main = {}
        for main_status, subs in self.taxonomy.items():
            for sub_code in subs.keys():
                self.sub_to_main[sub_code] = main_status
    
    def _build_taxonomy_text(self) -> str:
        """Build taxonomy text for prompt."""
        lines = []
        for main_status, subs in self.taxonomy.items():
            lines.append(f"### {main_status}")
            for code, info in subs.items():
                lines.append(f"- {code}: {info['chn_meaning']}")
            lines.append("")
        return "\n".join(lines)
    
    def _build_enum_list(self) -> str:
        """Build list of valid sub_status codes."""
        codes = []
        for subs in self.taxonomy.values():
            codes.extend(subs.keys())
        return ", ".join(codes)
    
    def _get_examples(self, n: int = 3) -> List[Dict]:
        """Get n random examples from sample cases."""
        import random
        return random.sample(self.sample_cases, min(n, len(self.sample_cases)))
    
    def _build_examples_text(self, examples: List[Dict]) -> str:
        """Build examples text for prompt."""
        lines = []
        for i, ex in enumerate(examples, 1):
            # Truncate trace to first 5 lines for brevity
            trace_lines = ex['trace'].split('\n')[:5]
            trace_short = '\n'.join(trace_lines)
            if len(trace_lines) < len(ex['trace'].split('\n')):
                trace_short += '\n...'
            
            lines.append(f"案例{i}:")
            lines.append(f"轨迹: {trace_short}")
            lines.append(f"状态: {ex['sub_status']}")
            lines.append(f"原因: {ex['reason']}")
            lines.append("")
        return "\n".join(lines)
    
    def _build_prompt(self, trace: str) -> List[Dict[str, str]]:
        """Build the full prompt messages."""
        from string import Template
        
        # Get examples
        examples = self._get_examples(self.num_examples)
        
        # Build system prompt using Template for $ placeholders
        system_template = Template(self.template["system_prompt"])
        system_prompt = system_template.safe_substitute(
            taxonomy=self._build_taxonomy_text(),
            enum_list=self._build_enum_list()
        )
        
        # Build user prompt
        user_template = Template(self.template["user_prompt"])
        user_prompt = user_template.safe_substitute(
            examples=self._build_examples_text(examples),
            trace=trace
        )
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _parse_response(self, response_text: str) -> LabelResult:
        """Parse LLM response into LabelResult."""
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        
        if not json_match:
            return LabelResult(
                sub_status="",
                main_status="",
                confidence=0.0,
                evidence=[],
                explanation="",
                is_valid=False,
                error="No JSON found in response"
            )
        
        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            return LabelResult(
                sub_status="",
                main_status="",
                confidence=0.0,
                evidence=[],
                explanation="",
                is_valid=False,
                error=f"Invalid JSON: {e}"
            )
        
        sub_status = data.get("sub_status", "")
        main_status = self.sub_to_main.get(sub_status, "")
        
        return LabelResult(
            sub_status=sub_status,
            main_status=main_status,
            confidence=float(data.get("confidence", 0.0)),
            evidence=data.get("evidence", []),
            explanation=data.get("explanation", ""),
            is_valid=sub_status in self.sub_to_main
        )
    
    def label(self, trace: str) -> LabelResult:
        """
        Label a logistics trace.
        
        Args:
            trace: The logistics tracking text
            
        Returns:
            LabelResult with predicted status
        """
        original_trace = trace
        anonymized_trace = trace
        detected_names = []
        
        # Anonymize if enabled
        if self.anonymize and self.anonymizer:
            anon_result = self.anonymizer.anonymize_trace(trace)
            anonymized_trace = anon_result.anonymized_text
            detected_names = anon_result.detected_names
            trace = anonymized_trace  # Use anonymized trace for LLM
        
        messages = self._build_prompt(trace)
        
        try:
            response = self.client.complete(messages, temperature=0.0, max_tokens=500)
            result = self._parse_response(response.content)
            # Add anonymization info to result
            result.original_trace = original_trace
            result.anonymized_trace = anonymized_trace
            result.detected_names = detected_names
            return result
        except Exception as e:
            return LabelResult(
                sub_status="",
                main_status="",
                confidence=0.0,
                evidence=[],
                explanation="",
                is_valid=False,
                error=f"API error: {e}",
                original_trace=original_trace,
                anonymized_trace=anonymized_trace,
                detected_names=detected_names
            )
    
    def label_batch(self, traces: List[str]) -> List[LabelResult]:
        """Label multiple traces."""
        return [self.label(trace) for trace in traces]


if __name__ == "__main__":
    # Example usage
    from llm_client import MoonshotClient
    
    # Create client
    client = MoonshotClient(
        api_key="your-api-key",
        model="moonshot-v1-128k"
    )
    
    # Create labeler
    labeler = SimpleLabeler(
        client=client,
        taxonomy_path="taxonomy.json",
        template_path="prompt_template.json",
        sample_cases_path="sample_cases.json",
        num_examples=3
    )
    
    # Test
    test_trace = """单号：YT2534601002506026
物流商：YunExpress
2025-12-15 15:43:00 Clearance processing completed - Import 
2025-12-15 08:05:00 International flight has arrived US"""
    
    result = labeler.label(test_trace)
    print(f"Status: {result.sub_status}")
    print(f"Main: {result.main_status}")
    print(f"Confidence: {result.confidence}")
    print(f"Explanation: {result.explanation}")
