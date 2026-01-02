"""
Configuration for the logistics status labeling pipeline.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ModelConfig:
    """Configuration for a single LLM model."""
    name: str
    provider: str  # "openai", "anthropic", "openrouter", "local"
    model_id: str
    api_key_env: str = ""
    base_url: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 2000
    weight: float = 1.0  # Weight for voting

@dataclass
class PipelineConfig:
    """Configuration for the labeling pipeline."""
    # Model configurations
    models: List[ModelConfig] = field(default_factory=list)
    
    # Voting settings
    num_samples_per_model: int = 1  # For self-consistency
    voting_strategy: str = "weighted_majority"  # "majority", "weighted_majority", "unanimous"
    min_confidence_threshold: float = 0.7
    
    # Few-shot settings
    num_few_shot_examples: int = 3
    use_retrieval_few_shot: bool = True
    
    # Quality control
    enable_rule_validation: bool = True
    mark_low_confidence_for_human: bool = True
    
    # Processing settings
    batch_size: int = 10
    max_retries: int = 3
    save_checkpoint_every: int = 100
    
    # Paths
    taxonomy_path: str = "taxonomy.json"
    sample_cases_path: str = "sample_cases.json"
    output_dir: str = "output"
    checkpoint_dir: str = "checkpoints"


# Default configuration with multiple models
DEFAULT_CONFIG = PipelineConfig(
    models=[
        ModelConfig(
            name="claude-sonnet",
            provider="anthropic",
            model_id="claude-sonnet-4-20250514",
            api_key_env="ANTHROPIC_API_KEY",
            temperature=0.0,
            weight=1.2
        ),
        ModelConfig(
            name="gpt-4o",
            provider="openai",
            model_id="gpt-4o",
            api_key_env="OPENAI_API_KEY",
            temperature=0.0,
            weight=1.0
        ),
        ModelConfig(
            name="gpt-4o-mini",
            provider="openai",
            model_id="gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
            temperature=0.0,
            weight=0.8
        ),
    ],
    num_samples_per_model=1,
    voting_strategy="weighted_majority",
    min_confidence_threshold=0.7,
    num_few_shot_examples=3,
    use_retrieval_few_shot=True,
    enable_rule_validation=True,
    mark_low_confidence_for_human=True,
    batch_size=10,
    max_retries=3,
    save_checkpoint_every=100,
)


# Single model configuration for testing
SINGLE_MODEL_CONFIG = PipelineConfig(
    models=[
        ModelConfig(
            name="gpt-4o-mini",
            provider="openai",
            model_id="gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
            temperature=0.0,
            weight=1.0
        ),
    ],
    num_samples_per_model=1,
    voting_strategy="majority",
    min_confidence_threshold=0.6,
    num_few_shot_examples=3,
    use_retrieval_few_shot=True,
    enable_rule_validation=True,
    mark_low_confidence_for_human=True,
    batch_size=10,
    max_retries=3,
    save_checkpoint_every=100,
)
