# 模型评估对比报告 (Model Evaluation Comparison Report)

测试样本数: 56

测试模型: GPT-5.2, Grok-4, Kimi


## 1. 总体准确率对比 (Overall Accuracy Comparison)

### 单阶段 (Single-Stage 28-Class)

| 模型 | 子状态准确率 | 主状态准确率 |
|------|-------------|-------------|
| GPT-5.2 | 42/56 = 75.00% | 49/56 = 87.50% |
| Grok-4 | 43/56 = 76.79% | 46/56 = 82.14% |
| Kimi | 30/56 = 53.57% | 40/56 = 71.43% |

### 分层分类 (Hierarchical Two-Stage)

| 模型 | 子状态准确率 | 不确定率 |
|------|-------------|---------|
| GPT-5.2 | 42/56 = 75.00% | 0/56 = 0.00% |
| Grok-4 | 41/56 = 73.21% | 0/56 = 0.00% |
| Kimi | 24/56 = 42.86% | 16/56 = 28.57% |

### 单阶段 vs 分层对比

| 模型 | 单阶段准确率 | 分层准确率 | 变化 |
|------|------------|----------|------|
| GPT-5.2 | 75.00% | 75.00% | 0.00% |
| Grok-4 | 76.79% | 73.21% | -3.57% |
| Kimi | 53.57% | 42.86% | -10.71% |

## 2. 错误共性分析 (Error Commonality Analysis)

分析不同模型的错误是否存在共性，以评估多模型投票的有效性。

### 单阶段分类错误共性

**统计结果:**

- 所有模型都正确的样本: 26/56 (46.4%)
- 所有模型都错误的样本 (共性错误): 7/56 (12.5%)
- 仅部分模型错误的样本 (投票可解决): 23/56 (41.1%)

**投票有效性分析:**

在所有错误样本中，76.7% 的错误可以通过多模型投票解决。

**共性错误样本 (所有模型都判断错误):**

这些样本可能需要业务层面的规则澄清或数据标注修正。

| 序号 | 期望状态 | GPT-5.2预测 | Grok-4预测 | Kimi预测 |
|------|----------|-------------|------------|----------|
| 17 | WAITING_DELIVERY_01 | IN_TRANSIT_07 | IN_TRANSIT_07 | IN_TRANSIT_07 |
| 23 | DELIVERED_01 | DELIVERED_04 | DELIVERED_04 | DELIVERED_04 |
| 34 | DELIVERY_FAILED_02 | DELIVERY_FAILED_04 | WAITING_DELIVERY_03 | WAITING_DELIVERY_03 |
| 49 | ABNORMAL_06 | DELIVERED_01 | DELIVERED_01 | DELIVERED_01 |
| 52 | ABNORMAL_07 | DELIVERY_FAILED_01 | DELIVERY_FAILED_01 | DELIVERY_FAILED_01 |
| 53 | ABNORMAL_08 | WAITING_DELIVERY_03 | DELIVERY_FAILED_04 |  |
| 54 | ABNORMAL_08 | DELIVERY_FAILED_04 | DELIVERY_FAILED_04 |  |

**共性错误详情:**

#### 样本 17

**期望状态:** WAITING_DELIVERY_01

**轨迹:**
```
单号：6A04751048755
物流商：LaPoste
国家：France->France
2025-12-15 07:55:10 Votre colis est sur son site de distribution. Nous le préparons pour le mettre en livraison. 
2025-12-13 12:35:35 Votre colis est sur son site de distribution. Nous le préparons pour le mettre en livraison. 
2025-12-12 10:51:32 Votre...
```

| 模型 | 预测 | 置信度 |
|------|------|--------|
| GPT-5.2 | IN_TRANSIT_07 | 0.74 |
| Grok-4 | IN_TRANSIT_07 | 0.95 |
| Kimi | IN_TRANSIT_07 | 0.95 |

#### 样本 23

**期望状态:** DELIVERED_01

**轨迹:**
```
单号：886917239600
物流商：FedEx
国家：USA->USA
2025-12-11 14:21:58 Delivered, Left at front door. Signature Service not requested. Philadelphia, PA, US
2025-12-11 04:49:00 On FedEx vehicle for delivery PHILADELPHIA, PA, US
2025-12-11 04:37:00 At local FedEx facility PHILADELPHIA, PA, US
2025-12-11 02:20:08 D...
```

| 模型 | 预测 | 置信度 |
|------|------|--------|
| GPT-5.2 | DELIVERED_04 | 0.96 |
| Grok-4 | DELIVERED_04 | 1.00 |
| Kimi | DELIVERED_04 | 1.00 |

#### 样本 34

**期望状态:** DELIVERY_FAILED_02

**轨迹:**
```
单号：15504652683779
物流商：DPD(UK)
国家：UK->未知
2025-12-16 07:40:00 We missed you. Your driver Stephen won't be back today but you can still rearrange your delivery. DPD
2025-12-16 07:13:00 Your parcel will be with you today DPD
2025-12-15 23:19:00 Your parcel is at our depot ready for delivery DPD
2025-12-...
```

| 模型 | 预测 | 置信度 |
|------|------|--------|
| GPT-5.2 | DELIVERY_FAILED_04 | 0.84 |
| Grok-4 | WAITING_DELIVERY_03 | 0.95 |
| Kimi | WAITING_DELIVERY_03 | 0.90 |

#### 样本 49

**期望状态:** ABNORMAL_06

**轨迹:**
```
单号：7032402160
物流商：DHL
国家：China->USA
2025-11-24 17:06:00 Delivered TAMPA - Florida - USA
2025-11-22 11:37:00 Returned to shipper TUEN MUN - HONG KONG SAR, CHINA
2025-11-21 19:29:00 Shipment is on hold TUEN MUN - HONG KONG SAR, CHINA
2025-11-21 07:23:00 Payment is received and recorded for shipment re...
```

| 模型 | 预测 | 置信度 |
|------|------|--------|
| GPT-5.2 | DELIVERED_01 | 0.92 |
| Grok-4 | DELIVERED_01 | 0.90 |
| Kimi | DELIVERED_01 | 1.00 |

#### 样本 52

**期望状态:** ABNORMAL_07

**轨迹:**
```
单号：UK676566335YP
物流商：Yanwen
国家：未知->USA
2025-12-10 12:51:44 Parcel returned to warehouse New Windsor NY
2025-12-10 12:51:36 Failed delivery attempt, returning to the warehouse New Windsor NY
2025-12-10 12:51:28 Invalid address in arrival scan Albany NY
2025-12-10 12:51:21 Arrival scan Albany NY
2025-...
```

| 模型 | 预测 | 置信度 |
|------|------|--------|
| GPT-5.2 | DELIVERY_FAILED_01 | 0.92 |
| Grok-4 | DELIVERY_FAILED_01 | 0.95 |
| Kimi | DELIVERY_FAILED_01 | 1.00 |

#### 样本 53

**期望状态:** ABNORMAL_08

**轨迹:**
```
单号：427322603885
物流商：FedEx
国家：China->Réunion
2025-12-16 09:40:00 Delivery exception, Held, unable to collect payment ST MARIE, , RE
2025-12-15 10:16:00 Delivery exception, Held, unable to collect payment ST MARIE, , RE
2025-12-12 17:43:00 Delivery exception, Held, unable to collect payment ST MARIE, ...
```

| 模型 | 预测 | 置信度 |
|------|------|--------|
| GPT-5.2 | WAITING_DELIVERY_03 | 0.74 |
| Grok-4 | DELIVERY_FAILED_04 | 1.00 |
| Kimi |  | 0.00 |

#### 样本 54

**期望状态:** ABNORMAL_08

**轨迹:**
```
单号：SYRM160436531
物流商：SUNYOU
国家：China->Switzerland
2025-12-15 07:31:00 Delivery Exception Bülach Zustellung, CH
2025-12-13 08:07:00 Delivery In Progress Zürich Briefzentrum, CH
2025-12-12 09:52:00 Arrived At The Processing Certer Of Last Mile Provider CH
2025-12-11 10:54:00 Hand Over To Last Mile CH
...
```

| 模型 | 预测 | 置信度 |
|------|------|--------|
| GPT-5.2 | DELIVERY_FAILED_04 | 0.70 |
| Grok-4 | DELIVERY_FAILED_04 | 0.95 |
| Kimi |  | 0.00 |

**部分模型错误样本 (投票可解决):**

这些样本中至少有一个模型判断正确，多模型投票可以提高准确率。

| 序号 | 期望状态 | GPT-5.2 | Grok-4 | Kimi |
|------|----------|---------|--------|------|
| 1 | IN_TRANSIT_01 | OK | X->INFO_RECEIVED_01 | X->INFO_RECEIVED_01 |
| 2 | IN_TRANSIT_01 | X->IN_TRANSIT_02 | OK | X->IN_TRANSIT_02 |
| 4 | IN_TRANSIT_02 | OK | OK | X->IN_TRANSIT_06 |
| 5 | IN_TRANSIT_03 | OK | X->IN_TRANSIT_06 | X->IN_TRANSIT_06 |
| 7 | IN_TRANSIT_04 | X->IN_TRANSIT_03 | OK | X->IN_TRANSIT_02 |
| 13 | IN_TRANSIT_07 | X->IN_TRANSIT_02 | OK | OK |
| 14 | IN_TRANSIT_07 | OK | OK | X->IN_TRANSIT_02 |
| 15 | IN_TRANSIT_08 | OK | OK | X->IN_TRANSIT_05 |
| 16 | IN_TRANSIT_08 | OK | OK | X->IN_TRANSIT_05 |
| 18 | WAITING_DELIVERY_01 | OK | OK | X->IN_TRANSIT_07 |
| 21 | WAITING_DELIVERY_03 | OK | X->DELIVERY_FAILED_04 | OK |
| 22 | WAITING_DELIVERY_03 | X->DELIVERY_FAILED_04 | OK | X->DELIVERY_FAILED_04 |
| 26 | DELIVERED_02 | OK | OK | X->IN_TRANSIT_07 |
| 30 | DELIVERED_04 | OK | OK | X-> |
| 31 | DELIVERY_FAILED_01 | X->DELIVERY_FAILED_04 | OK | X-> |
| 32 | DELIVERY_FAILED_01 | OK | OK | X-> |
| 35 | DELIVERY_FAILED_03 | X->DELIVERY_FAILED_01 | X->ABNORMAL_03 | OK |
| 37 | DELIVERY_FAILED_04 | OK | X->WAITING_DELIVERY_03 | X->WAITING_DELIVERY_03 |
| 38 | DELIVERY_FAILED_04 | OK | OK | X->DELIVERY_FAILED_02 |
| 43 | ABNORMAL_03 | X->DELIVERED_01 | OK | X->DELIVERED_03 |
| 50 | ABNORMAL_06 | OK | OK | X->ABNORMAL_04 |
| 51 | ABNORMAL_07 | OK | X->ABNORMAL_06 | OK |
| 55 | INFO_RECEIVED_01 | OK | OK | X-> |

### 分层分类错误共性

**统计结果:**

- 所有模型都正确的样本: 20/56 (35.7%)
- 所有模型都错误的样本 (共性错误): 8/56 (14.3%)
- 仅部分模型错误的样本 (投票可解决): 28/56 (50.0%)

**投票有效性分析:**

在所有错误样本中，77.8% 的错误可以通过多模型投票解决。

## 3. 结论与建议 (Conclusions and Recommendations)

### 最佳模型

- **单阶段最佳:** Grok-4 (76.79%)
- **分层最佳:** GPT-5.2 (75.00%)

### 投票策略建议

基于错误共性分析，**推荐使用多模型投票**策略：
- 单阶段分类中，23/30 (76.7%) 的错误可通过投票解决
- 共性错误仅占 7/30 (23.3%)，说明不同模型的错误模式有差异
- 建议采用 GPT-5.2 + Grok-4 双模型投票，Kimi作为备选

### 共性错误处理建议

共有 7 个样本所有模型都判断错误，建议：
1. 检查这些样本的标注是否正确
2. 分析是否存在分类规则不清晰的情况
3. 考虑在few-shot中增加类似案例
