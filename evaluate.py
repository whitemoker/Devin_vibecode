"""
Evaluate LLM labeling accuracy on test dataset.
Uses test_dataset.json (28 samples, 1 per sub-status).
Few-shot examples come from sample_cases_fewshot.json (56 samples, 2 per sub-status).
"""
import json
import argparse
from collections import defaultdict
from typing import Dict, List

from llm_client import MoonshotClient
from simple_labeler import SimpleLabeler


def load_test_data(path: str = "test_dataset.json") -> List[Dict]:
    """Load test dataset."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate(
    labeler: SimpleLabeler,
    test_data: List[Dict],
    verbose: bool = True
) -> Dict:
    """
    Evaluate labeler on test dataset.
    
    Returns:
        Dict with accuracy metrics.
    """
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
            print(f"\n[{i+1}/{total}] Testing {expected_sub}...")
        
        result = labeler.label(trace)
        predicted_sub = result.sub_status
        predicted_main = result.main_status
        
        is_correct = predicted_sub == expected_sub
        is_main_correct = predicted_main == expected_main
        
        if is_correct:
            correct += 1
        else:
            errors_by_status[expected_sub].append({
                'expected': expected_sub,
                'predicted': predicted_sub,
                'confidence': result.confidence
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
        
        if verbose:
            status = "OK" if is_correct else "WRONG"
            print(f"  Expected: {expected_sub}")
            print(f"  Predicted: {predicted_sub} (conf: {result.confidence:.2f})")
            print(f"  Result: {status}")
    
    # Calculate metrics
    accuracy = correct / total if total > 0 else 0
    main_accuracy = correct_main / total if total > 0 else 0
    
    metrics = {
        'total': total,
        'correct': correct,
        'accuracy': accuracy,
        'main_correct': correct_main,
        'main_accuracy': main_accuracy,
        'errors_by_status': dict(errors_by_status),
        'results': results
    }
    
    return metrics


def print_report(metrics: Dict):
    """Print evaluation report."""
    print("\n" + "=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)
    
    print(f"\nSub-status Accuracy: {metrics['correct']}/{metrics['total']} = {metrics['accuracy']:.2%}")
    print(f"Main-status Accuracy: {metrics['main_correct']}/{metrics['total']} = {metrics['main_accuracy']:.2%}")
    
    if metrics['errors_by_status']:
        print("\nErrors by status:")
        for status, errors in metrics['errors_by_status'].items():
            for err in errors:
                print(f"  {status} -> {err['predicted']} (conf: {err['confidence']:.2f})")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Evaluate LLM labeling accuracy')
    parser.add_argument('--api-key', required=True, help='Kimi API key')
    parser.add_argument('--model', default='moonshot-v1-128k', help='Model name')
    parser.add_argument('--test-data', default='test_dataset.json', help='Test dataset path')
    parser.add_argument('--fewshot-data', default='sample_cases_fewshot.json', help='Few-shot examples path')
    parser.add_argument('--template', default='prompt_template.yaml', help='Prompt template path')
    parser.add_argument('--num-examples', type=int, default=3, help='Number of few-shot examples')
    parser.add_argument('--anonymize', action='store_true', help='Enable name anonymization')
    parser.add_argument('--output', default='eval_results.json', help='Output results path')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode')
    args = parser.parse_args()
    
    # Create client
    client = MoonshotClient(api_key=args.api_key, model=args.model)
    
    # Create labeler with few-shot data (not test data)
    labeler = SimpleLabeler(
        client=client,
        taxonomy_path='taxonomy.json',
        template_path=args.template,
        sample_cases_path=args.fewshot_data,
        num_examples=args.num_examples,
        anonymize=args.anonymize
    )
    
    # Load test data
    test_data = load_test_data(args.test_data)
    
    print(f"Evaluating on {len(test_data)} test samples...")
    print(f"Using {args.num_examples} few-shot examples from {args.fewshot_data}")
    print(f"Model: {args.model}")
    
    # Run evaluation
    metrics = evaluate(labeler, test_data, verbose=not args.quiet)
    
    # Print report
    print_report(metrics)
    
    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
