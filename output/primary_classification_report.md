# Primary Classification Test Report

Generated: 2026-01-09 12:56:36

## Overall Results

| Model | Prompt | Accuracy | Correct/Total | Avg Latency |
|-------|--------|----------|---------------|-------------|
| gemini-3 | rule_based | 89.00% | 89/100 | 5806ms |
| gpt-5.2 | rule_based | 88.00% | 88/100 | 1867ms |
| claude-4.5 | evidence_based | 86.00% | 86/100 | 3842ms |
| grok-4 | evidence_based | 85.00% | 85/100 | 17325ms |
| gpt-5.2 | evidence_based | 84.00% | 84/100 | 2555ms |
| claude-4.5 | rule_based | 82.00% | 82/100 | 3247ms |
| grok-4 | rule_based | 81.00% | 81/100 | 18099ms |
| gemini-3 | evidence_based | 81.00% | 81/100 | 6749ms |
| gpt-5.2 | time_based | 80.00% | 80/100 | 1875ms |
| gemini-3 | time_based | 80.00% | 80/100 | 5479ms |
| grok-4 | time_based | 78.00% | 78/100 | 15852ms |
| claude-4.5 | time_based | 78.00% | 78/100 | 2903ms |

## Best Combinations

**Best Overall**: gemini-3 + rule_based (89.00%)

**Best per Model**:
- gemini-3: rule_based (89.00%)
- gpt-5.2: rule_based (88.00%)
- claude-4.5: evidence_based (86.00%)
- grok-4: evidence_based (85.00%)

## Per-Category Accuracy (Best Model)

| Category | Accuracy | Correct/Total |
|----------|----------|---------------|
| INFO_RECEIVED | 100.00% | 17/17 |
| IN_TRANSIT | 94.12% | 16/17 |
| WAITING_DELIVERY | 82.35% | 14/17 |
| DELIVERED | 94.12% | 16/17 |
| DELIVERY_FAILED | 100.00% | 16/16 |
| ABNORMAL | 62.50% | 10/16 |

## Confusion Matrix (Best Model)

Rows = True Label, Columns = Predicted Label

| True \ Pred | INFO_RECEIVED | IN_TRANSIT | WAITING_DELIVERY | DELIVERED | DELIVERY_FAILED | ABNORMAL |
|---|---|---|---|---|---|---|
| INFO_RECEIVED | 17 | 0 | 0 | 0 | 0 | 0 |
| IN_TRANSIT | 0 | 16 | 1 | 0 | 0 | 0 |
| WAITING_DELIVERY | 0 | 0 | 14 | 1 | 2 | 0 |
| DELIVERED | 0 | 0 | 0 | 16 | 0 | 1 |
| DELIVERY_FAILED | 0 | 0 | 0 | 0 | 16 | 0 |
| ABNORMAL | 1 | 0 | 0 | 5 | 0 | 10 |