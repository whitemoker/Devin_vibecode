#!/usr/bin/env python3
"""Generate report with error commonality analysis."""
import json
import os

PROJECT_ROOT = "/home/ubuntu/repos/logistics-labeling"
TAXONOMY_PATH = os.path.join(PROJECT_ROOT, 'resources', 'taxonomy', 'taxonomy.json')
TEST_PATH = os.path.join(PROJECT_ROOT, 'resources', 'datasets', 'test.json')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')

MODEL_FILES = {
    "GPT-5.2": "gpt_5.2",
    "Grok-4": "grok_4", 
    "Kimi": "kimi"
}
MODELS = ["GPT-5.2", "Grok-4", "Kimi"]

# Load data
with open(TAXONOMY_PATH, 'r', encoding='utf-8') as f:
    taxonomy = json.load(f)
with open(TEST_PATH, 'r', encoding='utf-8') as f:
    test_data = json.load(f)

# Load results
single_results = {}
hierarchical_results = {}

for model_name in MODELS:
    model_key = MODEL_FILES[model_name]
    
    single_path = os.path.join(OUTPUT_DIR, f"{model_key}_single_results.json")
    with open(single_path, 'r', encoding='utf-8') as f:
        single_results[model_name] = json.load(f)
    
    hier_path = os.path.join(OUTPUT_DIR, f"{model_key}_hierarchical_results.json")
    with open(hier_path, 'r', encoding='utf-8') as f:
        hierarchical_results[model_name] = json.load(f)

# Generate report
lines = []
lines.append("# 模型评估对比报告 (Model Evaluation Comparison Report)\n")
lines.append("测试样本数: 56\n")
lines.append("测试模型: GPT-5.2, Grok-4, Kimi\n")
lines.append("")

# Overall accuracy
lines.append("## 1. 总体准确率对比 (Overall Accuracy Comparison)\n")
lines.append("### 单阶段 (Single-Stage 28-Class)\n")
lines.append("| 模型 | 子状态准确率 | 主状态准确率 |")
lines.append("|------|-------------|-------------|")

for model_name in MODELS:
    stats = single_results[model_name]['stats']
    sub_acc = f"{stats['correct']}/{stats['total']} = {stats['accuracy']:.2%}"
    main_acc = f"{stats['main_correct']}/{stats['total']} = {stats['main_accuracy']:.2%}"
    lines.append(f"| {model_name} | {sub_acc} | {main_acc} |")

lines.append("")
lines.append("### 分层分类 (Hierarchical Two-Stage)\n")
lines.append("| 模型 | 子状态准确率 | 不确定率 |")
lines.append("|------|-------------|---------|")

for model_name in MODELS:
    stats = hierarchical_results[model_name]['stats']
    sub_acc = f"{stats['correct']}/{stats['total']} = {stats['accuracy']:.2%}"
    unc_rate = f"{stats.get('uncertain', 0)}/{stats['total']} = {stats.get('uncertain_rate', 0):.2%}"
    lines.append(f"| {model_name} | {sub_acc} | {unc_rate} |")

lines.append("")
lines.append("### 单阶段 vs 分层对比\n")
lines.append("| 模型 | 单阶段准确率 | 分层准确率 | 变化 |")
lines.append("|------|------------|----------|------|")

for model_name in MODELS:
    single_acc = single_results[model_name]['stats']['accuracy']
    hier_acc = hierarchical_results[model_name]['stats']['accuracy']
    diff = hier_acc - single_acc
    diff_str = f"+{diff:.2%}" if diff > 0 else f"{diff:.2%}"
    lines.append(f"| {model_name} | {single_acc:.2%} | {hier_acc:.2%} | {diff_str} |")

lines.append("")

# Error Commonality Analysis
lines.append("## 2. 错误共性分析 (Error Commonality Analysis)\n")
lines.append("分析不同模型的错误是否存在共性，以评估多模型投票的有效性。\n")

# Single-stage errors
lines.append("### 单阶段分类错误共性\n")

model_errors_single = {}
for model_name in MODELS:
    model_errors_single[model_name] = set()
    for i, r in enumerate(single_results[model_name]['results']):
        if not r['correct']:
            model_errors_single[model_name].add(i)

all_indices = set(range(56))
all_wrong = model_errors_single[MODELS[0]].copy()
for model_name in MODELS[1:]:
    all_wrong &= model_errors_single[model_name]

any_wrong = set()
for model_name in MODELS:
    any_wrong |= model_errors_single[model_name]

some_wrong = any_wrong - all_wrong
all_correct = all_indices - any_wrong

lines.append("**统计结果:**\n")
lines.append(f"- 所有模型都正确的样本: {len(all_correct)}/56 ({len(all_correct)/56:.1%})")
lines.append(f"- 所有模型都错误的样本 (共性错误): {len(all_wrong)}/56 ({len(all_wrong)/56:.1%})")
lines.append(f"- 仅部分模型错误的样本 (投票可解决): {len(some_wrong)}/56 ({len(some_wrong)/56:.1%})\n")

voting_effectiveness = 0
if len(any_wrong) > 0:
    voting_effectiveness = len(some_wrong) / len(any_wrong)
    lines.append("**投票有效性分析:**\n")
    lines.append(f"在所有错误样本中，{voting_effectiveness:.1%} 的错误可以通过多模型投票解决。\n")

# Common errors detail
if all_wrong:
    lines.append("**共性错误样本 (所有模型都判断错误):**\n")
    lines.append("这些样本可能需要业务层面的规则澄清或数据标注修正。\n")
    lines.append("| 序号 | 期望状态 | GPT-5.2预测 | Grok-4预测 | Kimi预测 |")
    lines.append("|------|----------|-------------|------------|----------|")
    for idx in sorted(all_wrong):
        expected = single_results[MODELS[0]]['results'][idx]['expected']
        row = f"| {idx+1} | {expected} |"
        for model_name in MODELS:
            pred = single_results[model_name]['results'][idx]['predicted']
            row += f" {pred} |"
        lines.append(row)
    lines.append("")
    
    # Show trace for common errors
    lines.append("**共性错误详情:**\n")
    for idx in sorted(all_wrong):
        expected = single_results[MODELS[0]]['results'][idx]['expected']
        lines.append(f"#### 样本 {idx+1}\n")
        lines.append(f"**期望状态:** {expected}\n")
        lines.append("**轨迹:**")
        trace = test_data[idx]['trace'][:300] + "..." if len(test_data[idx]['trace']) > 300 else test_data[idx]['trace']
        lines.append("```")
        lines.append(trace)
        lines.append("```\n")
        lines.append("| 模型 | 预测 | 置信度 |")
        lines.append("|------|------|--------|")
        for model_name in MODELS:
            r = single_results[model_name]['results'][idx]
            lines.append(f"| {model_name} | {r['predicted']} | {r['confidence']:.2f} |")
        lines.append("")

# Voting can help
if some_wrong:
    lines.append("**部分模型错误样本 (投票可解决):**\n")
    lines.append("这些样本中至少有一个模型判断正确，多模型投票可以提高准确率。\n")
    lines.append("| 序号 | 期望状态 | GPT-5.2 | Grok-4 | Kimi |")
    lines.append("|------|----------|---------|--------|------|")
    for idx in sorted(some_wrong):
        expected = single_results[MODELS[0]]['results'][idx]['expected']
        row = f"| {idx+1} | {expected} |"
        for model_name in MODELS:
            r = single_results[model_name]['results'][idx]
            if r['correct']:
                row += " OK |"
            else:
                row += f" X->{r['predicted']} |"
        lines.append(row)
    lines.append("")

# Hierarchical errors
lines.append("### 分层分类错误共性\n")

model_errors_hier = {}
for model_name in MODELS:
    model_errors_hier[model_name] = set()
    for i, r in enumerate(hierarchical_results[model_name]['results']):
        if not r['correct']:
            model_errors_hier[model_name].add(i)

all_wrong_hier = model_errors_hier[MODELS[0]].copy()
for model_name in MODELS[1:]:
    all_wrong_hier &= model_errors_hier[model_name]

any_wrong_hier = set()
for model_name in MODELS:
    any_wrong_hier |= model_errors_hier[model_name]

some_wrong_hier = any_wrong_hier - all_wrong_hier
all_correct_hier = all_indices - any_wrong_hier

lines.append("**统计结果:**\n")
lines.append(f"- 所有模型都正确的样本: {len(all_correct_hier)}/56 ({len(all_correct_hier)/56:.1%})")
lines.append(f"- 所有模型都错误的样本 (共性错误): {len(all_wrong_hier)}/56 ({len(all_wrong_hier)/56:.1%})")
lines.append(f"- 仅部分模型错误的样本 (投票可解决): {len(some_wrong_hier)}/56 ({len(some_wrong_hier)/56:.1%})\n")

if len(any_wrong_hier) > 0:
    voting_effectiveness_hier = len(some_wrong_hier) / len(any_wrong_hier)
    lines.append("**投票有效性分析:**\n")
    lines.append(f"在所有错误样本中，{voting_effectiveness_hier:.1%} 的错误可以通过多模型投票解决。\n")

# Conclusions
lines.append("## 3. 结论与建议 (Conclusions and Recommendations)\n")

best_single = max(MODELS, key=lambda m: single_results[m]['stats']['accuracy'])
best_hier = max(MODELS, key=lambda m: hierarchical_results[m]['stats']['accuracy'])

lines.append("### 最佳模型\n")
lines.append(f"- **单阶段最佳:** {best_single} ({single_results[best_single]['stats']['accuracy']:.2%})")
lines.append(f"- **分层最佳:** {best_hier} ({hierarchical_results[best_hier]['stats']['accuracy']:.2%})\n")

lines.append("### 投票策略建议\n")
if len(some_wrong) > len(all_wrong):
    lines.append("基于错误共性分析，**推荐使用多模型投票**策略：")
    lines.append(f"- 单阶段分类中，{len(some_wrong)}/{len(any_wrong)} ({len(some_wrong)/len(any_wrong):.1%}) 的错误可通过投票解决")
    lines.append(f"- 共性错误仅占 {len(all_wrong)}/{len(any_wrong)} ({len(all_wrong)/len(any_wrong):.1%})，说明不同模型的错误模式有差异")
    lines.append("- 建议采用 GPT-5.2 + Grok-4 双模型投票，Kimi作为备选\n")
else:
    lines.append("基于错误共性分析，多模型投票的效果可能有限：")
    lines.append("- 共性错误占比较高，说明模型在相同样本上犯错")
    lines.append("- 建议优先改进prompt或增加few-shot样本\n")

lines.append("### 共性错误处理建议\n")
if all_wrong:
    lines.append(f"共有 {len(all_wrong)} 个样本所有模型都判断错误，建议：")
    lines.append("1. 检查这些样本的标注是否正确")
    lines.append("2. 分析是否存在分类规则不清晰的情况")
    lines.append("3. 考虑在few-shot中增加类似案例\n")

# Write report
output_path = os.path.join(OUTPUT_DIR, "full_comparison_report.md")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Report saved to: {output_path}")
print(f"\nSummary:")
print(f"- All correct: {len(all_correct)}/56")
print(f"- All wrong (common errors): {len(all_wrong)}/56")
print(f"- Some wrong (voting can help): {len(some_wrong)}/56")
if voting_effectiveness > 0:
    print(f"- Voting effectiveness: {voting_effectiveness:.1%}")
