# Hierarchical Labeler Evaluation Report

## Overall Accuracy Comparison

| Model | Sub-status Acc | Main-status Acc | Uncertain Rate |
|-------|---------------|-----------------|----------------|
| Kimi-Hierarchical | 39.29% (22/56) | 57.14% (32/56) | 0.00% |
| GPT5-Hierarchical | 75.00% (42/56) | 85.71% (48/56) | 3.57% |
| Claude45-Hierarchical | 78.57% (44/56) | 91.07% (51/56) | 0.00% |

## Confusion Matrices

### Kimi-Hierarchical Confusion Matrix

| Expected \ Predicted | AB01 | AB02 | AB03 | AB04 | AB05 | AB06 | AB07 | AB08 | DL01 | DL02 | DL03 | DL04 | DF01 | DF02 | DF03 | DF04 | IR01 | IT01 | IT02 | IT03 | IT04 | IT05 | IT06 | IT07 | IT08 | UNKNOWN | WD01 | WD02 | WD03 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AB01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . |
| AB02 | . | **1** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 1 | . | . | . |
| AB03 | . | . | **1** | . | . | . | . | . | . | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB04 | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB05 | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB06 | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB07 | . | . | . | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 1 | . | . | . |
| AB08 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . |
| DL01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . |
| DL02 | . | . | . | . | . | . | . | . | . | **1** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 1 | . | . |
| DL03 | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DL04 | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DF01 | . | . | . | . | . | . | . | . | . | . | . | . | **1** | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DF02 | . | . | . | . | . | . | . | . | . | . | . | . | . | **1** | 1 | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DF03 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . |
| DF04 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . |
| IR01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . |
| IT01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **1** | 1 | . | . | . | . | . | . | . | . | . | . |
| IT02 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . |
| IT03 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **1** | . | 1 | . | . | . | . | . | . | . |
| IT04 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 1 | 1 | . | . | . | . | . | . | . | . | . |
| IT05 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . |
| IT06 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **1** | . | 1 | . | . | . | . |
| IT07 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 1 | . | . | . | . | . | . | . | 1 | . | . |
| IT08 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 1 | . | . | **1** | . | . | . | . |
| UNKNOWN | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| WD01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 1 | **1** | . | . |
| WD02 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . |
| WD03 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . |

*Legend: IT=IN_TRANSIT, WD=WAITING_DELIVERY, DL=DELIVERED, DF=DELIVERY_FAILED, AB=ABNORMAL, IR=INFO_RECEIVED*

### GPT5-Hierarchical Confusion Matrix

| Expected \ Predicted | AB01 | AB02 | AB03 | AB04 | AB05 | AB06 | AB07 | AB08 | DL01 | DL02 | DL03 | DL04 | DF01 | DF02 | DF03 | DF04 | IR01 | IT01 | IT02 | IT03 | IT04 | IT05 | IT06 | IT07 | IT08 | WD01 | WD02 | WD03 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AB01 | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB02 | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB03 | . | . | **1** | . | . | . | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB04 | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB05 | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB06 | . | . | . | . | . | . | . | . | 2 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB07 | . | . | . | . | . | 1 | . | . | . | . | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB08 | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DL01 | . | . | . | . | . | . | . | . | **1** | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DL02 | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DL03 | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DL04 | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DF01 | . | . | . | . | . | . | . | . | . | . | . | . | **1** | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . |
| DF02 | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DF03 | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | **1** | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DF04 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . |
| IR01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . |
| IT01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **1** | 1 | . | . | . | . | . | . | . | . | . |
| IT02 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . |
| IT03 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . |
| IT04 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . |
| IT05 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . |
| IT06 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . |
| IT07 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . |
| IT08 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . |
| WD01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 1 | . | **1** | . | . |
| WD02 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . |
| WD03 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . | . | . | . | . | . | . | . | . | . |

*Legend: IT=IN_TRANSIT, WD=WAITING_DELIVERY, DL=DELIVERED, DF=DELIVERY_FAILED, AB=ABNORMAL, IR=INFO_RECEIVED*

### Claude45-Hierarchical Confusion Matrix

| Expected \ Predicted | AB01 | AB02 | AB03 | AB04 | AB05 | AB06 | AB07 | AB08 | DL01 | DL02 | DL03 | DL04 | DF01 | DF02 | DF03 | DF04 | IR01 | IT01 | IT02 | IT03 | IT04 | IT05 | IT06 | IT07 | IT08 | WD01 | WD02 | WD03 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AB01 | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB02 | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB03 | . | . | **1** | . | . | . | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB04 | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB05 | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB06 | . | . | . | . | . | **1** | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB07 | . | . | . | . | . | 1 | **1** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| AB08 | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DL01 | . | . | . | . | . | . | . | . | **1** | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DL02 | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DL03 | . | . | . | . | . | . | . | . | 1 | . | **1** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DL04 | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DF01 | . | . | . | . | . | . | . | . | . | . | . | . | **1** | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | . |
| DF02 | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DF03 | . | . | 1 | . | . | . | . | . | . | . | . | . | . | . | **1** | . | . | . | . | . | . | . | . | . | . | . | . | . |
| DF04 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . | . |
| IR01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . | . |
| IT01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . | . |
| IT02 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . | . |
| IT03 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . | . | . |
| IT04 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . | . | . | . | . | . |
| IT05 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . | . |
| IT06 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . | . |
| IT07 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . | . | . |
| IT08 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 1 | . | . | **1** | . | . | . |
| WD01 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . | . |
| WD02 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | **2** | . |
| WD03 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . | . | . | . | . | . | . | . | . | . |

*Legend: IT=IN_TRANSIT, WD=WAITING_DELIVERY, DL=DELIVERED, DF=DELIVERY_FAILED, AB=ABNORMAL, IR=INFO_RECEIVED*

## Bad Case Analysis

Total unique bad cases: 23

### Bad Case 1

**Expected:** IN_TRANSIT_01 (IN_TRANSIT)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | IN_TRANSIT | 1.00 | IN_TRANSIT_02 | 0.90 | IN_TRANSIT_02 | No |
| GPT5-Hierarchical | IN_TRANSIT | 0.92 | IN_TRANSIT_02 | 0.90 | IN_TRANSIT_02 | No |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 2

**Expected:** IN_TRANSIT_03 (IN_TRANSIT)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | IN_TRANSIT | 1.00 | IN_TRANSIT_05 | 0.90 | IN_TRANSIT_05 | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 3

**Expected:** IN_TRANSIT_04 (IN_TRANSIT)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | IN_TRANSIT | 1.00 | IN_TRANSIT_03 | 0.80 | IN_TRANSIT_03 | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | IN_TRANSIT | 0.95 | IN_TRANSIT_03 | 0.90 | IN_TRANSIT_03 | No |

### Bad Case 4

**Expected:** IN_TRANSIT_06 (IN_TRANSIT)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | IN_TRANSIT | 1.00 | IN_TRANSIT_08 | 0.90 | IN_TRANSIT_08 | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 5

**Expected:** IN_TRANSIT_07 (IN_TRANSIT)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | IN_TRANSIT | 1.00 | IN_TRANSIT_02 | 0.90 | IN_TRANSIT_02 | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 6

**Expected:** IN_TRANSIT_08 (IN_TRANSIT)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | IN_TRANSIT | 1.00 | IN_TRANSIT_05 | 0.90 | IN_TRANSIT_05 | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | IN_TRANSIT | 0.95 | IN_TRANSIT_05 | 0.95 | IN_TRANSIT_05 | No |

### Bad Case 7

**Expected:** WAITING_DELIVERY_01 (OUT_FOR_DELIVERY)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | IN_TRANSIT | 0.82 | IN_TRANSIT_07 | 0.95 | IN_TRANSIT_07 | No |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 8

**Expected:** WAITING_DELIVERY_02 (OUT_FOR_DELIVERY)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 9

**Expected:** WAITING_DELIVERY_03 (OUT_FOR_DELIVERY)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | DELIVERY_FAILED | 0.96 | DELIVERY_FAILED_04 | 0.82 | DELIVERY_FAILED_04 | No |
| Claude45-Hierarchical | DELIVERY_FAILED | 0.95 | DELIVERY_FAILED_04 | 0.85 | DELIVERY_FAILED_04 | No |

### Bad Case 10

**Expected:** DELIVERED_01 (DELIVERED)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | DELIVERED | 1.00 | DELIVERED_04 | 0.98 | DELIVERED_04 | No |
| Claude45-Hierarchical | DELIVERED | 0.98 | DELIVERED_04 | 0.95 | DELIVERED_04 | No |

### Bad Case 11

**Expected:** DELIVERED_02 (DELIVERED)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | OUT_FOR_DELIVERY | 1.00 | WAITING_DELIVERY_01 | 0.90 | WAITING_DELIVERY_01 | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 12

**Expected:** DELIVERY_FAILED_01 (DELIVERY_FAILED)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | DELIVERY_FAILED | 1.00 | DELIVERY_FAILED_04 | 0.90 | DELIVERY_FAILED_04 | No |
| GPT5-Hierarchical | DELIVERY_FAILED | 0.96 | DELIVERY_FAILED_04 | 0.88 | DELIVERY_FAILED_04 | No |
| Claude45-Hierarchical | DELIVERY_FAILED | 0.95 | DELIVERY_FAILED_04 | 0.85 | DELIVERY_FAILED_04 | No |

### Bad Case 13

**Expected:** DELIVERY_FAILED_02 (DELIVERY_FAILED)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | DELIVERY_FAILED | 1.00 | DELIVERY_FAILED_03 | 0.90 | DELIVERY_FAILED_03 | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 14

**Expected:** DELIVERY_FAILED_03 (DELIVERY_FAILED)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | EXCEPTION | 0.90 | ABNORMAL_03 | 0.86 | ABNORMAL_03 | No |
| Claude45-Hierarchical | EXCEPTION | 0.95 | ABNORMAL_03 | 0.85 | ABNORMAL_03 | No |

### Bad Case 15

**Expected:** DELIVERY_FAILED_04 (DELIVERY_FAILED)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 16

**Expected:** ABNORMAL_01 (EXCEPTION)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 17

**Expected:** ABNORMAL_02 (EXCEPTION)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 18

**Expected:** ABNORMAL_03 (EXCEPTION)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | DELIVERED | 1.00 | DELIVERED_04 | 0.90 | DELIVERED_04 | No |
| GPT5-Hierarchical | DELIVERED | 0.97 | DELIVERED_01 | 0.80 | DELIVERED_01 | No |
| Claude45-Hierarchical | DELIVERED | 0.95 | DELIVERED_01 | 0.85 | DELIVERED_01 | No |

### Bad Case 19

**Expected:** ABNORMAL_06 (EXCEPTION)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | DELIVERED | 1.00 | DELIVERED_04 | 0.90 | DELIVERED_04 | No |
| GPT5-Hierarchical | DELIVERED | 0.90 | DELIVERED_01 | 0.80 | DELIVERED_01 | No |
| Claude45-Hierarchical | DELIVERED | 0.95 | DELIVERED_01 | 0.85 | DELIVERED_01 | No |

### Bad Case 20

**Expected:** ABNORMAL_07 (EXCEPTION)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | DELIVERY_FAILED | 0.94 | DELIVERY_FAILED_01 | 0.97 | DELIVERY_FAILED_01 | No |
| Claude45-Hierarchical | EXCEPTION | 0.95 | ABNORMAL_06 | 0.95 | ABNORMAL_06 | No |

### Bad Case 21

**Expected:** ABNORMAL_08 (EXCEPTION)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 22

**Expected:** INFO_RECEIVED_01 (INFO_RECEIVED)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical |  | 0.00 |  | 0.00 | UNKNOWN | No |
| GPT5-Hierarchical | - | - | - | - | (correct) | - |
| Claude45-Hierarchical | - | - | - | - | (correct) | - |

### Bad Case 23

**Expected:** DELIVERED_03 (DELIVERED)

| Model | Stage1 Main | Stage1 Conf | Stage2 Sub | Stage2 Conf | Final | Uncertain |
|-------|-------------|-------------|------------|-------------|-------|-----------|
| Kimi-Hierarchical | - | - | - | - | (correct) | - |
| GPT5-Hierarchical | DELIVERED | 0.99 | DELIVERED_04 | 0.78 | DELIVERED_04 | No |
| Claude45-Hierarchical | DELIVERED | 0.98 | DELIVERED_01 | 0.85 | DELIVERED_01 | No |
