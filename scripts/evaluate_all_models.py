#!/usr/bin/env python3
"""
Comprehensive evaluation script for all models with both single-stage and hierarchical pipelines.
Tests: GPT-5.2, Grok-4, Kimi on 56 test samples.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import time
from collections import defaultdict
from typing import Dict, List, Tuple
from dataclasses import dataclass

from llm_client import MoonshotClient, AbacusClient
from simple_labeler import SimpleLabeler
from hierarchical_labeler import HierarchicalLabeler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAXONOMY_PATH = os.path.join(PROJECT_ROOT, 'resources', 'taxonomy', 'taxonomy.json')
FEWSHOT_PATH = os.path.join(PROJECT_ROOT, 'resources', 'datasets', 'fewshot.json')
TEST_PATH = os.path.join(PROJECT_ROOT, 'resources', 'datasets', 'test.json')
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, 'resources', 'prompts', 'prompt_template.yaml')
MAIN_STAGE_PATH = os.path.join(PROJECT_ROOT, 'resources', 'prompts', 'main_stage.yaml')
SUB_STAGE_PATH = os.path.join(PROJECT_ROOT, 'resources', 'prompts', 'sub_stage.yaml')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')

# API Keys - load from environment variables
ABACUS_API_KEY = os.environ.get("ABACUS_API_KEY", "")
KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "")

# Models to test
MODELS = [
    {"name": "GPT-5.2", "provider": "abacus", "model": "gpt-5.2", "api_key": ABACUS_API_KEY},
    {"name": "Grok-4", "provider": "abacus", "model": "grok-4-0709", "api_key": ABACUS_API_KEY},
    {"name": "Kimi", "provider": "kimi", "model": "moonshot-v1-128k", "api_key": KIMI_API_KEY},
]


@dataclass
class EvalResult:
    expected_sub: str
    predicted_sub: str
    expected_main: str
    predicted_main: str
    is_correct: bool
    is_main_correct: bool
    confidence: float
    explanation: str
    trace_snippet: str
    reason: str


def load_data():
    """Load taxonomy and test data."""
    with open(TAXONOMY_PATH, 'r', encoding='utf-8') as f:
        taxonomy = json.load(f)
    with open(TEST_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    return taxonomy, test_data


def create_client(model_config: Dict):
    """Create LLM client based on config."""
    if model_config["provider"] == "kimi":
        return MoonshotClient(api_key=model_config["api_key"], model=model_config["model"])
    else:
        return AbacusClient(api_key=model_config["api_key"], model=model_config["model"])


def evaluate_single_stage(client, test_data: List[Dict], model_name: str) -> Tuple[List[EvalResult], Dict]:
    """Evaluate using single-stage (28-class) pipeline."""
    labeler = SimpleLabeler(
        client=client,
        taxonomy_path=TAXONOMY_PATH,
        template_path=TEMPLATE_PATH,
        sample_cases_path=FEWSHOT_PATH,
        num_examples=3,
        anonymize=False
    )
    
    results = []
    correct = 0
    correct_main = 0
    total = len(test_data)
    
    for i, item in enumerate(test_data):
        trace = item['trace']
        expected_sub = item['sub_status']
        expected_main = item['main_status']
        reason = item.get('reason', '')
        
        print(f"[{model_name}][Single][{i+1}/{total}] Testing {expected_sub}...", end=' ', flush=True)
        
        try:
            result = labeler.label(trace)
            predicted_sub = result.sub_status
            predicted_main = result.main_status
            confidence = result.confidence
            explanation = result.explanation
        except Exception as e:
            print(f"ERROR: {e}")
            predicted_sub = "ERROR"
            predicted_main = "ERROR"
            confidence = 0.0
            explanation = str(e)
        
        is_correct = predicted_sub == expected_sub
        is_main_correct = predicted_main == expected_main
        
        if is_correct:
            correct += 1
            print("OK")
        else:
            print(f"WRONG -> {predicted_sub}")
        
        if is_main_correct:
            correct_main += 1
        
        trace_snippet = trace[:200] + "..." if len(trace) > 200 else trace
        
        results.append(EvalResult(
            expected_sub=expected_sub,
            predicted_sub=predicted_sub,
            expected_main=expected_main,
            predicted_main=predicted_main,
            is_correct=is_correct,
            is_main_correct=is_main_correct,
            confidence=confidence,
            explanation=explanation,
            trace_snippet=trace_snippet,
            reason=reason
        ))
        
        time.sleep(0.5)  # Rate limiting
    
    stats = {
        'total': total,
        'correct': correct,
        'accuracy': correct / total if total > 0 else 0,
        'main_correct': correct_main,
        'main_accuracy': correct_main / total if total > 0 else 0,
    }
    
    return results, stats


def evaluate_hierarchical(client, test_data: List[Dict], model_name: str, taxonomy: Dict) -> Tuple[List[EvalResult], Dict]:
    """Evaluate using hierarchical (two-stage) pipeline."""
    labeler = HierarchicalLabeler(
        client=client,
        taxonomy_path=TAXONOMY_PATH,
        main_template_path=MAIN_STAGE_PATH,
        sub_template_path=SUB_STAGE_PATH,
        fewshot_path=FEWSHOT_PATH,
        main_threshold=0.6,
        sub_threshold=0.6
    )
    
    results = []
    correct = 0
    correct_main = 0
    uncertain = 0
    total = len(test_data)
    
    for i, item in enumerate(test_data):
        trace = item['trace']
        expected_sub = item['sub_status']
        expected_main = item['main_status']
        reason = item.get('reason', '')
        
        print(f"[{model_name}][Hierarchical][{i+1}/{total}] Testing {expected_sub}...", end=' ', flush=True)
        
        try:
            result = labeler.label(trace)
            predicted_sub = result.sub_status
            predicted_main = result.main_status
            confidence = result.confidence
            explanation = result.explanation
            
            if predicted_sub == "UNKNOWN":
                uncertain += 1
        except Exception as e:
            print(f"ERROR: {e}")
            predicted_sub = "ERROR"
            predicted_main = "ERROR"
            confidence = 0.0
            explanation = str(e)
        
        is_correct = predicted_sub == expected_sub
        is_main_correct = predicted_main == expected_main
        
        if is_correct:
            correct += 1
            print("OK")
        elif predicted_sub == "UNKNOWN":
            print("UNCERTAIN")
        else:
            print(f"WRONG -> {predicted_sub}")
        
        if is_main_correct:
            correct_main += 1
        
        trace_snippet = trace[:200] + "..." if len(trace) > 200 else trace
        
        results.append(EvalResult(
            expected_sub=expected_sub,
            predicted_sub=predicted_sub,
            expected_main=expected_main,
            predicted_main=predicted_main,
            is_correct=is_correct,
            is_main_correct=is_main_correct,
            confidence=confidence,
            explanation=explanation,
            trace_snippet=trace_snippet,
            reason=reason
        ))
        
        time.sleep(0.5)  # Rate limiting
    
    stats = {
        'total': total,
        'correct': correct,
        'accuracy': correct / total if total > 0 else 0,
        'main_correct': correct_main,
        'main_accuracy': correct_main / total if total > 0 else 0,
        'uncertain': uncertain,
        'uncertain_rate': uncertain / total if total > 0 else 0,
    }
    
    return results, stats


def generate_confusion_matrix(results: List[EvalResult], all_labels: List[str]) -> Dict[str, Dict[str, int]]:
    """Generate confusion matrix from results."""
    matrix = {label: {l: 0 for l in all_labels} for label in all_labels}
    for r in results:
        expected = r.expected_sub
        predicted = r.predicted_sub
        if expected in matrix and predicted in all_labels:
            matrix[expected][predicted] += 1
        elif expected in matrix:
            if "OTHER" not in matrix[expected]:
                for label in all_labels:
                    matrix[label]["OTHER"] = 0
            matrix[expected]["OTHER"] = matrix[expected].get("OTHER", 0) + 1
    return matrix


def format_confusion_matrix_md(matrix: Dict[str, Dict[str, int]], all_labels: List[str], model_name: str) -> List[str]:
    """Format confusion matrix as Markdown table."""
    lines = []
    lines.append(f"### {model_name} Confusion Matrix\n")
    
    # Find labels that have any predictions or expectations
    active_labels = set()
    for expected, preds in matrix.items():
        for pred, count in preds.items():
            if count > 0:
                active_labels.add(expected)
                active_labels.add(pred)
    
    sorted_labels = sorted(active_labels)
    
    # Create header with abbreviated labels
    header = "| Expected \\ Predicted |"
    separator = "|---|"
    for label in sorted_labels:
        short = label.replace("IN_TRANSIT_", "IT").replace("WAITING_DELIVERY_", "WD").replace("DELIVERED_", "DL").replace("DELIVERY_FAILED_", "DF").replace("ABNORMAL_", "AB").replace("INFO_RECEIVED_", "IR")
        header += f" {short} |"
        separator += "---|"
    
    lines.append(header)
    lines.append(separator)
    
    # Create rows
    for expected in sorted_labels:
        short_exp = expected.replace("IN_TRANSIT_", "IT").replace("WAITING_DELIVERY_", "WD").replace("DELIVERED_", "DL").replace("DELIVERY_FAILED_", "DF").replace("ABNORMAL_", "AB").replace("INFO_RECEIVED_", "IR")
        row = f"| {short_exp} |"
        for predicted in sorted_labels:
            count = matrix.get(expected, {}).get(predicted, 0)
            if count > 0:
                if expected == predicted:
                    row += f" **{count}** |"
                else:
                    row += f" {count} |"
            else:
                row += " . |"
        lines.append(row)
    
    lines.append("")
    lines.append("*Legend: IT=IN_TRANSIT, WD=WAITING_DELIVERY, DL=DELIVERED, DF=DELIVERY_FAILED, AB=ABNORMAL, IR=INFO_RECEIVED*\n")
    
    return lines


def generate_report(
    single_results: Dict[str, Tuple[List[EvalResult], Dict]],
    hierarchical_results: Dict[str, Tuple[List[EvalResult], Dict]],
    all_labels: List[str],
    output_path: str
):
    """Generate comprehensive comparison report."""
    lines = []
    
    # Title
    lines.append("# 模型评估对比报告 (Model Evaluation Comparison Report)\n")
    lines.append(f"测试样本数: 56\n")
    lines.append(f"测试模型: GPT-5.2, Grok-4, Kimi\n")
    lines.append("")
    
    # Overall accuracy comparison
    lines.append("## 1. 总体准确率对比 (Overall Accuracy Comparison)\n")
    lines.append("### 单阶段 (Single-Stage 28-Class)\n")
    lines.append("| 模型 | 子状态准确率 | 主状态准确率 |")
    lines.append("|------|-------------|-------------|")
    
    for model_name, (results, stats) in single_results.items():
        sub_acc = f"{stats['correct']}/{stats['total']} = {stats['accuracy']:.2%}"
        main_acc = f"{stats['main_correct']}/{stats['total']} = {stats['main_accuracy']:.2%}"
        lines.append(f"| {model_name} | {sub_acc} | {main_acc} |")
    
    lines.append("")
    lines.append("### 分层分类 (Hierarchical Two-Stage)\n")
    lines.append("| 模型 | 子状态准确率 | 主状态准确率 | 不确定率 |")
    lines.append("|------|-------------|-------------|---------|")
    
    for model_name, (results, stats) in hierarchical_results.items():
        sub_acc = f"{stats['correct']}/{stats['total']} = {stats['accuracy']:.2%}"
        main_acc = f"{stats['main_correct']}/{stats['total']} = {stats['main_accuracy']:.2%}"
        unc_rate = f"{stats.get('uncertain', 0)}/{stats['total']} = {stats.get('uncertain_rate', 0):.2%}"
        lines.append(f"| {model_name} | {sub_acc} | {main_acc} | {unc_rate} |")
    
    lines.append("")
    
    # Comparison table
    lines.append("### 单阶段 vs 分层对比\n")
    lines.append("| 模型 | 单阶段准确率 | 分层准确率 | 变化 |")
    lines.append("|------|------------|----------|------|")
    
    for model_name in single_results.keys():
        single_acc = single_results[model_name][1]['accuracy']
        hier_acc = hierarchical_results[model_name][1]['accuracy']
        diff = hier_acc - single_acc
        diff_str = f"+{diff:.2%}" if diff > 0 else f"{diff:.2%}"
        lines.append(f"| {model_name} | {single_acc:.2%} | {hier_acc:.2%} | {diff_str} |")
    
    lines.append("")
    
    # Confusion matrices for single-stage
    lines.append("## 2. 混淆矩阵 - 单阶段 (Confusion Matrices - Single-Stage)\n")
    for model_name, (results, stats) in single_results.items():
        matrix = generate_confusion_matrix(results, all_labels)
        lines.extend(format_confusion_matrix_md(matrix, all_labels, model_name))
    
    # Confusion matrices for hierarchical
    lines.append("## 3. 混淆矩阵 - 分层 (Confusion Matrices - Hierarchical)\n")
    for model_name, (results, stats) in hierarchical_results.items():
        matrix = generate_confusion_matrix(results, all_labels)
        lines.extend(format_confusion_matrix_md(matrix, all_labels, model_name))
    
    # Bad case analysis - Single Stage
    lines.append("## 4. Bad Case 分析 - 单阶段 (Bad Case Analysis - Single-Stage)\n")
    
    # Group by expected status
    bad_cases_single = defaultdict(list)
    for model_name, (results, stats) in single_results.items():
        for r in results:
            if not r.is_correct:
                bad_cases_single[r.expected_sub].append((model_name, r))
    
    for expected_sub in sorted(bad_cases_single.keys()):
        cases = bad_cases_single[expected_sub]
        lines.append(f"### {expected_sub}\n")
        
        # Group by trace
        by_trace = defaultdict(dict)
        for model_name, r in cases:
            by_trace[r.trace_snippet][model_name] = r
        
        for trace, model_results in by_trace.items():
            lines.append(f"**轨迹片段:**")
            lines.append(f"```")
            lines.append(trace)
            lines.append(f"```")
            lines.append("")
            lines.append("| 模型 | 预测 | 置信度 | 解释 |")
            lines.append("|------|------|--------|------|")
            
            for model_name in single_results.keys():
                if model_name in model_results:
                    r = model_results[model_name]
                    exp_short = r.explanation[:60] + "..." if len(r.explanation) > 60 else r.explanation
                    lines.append(f"| {model_name} | **错误** -> {r.predicted_sub} | {r.confidence:.2f} | {exp_short} |")
                else:
                    # Model got it right
                    lines.append(f"| {model_name} | 正确 | - | - |")
            
            lines.append("")
        
        lines.append("---\n")
    
    # Bad case analysis - Hierarchical
    lines.append("## 5. Bad Case 分析 - 分层 (Bad Case Analysis - Hierarchical)\n")
    
    bad_cases_hier = defaultdict(list)
    for model_name, (results, stats) in hierarchical_results.items():
        for r in results:
            if not r.is_correct:
                bad_cases_hier[r.expected_sub].append((model_name, r))
    
    for expected_sub in sorted(bad_cases_hier.keys()):
        cases = bad_cases_hier[expected_sub]
        lines.append(f"### {expected_sub}\n")
        
        by_trace = defaultdict(dict)
        for model_name, r in cases:
            by_trace[r.trace_snippet][model_name] = r
        
        for trace, model_results in by_trace.items():
            lines.append(f"**轨迹片段:**")
            lines.append(f"```")
            lines.append(trace)
            lines.append(f"```")
            lines.append("")
            lines.append("| 模型 | 预测 | 置信度 | 解释 |")
            lines.append("|------|------|--------|------|")
            
            for model_name in hierarchical_results.keys():
                if model_name in model_results:
                    r = model_results[model_name]
                    exp_short = r.explanation[:60] + "..." if len(r.explanation) > 60 else r.explanation
                    status = "不确定" if r.predicted_sub == "UNKNOWN" else f"**错误** -> {r.predicted_sub}"
                    lines.append(f"| {model_name} | {status} | {r.confidence:.2f} | {exp_short} |")
                else:
                    lines.append(f"| {model_name} | 正确 | - | - |")
            
            lines.append("")
        
        lines.append("---\n")
    
    # Error Commonality Analysis
    lines.append("## 6. 错误共性分析 (Error Commonality Analysis)\n")
    lines.append("分析不同模型的错误是否存在共性，以评估多模型投票的有效性。\n")
    
    # Analyze single-stage errors
    lines.append("### 单阶段分类错误共性\n")
    
    # Build error sets per model
    model_errors_single = {}
    for model_name, (results, _) in single_results.items():
        model_errors_single[model_name] = set()
        for i, r in enumerate(results):
            if not r.is_correct:
                model_errors_single[model_name].add(i)
    
    model_names = list(single_results.keys())
    all_indices = set(range(len(list(single_results.values())[0][0])))
    
    # Find common errors (all models wrong)
    all_wrong = model_errors_single[model_names[0]].copy()
    for model_name in model_names[1:]:
        all_wrong &= model_errors_single[model_name]
    
    # Find samples where at least one model is wrong
    any_wrong = set()
    for model_name in model_names:
        any_wrong |= model_errors_single[model_name]
    
    # Find samples where only some models are wrong (voting can help)
    some_wrong = any_wrong - all_wrong
    
    # Find samples where all models are correct
    all_correct = all_indices - any_wrong
    
    lines.append(f"**统计结果:**\n")
    lines.append(f"- 所有模型都正确的样本: {len(all_correct)}/56 ({len(all_correct)/56:.1%})")
    lines.append(f"- 所有模型都错误的样本 (共性错误): {len(all_wrong)}/56 ({len(all_wrong)/56:.1%})")
    lines.append(f"- 仅部分模型错误的样本 (投票可解决): {len(some_wrong)}/56 ({len(some_wrong)/56:.1%})\n")
    
    # Voting effectiveness
    if len(any_wrong) > 0:
        voting_effectiveness = len(some_wrong) / len(any_wrong)
        lines.append(f"**投票有效性分析:**\n")
        lines.append(f"在所有错误样本中，{voting_effectiveness:.1%} 的错误可以通过多模型投票解决。\n")
    
    # List common errors
    if all_wrong:
        lines.append(f"**共性错误样本 (所有模型都判断错误):**\n")
        lines.append("这些样本可能需要业务层面的规则澄清或数据标注修正。\n")
        lines.append("| 序号 | 期望状态 | 轨迹片段 |")
        lines.append("|------|----------|----------|")
        test_results = list(single_results.values())[0][0]
        for idx in sorted(all_wrong):
            r = test_results[idx]
            trace_short = r.trace_snippet[:80].replace('\n', ' ') + "..."
            lines.append(f"| {idx+1} | {r.expected_sub} | {trace_short} |")
        lines.append("")
        
        # Show each model's prediction for common errors
        lines.append("**共性错误详情:**\n")
        for idx in sorted(all_wrong):
            lines.append(f"#### 样本 {idx+1}\n")
            r = test_results[idx]
            lines.append(f"**期望状态:** {r.expected_sub}\n")
            lines.append(f"**轨迹:**")
            lines.append(f"```")
            lines.append(r.trace_snippet)
            lines.append(f"```\n")
            lines.append("| 模型 | 预测 | 置信度 |")
            lines.append("|------|------|--------|")
            for model_name, (results, _) in single_results.items():
                pred = results[idx].predicted_sub
                conf = results[idx].confidence
                lines.append(f"| {model_name} | {pred} | {conf:.2f} |")
            lines.append("")
    
    # List samples where voting can help
    if some_wrong:
        lines.append(f"**部分模型错误样本 (投票可解决):**\n")
        lines.append("这些样本中至少有一个模型判断正确，多模型投票可以提高准确率。\n")
        lines.append("| 序号 | 期望状态 | GPT-5.2 | Grok-4 | Kimi |")
        lines.append("|------|----------|---------|--------|------|")
        test_results = list(single_results.values())[0][0]
        for idx in sorted(some_wrong):
            r = test_results[idx]
            row = f"| {idx+1} | {r.expected_sub} |"
            for model_name in model_names:
                results = single_results[model_name][0]
                if results[idx].is_correct:
                    row += " ✓ |"
                else:
                    row += f" ✗→{results[idx].predicted_sub} |"
            lines.append(row)
        lines.append("")
    
    # Analyze hierarchical errors
    lines.append("### 分层分类错误共性\n")
    
    model_errors_hier = {}
    for model_name, (results, _) in hierarchical_results.items():
        model_errors_hier[model_name] = set()
        for i, r in enumerate(results):
            if not r.is_correct:
                model_errors_hier[model_name].add(i)
    
    all_wrong_hier = model_errors_hier[model_names[0]].copy()
    for model_name in model_names[1:]:
        all_wrong_hier &= model_errors_hier[model_name]
    
    any_wrong_hier = set()
    for model_name in model_names:
        any_wrong_hier |= model_errors_hier[model_name]
    
    some_wrong_hier = any_wrong_hier - all_wrong_hier
    all_correct_hier = all_indices - any_wrong_hier
    
    lines.append(f"**统计结果:**\n")
    lines.append(f"- 所有模型都正确的样本: {len(all_correct_hier)}/56 ({len(all_correct_hier)/56:.1%})")
    lines.append(f"- 所有模型都错误的样本 (共性错误): {len(all_wrong_hier)}/56 ({len(all_wrong_hier)/56:.1%})")
    lines.append(f"- 仅部分模型错误的样本 (投票可解决): {len(some_wrong_hier)}/56 ({len(some_wrong_hier)/56:.1%})\n")
    
    if len(any_wrong_hier) > 0:
        voting_effectiveness_hier = len(some_wrong_hier) / len(any_wrong_hier)
        lines.append(f"**投票有效性分析:**\n")
        lines.append(f"在所有错误样本中，{voting_effectiveness_hier:.1%} 的错误可以通过多模型投票解决。\n")
    
    # Summary and recommendations
    lines.append("## 7. 结论与建议 (Conclusions and Recommendations)\n")
    
    # Best model
    best_single = max(single_results.items(), key=lambda x: x[1][1]['accuracy'])
    best_hier = max(hierarchical_results.items(), key=lambda x: x[1][1]['accuracy'])
    
    lines.append("### 最佳模型\n")
    lines.append(f"- **单阶段最佳:** {best_single[0]} ({best_single[1][1]['accuracy']:.2%})")
    lines.append(f"- **分层最佳:** {best_hier[0]} ({best_hier[1][1]['accuracy']:.2%})\n")
    
    lines.append("### 投票策略建议\n")
    if len(some_wrong) > len(all_wrong):
        lines.append("基于错误共性分析，**推荐使用多模型投票**策略：")
        lines.append(f"- 单阶段分类中，{len(some_wrong)}/{len(any_wrong)} ({len(some_wrong)/len(any_wrong):.1%}) 的错误可通过投票解决")
        lines.append(f"- 共性错误仅占 {len(all_wrong)}/{len(any_wrong)} ({len(all_wrong)/len(any_wrong):.1%})，说明不同模型的错误模式有差异")
        lines.append("- 建议采用 GPT-5.2 + Grok-4 双模型投票，Kimi作为备选\n")
    else:
        lines.append("基于错误共性分析，多模型投票的效果可能有限：")
        lines.append(f"- 共性错误占比较高 ({len(all_wrong)/len(any_wrong):.1%})，说明模型在相同样本上犯错")
        lines.append("- 建议优先改进prompt或增加few-shot样本\n")
    
    lines.append("### 共性错误处理建议\n")
    if all_wrong:
        lines.append(f"共有 {len(all_wrong)} 个样本所有模型都判断错误，建议：")
        lines.append("1. 检查这些样本的标注是否正确")
        lines.append("2. 分析是否存在分类规则不清晰的情况")
        lines.append("3. 考虑在few-shot中增加类似案例\n")
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\nReport saved to: {output_path}")


def main():
    print("=" * 60)
    print("Comprehensive Model Evaluation")
    print("=" * 60)
    
    # Load data
    taxonomy, test_data = load_data()
    
    # Get all sub-status labels
    all_labels = []
    for main_key, subs in taxonomy.items():
        all_labels.extend(subs.keys())
    all_labels.extend(["UNKNOWN", "ERROR", "OTHER"])
    
    print(f"Loaded {len(test_data)} test samples")
    print(f"Testing {len(MODELS)} models: {[m['name'] for m in MODELS]}")
    print("")
    
    single_results = {}
    hierarchical_results = {}
    
    for model_config in MODELS:
        model_name = model_config["name"]
        print(f"\n{'='*60}")
        print(f"Testing: {model_name}")
        print(f"{'='*60}")
        
        client = create_client(model_config)
        
        # Single-stage evaluation
        print(f"\n--- Single-Stage (28-class) ---")
        single_res, single_stats = evaluate_single_stage(client, test_data, model_name)
        single_results[model_name] = (single_res, single_stats)
        print(f"Single-Stage Accuracy: {single_stats['correct']}/{single_stats['total']} = {single_stats['accuracy']:.2%}")
        
        # Save intermediate results
        with open(os.path.join(OUTPUT_DIR, f"{model_name.lower().replace('-', '_')}_single_results.json"), 'w', encoding='utf-8') as f:
            json.dump({
                'model': model_name,
                'pipeline': 'single-stage',
                'stats': single_stats,
                'results': [{'expected': r.expected_sub, 'predicted': r.predicted_sub, 'correct': r.is_correct, 'confidence': r.confidence} for r in single_res]
            }, f, ensure_ascii=False, indent=2)
        
        # Hierarchical evaluation
        print(f"\n--- Hierarchical (Two-Stage) ---")
        hier_res, hier_stats = evaluate_hierarchical(client, test_data, model_name, taxonomy)
        hierarchical_results[model_name] = (hier_res, hier_stats)
        print(f"Hierarchical Accuracy: {hier_stats['correct']}/{hier_stats['total']} = {hier_stats['accuracy']:.2%}")
        
        # Save intermediate results
        with open(os.path.join(OUTPUT_DIR, f"{model_name.lower().replace('-', '_')}_hierarchical_results.json"), 'w', encoding='utf-8') as f:
            json.dump({
                'model': model_name,
                'pipeline': 'hierarchical',
                'stats': hier_stats,
                'results': [{'expected': r.expected_sub, 'predicted': r.predicted_sub, 'correct': r.is_correct, 'confidence': r.confidence} for r in hier_res]
            }, f, ensure_ascii=False, indent=2)
    
    # Generate comprehensive report
    print(f"\n{'='*60}")
    print("Generating comparison report...")
    print(f"{'='*60}")
    
    generate_report(
        single_results,
        hierarchical_results,
        all_labels,
        os.path.join(OUTPUT_DIR, "full_comparison_report.md")
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nSingle-Stage (28-class):")
    for model_name, (_, stats) in single_results.items():
        print(f"  {model_name}: {stats['accuracy']:.2%}")
    
    print("\nHierarchical (Two-Stage):")
    for model_name, (_, stats) in hierarchical_results.items():
        print(f"  {model_name}: {stats['accuracy']:.2%}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
