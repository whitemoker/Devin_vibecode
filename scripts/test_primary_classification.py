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
    "claude-opus-4.5": "claude-opus-4-5-20251101",
    "gemini-3": "gemini-3-pro-preview"
}


@dataclass
class TestResult:
    tracking_no: str
    true_label: str
    true_sub_status: str  # Original sub_status (e.g., DELIVERED_01)
    predicted_label: str
    confidence: float
    explanation: str
    model: str
    prompt_type: str
    prompt_version: str
    latency_ms: float
    raw_response: str
    error_type: str  # none/empty_response/timeout/parse_error
    retry_count: int
    has_return_evidence: bool  # Whether trace had RETURN_EVIDENCE marker
    trace_char_len: int  # Length of input trace
    latest_event: str  # Latest event text for quick reference


def load_goldenset(path: str) -> Dict[str, List[Dict]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_primary_from_sub_status(sub_status: str) -> str:
    """Extract primary category from sub_status (e.g., DELIVERED_01 -> DELIVERED)"""
    if "_" in sub_status:
        return sub_status.rsplit("_", 1)[0]
    return sub_status

def sample_balanced(goldenset: Dict[str, List[Dict]], total_samples: int = 100) -> List[Dict]:
    """Sample balanced by the LAST EVENT's sub_status (not trajectory-level category)"""
    # First, collect all samples with their true_label from last event's sub_status
    all_samples_by_primary = {cat: [] for cat in PRIMARY_CATEGORIES}
    
    for category, tracking_list in goldenset.items():
        for sample in tracking_list:
            events = sample.get("events", [])
            if events:
                last_sub_status = events[-1].get("transit_sub_status", "")
                true_primary = get_primary_from_sub_status(last_sub_status)
                if true_primary in PRIMARY_CATEGORIES:
                    all_samples_by_primary[true_primary].append({
                        "tracking_no": sample.get("tracking_no", "unknown"),
                        "true_label": true_primary,
                        "events": events
                    })
    
    # Now sample balanced from each primary category
    samples = []
    per_category = total_samples // len(PRIMARY_CATEGORIES)
    remainder = total_samples % len(PRIMARY_CATEGORIES)
    
    for i, category in enumerate(PRIMARY_CATEGORIES):
        category_samples = all_samples_by_primary.get(category, [])
        n = per_category + (1 if i < remainder else 0)
        n = min(n, len(category_samples))
        
        if category_samples:
            selected = random.sample(category_samples, n)
            samples.extend(selected)
    
    random.shuffle(samples)
    return samples


# STRONG return evidence: only these should override a final "delivered" status
# Weak evidence (refused, delivery failed, rescheduled) should NOT override delivered
STRONG_RETURN_KEYWORDS = [
    "return to sender", "returned to sender", "back to sender", "back to shipper",
    "rto", "rts", "return shipment", "returned shipment",
    "zurück an absender", "retour à l'expéditeur", "devuelto al remitente",
    "退回发件人", "退回寄件人", "退件完成"
]

# Broader return keywords (for reference, but not used to override delivered)
RETURN_KEYWORDS = STRONG_RETURN_KEYWORDS

def has_return_evidence(text: str) -> bool:
    """Check if text contains return/退回 evidence."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in RETURN_KEYWORDS)

def format_trace(events: List[Dict], max_events: int = 20) -> str:
    """Format trace events for LLM input.
    
    Args:
        events: List of event dictionaries
        max_events: Maximum number of events to include (default: 20, covers 75% of data without truncation)
    
    Returns:
        Formatted trace string with latest event highlighted and return evidence preserved
    """
    if not events:
        return "No events available"
    
    latest_event = events[-1] if events else {}
    details = latest_event.get("details", [])
    
    if not details:
        return "No event details available"
    
    # First pass: find return evidence in ALL events (before truncation)
    return_evidence_lines = []
    for detail in details:
        if isinstance(detail, str):
            line = detail
        elif isinstance(detail, dict):
            time_str = detail.get("time", "")
            desc = detail.get("description", "")
            location = detail.get("location", "")
            line = f"{time_str} {desc}"
            if location:
                line += f" [{location}]"
        else:
            continue
        
        if has_return_evidence(line):
            return_evidence_lines.append(line)
    
    # Keep only the latest N events for main trace
    recent_details = details[-max_events:]
    
    lines = []
    
    # Add return evidence section if found (and not already in recent details)
    if return_evidence_lines:
        # Check if return evidence is already in recent details
        recent_texts = set()
        for detail in recent_details:
            if isinstance(detail, str):
                recent_texts.add(detail)
            elif isinstance(detail, dict):
                time_str = detail.get("time", "")
                desc = detail.get("description", "")
                recent_texts.add(f"{time_str} {desc}")
        
        # Add return evidence that's not in recent details
        missing_evidence = [e for e in return_evidence_lines if not any(e in rt or rt in e for rt in recent_texts)]
        if missing_evidence:
            lines.append(">>> RETURN_EVIDENCE (from earlier in trajectory):")
            for evidence in missing_evidence[:3]:  # Limit to 3 evidence lines
                lines.append(f"  {evidence}")
            lines.append("")
    
    # Add recent events
    total = len(recent_details)
    for i, detail in enumerate(recent_details):
        is_latest = (i == total - 1)
        
        if isinstance(detail, str):
            line = detail
        elif isinstance(detail, dict):
            time_str = detail.get("time", "")
            desc = detail.get("description", "")
            location = detail.get("location", "")
            line = f"{time_str} {desc}"
            if location:
                line += f" [{location}]"
        else:
            continue
        
        # Highlight the latest event
        if is_latest:
            lines.append(f">>> LATEST: {line}")
        else:
            lines.append(line)
    
    return "\n".join(lines)


def load_prompt(prompt_path: str) -> Dict[str, str]:
    with open(prompt_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def call_llm(client: OpenAI, model: str, system_prompt: str, user_prompt: str, use_json_mode: bool = True, max_retries: int = 3) -> tuple:
    """Returns (content, latency_ms, retry_count)"""
    start_time = time.time()
    
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.0,
                "max_tokens": 500,
                "timeout": 60.0  # Increase timeout
            }
            
            if use_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            # Retry if response is empty
            if not content or content.strip() == "":
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                else:
                    latency_ms = (time.time() - start_time) * 1000
                    return "ERROR: Empty response after retries", latency_ms, attempt + 1
            
            latency_ms = (time.time() - start_time) * 1000
            return content, latency_ms, attempt
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
                continue
            latency_ms = (time.time() - start_time) * 1000
            return f"ERROR: {str(e)}", latency_ms, attempt + 1
    
    latency_ms = (time.time() - start_time) * 1000
    return "ERROR: Max retries exceeded", latency_ms, max_retries


def parse_response(response: str) -> tuple:
    # Strip markdown code blocks if present (Claude sometimes wraps JSON in ```json ... ```)
    if response and "```" in response:
        # Extract content between code blocks
        import re as re_local
        code_block_match = re_local.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if code_block_match:
            response = code_block_match.group(1).strip()
    
    # Try to parse the entire response as JSON first (for JSON mode responses)
    try:
        data = json.loads(response)
        
        # Handle array response (API sometimes returns [{...}] instead of {...})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        
        if isinstance(data, dict):
            status = data.get("primary_status", "UNKNOWN")
            confidence = float(data.get("confidence", 0.0))
            explanation = data.get("explanation", "")
            if status != "UNKNOWN" and status in PRIMARY_CATEGORIES:
                return status, confidence, explanation
    except:
        pass
    
    # Try to extract JSON from response using regex
    try:
        json_match = re.search(r'\{.*?"primary_status".*?\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            status = data.get("primary_status", "UNKNOWN")
            confidence = float(data.get("confidence", 0.0))
            explanation = data.get("explanation", "")
            if status != "UNKNOWN" and status in PRIMARY_CATEGORIES:
                return status, confidence, explanation
    except:
        pass
    
    # Fallback: extract category from text
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
    prompt_filter: List[str] = None,
    max_events: int = 20
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
        trace = format_trace(sample["events"], max_events=max_events)
        system_prompt = prompt_data["system_prompt"]
        user_prompt = prompt_data["user_prompt"].replace("$trace", trace)
        
        # Get latest event text for reference
        events = sample.get("events", [])
        latest_event = ""
        true_sub_status = ""
        if events:
            last_evt = events[-1]
            true_sub_status = last_evt.get("transit_sub_status", "")
            details = last_evt.get("details", [])
            if details:
                latest_event = str(details[-1])[:200]  # Truncate for storage
        
        # Check if trace has return evidence
        trace_has_return = ">>> RETURN_EVIDENCE" in trace
        
        response, latency, retry_count = call_llm(client, model_id, system_prompt, user_prompt, use_json_mode)
        predicted, confidence, explanation = parse_response(response)
        
        # Determine error type
        error_type = "none"
        if not response or response.strip() == "":
            error_type = "empty_response"
        elif response.startswith("ERROR:"):
            if "timeout" in response.lower():
                error_type = "timeout"
            else:
                error_type = "http_error"
        elif predicted == "UNKNOWN":
            error_type = "parse_error"
        
        result = TestResult(
            tracking_no=sample["tracking_no"],
            true_label=sample["true_label"],
            true_sub_status=true_sub_status,
            predicted_label=predicted,
            confidence=confidence,
            explanation=explanation,
            model=model_name,
            prompt_type=prompt_name,
            prompt_version=prompt_version or "default",
            latency_ms=latency,
            raw_response=response,
            error_type=error_type,
            retry_count=retry_count,
            has_return_evidence=trace_has_return,
            trace_char_len=len(trace),
            latest_event=latest_event
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


def save_predictions_long(results: Dict[str, List[TestResult]], output_path: str, run_id: str):
    """Save predictions in long format (one row per prediction) to JSONL."""
    with open(output_path, "w", encoding="utf-8") as f:
        for expert_key, test_results in results.items():
            for i, r in enumerate(test_results):
                record = {
                    "run_id": run_id,
                    "sample_id": f"{r.tracking_no}",
                    "tracking_no": r.tracking_no,
                    "true_label": r.true_label,
                    "true_sub_status": r.true_sub_status,
                    "expert_id": expert_key,
                    "model": r.model,
                    "prompt_type": r.prompt_type,
                    "prompt_version": r.prompt_version,
                    "pred_primary": r.predicted_label,
                    "confidence": r.confidence,
                    "explanation": r.explanation[:500] if r.explanation else "",
                    "latency_ms": r.latency_ms,
                    "error_type": r.error_type,
                    "retry_count": r.retry_count,
                    "has_return_evidence": r.has_return_evidence,
                    "trace_char_len": r.trace_char_len,
                    "latest_event": r.latest_event,
                    "is_correct": r.predicted_label == r.true_label,
                    "raw_response": r.raw_response if r.error_type != "none" else None
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Predictions (long format) saved to: {output_path}")


def save_samples_wide(results: Dict[str, List[TestResult]], output_path: str, run_id: str):
    """Save samples in wide format (one row per sample, columns for each expert)."""
    import csv
    import math
    
    # Group results by tracking_no
    samples_data = {}
    expert_keys = sorted(results.keys())
    
    for expert_key, test_results in results.items():
        for r in test_results:
            if r.tracking_no not in samples_data:
                samples_data[r.tracking_no] = {
                    "sample_id": r.tracking_no,
                    "tracking_no": r.tracking_no,
                    "true_label": r.true_label,
                    "true_sub_status": r.true_sub_status,
                    "has_return_evidence": r.has_return_evidence,
                    "trace_char_len": r.trace_char_len,
                    "experts": {}
                }
            samples_data[r.tracking_no]["experts"][expert_key] = {
                "pred": r.predicted_label,
                "conf": r.confidence,
                "is_correct": r.predicted_label == r.true_label
            }
    
    # Calculate disagreement features for each sample
    rows = []
    for tracking_no, sample in samples_data.items():
        row = {
            "run_id": run_id,
            "sample_id": sample["sample_id"],
            "tracking_no": sample["tracking_no"],
            "true_label": sample["true_label"],
            "true_sub_status": sample["true_sub_status"],
            "has_return_evidence": sample["has_return_evidence"],
            "trace_char_len": sample["trace_char_len"]
        }
        
        # Add expert predictions
        preds = []
        confs = []
        for expert_key in expert_keys:
            if expert_key in sample["experts"]:
                exp = sample["experts"][expert_key]
                row[f"{expert_key}_pred"] = exp["pred"]
                row[f"{expert_key}_conf"] = exp["conf"]
                row[f"{expert_key}_correct"] = exp["is_correct"]
                if exp["pred"] != "UNKNOWN":
                    preds.append(exp["pred"])
                    confs.append(exp["conf"])
            else:
                row[f"{expert_key}_pred"] = None
                row[f"{expert_key}_conf"] = None
                row[f"{expert_key}_correct"] = None
        
        # Calculate disagreement features
        if preds:
            from collections import Counter
            vote_counts = Counter(preds)
            n_unique = len(vote_counts)
            max_vote = max(vote_counts.values())
            max_vote_share = max_vote / len(preds)
            
            # Vote entropy
            total = len(preds)
            entropy = 0
            for count in vote_counts.values():
                p = count / total
                if p > 0:
                    entropy -= p * math.log2(p)
            
            # Top labels by votes
            sorted_labels = vote_counts.most_common()
            top1_label = sorted_labels[0][0]
            top1_votes = sorted_labels[0][1]
            top2_label = sorted_labels[1][0] if len(sorted_labels) > 1 else None
            top2_votes = sorted_labels[1][1] if len(sorted_labels) > 1 else 0
            
            # Confidence stats
            conf_mean = sum(confs) / len(confs) if confs else 0
            conf_min = min(confs) if confs else 0
            
            # Abstain count (UNKNOWN predictions)
            abstain_count = sum(1 for exp in sample["experts"].values() if exp["pred"] == "UNKNOWN")
            
            row["n_unique_preds"] = n_unique
            row["max_vote"] = max_vote
            row["max_vote_share"] = round(max_vote_share, 3)
            row["vote_entropy"] = round(entropy, 3)
            row["top1_label"] = top1_label
            row["top1_votes"] = top1_votes
            row["top2_label"] = top2_label
            row["top2_votes"] = top2_votes
            row["conf_mean"] = round(conf_mean, 3)
            row["conf_min"] = round(conf_min, 3)
            row["abstain_count"] = abstain_count
            row["need_review"] = n_unique > 1 or abstain_count > 0
            
            # Majority vote prediction
            row["majority_pred"] = top1_label
            row["majority_correct"] = top1_label == sample["true_label"]
        
        rows.append(row)
    
    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    print(f"Samples (wide format) saved to: {output_path}")
    return rows


def save_ensemble_summary(results: Dict[str, List[TestResult]], samples_wide: List[Dict], output_path: str, run_id: str):
    """Save ensemble analysis summary including diversity metrics and ensemble simulation."""
    from collections import Counter
    
    expert_keys = sorted(results.keys())
    
    # Single expert metrics
    expert_metrics = {}
    for expert_key, test_results in results.items():
        correct = sum(1 for r in test_results if r.predicted_label == r.true_label)
        total = len(test_results)
        accuracy = correct / total if total > 0 else 0
        
        # Per-class accuracy
        class_correct = defaultdict(int)
        class_total = defaultdict(int)
        for r in test_results:
            class_total[r.true_label] += 1
            if r.predicted_label == r.true_label:
                class_correct[r.true_label] += 1
        
        class_accuracy = {cls: class_correct[cls] / class_total[cls] if class_total[cls] > 0 else 0 
                         for cls in class_total}
        
        # Confidence stats
        confs = [r.confidence for r in test_results if r.predicted_label != "UNKNOWN"]
        correct_confs = [r.confidence for r in test_results if r.predicted_label == r.true_label]
        wrong_confs = [r.confidence for r in test_results if r.predicted_label != r.true_label and r.predicted_label != "UNKNOWN"]
        
        expert_metrics[expert_key] = {
            "accuracy": round(accuracy, 4),
            "correct": correct,
            "total": total,
            "class_accuracy": {k: round(v, 4) for k, v in class_accuracy.items()},
            "avg_confidence": round(sum(confs) / len(confs), 4) if confs else 0,
            "avg_conf_correct": round(sum(correct_confs) / len(correct_confs), 4) if correct_confs else 0,
            "avg_conf_wrong": round(sum(wrong_confs) / len(wrong_confs), 4) if wrong_confs else 0,
            "error_count": sum(1 for r in test_results if r.error_type != "none")
        }
    
    # Ensemble simulation: majority voting
    majority_correct = sum(1 for s in samples_wide if s.get("majority_correct", False))
    majority_accuracy = majority_correct / len(samples_wide) if samples_wide else 0
    
    # Disagreement stats
    disagreement_count = sum(1 for s in samples_wide if s.get("n_unique_preds", 1) > 1)
    disagreement_rate = disagreement_count / len(samples_wide) if samples_wide else 0
    
    # Complementarity: cases where one expert is wrong but another is right
    complementarity = {}
    for i, exp1 in enumerate(expert_keys):
        for exp2 in expert_keys[i+1:]:
            both_correct = 0
            both_wrong = 0
            exp1_only = 0
            exp2_only = 0
            for s in samples_wide:
                c1 = s.get(f"{exp1}_correct", False)
                c2 = s.get(f"{exp2}_correct", False)
                if c1 and c2:
                    both_correct += 1
                elif not c1 and not c2:
                    both_wrong += 1
                elif c1 and not c2:
                    exp1_only += 1
                else:
                    exp2_only += 1
            complementarity[f"{exp1}_vs_{exp2}"] = {
                "both_correct": both_correct,
                "both_wrong": both_wrong,
                f"{exp1}_only": exp1_only,
                f"{exp2}_only": exp2_only
            }
    
    summary = {
        "run_id": run_id,
        "total_samples": len(samples_wide),
        "total_experts": len(expert_keys),
        "expert_keys": expert_keys,
        "expert_metrics": expert_metrics,
        "ensemble_simulation": {
            "majority_voting": {
                "accuracy": round(majority_accuracy, 4),
                "correct": majority_correct,
                "total": len(samples_wide)
            }
        },
        "diversity_metrics": {
            "disagreement_count": disagreement_count,
            "disagreement_rate": round(disagreement_rate, 4),
            "avg_unique_preds": round(sum(s.get("n_unique_preds", 1) for s in samples_wide) / len(samples_wide), 2) if samples_wide else 0,
            "avg_vote_entropy": round(sum(s.get("vote_entropy", 0) for s in samples_wide) / len(samples_wide), 3) if samples_wide else 0
        },
        "complementarity": complementarity
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Ensemble summary saved to: {output_path}")
    return summary


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
    parser.add_argument("--max-events", "-e", type=int, default=20, help="Maximum number of events to include in trace (default: 20, covers 75%% of data)")
    parser.add_argument("--run-id", default="", help="Run ID for tracking. If not provided, uses timestamp.")
    args = parser.parse_args()
    
    random.seed(args.seed)
    
    # Generate run_id for tracking
    import hashlib
    from datetime import datetime
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    
    project_root = Path(__file__).parent.parent
    goldenset_path = project_root / "goldenset.json"
    prompts_dir = project_root / "resources" / "prompts"
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Create run-specific output directory
    run_output_dir = output_dir / f"run_{run_id}"
    run_output_dir.mkdir(exist_ok=True)
    
    # Load samples from fixed test set or sample from goldenset
    if args.test_set:
        print(f"Loading fixed test samples from: {args.test_set}")
        samples = load_test_samples(args.test_set)
        print(f"Loaded {len(samples)} samples")
        test_set_path = args.test_set
    else:
        print("Loading goldenset...")
        goldenset = load_goldenset(str(goldenset_path))
        
        print(f"Sampling {args.samples} balanced records...")
        samples = sample_balanced(goldenset, args.samples)
        print(f"Sampled {len(samples)} records")
        test_set_path = "sampled_from_goldenset"
        
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
    
    # Save run metadata
    run_metadata = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "test_set_path": test_set_path,
        "total_samples": len(samples),
        "prompt_version": args.version or "default",
        "max_events": args.max_events,
        "json_mode": not args.no_json_mode,
        "seed": args.seed,
        "workers": args.workers,
        "models": list(model_filter) if model_filter else list(MODELS.keys()),
        "prompts": list(prompt_filter) if prompt_filter else ["rule_based", "time_based", "evidence_based"],
        "category_distribution": dict(category_counts)
    }
    
    metadata_path = run_output_dir / "run_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(run_metadata, f, indent=2, ensure_ascii=False)
    print(f"Run metadata saved to: {metadata_path}")
    
    print(f"\nRunning tests (run_id={run_id}, max_events={args.max_events})...")
    results = run_tests(
        samples, 
        str(prompts_dir), 
        str(output_dir),
        prompt_version=args.version,
        use_json_mode=not args.no_json_mode,
        max_workers=args.workers,
        model_filter=model_filter,
        prompt_filter=prompt_filter,
        max_events=args.max_events
    )
    
    print("\nCalculating metrics...")
    metrics = calculate_metrics(results)
    
    # Include version in output filenames
    version_suffix = f"_{args.version}" if args.version else ""
    
    # Save comprehensive data files
    print("\n" + "="*80)
    print("SAVING COMPREHENSIVE DATA FOR ENSEMBLE ANALYSIS")
    print("="*80)
    
    # 1. predictions_long.jsonl - one row per prediction
    predictions_long_path = run_output_dir / "predictions_long.jsonl"
    save_predictions_long(results, str(predictions_long_path), run_id)
    
    # 2. samples_wide.csv - one row per sample with all expert predictions
    samples_wide_path = run_output_dir / "samples_wide.csv"
    samples_wide = save_samples_wide(results, str(samples_wide_path), run_id)
    
    # 3. ensemble_summary.json - diversity metrics and ensemble simulation
    summary_path = run_output_dir / "ensemble_summary.json"
    summary = save_ensemble_summary(results, samples_wide, str(summary_path), run_id)
    
    # 4. Generate markdown report
    report_path = run_output_dir / "report.md"
    print(f"\nGenerating report: {report_path}")
    generate_report(metrics, str(report_path))
    
    # 5. Save legacy results format for compatibility
    results_path = run_output_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        serializable_results = {}
        for key, test_results in results.items():
            serializable_results[key] = [
                {
                    "tracking_no": r.tracking_no,
                    "true_label": r.true_label,
                    "true_sub_status": r.true_sub_status,
                    "predicted_label": r.predicted_label,
                    "confidence": r.confidence,
                    "explanation": r.explanation,
                    "model": r.model,
                    "prompt_type": r.prompt_type,
                    "prompt_version": r.prompt_version,
                    "latency_ms": r.latency_ms,
                    "error_type": r.error_type,
                    "retry_count": r.retry_count,
                    "has_return_evidence": r.has_return_evidence,
                    "raw_response": r.raw_response if r.error_type != "none" else None
                }
                for r in test_results
            ]
        json.dump({
            "run_id": run_id,
            "version": args.version or "default",
            "samples": len(samples),
            "json_mode": not args.no_json_mode,
            "results": serializable_results, 
            "metrics": metrics
        }, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*80)
    print("RUN COMPLETE")
    print("="*80)
    print(f"Run ID: {run_id}")
    print(f"Output directory: {run_output_dir}")
    print(f"\nFiles generated:")
    print(f"  - run_metadata.json: Run configuration and parameters")
    print(f"  - predictions_long.jsonl: {sum(len(v) for v in results.values())} predictions (one per line)")
    print(f"  - samples_wide.csv: {len(samples_wide)} samples with all expert predictions")
    print(f"  - ensemble_summary.json: Diversity metrics and ensemble simulation")
    print(f"  - report.md: Human-readable report")
    print(f"  - results.json: Full results in JSON format")
    
    # Print key metrics
    print(f"\n--- KEY METRICS ---")
    print(f"Best single expert: {max(summary['expert_metrics'].items(), key=lambda x: x[1]['accuracy'])}")
    print(f"Majority voting accuracy: {summary['ensemble_simulation']['majority_voting']['accuracy']:.2%}")
    print(f"Disagreement rate: {summary['diversity_metrics']['disagreement_rate']:.2%}")
    print(f"Average vote entropy: {summary['diversity_metrics']['avg_vote_entropy']:.3f}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
