"""
Multi-angle * Multi-model Ensemble Labeler for logistics status classification.

This module implements an ensemble approach that combines:
1. Multiple LLM models (e.g., GPT-5.2, Grok-4, Kimi)
2. Multiple prompt angles/perspectives (e.g., rule-based, time-based, evidence-based)

The ensemble collects predictions from all (model, prompt_variant) combinations
and uses a weighted voting mechanism to produce the final prediction.
"""
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


class PromptAngle(Enum):
    """Different prompt angles/perspectives for classification."""
    RULE_BASED = "rule_based"           # Strict rule-based classification
    TIME_BASED = "time_based"           # Focus on latest events only
    EVIDENCE_BASED = "evidence_based"   # Extract evidence first, then classify
    HIERARCHICAL = "hierarchical"       # Two-stage: main status -> sub status


@dataclass
class Prediction:
    """A single prediction from one (model, prompt_variant) combination."""
    sub_status: str
    main_status: str
    confidence: float
    explanation: str
    evidence: List[str] = field(default_factory=list)
    
    # Metadata
    model_name: str = ""
    prompt_angle: str = ""
    latency_ms: float = 0.0
    raw_response: str = ""
    is_valid: bool = True
    error: str = ""


@dataclass
class EnsembleResult:
    """Final result from ensemble labeling."""
    # Final prediction
    sub_status: str
    main_status: str
    confidence: float
    explanation: str
    
    # Voting details
    vote_count: int = 0
    agreement_ratio: float = 0.0
    needs_human_review: bool = False
    review_reason: str = ""
    
    # All individual predictions for audit
    predictions: List[Prediction] = field(default_factory=list)
    
    # Voting breakdown
    sub_status_votes: Dict[str, float] = field(default_factory=dict)
    main_status_votes: Dict[str, float] = field(default_factory=dict)


@dataclass
class PromptVariant:
    """Configuration for a prompt variant/angle."""
    angle: PromptAngle
    template_path: str
    weight: float = 1.0
    description: str = ""
    
    # Optional overrides
    num_examples: int = 3
    extra_instructions: str = ""


@dataclass
class ModelConfig:
    """Configuration for an LLM model."""
    name: str
    provider: str
    model_id: str
    api_key_env: str
    weight: float = 1.0
    base_url: Optional[str] = None


class EnsembleLabeler:
    """
    Orchestrator for multi-angle * multi-model ensemble labeling.
    
    Architecture:
    - Bottom layer: Existing labelers (SimpleLabeler, HierarchicalLabeler)
    - Middle layer: PromptVariant abstraction for different angles
    - Top layer: EnsembleLabeler orchestrates and aggregates
    
    Usage:
        ensemble = EnsembleLabeler(
            taxonomy_path="resources/taxonomy/taxonomy.json",
            fewshot_path="resources/datasets/fewshot.json",
        )
        
        # Add models
        ensemble.add_model(ModelConfig(
            name="GPT-5.2",
            provider="abacus",
            model_id="gpt-5.2",
            api_key_env="ABACUS_API_KEY",
            weight=1.2
        ))
        
        # Add prompt angles
        ensemble.add_prompt_variant(PromptVariant(
            angle=PromptAngle.RULE_BASED,
            template_path="resources/prompts/rule_based.yaml",
            weight=1.0
        ))
        
        # Label
        result = ensemble.label(trace_text)
    """
    
    def __init__(
        self,
        taxonomy_path: str,
        fewshot_path: str,
        aggregation_strategy: str = "weighted_vote",
        min_confidence_threshold: float = 0.5,
        disagreement_threshold: float = 0.3,
        parallel: bool = False,
        dry_run: bool = False,
    ):
        self.taxonomy_path = taxonomy_path
        self.fewshot_path = fewshot_path
        self.aggregation_strategy = aggregation_strategy
        self.min_confidence_threshold = min_confidence_threshold
        self.disagreement_threshold = disagreement_threshold
        self.parallel = parallel
        self.dry_run = dry_run
        
        # Load taxonomy
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            self.taxonomy = json.load(f)
        
        # Build mappings
        self.sub_to_main = {}
        self.main_to_subs = {}
        self._build_mappings()
        
        # Model and prompt configurations
        self.models: List[ModelConfig] = []
        self.prompt_variants: List[PromptVariant] = []
        
        # Clients (lazy initialized)
        self._clients: Dict[str, BaseLLMClient] = {}
        
        # Labelers cache
        self._labelers: Dict[str, Any] = {}
    
    def _build_mappings(self):
        """Build sub_status to main_status mappings."""
        main_status_map = {
            "In transit/运输途中": "IN_TRANSIT",
            "Out for delivery/派送中": "OUT_FOR_DELIVERY",
            "Delivered/签收": "DELIVERED",
            "Failed attempt/投递失败": "DELIVERY_FAILED",
            "Exception/可能异常": "EXCEPTION",
            "Info received/等待揽收": "INFO_RECEIVED",
        }
        
        for main_key, subs in self.taxonomy.items():
            main_code = main_status_map.get(main_key, main_key)
            self.main_to_subs[main_code] = list(subs.keys())
            for sub_code in subs.keys():
                self.sub_to_main[sub_code] = main_code
    
    def add_model(self, config: ModelConfig):
        """Add a model to the ensemble."""
        self.models.append(config)
        logger.info(f"Added model: {config.name} (weight={config.weight})")
    
    def add_prompt_variant(self, variant: PromptVariant):
        """Add a prompt variant/angle to the ensemble."""
        self.prompt_variants.append(variant)
        logger.info(f"Added prompt variant: {variant.angle.value} (weight={variant.weight})")
    
    def _get_client(self, config: ModelConfig) -> Optional[BaseLLMClient]:
        """Get or create an LLM client for a model config."""
        if self.dry_run:
            return None
        
        cache_key = f"{config.provider}_{config.model_id}"
        if cache_key in self._clients:
            return self._clients[cache_key]
        
        import os
        api_key = os.environ.get(config.api_key_env)
        if not api_key:
            logger.warning(f"API key not found for {config.name} (env: {config.api_key_env})")
            return None
        
        try:
            from llm_client import LLMClientFactory
            client = LLMClientFactory.create(
                provider=config.provider,
                model=config.model_id,
                api_key=api_key,
                base_url=config.base_url
            )
            self._clients[cache_key] = client
            return client
        except Exception as e:
            logger.error(f"Failed to create client for {config.name}: {e}")
            return None
    
    def _get_labeler(self, model_config: ModelConfig, prompt_variant: PromptVariant) -> Any:
        """Get or create a labeler for a (model, prompt_variant) combination."""
        cache_key = f"{model_config.name}_{prompt_variant.angle.value}"
        if cache_key in self._labelers:
            return self._labelers[cache_key]
        
        client = self._get_client(model_config)
        if client is None and not self.dry_run:
            return None
        
        # Create appropriate labeler based on angle
        if prompt_variant.angle == PromptAngle.HIERARCHICAL:
            from hierarchical_labeler import HierarchicalLabeler
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            labeler = HierarchicalLabeler(
                client=client,
                taxonomy_path=self.taxonomy_path,
                main_template_path=os.path.join(project_root, 'resources', 'prompts', 'main_stage.yaml'),
                sub_template_path=os.path.join(project_root, 'resources', 'prompts', 'sub_stage.yaml'),
                fewshot_path=self.fewshot_path,
            )
        else:
            from simple_labeler import SimpleLabeler
            labeler = SimpleLabeler(
                client=client,
                taxonomy_path=self.taxonomy_path,
                template_path=prompt_variant.template_path,
                sample_cases_path=self.fewshot_path,
                num_examples=prompt_variant.num_examples,
            )
        
        self._labelers[cache_key] = labeler
        return labeler
    
    def _make_prediction(
        self,
        trace: str,
        model_config: ModelConfig,
        prompt_variant: PromptVariant
    ) -> Prediction:
        """Make a single prediction using one (model, prompt_variant) combination."""
        start_time = time.time()
        
        # Dry run mode - return mock prediction
        if self.dry_run:
            return Prediction(
                sub_status="MOCK_STATUS",
                main_status="MOCK_MAIN",
                confidence=0.8,
                explanation="Dry run mode - no actual API call",
                model_name=model_config.name,
                prompt_angle=prompt_variant.angle.value,
                latency_ms=0.0,
                is_valid=True
            )
        
        labeler = self._get_labeler(model_config, prompt_variant)
        if labeler is None:
            return Prediction(
                sub_status="",
                main_status="",
                confidence=0.0,
                explanation="",
                model_name=model_config.name,
                prompt_angle=prompt_variant.angle.value,
                is_valid=False,
                error="Failed to create labeler (missing API key?)"
            )
        
        try:
            result = labeler.label(trace)
            latency_ms = (time.time() - start_time) * 1000
            
            return Prediction(
                sub_status=result.sub_status,
                main_status=result.main_status if hasattr(result, 'main_status') else self.sub_to_main.get(result.sub_status, ""),
                confidence=result.confidence,
                explanation=result.explanation,
                evidence=result.evidence if hasattr(result, 'evidence') else [],
                model_name=model_config.name,
                prompt_angle=prompt_variant.angle.value,
                latency_ms=latency_ms,
                is_valid=result.is_valid if hasattr(result, 'is_valid') else True,
                error=result.error if hasattr(result, 'error') else ""
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Prediction error ({model_config.name}, {prompt_variant.angle.value}): {e}")
            return Prediction(
                sub_status="",
                main_status="",
                confidence=0.0,
                explanation="",
                model_name=model_config.name,
                prompt_angle=prompt_variant.angle.value,
                latency_ms=latency_ms,
                is_valid=False,
                error=str(e)
            )
    
    def _collect_predictions(self, trace: str) -> List[Prediction]:
        """Collect predictions from all (model, prompt_variant) combinations."""
        predictions = []
        
        if self.parallel:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=len(self.models) * len(self.prompt_variants)) as executor:
                futures = {}
                for model_config in self.models:
                    for prompt_variant in self.prompt_variants:
                        future = executor.submit(
                            self._make_prediction,
                            trace,
                            model_config,
                            prompt_variant
                        )
                        futures[future] = (model_config.name, prompt_variant.angle.value)
                
                for future in as_completed(futures):
                    try:
                        prediction = future.result()
                        predictions.append(prediction)
                    except Exception as e:
                        model_name, angle = futures[future]
                        logger.error(f"Future error ({model_name}, {angle}): {e}")
        else:
            # Sequential execution
            for model_config in self.models:
                for prompt_variant in self.prompt_variants:
                    prediction = self._make_prediction(trace, model_config, prompt_variant)
                    predictions.append(prediction)
        
        return predictions
    
    def _aggregate_predictions(self, predictions: List[Prediction]) -> EnsembleResult:
        """Aggregate predictions using weighted voting."""
        if not predictions:
            return EnsembleResult(
                sub_status="",
                main_status="",
                confidence=0.0,
                explanation="No predictions available",
                needs_human_review=True,
                review_reason="No valid predictions"
            )
        
        # Filter valid predictions
        valid_predictions = [p for p in predictions if p.is_valid and p.sub_status]
        
        if not valid_predictions:
            return EnsembleResult(
                sub_status="",
                main_status="",
                confidence=0.0,
                explanation="All predictions failed",
                predictions=predictions,
                needs_human_review=True,
                review_reason="All predictions failed"
            )
        
        # Get model and prompt weights
        model_weights = {m.name: m.weight for m in self.models}
        prompt_weights = {p.angle.value: p.weight for p in self.prompt_variants}
        
        # Calculate weighted votes for sub_status
        sub_votes: Dict[str, float] = {}
        main_votes: Dict[str, float] = {}
        
        for pred in valid_predictions:
            # Calculate weight: model_weight * prompt_weight * f(confidence)
            model_w = model_weights.get(pred.model_name, 1.0)
            prompt_w = prompt_weights.get(pred.prompt_angle, 1.0)
            # Clip confidence to [0.5, 1.0] to avoid over-reliance on self-reported confidence
            conf_w = max(0.5, min(1.0, pred.confidence))
            total_weight = model_w * prompt_w * conf_w
            
            # Vote for sub_status
            if pred.sub_status:
                sub_votes[pred.sub_status] = sub_votes.get(pred.sub_status, 0) + total_weight
            
            # Vote for main_status
            if pred.main_status:
                main_votes[pred.main_status] = main_votes.get(pred.main_status, 0) + total_weight
        
        # Get winner
        if not sub_votes:
            return EnsembleResult(
                sub_status="",
                main_status="",
                confidence=0.0,
                explanation="No valid votes",
                predictions=predictions,
                needs_human_review=True,
                review_reason="No valid votes"
            )
        
        # Sort by votes
        sorted_sub = sorted(sub_votes.items(), key=lambda x: x[1], reverse=True)
        sorted_main = sorted(main_votes.items(), key=lambda x: x[1], reverse=True)
        
        winner_sub = sorted_sub[0][0]
        winner_sub_votes = sorted_sub[0][1]
        winner_main = sorted_main[0][0] if sorted_main else self.sub_to_main.get(winner_sub, "")
        
        # Calculate agreement ratio
        total_votes = sum(sub_votes.values())
        agreement_ratio = winner_sub_votes / total_votes if total_votes > 0 else 0
        
        # Calculate confidence (normalized vote weight)
        max_possible_votes = sum(model_weights.values()) * sum(prompt_weights.values())
        confidence = winner_sub_votes / max_possible_votes if max_possible_votes > 0 else 0
        
        # Determine if human review is needed
        needs_review = False
        review_reason = ""
        
        # Check disagreement
        if len(sorted_sub) > 1:
            second_votes = sorted_sub[1][1]
            vote_gap = (winner_sub_votes - second_votes) / total_votes if total_votes > 0 else 1
            if vote_gap < self.disagreement_threshold:
                needs_review = True
                review_reason = f"High disagreement: top2 gap = {vote_gap:.2%}"
        
        # Check low confidence
        if confidence < self.min_confidence_threshold:
            needs_review = True
            review_reason = f"Low confidence: {confidence:.2%}"
        
        # Build explanation from winning predictions
        winning_explanations = [
            p.explanation for p in valid_predictions 
            if p.sub_status == winner_sub and p.explanation
        ]
        combined_explanation = "; ".join(winning_explanations[:2]) if winning_explanations else ""
        
        return EnsembleResult(
            sub_status=winner_sub,
            main_status=winner_main,
            confidence=confidence,
            explanation=combined_explanation,
            vote_count=len(valid_predictions),
            agreement_ratio=agreement_ratio,
            needs_human_review=needs_review,
            review_reason=review_reason,
            predictions=predictions,
            sub_status_votes=dict(sorted_sub),
            main_status_votes=dict(sorted_main)
        )
    
    def label(self, trace: str) -> EnsembleResult:
        """
        Label a logistics trace using multi-angle * multi-model ensemble.
        
        Args:
            trace: The logistics tracking text
            
        Returns:
            EnsembleResult with final prediction and all individual predictions
        """
        if not self.models:
            raise ValueError("No models configured. Use add_model() to add models.")
        
        if not self.prompt_variants:
            raise ValueError("No prompt variants configured. Use add_prompt_variant() to add variants.")
        
        # Collect predictions from all combinations
        predictions = self._collect_predictions(trace)
        
        # Aggregate predictions
        result = self._aggregate_predictions(predictions)
        
        return result
    
    def label_batch(self, traces: List[str]) -> List[EnsembleResult]:
        """Label multiple traces."""
        return [self.label(trace) for trace in traces]
    
    def get_config_summary(self) -> Dict:
        """Get a summary of the ensemble configuration."""
        return {
            "models": [
                {"name": m.name, "provider": m.provider, "weight": m.weight}
                for m in self.models
            ],
            "prompt_variants": [
                {"angle": p.angle.value, "weight": p.weight, "template": p.template_path}
                for p in self.prompt_variants
            ],
            "aggregation_strategy": self.aggregation_strategy,
            "min_confidence_threshold": self.min_confidence_threshold,
            "disagreement_threshold": self.disagreement_threshold,
            "dry_run": self.dry_run,
            "total_combinations": len(self.models) * len(self.prompt_variants)
        }


def create_default_ensemble(
    taxonomy_path: str,
    fewshot_path: str,
    prompts_dir: str,
    dry_run: bool = False
) -> EnsembleLabeler:
    """
    Create an ensemble labeler with default configuration.
    
    Default setup:
    - Models: GPT-5.2 (weight=1.2), Grok-4 (weight=1.0)
    - Angles: Rule-based, Time-based, Evidence-based
    """
    import os
    
    ensemble = EnsembleLabeler(
        taxonomy_path=taxonomy_path,
        fewshot_path=fewshot_path,
        dry_run=dry_run
    )
    
    # Add models (weights based on evaluation results)
    ensemble.add_model(ModelConfig(
        name="GPT-5.2",
        provider="abacus",
        model_id="gpt-5.2",
        api_key_env="ABACUS_API_KEY",
        weight=1.2  # Slightly higher weight based on evaluation
    ))
    
    ensemble.add_model(ModelConfig(
        name="Grok-4",
        provider="abacus",
        model_id="grok-4-0709",
        api_key_env="ABACUS_API_KEY",
        weight=1.0
    ))
    
    # Add prompt variants
    ensemble.add_prompt_variant(PromptVariant(
        angle=PromptAngle.RULE_BASED,
        template_path=os.path.join(prompts_dir, "rule_based.yaml"),
        weight=1.0,
        description="Strict rule-based classification with explicit priority rules"
    ))
    
    ensemble.add_prompt_variant(PromptVariant(
        angle=PromptAngle.TIME_BASED,
        template_path=os.path.join(prompts_dir, "time_based.yaml"),
        weight=1.0,
        description="Focus on latest 1-3 events for classification"
    ))
    
    ensemble.add_prompt_variant(PromptVariant(
        angle=PromptAngle.EVIDENCE_BASED,
        template_path=os.path.join(prompts_dir, "evidence_based.yaml"),
        weight=1.0,
        description="Extract evidence first, then classify"
    ))
    
    return ensemble


if __name__ == "__main__":
    # Example usage with dry run
    import os
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    ensemble = create_default_ensemble(
        taxonomy_path=os.path.join(project_root, "resources", "taxonomy", "taxonomy.json"),
        fewshot_path=os.path.join(project_root, "resources", "datasets", "fewshot.json"),
        prompts_dir=os.path.join(project_root, "resources", "prompts"),
        dry_run=True  # No actual API calls
    )
    
    print("Ensemble Configuration:")
    print(json.dumps(ensemble.get_config_summary(), indent=2))
    
    # Test with a sample trace
    test_trace = """单号：YT2534601002506026
物流商：YunExpress
2025-12-15 15:43:00 Clearance processing completed - Import 
2025-12-15 08:05:00 International flight has arrived US"""
    
    result = ensemble.label(test_trace)
    print(f"\nResult (dry run):")
    print(f"  Sub Status: {result.sub_status}")
    print(f"  Main Status: {result.main_status}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Vote Count: {result.vote_count}")
    print(f"  Needs Review: {result.needs_human_review}")
