# Primary Classification Test Report

Generated: 2026-01-10 09:11:23

## Overall Results

| Model | Prompt | Accuracy | Correct/Total | Avg Latency |
|-------|--------|----------|---------------|-------------|
| gpt-5.2 | time_based | 52.00% | 26/50 | 2072ms |
| gpt-5.2 | evidence_based | 50.00% | 25/50 | 3066ms |
| gpt-5.2 | rule_based | 48.00% | 24/50 | 2276ms |
| grok-4 | time_based | 48.00% | 24/50 | 9870ms |
| grok-4 | evidence_based | 48.00% | 24/50 | 15386ms |
| claude-opus-4.5 | time_based | 46.00% | 23/50 | 2615ms |
| claude-opus-4.5 | evidence_based | 46.00% | 23/50 | 2784ms |
| gemini-3 | rule_based | 46.00% | 23/50 | 4400ms |
| grok-4 | rule_based | 46.00% | 23/50 | 13020ms |
| claude-opus-4.5 | rule_based | 44.00% | 22/50 | 2732ms |
| gemini-3 | time_based | 44.00% | 22/50 | 5724ms |
| gemini-3 | evidence_based | 40.00% | 20/50 | 5505ms |

## Best Combinations

**Best Overall**: gpt-5.2 + time_based (52.00%)

**Best per Model**:
- gpt-5.2: time_based (52.00%)
- grok-4: time_based (48.00%)
- claude-opus-4.5: time_based (46.00%)
- gemini-3: rule_based (46.00%)

## Per-Category Accuracy (Best Model)

| Category | Accuracy | Correct/Total |
|----------|----------|---------------|
| INFO_RECEIVED | 55.56% | 5/9 |
| IN_TRANSIT | 77.78% | 7/9 |
| WAITING_DELIVERY | 37.50% | 3/8 |
| DELIVERED | 62.50% | 5/8 |
| DELIVERY_FAILED | 25.00% | 2/8 |
| ABNORMAL | 50.00% | 4/8 |

## Confusion Matrix (Best Model)

Rows = True Label, Columns = Predicted Label

| True \ Pred | INFO_RECEIVED | IN_TRANSIT | WAITING_DELIVERY | DELIVERED | DELIVERY_FAILED | ABNORMAL |
|---|---|---|---|---|---|---|
| INFO_RECEIVED | 5 | 0 | 0 | 0 | 0 | 0 |
| IN_TRANSIT | 0 | 7 | 0 | 0 | 0 | 0 |
| WAITING_DELIVERY | 0 | 0 | 3 | 1 | 1 | 0 |
| DELIVERED | 0 | 0 | 0 | 5 | 0 | 0 |
| DELIVERY_FAILED | 0 | 0 | 0 | 0 | 2 | 0 |
| ABNORMAL | 0 | 0 | 0 | 0 | 0 | 4 |