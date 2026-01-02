"""
Core labeling module for logistics status classification.
Handles prompt construction, LLM calls, and response parsing.
"""
import json
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from taxonomy_manager import TaxonomyManager
from few_shot_retriever import FewShotRetriever, SampleCase
from preprocessor import TracePreprocessor, ProcessedTrace
from llm_client import BaseLLMClient, LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class LabelPrediction:
    """A single label prediction from one model."""
    main_status: str
    sub_status: str
    confidence: float
    evidence: List[str]  # Lines from the trace that support the prediction
    explanation: str
    model_name: str
    raw_response: str
    is_valid: bool = True
    validation_error: str = ""


@dataclass
class LabelResult:
    """Final labeling result after voting/consensus."""
    main_status: str
    sub_status: str
    confidence: float
    evidence: List[str]
    explanation: str
    predictions: List[LabelPrediction]
    voting_details: Dict[str, Any]
    needs_human_review: bool = False
    review_reason: str = ""


class PromptBuilder:
    """Builds prompts for logistics status classification."""
    
    SYSTEM_PROMPT_TEMPLATE = """You are an expert logistics status classifier. Your task is to analyze logistics tracking information and classify the current status of a package.

## Classification Taxonomy

{taxonomy}

## Important Rules

1. Analyze the tracking events carefully, especially the most recent events
2. Identify the key evidence that determines the status
3. Choose the most specific sub-status that matches the evidence
4. If the status is ambiguous, choose the default sub-status for that main category
5. Output your response in the exact JSON format specified

## Output Format

You MUST respond with a valid JSON object in this exact format:
```json
{{
    "main_status": "<main status name>",
    "sub_status": "<sub status code>",
    "confidence": <0.0-1.0>,
    "evidence": ["<line 1 from trace>", "<line 2 from trace>"],
    "explanation": "<brief explanation in 1-2 sentences>"
}}
```

Valid sub_status codes: {enum_list}
"""

    USER_PROMPT_TEMPLATE = """## Few-shot Examples

{examples}

## Task

Classify the following logistics trace:

```
{trace}
```

Respond with ONLY the JSON object, no other text."""

    def __init__(self, taxonomy_manager: TaxonomyManager, few_shot_retriever: FewShotRetriever):
        self.taxonomy_manager = taxonomy_manager
        self.few_shot_retriever = few_shot_retriever
    
    def build_system_prompt(self) -> str:
        """Build the system prompt with taxonomy."""
        return self.SYSTEM_PROMPT_TEMPLATE.format(
            taxonomy=self.taxonomy_manager.build_taxonomy_prompt(),
            enum_list=self.taxonomy_manager.build_enum_list()
        )
    
    def build_user_prompt(
        self, 
        trace: str, 
        examples: List[SampleCase],
    ) -> str:
        """Build the user prompt with examples and trace."""
        examples_text = self.few_shot_retriever.format_examples_for_prompt(examples)
        
        return self.USER_PROMPT_TEMPLATE.format(
            examples=examples_text,
            trace=trace
        )
    
    def build_messages(
        self, 
        trace: str, 
        examples: List[SampleCase],
    ) -> List[Dict[str, str]]:
        """Build the full message list for the LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(trace, examples)}
        ]


class ResponseParser:
    """Parses LLM responses into structured predictions."""
    
    def __init__(self, taxonomy_manager: TaxonomyManager):
        self.taxonomy_manager = taxonomy_manager
    
    def parse(self, response_text: str, model_name: str) -> LabelPrediction:
        """Parse an LLM response into a LabelPrediction."""
        # Try to extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        
        if not json_match:
            return LabelPrediction(
                main_status="",
                sub_status="",
                confidence=0.0,
                evidence=[],
                explanation="",
                model_name=model_name,
                raw_response=response_text,
                is_valid=False,
                validation_error="No JSON found in response"
            )
        
        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            return LabelPrediction(
                main_status="",
                sub_status="",
                confidence=0.0,
                evidence=[],
                explanation="",
                model_name=model_name,
                raw_response=response_text,
                is_valid=False,
                validation_error=f"Invalid JSON: {e}"
            )
        
        # Extract fields
        main_status = data.get("main_status", "")
        sub_status = data.get("sub_status", "")
        confidence = float(data.get("confidence", 0.0))
        evidence = data.get("evidence", [])
        explanation = data.get("explanation", "")
        
        # Ensure evidence is a list
        if isinstance(evidence, str):
            evidence = [evidence]
        
        # Validate the prediction
        is_valid, validation_error = self._validate(main_status, sub_status)
        
        return LabelPrediction(
            main_status=main_status,
            sub_status=sub_status,
            confidence=confidence,
            evidence=evidence,
            explanation=explanation,
            model_name=model_name,
            raw_response=response_text,
            is_valid=is_valid,
            validation_error=validation_error
        )
    
    def _validate(self, main_status: str, sub_status: str) -> Tuple[bool, str]:
        """Validate a prediction against the taxonomy."""
        if not sub_status:
            return False, "Missing sub_status"
        
        if not self.taxonomy_manager.is_valid_sub_status(sub_status):
            return False, f"Invalid sub_status: {sub_status}"
        
        expected_main = self.taxonomy_manager.get_main_for_sub(sub_status)
        if main_status and expected_main and main_status != expected_main:
            # Auto-correct the main status
            return True, f"Main status corrected from {main_status} to {expected_main}"
        
        return True, ""


class RuleValidator:
    """Validates predictions using business rules."""
    
    # Rules: (pattern_in_trace, forbidden_statuses, required_statuses)
    RULES = [
        # If "delivered" or "签收" appears, should not be in transit
        {
            "name": "delivered_not_in_transit",
            "patterns": [r'\bdelivered\b', r'签收', r'妥投', r'已投递'],
            "forbidden_main": ["In transit/运输途中", "Info received/等待揽收"],
            "required_main": None,
        },
        # If "out for delivery" appears, should be in delivery phase
        {
            "name": "out_for_delivery",
            "patterns": [r'out for delivery', r'派送中', r'正在派送'],
            "forbidden_main": ["Info received/等待揽收"],
            "required_main": None,
        },
        # If only "label created" or "info received", should be waiting for pickup
        {
            "name": "label_created_only",
            "patterns": [r'label created', r'shipping label', r'信息已收到', r'预报'],
            "forbidden_main": None,
            "required_main": None,  # This is a soft rule
        },
        # If "returned" or "退回" appears, should be in exception
        {
            "name": "returned_package",
            "patterns": [r'\breturned?\b', r'return to sender', r'退回', r'退件'],
            "forbidden_main": ["Delivered/签收"],
            "required_main": None,
        },
        # If "customs" + "detained/held" appears, should be customs exception
        {
            "name": "customs_detained",
            "patterns": [r'customs.*(?:detained|held|扣留)', r'海关.*扣'],
            "forbidden_main": ["Delivered/签收"],
            "required_main": None,
        },
    ]
    
    def validate(self, trace: str, prediction: LabelPrediction) -> Tuple[bool, List[str]]:
        """
        Validate a prediction against business rules.
        Returns (is_valid, list_of_warnings).
        """
        warnings = []
        trace_lower = trace.lower()
        
        for rule in self.RULES:
            # Check if any pattern matches
            pattern_matched = False
            for pattern in rule["patterns"]:
                if re.search(pattern, trace_lower, re.IGNORECASE):
                    pattern_matched = True
                    break
            
            if not pattern_matched:
                continue
            
            # Check forbidden main statuses
            if rule["forbidden_main"]:
                if prediction.main_status in rule["forbidden_main"]:
                    warnings.append(
                        f"Rule '{rule['name']}' violated: "
                        f"main_status '{prediction.main_status}' is forbidden when pattern matches"
                    )
            
            # Check required main statuses
            if rule["required_main"]:
                if prediction.main_status not in rule["required_main"]:
                    warnings.append(
                        f"Rule '{rule['name']}' suggests: "
                        f"main_status should be one of {rule['required_main']}"
                    )
        
        # A prediction is invalid only if there are hard violations
        is_valid = len([w for w in warnings if "violated" in w]) == 0
        
        return is_valid, warnings


class SingleModelLabeler:
    """Labeler using a single LLM model."""
    
    def __init__(
        self,
        client: BaseLLMClient,
        model_name: str,
        taxonomy_manager: TaxonomyManager,
        few_shot_retriever: FewShotRetriever,
        preprocessor: TracePreprocessor,
        num_few_shot: int = 3,
        use_retrieval: bool = True,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ):
        self.client = client
        self.model_name = model_name
        self.taxonomy_manager = taxonomy_manager
        self.few_shot_retriever = few_shot_retriever
        self.preprocessor = preprocessor
        self.num_few_shot = num_few_shot
        self.use_retrieval = use_retrieval
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self.prompt_builder = PromptBuilder(taxonomy_manager, few_shot_retriever)
        self.response_parser = ResponseParser(taxonomy_manager)
        self.rule_validator = RuleValidator()
    
    def label(self, trace: str, num_samples: int = 1) -> List[LabelPrediction]:
        """Label a trace, optionally with multiple samples for self-consistency."""
        # Preprocess the trace
        processed = self.preprocessor.process(trace)
        formatted_trace = self.preprocessor.format_for_prompt(processed)
        
        # Get few-shot examples
        if self.use_retrieval:
            examples = self.few_shot_retriever.get_examples_by_keyword_similarity(
                trace, n=self.num_few_shot
            )
        else:
            examples = self.few_shot_retriever.get_random_examples(n=self.num_few_shot)
        
        # Build messages
        messages = self.prompt_builder.build_messages(formatted_trace, examples)
        
        # Get predictions
        predictions = []
        for i in range(num_samples):
            temp = self.temperature if num_samples == 1 else max(0.3, self.temperature)
            
            try:
                response = self.client.complete(
                    messages=messages,
                    temperature=temp,
                    max_tokens=self.max_tokens
                )
                
                prediction = self.response_parser.parse(response.content, self.model_name)
                
                # Validate with rules
                is_valid, warnings = self.rule_validator.validate(trace, prediction)
                if warnings:
                    prediction.validation_error = "; ".join(warnings)
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error from {self.model_name}: {e}")
                predictions.append(LabelPrediction(
                    main_status="",
                    sub_status="",
                    confidence=0.0,
                    evidence=[],
                    explanation="",
                    model_name=self.model_name,
                    raw_response=str(e),
                    is_valid=False,
                    validation_error=f"API error: {e}"
                ))
        
        return predictions
