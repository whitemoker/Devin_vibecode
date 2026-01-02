#!/usr/bin/env python3
"""
Evaluate LLM models on logistics status classification.
Supports multiple models: Kimi, GPT-5, Claude-4.5.

Usage:
    python scripts/evaluate_models.py --provider kimi --api-key YOUR_KEY
    python scripts/evaluate_models.py --provider abacus --model gpt-5 --api-key YOUR_KEY
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import argparse
from collections import defaultdict
from typing import Dict, List

from llm_client import MoonshotClient, AbacusClient
from simple_labeler import SimpleLabeler

# Resource paths (relative to project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAXONOMY_PATH = os.path.join(PROJECT_ROOT, 'resources', 'taxonomy', 'taxonomy.json')
FEWSHOT_PATH = os.path.join(PROJECT_ROOT, 'resources', 'datasets', 'fewshot.json')
TEST_PATH = os.path.join(PROJECT_ROOT, 'resources', 'datasets', 'test.json')
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, 'resources', 'prompts', 'prompt_template.yaml')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')


def load_test_data(path: str = None) -> List[Dict]:
    """Load test dataset."""
    path = path or TEST_PATH
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate(
    labeler: SimpleLabeler,
    test_data: List[Dict],
    verbose: bool = True
) -> Dict:
    """Evaluate labeler on test dataset."""
    total = len(test_data)
    correct = 0
    correct_main = 0
    
    results = []
    errors_by_status = defaultdict(list)
    
    for i, item in enumerate(test_data):
        trace = item['trace']
        expected_sub = item['sub_status']
        expected_main = item['main_status']
        
        if verbose:
            print(f"[{i+1}/{total}] Testing {expected_sub}...", end=' ')
        
        result = labeler.label(trace)
        predicted_sub = result.sub_status
        predicted_main = result.main_status
        
        is_correct = predicted_sub == expected_sub
        is_main_correct = predicted_main == expected_main
        
        if is_correct:
            correct += 1
            if verbose:
                print("OK")
        else:
            if verbose:
                print(f"WRONG (predicted: {predicted_sub})")
            errors_by_status[expected_sub].append({
                'expected': expected_sub,
                'predicted': predicted_sub,
                'confidence': result.confidence,
                'explanation': result.explanation
            })
        
        if is_main_correct:
            correct_main += 1
        
        results.append({
            'expected_sub': expected_sub,
            'predicted_sub': predicted_sub,
            'expected_main': expected_main,
            'predicted_main': predicted_main,
            'is_correct': is_correct,
            'is_main_correct': is_main_correct,
            'confidence': result.confidence,
            'explanation': result.explanation
        })
    
    accuracy = correct / total if total > 0 else 0
    main_accuracy = correct_main / total if total > 0 else 0
    
    return {
        'total': total,
        'correct': correct,
        'accuracy': accuracy,
        'main_correct': correct_main,
        'main_accuracy': main_accuracy,
        'errors_by_status': dict(errors_by_status),
        'results': results
    }


def main():
    parser = argparse.ArgumentParser(description='Evaluate LLM labeling accuracy')
    parser.add_argument('--provider', choices=['kimi', 'abacus'], required=True, help='LLM provider')
    parser.add_argument('--model', default=None, help='Model name (default: moonshot-v1-128k for kimi, gpt-5 for abacus)')
    parser.add_argument('--api-key', required=True, help='API key')
    parser.add_argument('--num-examples', type=int, default=3, help='Number of few-shot examples')
    parser.add_argument('--output', default=None, help='Output file path')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode')
    args = parser.parse_args()
    
    # Create client based on provider
    if args.provider == 'kimi':
        model = args.model or 'moonshot-v1-128k'
        client = MoonshotClient(api_key=args.api_key, model=model)
    else:  # abacus
        model = args.model or 'gpt-5'
        client = AbacusClient(api_key=args.api_key, model=model)
    
    # Create labeler
    labeler = SimpleLabeler(
        client=client,
        taxonomy_path=TAXONOMY_PATH,
        template_path=TEMPLATE_PATH,
        sample_cases_path=FEWSHOT_PATH,
        num_examples=args.num_examples,
        anonymize=False
    )
    
    # Load test data
    test_data = load_test_data()
    
    print(f"Evaluating {args.provider}/{model} on {len(test_data)} test samples...")
    print(f"Using {args.num_examples} few-shot examples")
    
    # Run evaluation
    metrics = evaluate(labeler, test_data, verbose=not args.quiet)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Sub-status Accuracy: {metrics['correct']}/{metrics['total']} = {metrics['accuracy']:.2%}")
    print(f"Main-status Accuracy: {metrics['main_correct']}/{metrics['total']} = {metrics['main_accuracy']:.2%}")
    print(f"{'='*60}")
    
    # Save results
    output_path = args.output or os.path.join(OUTPUT_DIR, f"{args.provider}_{model.replace('-', '_')}_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output_data = {
        'provider': args.provider,
        'model': model,
        **metrics
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
