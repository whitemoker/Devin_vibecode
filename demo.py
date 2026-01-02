#!/usr/bin/env python3
"""
Demo script for the logistics status labeling pipeline.
Tests the pipeline with sample cases from the taxonomy.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import SINGLE_MODEL_CONFIG, DEFAULT_CONFIG, PipelineConfig, ModelConfig
from taxonomy_manager import TaxonomyManager
from few_shot_retriever import FewShotRetriever
from preprocessor import TracePreprocessor
from pipeline import LabelingPipeline, LabelingTask
from evaluator import Evaluator


def load_test_cases(sample_cases_path: str, n_per_class: int = 1):
    """Load test cases from sample cases file."""
    with open(sample_cases_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    # Group by sub_status
    by_status = {}
    for case in cases:
        sub_status = case['sub_status']
        if sub_status not in by_status:
            by_status[sub_status] = []
        by_status[sub_status].append(case)
    
    # Take n_per_class from each
    test_cases = []
    for sub_status, status_cases in by_status.items():
        for i, case in enumerate(status_cases[:n_per_class]):
            test_cases.append({
                'id': f"{sub_status}_{i}",
                'trace': case['trace'],
                'gold_label': sub_status,
                'gold_main': case['main_status'],
                'reason': case['reason']
            })
    
    return test_cases


def run_demo_single_model():
    """Run demo with a single model."""
    print("=" * 60)
    print("Logistics Status Labeling Pipeline - Single Model Demo")
    print("=" * 60)
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            # Use Anthropic instead
            config = PipelineConfig(
                models=[
                    ModelConfig(
                        name="claude-sonnet",
                        provider="anthropic",
                        model_id="claude-sonnet-4-20250514",
                        api_key_env="ANTHROPIC_API_KEY",
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
            )
        else:
            print("\nERROR: No API key found!")
            print("Please set one of the following environment variables:")
            print("  - OPENAI_API_KEY")
            print("  - ANTHROPIC_API_KEY")
            print("\nExample:")
            print("  export OPENAI_API_KEY='your-key-here'")
            print("  python demo.py")
            return
    else:
        config = SINGLE_MODEL_CONFIG
    
    # Initialize pipeline
    print("\nInitializing pipeline...")
    pipeline = LabelingPipeline(config, base_dir=str(project_root))
    
    if not pipeline.labelers:
        print("ERROR: No models were initialized successfully!")
        return
    
    print(f"Models initialized: {list(pipeline.labelers.keys())}")
    
    # Load test cases
    print("\nLoading test cases...")
    test_cases = load_test_cases(str(project_root / "sample_cases.json"), n_per_class=1)
    print(f"Loaded {len(test_cases)} test cases")
    
    # Run labeling on a few samples
    print("\n" + "=" * 60)
    print("Running labeling on sample cases...")
    print("=" * 60)
    
    results = []
    for i, case in enumerate(test_cases[:5]):  # Test first 5 cases
        print(f"\n--- Test Case {i+1}: {case['id']} ---")
        print(f"Gold Label: {case['gold_label']}")
        print(f"Trace Preview: {case['trace'][:150]}...")
        
        task = LabelingTask(
            id=case['id'],
            trace=case['trace'],
            metadata={'gold_label': case['gold_label']}
        )
        
        try:
            output = pipeline.label_single(task)
            
            print(f"\nPrediction: {output.sub_status}")
            print(f"Confidence: {output.confidence:.2f}")
            print(f"Explanation: {output.explanation}")
            
            is_correct = output.sub_status == case['gold_label']
            print(f"Correct: {'YES' if is_correct else 'NO'}")
            
            if output.needs_human_review:
                print(f"Needs Review: {output.review_reason}")
            
            results.append({
                'id': case['id'],
                'predicted': output.sub_status,
                'gold': case['gold_label'],
                'confidence': output.confidence,
                'correct': is_correct
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                'id': case['id'],
                'predicted': '',
                'gold': case['gold_label'],
                'confidence': 0,
                'correct': False
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("Demo Summary")
    print("=" * 60)
    
    correct = sum(1 for r in results if r['correct'])
    total = len(results)
    print(f"Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    
    print("\nPipeline Statistics:")
    stats = pipeline.get_stats()
    for key, value in stats.items():
        if key != 'by_status':
            print(f"  {key}: {value}")
    
    return results


def run_demo_multi_model():
    """Run demo with multiple models for voting."""
    print("=" * 60)
    print("Logistics Status Labeling Pipeline - Multi-Model Demo")
    print("=" * 60)
    
    # Check for API keys
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    models = []
    if openai_key:
        models.append(ModelConfig(
            name="gpt-4o-mini",
            provider="openai",
            model_id="gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
            temperature=0.0,
            weight=1.0
        ))
    
    if anthropic_key:
        models.append(ModelConfig(
            name="claude-sonnet",
            provider="anthropic",
            model_id="claude-sonnet-4-20250514",
            api_key_env="ANTHROPIC_API_KEY",
            temperature=0.0,
            weight=1.2
        ))
    
    if not models:
        print("\nERROR: No API keys found!")
        print("Please set at least one of:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        return
    
    config = PipelineConfig(
        models=models,
        num_samples_per_model=1,
        voting_strategy="weighted_majority",
        min_confidence_threshold=0.6,
        num_few_shot_examples=3,
        use_retrieval_few_shot=True,
        enable_rule_validation=True,
        mark_low_confidence_for_human=True,
    )
    
    # Initialize pipeline
    print("\nInitializing pipeline...")
    pipeline = LabelingPipeline(config, base_dir=str(project_root))
    print(f"Models initialized: {list(pipeline.labelers.keys())}")
    
    # Load test cases
    test_cases = load_test_cases(str(project_root / "sample_cases.json"), n_per_class=1)
    
    # Run on a few samples
    print(f"\nRunning on {min(3, len(test_cases))} test cases with multi-model voting...")
    
    for case in test_cases[:3]:
        print(f"\n--- {case['id']} ---")
        
        task = LabelingTask(id=case['id'], trace=case['trace'])
        output = pipeline.label_single(task)
        
        print(f"Gold: {case['gold_label']}")
        print(f"Predicted: {output.sub_status}")
        print(f"Confidence: {output.confidence:.2f}")
        
        # Show individual model predictions
        print("Model votes:")
        for pred in output.predictions:
            print(f"  - {pred['model']}: {pred['sub_status']} (conf={pred['confidence']:.2f})")
        
        print(f"Voting details: {output.voting_details.get('weighted_votes', {})}")


def run_evaluation_demo():
    """Run evaluation on all sample cases."""
    print("=" * 60)
    print("Evaluation Demo")
    print("=" * 60)
    
    # Load taxonomy
    taxonomy = TaxonomyManager(str(project_root / "taxonomy.json"))
    
    # Create evaluator
    evaluator = Evaluator(taxonomy_manager=taxonomy)
    
    # Create mock predictions for demonstration
    test_cases = load_test_cases(str(project_root / "sample_cases.json"), n_per_class=1)
    
    # Simulate some predictions (in real use, these would come from the pipeline)
    mock_predictions = []
    for case in test_cases:
        # Simulate 80% accuracy
        import random
        if random.random() < 0.8:
            predicted = case['gold_label']
        else:
            # Pick a random wrong label
            all_labels = taxonomy.get_all_sub_statuses()
            wrong_labels = [l for l in all_labels if l != case['gold_label']]
            predicted = random.choice(wrong_labels) if wrong_labels else case['gold_label']
        
        mock_predictions.append({
            'id': case['id'],
            'predicted': predicted,
            'gold': case['gold_label'],
            'trace': case['trace'][:200]
        })
    
    # Run evaluation
    result = evaluator.evaluate(mock_predictions)
    
    print(result.summary)
    
    if result.error_analysis:
        print("\nError Analysis (first 5):")
        for error in result.error_analysis[:5]:
            print(f"  ID: {error['id']}")
            print(f"    Predicted: {error['predicted']}")
            print(f"    Gold: {error['gold']}")
            print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Logistics Labeling Pipeline Demo")
    parser.add_argument(
        "--mode", 
        choices=["single", "multi", "eval"],
        default="single",
        help="Demo mode: single (one model), multi (multiple models), eval (evaluation)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "single":
        run_demo_single_model()
    elif args.mode == "multi":
        run_demo_multi_model()
    elif args.mode == "eval":
        run_evaluation_demo()
