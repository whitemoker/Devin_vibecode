# Primary Classification Test Report

Generated: 2026-01-10 07:58:26

## Overall Results

| Model | Prompt | Accuracy | Correct/Total | Avg Latency |
|-------|--------|----------|---------------|-------------|
| gemini-3 | time_based | 79.00% | 79/100 | 4921ms |

## Best Combinations

**Best Overall**: gemini-3 + time_based (79.00%)

**Best per Model**:
- gemini-3: time_based (79.00%)

## Per-Category Accuracy (Best Model)

| Category | Accuracy | Correct/Total |
|----------|----------|---------------|
| INFO_RECEIVED | 100.00% | 17/17 |
| IN_TRANSIT | 58.82% | 10/17 |
| WAITING_DELIVERY | 76.47% | 13/17 |
| DELIVERED | 94.12% | 16/17 |
| DELIVERY_FAILED | 75.00% | 12/16 |
| ABNORMAL | 68.75% | 11/16 |

## Confusion Matrix (Best Model)

Rows = True Label, Columns = Predicted Label

| True \ Pred | INFO_RECEIVED | IN_TRANSIT | WAITING_DELIVERY | DELIVERED | DELIVERY_FAILED | ABNORMAL |
|---|---|---|---|---|---|---|
| INFO_RECEIVED | 17 | 0 | 0 | 0 | 0 | 0 |
| IN_TRANSIT | 4 | 10 | 3 | 0 | 0 | 0 |
| WAITING_DELIVERY | 0 | 0 | 13 | 1 | 3 | 0 |
| DELIVERED | 0 | 0 | 0 | 16 | 0 | 1 |
| DELIVERY_FAILED | 0 | 0 | 0 | 0 | 12 | 3 |
| ABNORMAL | 0 | 1 | 0 | 4 | 0 | 11 |