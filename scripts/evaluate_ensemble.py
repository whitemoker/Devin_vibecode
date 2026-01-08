#!/usr/bin/env python3
"""
Evaluation script for the multi-angle * multi-model ensemble labeler.

This script evaluates the ensemble labeling approach on the test dataset
and compares it with single-model results.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import time
import argparse
from typing import Dict, List, Tuple
from dataclasses import dataclass

from ensemble_labeler import (
    EnsembleLabeler, 
    ModelConfig, 
    PromptVariant, 
    PromptAngle,
    create_default_ensemble
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAXONOMY_PATH = os.path.join(PROJECT_ROOT, 'resources', 'taxonomy', 'taxonomy.json')
FEWSHOT_PATH = os.path.join(PROJECT_ROOT, 'resources', 'datasets', 'fewshot.json')
TEST_PATH = os.path.join(PROJECT_ROOT, 'resources', 'datasets', 'test.json')
PROMPTS_DIR = os.path.join(PROJECT_ROOT, 'resources', 'prompts')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')


@dataclass
class EvalResult:
    """Evaluation result for a single sample."""
    expected_sub: str
    predicted_sub: str
    expected_main: str
    predicted_main: str
    is_correct: bool
    is_main_correct: bool
    confidence: float
    agreement_ratio: float
    needs_review: bool
    vote_count: int
    trace_snippet: str


def load_test_data() -> List[Dict]:
    """Load test dataset."""
    with open(TEST_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_ensemble(
    models: List[str] = None,
    angles: List[str] = None,
    dry_run: bool = False
) -> EnsembleLabeler:
    """Create ensemble labeler with specified configuration."""
    
    ensemble = EnsembleLabeler(
        taxonomy_path=TAXONOMY_PATH,
        fewshot_path=FEWSHOT_PATH,
        dry_run=dry_run
    )
    
    # Default models
    if models is None:
        models = ["gpt-5.2", "grok-4"]
    
    # Add models
    model_configs = {
        "gpt-5.2": ModelConfig(
            name="GPT-5.2",
            provider="abacus",
            model_id="gpt-5.2",
            api_key_env="ABACUS_API_KEY",
            weight=1.2
        ),
        "grok-4": ModelConfig(
            name="Grok-4",
            provider="abacus",
            model_id="grok-4-0709",
            api_key_env="ABACUS_API_KEY",
            weight=1.0
        ),
        "kimi": ModelConfig(
            name="Kimi",
            provider="kimi",
            model_id="moonshot-v1-128k",
            api_key_env="KIMI_API_KEY",
            weight=0.8
        ),
    }
    
    for model_name in models:
        if model_name.lower() in model_configs:
            ensemble.add_model(model_configs[model_name.lower()])
        else:
            print(f"Warning: Unknown model '{model_name}'")
    
    # Default angles
    if angles is None:
        angles = ["rule_based", "time_based", "evidence_based"]
    
    # Add prompt variants
    angle_configs = {
        "rule_based": PromptVariant(
            angle=PromptAngle.RULE_BASED,
            template_path=os.path.join(PROMPTS_DIR, "rule_based.yaml"),
            weight=1.0,
            description="Strict rule-based classification"
        ),
        "time_based": PromptVariant(
            angle=PromptAngle.TIME_BASED,
            template_path=os.path.join(PROMPTS_DIR, "time_based.yaml"),
            weight=1.0,
            description="Focus on latest events"
        ),
        "evidence_based": PromptVariant(
            angle=PromptAngle.EVIDENCE_BASED,
            template_path=os.path.join(PROMPTS_DIR, "evidence_based.yaml"),
            weight=1.0,
            description="Extract evidence first"
        ),
        "hierarchical": PromptVariant(
            angle=PromptAngle.HIERARCHICAL,
            template_path="",  # Uses built-in templates
            weight=1.0,
            description="Two-stage classification"
        ),
    }
    
    for angle_name in angles:
        if angle_name.lower() in angle_configs:
            ensemble.add_prompt_variant(angle_configs[angle_name.lower()])
        else:
            print(f"Warning: Unknown angle '{angle_name}'")
    
    return ensemble


def evaluate(
    ensemble: EnsembleLabeler,
    test_data: List[Dict],
    limit: int = None
) -> Tuple[List[EvalResult], Dict]:
    """Run evaluation on test data."""
    
    results = []
    correct = 0
    correct_main = 0
    needs_review_count = 0
    total = min(len(test_data), limit) if limit else len(test_data)
    
    print(f"\nEvaluating ensemble on {total} samples...")
    print(f"Configuration: {len(ensemble.models)} models x {len(ensemble.prompt_variants)} angles = {len(ensemble.models) * len(ensemble.prompt_variants)} combinations")
    print("-" * 60)
    
    for i, item in enumerate(test_data[:total]):
        trace = item['trace']
        expected_sub = item['sub_status']
        expected_main = item['main_status']
        
        print(f"[{i+1}/{total}] Testing {expected_sub}...", end=' ', flush=True)
        
        try:
            result = ensemble.label(trace)
            predicted_sub = result.sub_status
            predicted_main = result.main_status
            confidence = result.confidence
            agreement = result.agreement_ratio
            needs_review = result.needs_human_review
            vote_count = result.vote_count
        except Exception as e:
            print(f"ERROR: {e}")
            predicted_sub = "ERROR"
            predicted_main = "ERROR"
            confidence = 0.0
            agreement = 0.0
            needs_review = True
            vote_count = 0
        
        is_correct = predicted_sub == expected_sub
        is_main_correct = predicted_main == expected_main
        
        if is_correct:
            correct += 1
            print(f"OK (conf={confidence:.2f}, agree={agreement:.2f})")
        else:
            print(f"WRONG -> {predicted_sub} (conf={confidence:.2f}, agree={agreement:.2f})")
        
        if is_main_correct:
            correct_main += 1
        
        if needs_review:
            needs_review_count += 1
        
        trace_snippet = trace[:200] + "..." if len(trace) > 200 else trace
        
        results.append(EvalResult(
            expected_sub=expected_sub,
            predicted_sub=predicted_sub,
            expected_main=expected_main,
            predicted_main=predicted_main,
            is_correct=is_correct,
            is_main_correct=is_main_correct,
            confidence=confidence,
            agreement_ratio=agreement,
            needs_review=needs_review,
            vote_count=vote_count,
            trace_snippet=trace_snippet
        ))
        
        time.sleep(0.5)  # Rate limiting
    
    stats = {
        'total': total,
        'correct': correct,
        'accuracy': correct / total if total > 0 else 0,
        'main_correct': correct_main,
        'main_accuracy': correct_main / total if total > 0 else 0,
        'needs_review': needs_review_count,
        'review_rate': needs_review_count / total if total > 0 else 0,
    }
    
    return results, stats


def generate_report(
    results: List[EvalResult],
    stats: Dict,
    ensemble: EnsembleLabeler,
    output_path: str
):
    """Generate evaluation report."""
    
    lines = []
    
    # Title
    lines.append("# Ensemble Labeler Evaluation Report\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Configuration
    lines.append("## Configuration\n")
    config = ensemble.get_config_summary()
    lines.append(f"- Models: {', '.join(m['name'] for m in config['models'])}")
    lines.append(f"- Prompt Angles: {', '.join(p['angle'] for p in config['prompt_variants'])}")
    lines.append(f"- Total Combinations: {config['total_combinations']}")
    lines.append(f"- Aggregation Strategy: {config['aggregation_strategy']}")
    lines.append("")
    
    # Overall Results
    lines.append("## Overall Results\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Samples | {stats['total']} |")
    lines.append(f"| Sub-status Accuracy | {stats['correct']}/{stats['total']} = {stats['accuracy']:.2%} |")
    lines.append(f"| Main-status Accuracy | {stats['main_correct']}/{stats['total']} = {stats['main_accuracy']:.2%} |")
    lines.append(f"| Needs Human Review | {stats['needs_review']}/{stats['total']} = {stats['review_rate']:.2%} |")
    lines.append("")
    
    # Error Analysis
    lines.append("## Error Analysis\n")
    
    errors = [r for r in results if not r.is_correct]
    if errors:
        lines.append(f"Total Errors: {len(errors)}\n")
        
        # Group by expected status
        from collections import defaultdict
        by_expected = defaultdict(list)
        for r in errors:
            by_expected[r.expected_sub].append(r)
        
        for expected_sub in sorted(by_expected.keys()):
            error_list = by_expected[expected_sub]
            lines.append(f"### {expected_sub} ({len(error_list)} errors)\n")
            
            for r in error_list[:3]:  # Show first 3 errors per category
                lines.append(f"**Predicted:** {r.predicted_sub} (conf={r.confidence:.2f}, agree={r.agreement_ratio:.2f})")
                lines.append(f"```")
                lines.append(r.trace_snippet)
                lines.append(f"```")
                lines.append("")
    else:
        lines.append("No errors!\n")
    
    # Human Review Cases
    lines.append("## Cases Flagged for Human Review\n")
    
    review_cases = [r for r in results if r.needs_review]
    if review_cases:
        lines.append(f"Total: {len(review_cases)}\n")
        lines.append("| Expected | Predicted | Confidence | Agreement | Correct |")
        lines.append("|----------|-----------|------------|-----------|---------|")
        
        for r in review_cases[:20]:  # Show first 20
            correct_mark = "Yes" if r.is_correct else "No"
            lines.append(f"| {r.expected_sub} | {r.predicted_sub} | {r.confidence:.2f} | {r.agreement_ratio:.2f} | {correct_mark} |")
    else:
        lines.append("No cases flagged for review.\n")
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\nReport saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate ensemble labeler")
    parser.add_argument("--models", nargs="+", default=["gpt-5.2", "grok-4"],
                        help="Models to use (default: gpt-5.2 grok-4)")
    parser.add_argument("--angles", nargs="+", default=["rule_based", "time_based", "evidence_based"],
                        help="Prompt angles to use")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of test samples")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without actual API calls")
    parser.add_argument("--output", type=str, default=None,
                        help="Output report path")
    
    args = parser.parse_args()
    
    # Create ensemble
    ensemble = create_ensemble(
        models=args.models,
        angles=args.angles,
        dry_run=args.dry_run
    )
    
    print("\nEnsemble Configuration:")
    print(json.dumps(ensemble.get_config_summary(), indent=2))
    
    # Load test data
    test_data = load_test_data()
    print(f"\nLoaded {len(test_data)} test samples")
    
    # Run evaluation
    results, stats = evaluate(ensemble, test_data, limit=args.limit)
    
    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Sub-status Accuracy: {stats['correct']}/{stats['total']} = {stats['accuracy']:.2%}")
    print(f"Main-status Accuracy: {stats['main_correct']}/{stats['total']} = {stats['main_accuracy']:.2%}")
    print(f"Needs Human Review: {stats['needs_review']}/{stats['total']} = {stats['review_rate']:.2%}")
    
    # Generate report
    output_path = args.output or os.path.join(OUTPUT_DIR, "ensemble_evaluation_report.md")
    generate_report(results, stats, ensemble, output_path)
    
    # Save raw results
    results_path = output_path.replace('.md', '_results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': stats,
            'results': [
                {
                    'expected_sub': r.expected_sub,
                    'predicted_sub': r.predicted_sub,
                    'expected_main': r.expected_main,
                    'predicted_main': r.predicted_main,
                    'is_correct': r.is_correct,
                    'confidence': r.confidence,
                    'agreement_ratio': r.agreement_ratio,
                    'needs_review': r.needs_review,
                }
                for r in results
            ]
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {results_path}")


if __name__ == "__main__":
    main()
