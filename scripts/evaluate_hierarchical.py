"""
Evaluate hierarchical (two-stage) labeler on test dataset.
Compares performance with single-stage labeler.
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_client import MoonshotClient, AbacusClient
from hierarchical_labeler import HierarchicalLabeler, TAXONOMY_TO_MAIN


@dataclass
class EvalResult:
    """Evaluation result for a single sample."""
    trace: str
    expected_sub: str
    expected_main: str
    predicted_sub: str
    predicted_main: str
    confidence: float
    explanation: str
    is_correct_sub: bool
    is_correct_main: bool
    is_uncertain: bool
    uncertain_stage: str
    stage1_main: str
    stage1_conf: float
    stage2_sub: str
    stage2_conf: float


def get_main_status(sub_status: str, taxonomy: Dict) -> str:
    """Get main status from sub status."""
    for main_key, subs in taxonomy.items():
        if sub_status in subs:
            return TAXONOMY_TO_MAIN.get(main_key, main_key)
    return "UNKNOWN"


def evaluate_model(
    labeler: HierarchicalLabeler,
    test_data: List[Dict],
    taxonomy: Dict,
    model_name: str
) -> Tuple[List[EvalResult], Dict]:
    """Evaluate a model on test data."""
    results = []
    correct_sub = 0
    correct_main = 0
    uncertain_count = 0
    
    print(f"\nEvaluating {model_name}...")
    
    for i, sample in enumerate(test_data):
        trace = sample["trace"]
        expected_sub = sample["sub_status"]
        expected_main = get_main_status(expected_sub, taxonomy)
        
        try:
            result = labeler.label(trace)
            
            is_correct_sub = result.sub_status == expected_sub
            is_correct_main = result.main_status == expected_main
            
            if is_correct_sub:
                correct_sub += 1
            if is_correct_main:
                correct_main += 1
            if result.is_uncertain:
                uncertain_count += 1
            
            eval_result = EvalResult(
                trace=trace[:200] + "..." if len(trace) > 200 else trace,
                expected_sub=expected_sub,
                expected_main=expected_main,
                predicted_sub=result.sub_status,
                predicted_main=result.main_status,
                confidence=result.confidence,
                explanation=result.explanation,
                is_correct_sub=is_correct_sub,
                is_correct_main=is_correct_main,
                is_uncertain=result.is_uncertain,
                uncertain_stage=result.uncertain_stage,
                stage1_main=result.stage1_main_status,
                stage1_conf=result.stage1_confidence,
                stage2_sub=result.stage2_sub_status,
                stage2_conf=result.stage2_confidence
            )
            results.append(eval_result)
            
            status = "OK" if is_correct_sub else "WRONG"
            print(f"  [{i+1}/{len(test_data)}] {status} - Expected: {expected_sub}, Got: {result.sub_status}")
            
        except Exception as e:
            print(f"  [{i+1}/{len(test_data)}] ERROR: {e}")
            results.append(EvalResult(
                trace=trace[:200],
                expected_sub=expected_sub,
                expected_main=expected_main,
                predicted_sub="ERROR",
                predicted_main="ERROR",
                confidence=0.0,
                explanation=str(e),
                is_correct_sub=False,
                is_correct_main=False,
                is_uncertain=False,
                uncertain_stage="",
                stage1_main="",
                stage1_conf=0.0,
                stage2_sub="",
                stage2_conf=0.0
            ))
    
    total = len(test_data)
    stats = {
        "model": model_name,
        "total": total,
        "correct_sub": correct_sub,
        "correct_main": correct_main,
        "uncertain": uncertain_count,
        "sub_accuracy": correct_sub / total if total > 0 else 0,
        "main_accuracy": correct_main / total if total > 0 else 0,
        "uncertain_rate": uncertain_count / total if total > 0 else 0
    }
    
    print(f"\n{model_name} Results:")
    print(f"  Sub-status Accuracy: {stats['sub_accuracy']:.2%} ({correct_sub}/{total})")
    print(f"  Main-status Accuracy: {stats['main_accuracy']:.2%} ({correct_main}/{total})")
    print(f"  Uncertain Rate: {stats['uncertain_rate']:.2%} ({uncertain_count}/{total})")
    
    return results, stats


def generate_report(
    all_results: Dict[str, List[EvalResult]],
    all_stats: Dict[str, Dict],
    output_path: str
):
    """Generate comparison report in Markdown format."""
    lines = ["# Hierarchical Labeler Evaluation Report\n"]
    
    # Overall comparison
    lines.append("## Overall Accuracy Comparison\n")
    lines.append("| Model | Sub-status Acc | Main-status Acc | Uncertain Rate |")
    lines.append("|-------|---------------|-----------------|----------------|")
    
    for model, stats in all_stats.items():
        lines.append(f"| {model} | {stats['sub_accuracy']:.2%} ({stats['correct_sub']}/{stats['total']}) | {stats['main_accuracy']:.2%} ({stats['correct_main']}/{stats['total']}) | {stats['uncertain_rate']:.2%} |")
    
    lines.append("")
    
    # Bad cases analysis
    lines.append("## Bad Case Analysis\n")
    
    # Collect all bad cases
    all_bad_cases = {}
    for model, results in all_results.items():
        for r in results:
            if not r.is_correct_sub:
                key = r.expected_sub + "|" + r.trace[:100]
                if key not in all_bad_cases:
                    all_bad_cases[key] = {
                        "trace": r.trace,
                        "expected_sub": r.expected_sub,
                        "expected_main": r.expected_main,
                        "models": {}
                    }
                all_bad_cases[key]["models"][model] = {
                    "predicted_sub": r.predicted_sub,
                    "predicted_main": r.predicted_main,
                    "confidence": r.confidence,
                    "explanation": r.explanation,
                    "stage1_main": r.stage1_main,
                    "stage1_conf": r.stage1_conf,
                    "stage2_sub": r.stage2_sub,
                    "stage2_conf": r.stage2_conf,
                    "is_uncertain": r.is_uncertain,
                    "uncertain_stage": r.uncertain_stage
                }
    
    lines.append(f"Total unique bad cases: {len(all_bad_cases)}\n")
    
    for i, (key, case) in enumerate(all_bad_cases.items(), 1):
        lines.append(f"### Bad Case {i}\n")
        lines.append(f"**Expected:** {case['expected_sub']} ({case['expected_main']})\n")
        lines.append(f"**Trace (snippet):**")
        lines.append(f"```")
        lines.append(case['trace'][:300])
        lines.append(f"```\n")
        
        lines.append("| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |")
        lines.append("|-------|-------------|-------------|------------|-------------|-------|-----------|")
        
        for model in all_results.keys():
            if model in case["models"]:
                m = case["models"][model]
                uncertain = f"{m['uncertain_stage']}" if m['is_uncertain'] else "No"
                lines.append(f"| {model} | {m['stage1_main']} | {m['stage1_conf']:.2f} | {m['stage2_sub']} | {m['stage2_conf']:.2f} | {m['predicted_sub']} | {uncertain} |")
            else:
                lines.append(f"| {model} | - | - | - | - | (correct) | - |")
        
        lines.append("")
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"\nReport saved to: {output_path}")


def main():
    # Paths
    base_dir = Path(__file__).parent.parent
    taxonomy_path = base_dir / "resources/taxonomy/taxonomy.json"
    main_template_path = base_dir / "resources/prompts/main_stage.yaml"
    sub_template_path = base_dir / "resources/prompts/sub_stage.yaml"
    fewshot_path = base_dir / "resources/datasets/fewshot.json"
    test_path = base_dir / "resources/datasets/test.json"
    output_dir = base_dir / "output"
    
    # Load data
    with open(taxonomy_path, 'r', encoding='utf-8') as f:
        taxonomy = json.load(f)
    
    with open(test_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    print(f"Loaded {len(test_data)} test samples")
    
    # API keys (must be set via environment variables)
    kimi_key = os.environ.get("KIMI_API_KEY")
    abacus_key = os.environ.get("ABACUS_API_KEY")
    
    if not kimi_key:
        print("ERROR: KIMI_API_KEY environment variable not set")
        sys.exit(1)
    if not abacus_key:
        print("ERROR: ABACUS_API_KEY environment variable not set")
        sys.exit(1)
    
    all_results = {}
    all_stats = {}
    
    # Test with Kimi
    print("\n" + "="*50)
    print("Testing Kimi (moonshot-v1-128k) - Hierarchical")
    print("="*50)
    
    kimi_client = MoonshotClient(api_key=kimi_key, model="moonshot-v1-128k")
    kimi_labeler = HierarchicalLabeler(
        client=kimi_client,
        taxonomy_path=str(taxonomy_path),
        main_template_path=str(main_template_path),
        sub_template_path=str(sub_template_path),
        fewshot_path=str(fewshot_path),
        main_threshold=0.6,
        sub_threshold=0.5
    )
    
    kimi_results, kimi_stats = evaluate_model(kimi_labeler, test_data, taxonomy, "Kimi-Hierarchical")
    all_results["Kimi-Hierarchical"] = kimi_results
    all_stats["Kimi-Hierarchical"] = kimi_stats
    
    # Save Kimi results
    kimi_output = {
        "model": "Kimi-Hierarchical",
        "stats": kimi_stats,
        "results": [
            {
                "expected_sub": r.expected_sub,
                "expected_main": r.expected_main,
                "predicted_sub": r.predicted_sub,
                "predicted_main": r.predicted_main,
                "confidence": r.confidence,
                "is_correct_sub": r.is_correct_sub,
                "is_correct_main": r.is_correct_main,
                "is_uncertain": r.is_uncertain,
                "stage1_main": r.stage1_main,
                "stage1_conf": r.stage1_conf,
                "stage2_sub": r.stage2_sub,
                "stage2_conf": r.stage2_conf
            }
            for r in kimi_results
        ]
    }
    with open(output_dir / "kimi_hierarchical_results.json", 'w', encoding='utf-8') as f:
        json.dump(kimi_output, f, ensure_ascii=False, indent=2)
    
    # Test with GPT-5
    print("\n" + "="*50)
    print("Testing GPT-5 - Hierarchical")
    print("="*50)
    
    gpt5_client = AbacusClient(api_key=abacus_key, model="gpt-5")
    gpt5_labeler = HierarchicalLabeler(
        client=gpt5_client,
        taxonomy_path=str(taxonomy_path),
        main_template_path=str(main_template_path),
        sub_template_path=str(sub_template_path),
        fewshot_path=str(fewshot_path),
        main_threshold=0.6,
        sub_threshold=0.5
    )
    
    gpt5_results, gpt5_stats = evaluate_model(gpt5_labeler, test_data, taxonomy, "GPT5-Hierarchical")
    all_results["GPT5-Hierarchical"] = gpt5_results
    all_stats["GPT5-Hierarchical"] = gpt5_stats
    
    # Save GPT-5 results
    gpt5_output = {
        "model": "GPT5-Hierarchical",
        "stats": gpt5_stats,
        "results": [
            {
                "expected_sub": r.expected_sub,
                "expected_main": r.expected_main,
                "predicted_sub": r.predicted_sub,
                "predicted_main": r.predicted_main,
                "confidence": r.confidence,
                "is_correct_sub": r.is_correct_sub,
                "is_correct_main": r.is_correct_main,
                "is_uncertain": r.is_uncertain,
                "stage1_main": r.stage1_main,
                "stage1_conf": r.stage1_conf,
                "stage2_sub": r.stage2_sub,
                "stage2_conf": r.stage2_conf
            }
            for r in gpt5_results
        ]
    }
    with open(output_dir / "gpt5_hierarchical_results.json", 'w', encoding='utf-8') as f:
        json.dump(gpt5_output, f, ensure_ascii=False, indent=2)
    
    # Test with Claude-4.5
    print("\n" + "="*50)
    print("Testing Claude-4.5 - Hierarchical")
    print("="*50)
    
    claude_client = AbacusClient(api_key=abacus_key, model="claude-opus-4-5-20251101")
    claude_labeler = HierarchicalLabeler(
        client=claude_client,
        taxonomy_path=str(taxonomy_path),
        main_template_path=str(main_template_path),
        sub_template_path=str(sub_template_path),
        fewshot_path=str(fewshot_path),
        main_threshold=0.6,
        sub_threshold=0.5
    )
    
    claude_results, claude_stats = evaluate_model(claude_labeler, test_data, taxonomy, "Claude45-Hierarchical")
    all_results["Claude45-Hierarchical"] = claude_results
    all_stats["Claude45-Hierarchical"] = claude_stats
    
    # Save Claude results
    claude_output = {
        "model": "Claude45-Hierarchical",
        "stats": claude_stats,
        "results": [
            {
                "expected_sub": r.expected_sub,
                "expected_main": r.expected_main,
                "predicted_sub": r.predicted_sub,
                "predicted_main": r.predicted_main,
                "confidence": r.confidence,
                "is_correct_sub": r.is_correct_sub,
                "is_correct_main": r.is_correct_main,
                "is_uncertain": r.is_uncertain,
                "stage1_main": r.stage1_main,
                "stage1_conf": r.stage1_conf,
                "stage2_sub": r.stage2_sub,
                "stage2_conf": r.stage2_conf
            }
            for r in claude_results
        ]
    }
    with open(output_dir / "claude45_hierarchical_results.json", 'w', encoding='utf-8') as f:
        json.dump(claude_output, f, ensure_ascii=False, indent=2)
    
    # Generate comparison report
    generate_report(all_results, all_stats, str(output_dir / "hierarchical_comparison_report.md"))
    
    print("\n" + "="*50)
    print("Evaluation Complete!")
    print("="*50)


if __name__ == "__main__":
    main()
