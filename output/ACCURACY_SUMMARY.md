# 物流状态分类准确率汇总

> 更新日期: 2026-01-16
> 标签修正: 2个hard case已修正 (GM5453527420279432, WS14532782726884605DL)

## 总体准确率

| 指标 | 数值 |
|------|------|
| 总测试数 | 600 (50样本 × 4模型 × 3prompt) |
| 有效预测 | 543 |
| 正确预测 | 491 |
| **总体准确率** | **90.4%** |

## 投票准确率

| 方法 | 正确数 | 总数 | 准确率 |
|------|--------|------|--------|
| 简单多数投票 | 47 | 50 | **94.0%** |
| 专家加权投票 | 47 | 50 | **94.0%** |

## 按模型准确率

| 模型 | 正确数 | 总数 | 准确率 |
|------|--------|------|--------|
| GPT-5.2 | 142 | 150 | **94.7%** |
| Gemini-3 | 88 | 94 | **93.6%** |
| Grok-4 | 133 | 149 | **89.3%** |
| Claude-Opus-4.5 | 128 | 150 | **85.3%** |

## 按Prompt准确率

| Prompt | 正确数 | 总数 | 准确率 |
|--------|--------|------|--------|
| time_based | 161 | 175 | **92.0%** |
| evidence_based | 157 | 172 | **91.3%** |
| rule_based | 173 | 196 | **88.3%** |

## 按类别准确率

| 类别 | 正确数 | 总数 | 准确率 |
|------|--------|------|--------|
| WAITING_DELIVERY | 62 | 62 | **100.0%** |
| INFO_RECEIVED | 98 | 99 | **99.0%** |
| DELIVERY_FAILED | 88 | 95 | **92.6%** |
| DELIVERED | 93 | 101 | **92.1%** |
| ABNORMAL | 67 | 83 | **80.7%** |
| IN_TRANSIT | 83 | 103 | **80.6%** |

## Top 5 专家组合

| 专家 (模型_prompt) | 准确率 |
|-------------------|--------|
| gemini-3_time_based | **100.0%** |
| gpt-5.2_time_based | **98.0%** |
| gpt-5.2_evidence_based | **94.0%** |
| grok-4_evidence_based | **93.9%** |
| gpt-5.2_rule_based | **92.0%** |

## 相关文件

- `output/test_samples_50.json` - 50个测试样本（含修正后的true_label）
- `output/run_ensemble_50_v1/predictions_long_merged.jsonl` - 600条预测详情
- `output/ensemble_voting_results.json` - 投票结果详情
- `output/expert_coupling_analysis.json` - 专家耦合度分析
- `output/hard_cases_analysis.md` - Hard case分析

## 标签修正记录

| tracking_no | 原标签 | 修正后标签 |
|-------------|--------|------------|
| GM5453527420279432 | WAITING_DELIVERY | DELIVERY_FAILED |
| WS14532782726884605DL | WAITING_DELIVERY | DELIVERED |
