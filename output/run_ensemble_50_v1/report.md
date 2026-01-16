# Primary Classification Test Report (50 Samples × 4 Models × 3 Prompts)

> **IMPORTANT**: This report has been updated with corrected labels (2026-01-16)
> For the latest accuracy summary, see: `output/ACCURACY_SUMMARY.md`

## Updated Results (After Label Correction)

| 指标 | 结果 |
|------|------|
| 总体准确率 | **90.4%** (491/543有效预测) |
| 简单多数投票 | **94.0%** (47/50) |
| 专家加权投票 | **94.0%** (47/50) |

### 模型准确率

| Model | Accuracy | Correct/Total |
|-------|----------|---------------|
| GPT-5.2 | **94.7%** | 142/150 |
| Gemini-3 | **93.6%** | 88/94 |
| Grok-4 | **89.3%** | 133/149 |
| Claude-Opus-4.5 | **85.3%** | 128/150 |

### Prompt准确率

| Prompt | Accuracy | Correct/Total |
|--------|----------|---------------|
| time_based | **92.0%** | 161/175 |
| evidence_based | **91.3%** | 157/172 |
| rule_based | **88.3%** | 173/196 |

### 按类别准确率

| Category | Accuracy | Correct/Total |
|----------|----------|---------------|
| WAITING_DELIVERY | **100.0%** | 62/62 |
| INFO_RECEIVED | **99.0%** | 98/99 |
| DELIVERY_FAILED | **92.6%** | 88/95 |
| DELIVERED | **92.1%** | 93/101 |
| ABNORMAL | **80.7%** | 67/83 |
| IN_TRANSIT | **80.6%** | 83/103 |

### Top 5 专家组合

| Expert (Model_Prompt) | Accuracy |
|-----------------------|----------|
| gemini-3_time_based | **100.0%** |
| gpt-5.2_time_based | **98.0%** |
| gpt-5.2_evidence_based | **94.0%** |
| grok-4_evidence_based | **93.9%** |
| gpt-5.2_rule_based | **92.0%** |

## Label Corrections Applied

| tracking_no | Old Label | Corrected Label |
|-------------|-----------|-----------------|
| GM5453527420279432 | WAITING_DELIVERY | DELIVERY_FAILED |
| WS14532782726884605DL | WAITING_DELIVERY | DELIVERED |

---
*Original report generated: 2026-01-10 09:11:23*
*Updated with corrected labels: 2026-01-16*
