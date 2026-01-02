# 三模型性能对比报告

## 1. 总体准确率对比

| 模型 | 子状态准确率 | 主状态准确率 |
|------|-------------|-------------|
| Claude-4.5 | 25/28 = **89.29%** | 25/28 = 89.29% |
| GPT-5 | 22/28 = 78.57% | 24/28 = 85.71% |
| Kimi (moonshot-v1-128k) | 19/28 = 67.86% | 25/28 = 89.29% |

## 2. 各模型错误案例

| 模型 | 错误数 | 错误案例 |
|------|--------|----------|
| Kimi | 9个 | IN_TRANSIT_01, IN_TRANSIT_02, IN_TRANSIT_04, IN_TRANSIT_08, WAITING_DELIVERY_01, WAITING_DELIVERY_03, DELIVERED_02, DELIVERY_FAILED_02, DELIVERY_FAILED_04 |
| GPT-5 | 6个 | IN_TRANSIT_01, WAITING_DELIVERY_01, WAITING_DELIVERY_03, DELIVERED_03, ABNORMAL_07, ABNORMAL_08 |
| Claude-4.5 | 3个 | WAITING_DELIVERY_01, WAITING_DELIVERY_03, ABNORMAL_08 |

## 3. 共性Bad Case（2个以上模型都错）

### 3.1 WAITING_DELIVERY_01 (3个模型都错)

| 模型 | 预测结果 |
|------|----------|
| Kimi | IN_TRANSIT_07 |
| GPT-5 | IN_TRANSIT_07 |
| Claude-4.5 | IN_TRANSIT_07 |

**轨迹预览：**
```
单号：00K96P0N
物流商：GLS
2025-12-15 06:34:40 The parcel is expected to be delivered during the day. France Rixheim
2025-12-15 06:08:50 The parcel has reached the parcel center. France Rixheim
```

**标注原因：** 轨迹信息中虽然没有直接包含"Out for delivery"的关键词，但是有提到"The parcel is expected to be delivered during the day."，表面包裹正常会在今天签收，这里已经是签收前的最后一个节点了，大概率包裹已经在派送途中了。

---

### 3.2 WAITING_DELIVERY_03 (3个模型都错)

| 模型 | 预测结果 |
|------|----------|
| Kimi | DELIVERY_FAILED_04 |
| GPT-5 | DELIVERY_FAILED_04 |
| Claude-4.5 | DELIVERY_FAILED_04 |

**轨迹预览：**
```
单号：4PX3002300585543CN
物流商：4PX
国家：China->USA
2025-12-12 08:35:00 Notice Left (No Secure Location Available) -> We attempted to deliver your item at 8:35 am on December 12, 2025 in GREENCASTLE, PA 17225
```

**标注原因：** 出现了notice left的信息，这个是首次尝试派送，发现没有安全放置的地方，而决定后续再派送

---

### 3.3 ABNORMAL_08 (2个模型错)

| 模型 | 预测结果 |
|------|----------|
| Kimi | ✓ 正确 |
| GPT-5 | DELIVERY_FAILED_04 |
| Claude-4.5 | DELIVERY_FAILED_04 |

**轨迹预览：**
```
单号：SYRM160436531
物流商：SUNYOU
国家：China->Switzerland
2025-12-15 07:31:00 Delivery Exception Bülach Zustellung, CH
2025-12-13 08:07:00 Delivery In Progress Zürich Briefzentrum, CH
```

**标注原因：** Delivery Exception 表明是包裹异常，需要提醒客户，但未标明原因，所以标记为其他异常

---

### 3.4 IN_TRANSIT_01 (2个模型错)

| 模型 | 预测结果 |
|------|----------|
| Kimi | IN_TRANSIT_02 |
| GPT-5 | IN_TRANSIT_02 |
| Claude-4.5 | ✓ 正确 |

**轨迹预览：**
```
单号：ZC53472203799
物流商：China Post
2025-12-16 22:26:25 邮件离开【东莞市国际公司直属国际营业部】，正在发往【广商中心】 广东省,东莞市
2025-12-16 22:15:30 邮件已在【东莞市国际公司直属国际营业部】完成分拣，准备发出 广东省,东莞市
```

**标注原因：** 整体是一个运输中的状态，不太好归类到其他运输节点中，就放到当前的运输中了

---

## 4. 结论

1. **Claude-4.5表现最好**，准确率89.29%，仅3个错误
2. **GPT-5次之**，准确率78.57%，6个错误
3. **Kimi准确率最低**，67.86%，9个错误

### 共性错误分析

共性错误案例数：**4个**

| 案例 | 错误模型数 | 问题分析 |
|------|-----------|----------|
| WAITING_DELIVERY_01 | 3 | 模型无法识别隐含的"即将派送"语义 |
| WAITING_DELIVERY_03 | 3 | 模型将"首次尝试派送"误判为"派送失败" |
| ABNORMAL_08 | 2 | 模型将"Delivery Exception"误判为派送失败 |
| IN_TRANSIT_01 | 2 | 模型对"运输中"的细分状态判断不准 |

### 改进建议

1. 在分类规则中增加更明确的区分说明，特别是：
   - WAITING_DELIVERY vs IN_TRANSIT 的边界
   - WAITING_DELIVERY_03 vs DELIVERY_FAILED_04 的区别
   - ABNORMAL vs DELIVERY_FAILED 的区别

2. 增加更多相关的few-shot案例，覆盖边界情况

3. 考虑是否需要调整分类边界定义
