"""
Test script for primary classification with multiple LLMs and prompts.
Tests 4 LLMs (Grok-4, GPT-5.2, Claude-4.5, Gemini-3) x 3 prompts on samples.
Supports JSON mode, concurrent API calls, and prompt versioning (v0, v1, etc.)
"""
import json
import random
import time
import re
import os
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai import OpenAI
import yaml

ABACUS_API_KEY = os.environ.get("ABACUS_API_KEY", "s2_0186d9e4b8c74102b04cb60979b85088")
ABACUS_BASE_URL = "https://routellm.abacus.ai/v1"

PRIMARY_CATEGORIES = [
    "INFO_RECEIVED",
    "IN_TRANSIT",
    "WAITING_DELIVERY",
    "DELIVERED",
    "DELIVERY_FAILED",
    "ABNORMAL"
]

SEMANTIC_NAMES = {
    "INFO_RECEIVED": "Shipment Information Received",
    "IN_TRANSIT": "In Transit",
    "WAITING_DELIVERY": "Out for Delivery / Awaiting Pickup",
    "DELIVERED": "Delivered",
    "DELIVERY_FAILED": "Delivery Failed",
    "ABNORMAL": "Exception / Abnormal"
}

MODELS = {
    "grok-4": "grok-4-0709",
    "gpt-5.2": "gpt-5.2",
    "claude-4.5": "claude-sonnet-4-20250514",
    "gemini-3": "gemini-3-pro-preview"
}


@dataclass
class TestResult:
    tracking_no: str
    true_label: str
    predicted_label: str
    confidence: float
    explanation: str
    model: str
    prompt_type: str
    latency_ms: float
    raw_response: str


def load_goldenset(path: str) -> Dict[str, List[Dict]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sample_balanced(goldenset: Dict[str, List[Dict]], total_samples: int = 100) -> List[Dict]:
    samples = []
    per_category = total_samples // len(PRIMARY_CATEGORIES)
    remainder = total_samples % len(PRIMARY_CATEGORIES)
    
    for i, category in enumerate(PRIMARY_CATEGORIES):
        category_samples = goldenset.get(category, [])
        n = per_category + (1 if i < remainder else 0)
        n = min(n, len(category_samples))
        
        selected = random.sample(category_samples, n)
        for sample in selected:
            samples.append({
                "tracking_no": sample.get("tracking_no", "unknown"),
                "true_label": category,
                "events": sample.get("events", [])
            })
    
    random.shuffle(samples)
    return samples


def format_trace(events: List[Dict], max_events: int = 10) -> str:
    if not events:
        return "No events available"
    
    latest_event = events[-1] if events else {}
    details = latest_event.get("details", [])
    
    if not details:
        return "No event details available"
    
    recent_details = details[-max_events:]
    recent_details = list(reversed(recent_details))
    
    lines = []
    for detail in recent_details:
        if isinstance(detail, str):
            lines.append(detail)
        elif isinstance(detail, dict):
            time_str = detail.get("time", "")
            desc = detail.get("description", "")
            location = detail.get("location", "")
            line = f"{time_str} {desc}"
            if location:
                line += f" [{location}]"
            lines.append(line)
    
    return "\n".join(lines)


def load_prompt(prompt_path: str) -> Dict[str, str]:
    with open(prompt_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def call_llm(client: OpenAI, model: str, system_prompt: str, user_prompt: str, use_json_mode: bool = True) -> tuple:
    start_time = time.time()
    
    try:
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 500
        }
        
        if use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**kwargs)
        
        latency_ms = (time.time() - start_time) * 1000
        content = response.choices[0].message.content
        return content, latency_ms
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return f"ERROR: {str(e)}", latency_ms


def parse_response(response: str) -> tuple:
    try:
        json_match = re.search(r'\{[^{}]*"primary_status"[^{}]*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            status = data.get("primary_status", "UNKNOWN")
            confidence = float(data.get("confidence", 0.0))
            explanation = data.get("explanation", "")
            return status, confidence, explanation
    except:
        pass
    
    for category in PRIMARY_CATEGORIES:
        if category in response.upper():
            return category, 0.5, "Extracted from text"
    
    return "UNKNOWN", 0.0, "Failed to parse"


def run_tests(
    samples: List[Dict],
    prompts_dir: str,
    output_dir: str,
    prompt_version: str = "",
    use_json_mode: bool = True,
    max_workers: int = 4,
    model_filter: List[str] = None,
    prompt_filter: List[str] = None
) -> Dict[str, List[TestResult]]:
    
    client = OpenAI(api_key=ABACUS_API_KEY, base_url=ABACUS_BASE_URL)
    
    # Filter models if specified
    models_to_test = MODELS
    if model_filter:
        models_to_test = {k: v for k, v in MODELS.items() if k in model_filter}
        if not models_to_test:
            print(f"Warning: No valid models found in filter {model_filter}. Using all models.")
            models_to_test = MODELS
    
    # Support versioned prompts (e.g., v0, v1)
    suffix = f"_{prompt_version}" if prompt_version else ""
    all_prompt_files = {
        "rule_based": f"primary_rule_based{suffix}.yaml",
        "time_based": f"primary_time_based{suffix}.yaml",
        "evidence_based": f"primary_evidence_based{suffix}.yaml"
    }
    
    # Filter prompts if specified
    if prompt_filter:
        prompt_files = {k: v for k, v in all_prompt_files.items() if k in prompt_filter}
        if not prompt_files:
            print(f"Warning: No valid prompts found in filter {prompt_filter}. Using all prompts.")
            prompt_files = all_prompt_files
    else:
        prompt_files = all_prompt_files
    
    prompts = {}
    for name, filename in prompt_files.items():
        path = os.path.join(prompts_dir, filename)
        if os.path.exists(path):
            prompts[name] = load_prompt(path)
        else:
            print(f"Warning: Prompt file not found: {path}")
    
    results = defaultdict(list)
    results_lock = threading.Lock()
    total_tests = len(samples) * len(models_to_test) * len(prompts)
    completed = [0]
    
    print(f"Running {total_tests} tests ({len(samples)} samples x {len(models_to_test)} models x {len(prompts)} prompts)")
    print(f"Models: {list(models_to_test.keys())}")
    print(f"Prompts: {list(prompts.keys())}")
    print(f"Using JSON mode: {use_json_mode}, Concurrent workers: {max_workers}")
    print(f"Prompt version: {prompt_version or 'default'}")
    print("-" * 80)
    
    def process_single_test(sample, model_name, model_id, prompt_name, prompt_data):
        trace = format_trace(sample["events"])
        system_prompt = prompt_data["system_prompt"]
        user_prompt = prompt_data["user_prompt"].replace("$trace", trace)
        
        response, latency = call_llm(client, model_id, system_prompt, user_prompt, use_json_mode)
        predicted, confidence, explanation = parse_response(response)
        
        result = TestResult(
            tracking_no=sample["tracking_no"],
            true_label=sample["true_label"],
            predicted_label=predicted,
            confidence=confidence,
            explanation=explanation,
            model=model_name,
            prompt_type=prompt_name,
            latency_ms=latency,
            raw_response=response
        )
        
        key = f"{model_name}_{prompt_name}"
        
        with results_lock:
            results[key].append(result)
            completed[0] += 1
            is_correct = predicted == sample["true_label"]
            status = "OK" if is_correct else "WRONG"
            print(f"[{completed[0]}/{total_tests}] {model_name}/{prompt_name}: {sample['true_label']} -> {predicted} [{status}] ({latency:.0f}ms)")
        
        return result
    
    # Build list of all test tasks
    tasks = []
    for sample in samples:
        for model_name, model_id in models_to_test.items():
            for prompt_name, prompt_data in prompts.items():
                tasks.append((sample, model_name, model_id, prompt_name, prompt_data))
    
    # Run tests concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_test, *task) for task in tasks]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in test: {e}")
    
    return dict(results)


def calculate_metrics(results: Dict[str, List[TestResult]]) -> Dict[str, Dict]:
    metrics = {}
    
    for key, test_results in results.items():
        correct = sum(1 for r in test_results if r.predicted_label == r.true_label)
        total = len(test_results)
        accuracy = correct / total if total > 0 else 0
        
        confusion = defaultdict(lambda: defaultdict(int))
        for r in test_results:
            confusion[r.true_label][r.predicted_label] += 1
        
        per_category = {}
        for category in PRIMARY_CATEGORIES:
            cat_results = [r for r in test_results if r.true_label == category]
            cat_correct = sum(1 for r in cat_results if r.predicted_label == category)
            cat_total = len(cat_results)
            per_category[category] = {
                "correct": cat_correct,
                "total": cat_total,
                "accuracy": cat_correct / cat_total if cat_total > 0 else 0
            }
        
        avg_latency = sum(r.latency_ms for r in test_results) / len(test_results) if test_results else 0
        
        metrics[key] = {
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "per_category": per_category,
            "confusion_matrix": dict(confusion),
            "avg_latency_ms": avg_latency
        }
    
    return metrics


def generate_report(metrics: Dict[str, Dict], output_path: str):
    lines = []
    lines.append("# Primary Classification Test Report")
    lines.append("")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## Overall Results")
    lines.append("")
    lines.append("| Model | Prompt | Accuracy | Correct/Total | Avg Latency |")
    lines.append("|-------|--------|----------|---------------|-------------|")
    
    sorted_keys = sorted(metrics.keys(), key=lambda k: metrics[k]["accuracy"], reverse=True)
    for key in sorted_keys:
        m = metrics[key]
        model, prompt = key.split("_", 1)
        lines.append(f"| {model} | {prompt} | {m['accuracy']*100:.2f}% | {m['correct']}/{m['total']} | {m['avg_latency_ms']:.0f}ms |")
    
    lines.append("")
    lines.append("## Best Combinations")
    lines.append("")
    
    best_key = sorted_keys[0]
    best_m = metrics[best_key]
    model, prompt = best_key.split("_", 1)
    lines.append(f"**Best Overall**: {model} + {prompt} ({best_m['accuracy']*100:.2f}%)")
    lines.append("")
    
    model_best = {}
    for key in sorted_keys:
        model, prompt = key.split("_", 1)
        if model not in model_best:
            model_best[model] = (key, metrics[key]["accuracy"])
    
    lines.append("**Best per Model**:")
    for model, (key, acc) in sorted(model_best.items(), key=lambda x: x[1][1], reverse=True):
        _, prompt = key.split("_", 1)
        lines.append(f"- {model}: {prompt} ({acc*100:.2f}%)")
    
    lines.append("")
    lines.append("## Per-Category Accuracy (Best Model)")
    lines.append("")
    lines.append("| Category | Accuracy | Correct/Total |")
    lines.append("|----------|----------|---------------|")
    
    best_per_cat = metrics[best_key]["per_category"]
    for category in PRIMARY_CATEGORIES:
        cat_m = best_per_cat[category]
        lines.append(f"| {category} | {cat_m['accuracy']*100:.2f}% | {cat_m['correct']}/{cat_m['total']} |")
    
    lines.append("")
    lines.append("## Confusion Matrix (Best Model)")
    lines.append("")
    lines.append("Rows = True Label, Columns = Predicted Label")
    lines.append("")
    
    header = "| True \\ Pred | " + " | ".join(PRIMARY_CATEGORIES) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(PRIMARY_CATEGORIES) + 1))
    
    confusion = metrics[best_key]["confusion_matrix"]
    for true_cat in PRIMARY_CATEGORIES:
        row = f"| {true_cat} |"
        for pred_cat in PRIMARY_CATEGORIES:
            count = confusion.get(true_cat, {}).get(pred_cat, 0)
            row += f" {count} |"
        lines.append(row)
    
    report = "\n".join(lines)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n" + "=" * 80)
    print(report)
    
    return report


def save_test_samples(samples: List[Dict], output_path: str):
    """Save test samples to a JSON file for reproducibility."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "description": "Fixed test samples for primary classification evaluation",
            "total_samples": len(samples),
            "samples": samples
        }, f, indent=2, ensure_ascii=False)
    print(f"Test samples saved to: {output_path}")


def load_test_samples(input_path: str) -> List[Dict]:
    """Load test samples from a JSON file."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["samples"]


def main():
    parser = argparse.ArgumentParser(description="Test primary classification with multiple LLMs and prompts")
    parser.add_argument("--version", "-v", default="", help="Prompt version (e.g., v0, v1). Empty for default prompts.")
    parser.add_argument("--samples", "-n", type=int, default=100, help="Number of samples to test (default: 100)")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Number of concurrent workers (default: 4)")
    parser.add_argument("--no-json-mode", action="store_true", help="Disable JSON mode for API calls")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling (default: 42)")
    parser.add_argument("--models", "-m", default="", help="Comma-separated list of models to test (e.g., 'gemini-3,gpt-5.2'). Empty for all models.")
    parser.add_argument("--prompts", "-p", default="", help="Comma-separated list of prompts to test (e.g., 'time_based,rule_based'). Empty for all prompts.")
    parser.add_argument("--test-set", "-t", default="", help="Path to fixed test samples JSON file. If not provided, samples from goldenset.")
    parser.add_argument("--save-samples", "-s", default="", help="Save sampled data to this path (for creating fixed test sets).")
    args = parser.parse_args()
    
    random.seed(args.seed)
    
    project_root = Path(__file__).parent.parent
    goldenset_path = project_root / "goldenset.json"
    prompts_dir = project_root / "resources" / "prompts"
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Load samples from fixed test set or sample from goldenset
    if args.test_set:
        print(f"Loading fixed test samples from: {args.test_set}")
        samples = load_test_samples(args.test_set)
        print(f"Loaded {len(samples)} samples")
    else:
        print("Loading goldenset...")
        goldenset = load_goldenset(str(goldenset_path))
        
        print(f"Sampling {args.samples} balanced records...")
        samples = sample_balanced(goldenset, args.samples)
        print(f"Sampled {len(samples)} records")
        
        # Save samples if requested
        if args.save_samples:
            save_test_samples(samples, args.save_samples)
    
    category_counts = defaultdict(int)
    for s in samples:
        category_counts[s["true_label"]] += 1
    print(f"Distribution: {dict(category_counts)}")
    
    # Parse model and prompt filters
    model_filter = [m.strip() for m in args.models.split(",") if m.strip()] if args.models else None
    prompt_filter = [p.strip() for p in args.prompts.split(",") if p.strip()] if args.prompts else None
    
    print("\nRunning tests...")
    results = run_tests(
        samples, 
        str(prompts_dir), 
        str(output_dir),
        prompt_version=args.version,
        use_json_mode=not args.no_json_mode,
        max_workers=args.workers,
        model_filter=model_filter,
        prompt_filter=prompt_filter
    )
    
    print("\nCalculating metrics...")
    metrics = calculate_metrics(results)
    
    # Include version in output filenames
    version_suffix = f"_{args.version}" if args.version else ""
    report_path = output_dir / f"primary_classification_report{version_suffix}.md"
    print(f"\nGenerating report: {report_path}")
    generate_report(metrics, str(report_path))
    
    results_path = output_dir / f"primary_classification_results{version_suffix}.json"
    with open(results_path, "w", encoding="utf-8") as f:
        serializable_results = {}
        for key, test_results in results.items():
            serializable_results[key] = [
                {
                    "tracking_no": r.tracking_no,
                    "true_label": r.true_label,
                    "predicted_label": r.predicted_label,
                    "confidence": r.confidence,
                    "explanation": r.explanation,
                    "model": r.model,
                    "prompt_type": r.prompt_type,
                    "latency_ms": r.latency_ms
                }
                for r in test_results
            ]
        json.dump({
            "version": args.version or "default",
            "samples": args.samples,
            "json_mode": not args.no_json_mode,
            "results": serializable_results, 
            "metrics": metrics
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {results_path}")
    print("Done!")


if __name__ == "__main__":
    main()
