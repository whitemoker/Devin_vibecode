# 三模型性能对比报告

## 1. 总体准确率

| 模型 | 子状态准确率 | 主状态准确率 |
|------|-------------|-------------|
| **Claude-4.5** | 41/56 = **73.21%** | 49/56 = 87.50% |
| **GPT-5** | 41/56 = **73.21%** | 47/56 = 83.93% |
| **Kimi** | 30/56 = **53.57%** | 38/56 = 67.86% |

## 2. 错误统计

- **Kimi错误**: 26个
- **GPT-5错误**: 15个
- **Claude-4.5错误**: 15个

## 3. Bad Case详细分析

### ABNORMAL_07

**错误统计**: Kimi 2/2, GPT-5 2/2, Claude-4.5 1/2

**样本 1:**

```
单号：1Z1AC7490337112123
物流商：UPS
国家：USA->USA
2025-12-16 10:33:55 Package was returned to the sender BEND, OR, US
2025-12-16 09:53:17 Out For Delivery Today Bend, OR, US
2025-12-16 05:59:22 Processing at ...
```
**标注原因**: Package was returned to the sender. 并不代表已经退回签收了，只是表明包裹已经进入了退回流程

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | **错误** -> ABNORMAL_06 | 0.95 | Final scan shows "Package was returned to the send... |
| Claude-4.5 | **错误** -> ABNORMAL_06 | 0.95 | 最新轨迹显示'Package was returned to the sender'，包裹已退回给发... |

**样本 2:**

```
单号：UK676566335YP
物流商：Yanwen
国家：未知->USA
2025-12-10 12:51:44 Parcel returned to warehouse New Windsor NY
2025-12-10 12:51:36 Failed delivery attempt, returning to the warehouse New Windsor NY
2025-12-10...
```
**标注原因**: Parcel returned to warehouse. 表明包裹正在退回仓库的途中

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | **错误** -> DELIVERY_FAILED_01 | 0.86 | “Invalid address in arrival scan”表明地址有误；同时有“Failed... |
| Claude-4.5 | 正确 | 0.95 | "Parcel returned to warehouse" 和 "Failed delivery ... |

---

### ABNORMAL_05

**错误统计**: Kimi 2/2, GPT-5 1/2, Claude-4.5 1/2

**样本 1:**

```
单号：ROPC0021894732
物流商：Ekart
国家：India->India
2025-12-15 20:23:35 Marked RTO: ORDER_REJECT BHARUCH
2025-12-15 14:33:49 Unsuccessful Delivery attempt failed(Customer rejected) BHARUCH
2025-12-15 12:35:23...
```
**标注原因**: Unsuccessful Delivery attempt failed(Customer rejected) 和 Marked RTO: ORDER_REJECT 都表明包裹被拒收

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | **错误** -> ABNORMAL_07 | 0.95 | 最新记录显示“Marked RTO: ORDER_REJECT”，表明已标记退回发件人；且此前有“U... |
| Claude-4.5 | **错误** -> ABNORMAL_07 | 0.95 | Marked RTO: ORDER_REJECT 和 Customer rejected 表明客户拒... |

**样本 2:**

```
单号：68509017242
物流商：Bluedart
国家：India->India
2025-12-16 15:43:00 Consignee Refused To Accept Mumbai North Warehouse
2025-12-16 11:12:00 Shipment Out For Delivery Mumbai North Warehouse
2025-12-16 06:35...
```
**标注原因**: Consignee Refused To Accept 表明客户已经拒收

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | 正确 | 0.98 | “Consignee Refused To Accept” 明确表示收件人拒绝签收；此前“Shipm... |
| Claude-4.5 | 正确 | 0.95 | 最新轨迹显示'Consignee Refused To Accept'，收件人拒绝签收包裹... |

---

### ABNORMAL_06

**错误统计**: Kimi 2/2, GPT-5 1/2, Claude-4.5 1/2

**样本 1:**

```
单号：7032402160
物流商：DHL
国家：China->USA
2025-11-24 17:06:00 Delivered TAMPA - Florida - USA
2025-11-22 11:37:00 Returned to shipper TUEN MUN - HONG KONG SAR, CHINA
2025-11-21 19:29:00 Shipment is on hold ...
```
**标注原因**: Returned to shipper 退回寄件人事件触发后，过了两天显示为签收，所以确认是退回签收

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | **错误** -> DELIVERED_01 | 0.68 | 最新状态为“2025-11-24 17:06:00 Delivered TAMPA - Florid... |
| Claude-4.5 | **错误** -> DELIVERED_01 | 0.95 | 最新轨迹显示'Delivered TAMPA - Florida - USA'，包裹已成功送达... |

**样本 2:**

```
单号：9239590318442806722208
物流商：USPS
国家：USA->USA
2025-12-05 14:54:00 Delivered, To Original Sender -> Your item has been delivered to the original sender at 2:54 pm on December 5, 2025 in FRESNO, CA 937...
```
**标注原因**: Delivered, To Original Sender -> Your item has been delivered to the original sender. 表明这个包裹是退件签收，签收人是寄件人

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | 正确 | 0.98 | 显示“Delivered, To Original Sender”，且此前有“Return to S... |
| Claude-4.5 | 正确 | 0.95 | 最新轨迹显示'Delivered, To Original Sender'，包裹因地址不足(Insu... |

---

### DELIVERED_01

**错误统计**: Kimi 2/2, GPT-5 1/2, Claude-4.5 1/2

**样本 1:**

```
单号：886917239600
物流商：FedEx
国家：USA->USA
2025-12-11 14:21:58 Delivered, Left at front door. Signature Service not requested. Philadelphia, PA, US
2025-12-11 04:49:00 On FedEx vehicle for delivery PHILADE...
```
**标注原因**: 包裹明显已经投递到了家门口，标记为Delivered且无需签名

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | **错误** -> DELIVERED_04 | 0.98 | “Delivered, Left at front door.” 显示已投递至门口；“Signatu... |
| Claude-4.5 | **错误** -> DELIVERED_04 | 0.95 | "Delivered, Left at front door" 表明包裹已投递并放置在前门... |

**样本 2:**

```
单号：4PX3002242155798CN
物流商：4PX
国家：China->Germany
2025-12-04 12:03:00 The shipment has been successfully delivered Germany
2025-12-04 07:36:00 The shipment has been loaded onto the delivery vehicle Germ...
```
**标注原因**: 这是一个标准的签收包裹，倒数第二条信息中是包裹已经在进行最后的派送了，然后就是签收

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | 正确 | 0.96 | 最新轨迹显示“The shipment has been successfully delivere... |
| Claude-4.5 | 正确 | 0.95 | The shipment has been successfully delivered Germa... |

---

### IN_TRANSIT_04

**错误统计**: Kimi 2/2, GPT-5 0/2, Claude-4.5 2/2

**样本 1:**

```
单号：LZ348277808CN
物流商：China Post
国家：China->未知
2025-12-17 03:48:53 邮件离开【广州市国际互换局】，正在发往下一站 广东省,广州市
2025-12-16 23:03:06 【广州市国际互换局】已出口直封 广东省,广州市
2025-12-16 23:02:36 出口海关/放行 广东省,广州市
2025-12-16 21:54:25 送交出口...
```
**标注原因**: 【广州市国际互换局】已出口直封 ，表明包裹已经封装好，即将出口了

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> IN_TRANSIT_01 | 1.00 | 邮件离开广州市国际互换局，正在发往下一站，表明包裹正在运输途中。... |
| GPT-5 | 正确 | 0.82 | “出口海关/放行”“已出口直封”，显示已清关并完成出口直封，正待送往机场/交航；最新为“邮件离开…发... |
| Claude-4.5 | **错误** -> IN_TRANSIT_05 | 0.90 | 包裹已完成海关清关（出口海关/放行），离开广州市国际互换局正在发往下一站，表明已交航空公司运往目的国... |

**样本 2:**

```
单号：LZ339063340CN
物流商：China Post
国家：China->未知
2025-12-09 08:22:40 【郑州市国际互换局】已出口直封 河南省,郑州市
2025-12-09 08:22:10 出口海关/放行 河南省,郑州市
2025-12-09 07:53:00 送交出口海关 河南省,郑州市
2025-12-09 07:10:27 邮件到达【郑州市国际互换局】 河南省,郑...
```
**标注原因**: 【郑州市国际互换局】已出口直封，出现了已出口直封的字样

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> IN_TRANSIT_03 | 1.00 | 轨迹中'出口海关/放行 河南省,郑州市'表明包裹已经通过海关放行，'已出口直封 河南省,郑州市'说明... |
| GPT-5 | 正确 | 0.90 | “已出口直封”且此前为“出口海关/放行”，表示清关完成并封装，待送往机场。... |
| Claude-4.5 | **错误** -> IN_TRANSIT_03 | 0.95 | "出口海关/放行"表明包裹已完成海关清关，"已出口直封"表明包裹正准备发往目的国... |

---

### WAITING_DELIVERY_01

**错误统计**: Kimi 1/2, GPT-5 2/2, Claude-4.5 1/2

**样本 1:**

```
单号：6A04751048755
物流商：LaPoste
国家：France->France
2025-12-15 07:55:10 Votre colis est sur son site de distribution. Nous le préparons pour le mettre en livraison. 
2025-12-13 12:35:35 Votre colis est sur...
```
**标注原因**: 最新一条轨迹中包含“ous le préparons pour le mettre en livraison. ”，是法语中准备派送的意思，所以我们识别为WAITING_DELIVERY_01

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> IN_TRANSIT_07 | 0.90 | 轨迹信息中提到'Votre colis est sur son site de distributi... |
| GPT-5 | **错误** -> IN_TRANSIT_07 | 0.90 | “Votre colis est sur son site de distribution.” 表示... |
| Claude-4.5 | **错误** -> IN_TRANSIT_07 | 0.85 | 最新轨迹显示'Votre colis est sur son site de distributio... |

**样本 2:**

```
单号：00K96P0N
物流商：GLS
2025-12-15 06:34:40 The parcel is expected to be delivered during the day. France Rixheim
2025-12-15 06:08:50 The parcel has reached the parcel center. France Rixheim
2025-12-12 17...
```
**标注原因**: 轨迹信息中虽然没有直接包含“Out for delivery”的关键词，但是有提到“The parcel is expected to be delivered during the day.”，表面包裹正常会在今天签收，这里已经是签收前的最后一个节点了，大概率包裹已经在派送途中了。

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 0.90 | 最新的轨迹信息显示'The parcel is expected to be delivered d... |
| GPT-5 | **错误** -> IN_TRANSIT_07 | 0.78 | "The parcel has reached the parcel center. ... Rix... |
| Claude-4.5 | 正确 | 0.90 | "The parcel is expected to be delivered during the... |

---

### WAITING_DELIVERY_03

**错误统计**: Kimi 2/2, GPT-5 1/2, Claude-4.5 1/2

**样本 1:**

```
单号：9434650105501091825239
物流商：USPS
国家：USA->USA
2025-12-15 00:00:00 Reminder to Schedule Redelivery of Your Item 
2025-12-10 08:10:00 Notice Left (Receptacle Full/Item Oversized) HUSON,MT 59846
2025-12...
```
**标注原因**: 这个是一个包裹尺寸过大，提供了notice便签，然后预约再次派送包裹的信息

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | 正确 | 0.90 | 最新状态为“Reminder to Schedule Redelivery of Your Item... |
| Claude-4.5 | 正确 | 0.92 | Notice Left (Receptacle Full/Item Oversized)表明投递失败... |

**样本 2:**

```
单号：4PX3002300585543CN
物流商：4PX
国家：China->USA
2025-12-12 08:35:00 Notice Left (No Secure Location Available) -> We attempted to deliver your item at 8:35 am on December 12, 2025 in GREENCASTLE, PA 17225...
```
**标注原因**: 出现了notice left的信息，这个是首次尝试派送，发现没有安全放置的地方，而决定后续再派送

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | **错误** -> DELIVERY_FAILED_04 | 0.90 | 出现 'Notice Left (No Secure Location Available)' 与 ... |
| Claude-4.5 | **错误** -> DELIVERY_FAILED_04 | 0.85 | Notice Left (No Secure Location Available) 表明派送失败，... |

---

### ABNORMAL_03

**错误统计**: Kimi 1/2, GPT-5 1/2, Claude-4.5 1/2

**样本 1:**

```
单号：886717918318
物流商：FedEx
国家：Italy->Italy
2025-12-09 11:31:00 Delivered, Damaged, delivery completed Modena, MO, IT
2025-12-09 11:31:00 Delivered Modena, MO, IT
2025-12-09 08:50:00 On FedEx vehicle fo...
```
**标注原因**: Delivered, Damaged, delivery completed. 虽然是delivered签收，但明显出现了Damaged字眼，表示已经损坏，所以仍标记为异常

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> DELIVERED_03 | 1.00 | 包裹状态显示为 'Delivered, Damaged, delivery completed Mo... |
| GPT-5 | **错误** -> DELIVERED_01 | 0.95 | 2025-12-09 11:31 “Delivered, Damaged, delivery com... |
| Claude-4.5 | **错误** -> DELIVERED_01 | 0.90 | 最新轨迹显示'Delivered, delivery completed'，包裹已成功送达。虽有'D... |

**样本 2:**

```
单号：TBA326363759412
物流商：Amazon Shipping + Amazon MCF
国家：USA->USA
2025-12-14 07:06:16 Package lost AIRWAY HEIGHTS, WA, US
2025-12-05 10:50:15 Package arrived at the final hub/delivery station AIRWAY HEI...
```
**标注原因**: Package lost 表明包裹已经丢失

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 轨迹中最后一条信息显示'Package lost'，表明包裹已经丢失，符合异常状态中的包裹丢失情况。... |
| GPT-5 | 正确 | 0.98 | 轨迹显示“Package lost”，表明包裹已丢失；此前记录有“arrived at the fi... |
| Claude-4.5 | 正确 | 0.95 | 最新轨迹显示 'Package lost'，表明包裹已丢失。... |

---

### ABNORMAL_08

**错误统计**: Kimi 0/2, GPT-5 1/2, Claude-4.5 2/2

**样本 1:**

```
单号：427322603885
物流商：FedEx
国家：China->Réunion
2025-12-16 09:40:00 Delivery exception, Held, unable to collect payment ST MARIE, , RE
2025-12-15 10:16:00 Delivery exception, Held, unable to collect payme...
```
**标注原因**: Delivery exception, Held, unable to collect payment. 不属于无人认领、海关扣留、损坏、丢失、订单取消、退件类型，所以我们标记为其他异常

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 最新的轨迹信息显示包裹多次出现'Delivery exception, Held, unable t... |
| GPT-5 | 正确 | 0.86 | Repeated 'Delivery exception, Held, unable to coll... |
| Claude-4.5 | **错误** -> DELIVERY_FAILED_04 | 0.85 | 多次出现'Delivery exception, Held, unable to collect p... |

**样本 2:**

```
单号：SYRM160436531
物流商：SUNYOU
国家：China->Switzerland
2025-12-15 07:31:00 Delivery Exception Bülach Zustellung, CH
2025-12-13 08:07:00 Delivery In Progress Zürich Briefzentrum, CH
2025-12-12 09:52:00 Arri...
```
**标注原因**: Delivery Exception 表明是包裹异常，需要提醒客户，但为标明原因，所以标记为其他异常

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 轨迹中显示'Delivery Exception Bülach Zustellung, CH'表明包... |
| GPT-5 | **错误** -> DELIVERY_FAILED_04 | 0.82 | 出现“Delivery Exception”，说明派送阶段发生问题导致未能投递成功；此前有“Deli... |
| Claude-4.5 | **错误** -> DELIVERY_FAILED_04 | 0.85 | Delivery Exception 表明派送出现异常，之前有 Delivery In Progre... |

---

### DELIVERY_FAILED_04

**错误统计**: Kimi 2/2, GPT-5 1/2, Claude-4.5 0/2

**样本 1:**

```
单号：YT2533900707911155
物流商：YunExpress
国家：China->UK
2025-12-15 15:53:58 We've not been able to deliver today, we'll try on the next working day 
2025-12-15 11:30:55 ETA of delivery 
2025-12-15 11:23:34 ...
```
**标注原因**: We've not been able to deliver today, we'll try on the next working day. 可以看出来是投递失败，但是没有说明原因。

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> WAITING_DELIVERY_03 | 0.95 | 轨迹信息显示'Out For Delivery'和'We've not been able to d... |
| GPT-5 | **错误** -> WAITING_DELIVERY_03 | 0.83 | “We've not been able to deliver today, we'll try o... |
| Claude-4.5 | 正确 | 0.85 | 最新轨迹显示'We've not been able to deliver today, we'll... |

**样本 2:**

```
单号：4PX3002321628892CN
物流商：4PX
国家：China->Poland
2025-12-16 10:13:52 Delivery attempt unsuccessful UP Łańcut
2025-12-16 09:13:06 Out for delivery UP Łańcut
2025-12-16 08:26:22 Arrived at delivery office...
```
**标注原因**: Delivery attempt unsuccessful. 是典型的投递失败，且没有说明原因

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> DELIVERY_FAILED_02 | 1.00 | 轨迹中提到'Delivery attempt unsuccessful UP Łańcut'，表明因... |
| GPT-5 | 正确 | 0.82 | 最新轨迹显示“Delivery attempt unsuccessful”，说明本次派送失败；此前有... |
| Claude-4.5 | 正确 | 0.90 | Delivery attempt unsuccessful 表明投递失败，但未说明具体原因（非地址问... |

---

### IN_TRANSIT_01

**错误统计**: Kimi 2/2, GPT-5 1/2, Claude-4.5 0/2

**样本 1:**

```
单号：UK754362568YP
物流商：Yanwen
2025-12-17 07:34:00 Processing information input 
2025-12-17 00:20:42 Yanwen Pickup Scan 
2025-12-16 15:20:07 Order processed by shipper 
2025-12-15 23:23:22 Shipping Order...
```
**标注原因**: Processing information input .就属于比较宽泛的运输中状态

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> INFO_RECEIVED_01 | 0.95 | Processing information input 和 Yanwen Pickup Scan ... |
| GPT-5 | 正确 | 0.82 | 已出现“Yanwen Pickup Scan”取件扫描，且随后为“Processing inform... |
| Claude-4.5 | 正确 | 0.85 | Yanwen Pickup Scan 和 Processing information input ... |

**样本 2:**

```
单号：ZC53472203799
物流商：China Post
2025-12-16 22:26:25 邮件离开【东莞市国际公司直属国际营业部】，正在发往【广商中心】 广东省,东莞市
2025-12-16 22:15:30 邮件已在【东莞市国际公司直属国际营业部】完成分拣，准备发出 广东省,东莞市
2025-12-16 19:08:59 快件离开处理中心【东莞市】 东莞市
2025-12-16 1...
```
**标注原因**: 整体是一个运输中的状态，不太好归类到其他运输节点中，就放到当前的运输中了

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> IN_TRANSIT_02 | 0.95 | 邮件已在【东莞市国际公司直属国际营业部】完成分拣，准备发出，表明包裹已到达分拣中心... |
| GPT-5 | **错误** -> IN_TRANSIT_02 | 0.86 | 已到达并通过分拣中心后发出："邮件已在【东莞市国际公司直属国际营业部】完成分拣，准备发出"；此前有"... |
| Claude-4.5 | 正确 | 0.90 | 邮件离开东莞国际营业部，正在发往广商中心，包裹处于运输途中... |

---

### IN_TRANSIT_08

**错误统计**: Kimi 2/2, GPT-5 0/2, Claude-4.5 1/2

**样本 1:**

```
单号： LZ344114910CN
国家： 中国 -> 加拿大
2025-12-13 16:33 航空公司启运
2025-12-13 11:32 航空公司接收
2025-12-12 15:12 厦门市 36100153 已交承运商运输
2025-12-12 13:03 厦门市 36102199 邮件离开【厦门市国际互换局】，正在发往下一站
2025-12-12 11:02 厦门市 36102199...
```
**标注原因**: 航空公司启运表明包裹已经由航空公司开始运输了

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> IN_TRANSIT_05 | 1.00 | 轨迹信息显示'航空公司启运'和'航空公司接收'，表明包裹已交航空公司，运往目的国。... |
| GPT-5 | 正确 | 0.90 | 最新记录显示“航空公司启运”，表明已起飞；此前有“航空公司接收”，说明已交给航空公司准备出运。... |
| Claude-4.5 | **错误** -> IN_TRANSIT_05 | 0.95 | "航空公司启运"和"航空公司接收"表明包裹已交航空公司，正在运往目的国加拿大... |

**样本 2:**

```
单号：LZ339063340CN
物流商：China Post
国家：China->未知
2025-12-11 08:25:00 航空公司启运 
2025-12-11 08:24:00 航空公司启运 
2025-12-10 15:36:00 航空公司接收 
2025-12-09 13:44:52 航空公司接收 
2025-12-09 13:44:39 已交承运商运输 河南省,郑州市
2025-12...
```
**标注原因**: 航空公司启运 代表已经由航空公司在运输了

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> IN_TRANSIT_05 | 1.00 | 轨迹中显示'航空公司启运'和'航空公司接收'，表明包裹已交航空公司，正在运往目的国途中。... |
| GPT-5 | 正确 | 0.93 | 最新状态为“航空公司启运”，表示航班已起飞；此前出现“航空公司接收”作为前序进展。... |
| Claude-4.5 | 正确 | 0.90 | 航空公司启运表明包裹已上飞机，航班已起飞... |

---

### DELIVERED_02

**错误统计**: Kimi 2/2, GPT-5 0/2, Claude-4.5 0/2

**样本 1:**

```
单号：00340434156652354425
物流商：DHL Paket
国家：Germany->Germany
2025-12-10 16:39:00 The recipient has picked up the shipment from the PACKSTATION 
2025-12-10 12:27:00 The shipment is ready for pick-up at th...
```
**标注原因**: recipient has picked up the shipment from the PACKSTATION 表明包裹已经被收件人自提签收了

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | 正确 | 0.99 | Latest scan: 'The recipient has picked up the ship... |
| Claude-4.5 | 正确 | 0.95 | 收件人已在自提点领取包裹：'The recipient has picked up the ship... |

**样本 2:**

```
单号：SP0853393164586577
物流商：Super Parcel Track
2025-12-01 16:08:00 The item is collected at the pick-up point 
2025-12-01 12:31:00 The item is available at the pickup point 
2025-12-01 11:10:00 Driver i...
```
**标注原因**: The item is collected at the pick-up point 表明包裹已在自提点被领取，包裹已经签收成功

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> IN_TRANSIT_07 | 1.00 | The item is collected at the pick-up point and Dri... |
| GPT-5 | 正确 | 0.98 | “The item is collected at the pick-up point” 显示已在自... |
| Claude-4.5 | 正确 | 0.95 | The item is collected at the pick-up point 表明收件人已在... |

---

### DELIVERY_FAILED_03

**错误统计**: Kimi 0/2, GPT-5 1/2, Claude-4.5 1/2

**样本 1:**

```
单号：1ZE01A906864389677
物流商：UPS
2025-12-08 07:57:07 The investigation has been closed. We were unable to contact the receiver. 
2025-12-05 10:58:05 The street number is incorrect. This may delay deliver...
```
**标注原因**: We were unable to contact the receiver.表明无法联系上收件人

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 0.95 | 轨迹中提到 'The investigation has been closed. We were ... |
| GPT-5 | **错误** -> ABNORMAL_03 | 0.90 | "An investigation has been opened for your lost pa... |
| Claude-4.5 | **错误** -> ABNORMAL_03 | 0.85 | 最新轨迹显示'investigation has been closed. We were unab... |

**样本 2:**

```
单号：YT2532800707030504
物流商：YunExpress
国家：China->Greece
2025-12-05 11:27:37 Unsuccessful Delivery Does not answer the phone 
2025-12-05 10:35:07 Out for Delivery 
2025-12-05 07:13:36 Arrival Scan 
2025-...
```
**标注原因**: Unsuccessful Delivery Does not answer the phone 表明客户不接电话，所以联系不上

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 轨迹中提到 'Unsuccessful Delivery Does not answer the p... |
| GPT-5 | 正确 | 0.96 | 最新轨迹显示“Unsuccessful Delivery”且备注为“Does not answer ... |
| Claude-4.5 | 正确 | 0.95 | Unsuccessful Delivery Does not answer the phone 表明... |

---

### IN_TRANSIT_03

**错误统计**: Kimi 1/2, GPT-5 0/2, Claude-4.5 1/2

**样本 1:**

```
单号：UK717781415YP
物流商：Yanwen
国家：未知->USA
2025-12-15 23:32:00 International shipment release - Import 
2025-12-15 23:30:00 Pick up by local carrier at destination port 
2025-12-15 13:46:00 Port of destin...
```
**标注原因**: International shipment release - Import 表明包裹已经进口清关完成

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> IN_TRANSIT_06 | 1.00 | 轨迹显示'International shipment release - Import'和'Pic... |
| GPT-5 | 正确 | 0.90 | “International shipment release - Import” 表示进口清关放行... |
| Claude-4.5 | **错误** -> IN_TRANSIT_06 | 0.90 | 最新轨迹显示'International shipment release - Import'和'P... |

**样本 2:**

```
单号：JCY1128052543DH
物流商：JCEX
国家：China->USA
2025-12-13 00:15:30 US,Customs clearance completed US
2025-12-11 07:02:43 US,Arrived at US Airport US
2025-12-09 11:25:11 HK,Departure From HK Center HK
2025-...
```
**标注原因**: Customs clearance completed 表明包裹已经清关完成

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 最新一条信息显示'US,Customs clearance completed US'，表明包裹已完... |
| GPT-5 | 正确 | 0.95 | “Customs clearance completed”表明已完成清关；且此前有“Arrived ... |
| Claude-4.5 | 正确 | 0.95 | Customs clearance completed 表明包裹已完成海关清关，目前在美国境内等待后... |

---

### ABNORMAL_04

**错误统计**: Kimi 1/2, GPT-5 0/2, Claude-4.5 0/2

**样本 1:**

```
单号：3113222107524
物流商：Delhivery
国家：India->India
2025-12-16 18:04:40 Order cancelled by merchant/shipper Ranipet
==========================================
Powered by www.track123.com
```
**标注原因**: Order cancelled by merchant/shipper Ranipet. 表明包裹已经被卖家/寄件人取消寄件

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 包裹信息显示'Order cancelled by merchant/shipper Ranipet... |
| GPT-5 | 正确 | 0.97 | 轨迹显示“Order cancelled by merchant/shipper”，表明订单已被商家... |
| Claude-4.5 | 正确 | 0.95 | 轨迹显示'Order cancelled by merchant/shipper'，订单已被商家/发... |

**样本 2:**

```
单号：YT2533100707974200
物流商：YunExpress
国家：China->Denmark
2025-12-05 00:46:46 Change tracking number and relabel Mainland China, CN
2025-12-04 17:46:48 Forsendelsen er annulleret 
2025-12-02 10:46:37 Dep...
```
**标注原因**: 该包裹已被物流商取消（Cancelled），后续显示的“更换单号并重新贴标”属于物流系统操作记录，不代表包裹已重新发出或继续运输。

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** ->  | 0.00 | ... |
| GPT-5 | 正确 | 0.96 | 轨迹出现“Forsendelsen er annulleret”（包裹已取消，丹麦语），明确指向订单... |
| Claude-4.5 | 正确 | 0.95 | "Forsendelsen er annulleret"是丹麦语，意为"订单已取消"... |

---

### DELIVERED_03

**错误统计**: Kimi 0/2, GPT-5 1/2, Claude-4.5 0/2

**样本 1:**

```
单号：WS10321896033179621DL
物流商：Whats ship
国家：United Arab Emirates->United Arab Emirates
2025-12-05 16:04:06 The parcel has been signed by [Receiver signed]. If you have any queires, please contact 60056...
```
**标注原因**: 出现了Receiver signed的字样，说明确实是收件人已经签名了

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | The parcel has been signed by [Receiver signed]. 表... |
| GPT-5 | 正确 | 0.96 | The parcel has been signed by [Receiver signed]. E... |
| Claude-4.5 | 正确 | 0.95 | 轨迹显示'The parcel has been signed by [Receiver signe... |

**样本 2:**

```
单号：WS14153727173795534DL
物流商：Whats ship
国家：New Zealand->New Zealand
2025-12-01 15:23:05 Signature Obtained Palmerston North
2025-12-01 13:57:51 On Board - The parcel is on board the courier vehicle Pa...
```
**标注原因**: Signature Obtained代表已经获得了签名，所以是签字签收

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 轨迹中显示'Signature Obtained Palmerston North'，表明包裹已成功... |
| GPT-5 | **错误** -> DELIVERED_01 | 0.96 | “Signature Obtained”表明已成功送达并获取签名；之前的“On Board - Th... |
| Claude-4.5 | 正确 | 0.95 | Signature Obtained表明包裹已签收，收件人已签名确认收货。... |

---

### DELIVERY_FAILED_01

**错误统计**: Kimi 0/2, GPT-5 1/2, Claude-4.5 0/2

**样本 1:**

```
单号：420956709334610597204903139594
物流商：USPS
国家：USA->USA
2025-12-13 07:55:00 Delivery Attempted - No Access to Delivery Location RANCHO CORDOVA,CA
2025-12-13 06:10:00 Out for Delivery RANCHO CORDOVA,CA
...
```
**标注原因**: No Access to Delivery Location表明是由于地址问题而导致投递失败，虽然不是地址缺失，但是无法进入投递地点

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 轨迹中提到 'Delivery Attempted - No Access to Delivery ... |
| GPT-5 | **错误** -> DELIVERY_FAILED_04 | 0.90 | “Delivery Attempted - No Access to Delivery Locati... |
| Claude-4.5 | 正确 | 0.85 | "Delivery Attempted - No Access to Delivery Locati... |

**样本 2:**

```
单号：UK694821542YP
物流商：Yanwen
国家：未知->USA
2025-12-14 07:09:34 Delivery attempt unsuccessful.Delivery attempt unsuccessful.Delivery address is incorrect 
2025-12-13 09:25:27 Out for delivery. 
2025-12-13 ...
```
**标注原因**: Delivery attempt unsuccessful.Delivery address is incorrect 已经表明了是由于地址不正确而导致的投递失败

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 轨迹中提到'Delivery attempt unsuccessful.Delivery attem... |
| GPT-5 | 正确 | 0.98 | 最新轨迹显示“Delivery attempt unsuccessful... Delivery a... |
| Claude-4.5 | 正确 | 0.95 | Delivery attempt unsuccessful.Delivery address is ... |

---

### DELIVERY_FAILED_02

**错误统计**: Kimi 1/2, GPT-5 0/2, Claude-4.5 0/2

**样本 1:**

```
单号：CJPAFD0311500248YQ
物流商：CJ Packet
国家：China->UK
2025-12-15 11:59:17 Delivery failed. Not at home. UNITED KINGDOM
2025-12-15 08:57:00 Out for delivery UNITED KINGDOM
2025-12-13 01:35:40 Received by lo...
```
**标注原因**: Delivery failed. Not at home. 表明包裹是由于不在家导致的投递失败

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 轨迹显示 'Delivery failed. Not at home. UNITED KINGDOM... |
| GPT-5 | 正确 | 0.95 | “Delivery failed. Not at home.” 明确因收件人不在家导致派送失败；同日... |
| Claude-4.5 | 正确 | 0.95 | Delivery failed. Not at home. 明确表明因收件人不在家派送失败... |

**样本 2:**

```
单号：15504652683779
物流商：DPD(UK)
国家：UK->未知
2025-12-16 07:40:00 We missed you. Your driver Stephen won't be back today but you can still rearrange your delivery. DPD
2025-12-16 07:13:00 Your parcel will b...
```
**标注原因**: We missed you. 表明错过了，所以投递失败

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> WAITING_DELIVERY_03 | 0.90 | 轨迹中提到'Your parcel could not be delivered as the re... |
| GPT-5 | 正确 | 0.86 | 最新轨迹显示“We missed you... your driver... won't be ba... |
| Claude-4.5 | 正确 | 0.85 | "We missed you" 表明收件人不在家导致派送失败，司机今天不会再来但可以重新安排派送。... |

---

### IN_TRANSIT_02

**错误统计**: Kimi 1/2, GPT-5 0/2, Claude-4.5 0/2

**样本 1:**

```
单号：GFUS01024532980480
物流商：GOFO
国家：USA->USA
2025-12-16 14:14:16 Arrived at sorting center 
2025-12-15 18:05:14 Picked up by Shipping Partner, GOFO Awaiting Item 
2025-12-14 23:29:54 Shipping Label Crea...
```
**标注原因**: Arrived at sorting center表明已经到达分拣站。

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 0.95 | 轨迹信息显示'Arrived at sorting center'，表明包裹已到达分拣中心，符合'I... |
| GPT-5 | 正确 | 0.90 | 最新记录显示“Arrived at sorting center”，表明已到达分拣中心；此前“Pic... |
| Claude-4.5 | 正确 | 0.95 | Arrived at sorting center 表明包裹已到达分拣中心... |

**样本 2:**

```
单号：92419903032582543402551286
物流商：UPS
国家：未知->未知
2025-12-16 14:07:00 Arrived at USPS Facility US
2025-12-16 13:13:00 Shipment Received, Package Acceptance Pending Raleigh, NC, US
2025-12-16 12:58:00 De...
```
**标注原因**: Arrived at USPS Facility US. 表明包裹已经到达了USPS的站点

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | **错误** -> IN_TRANSIT_06 | 1.00 | 轨迹显示'Arrived at USPS Facility US'和'Departed UPS Fa... |
| GPT-5 | 正确 | 0.80 | 最新轨迹为“Arrived at USPS Facility”，且此前有“Accepted at U... |
| Claude-4.5 | 正确 | 0.85 | 最新轨迹显示'Arrived at USPS Facility'，包裹已到达USPS分拣设施，正在转... |

---

### IN_TRANSIT_06

**错误统计**: Kimi 0/2, GPT-5 0/2, Claude-4.5 1/2

**样本 1:**

```
单号：SYIT008798811
物流商：SUNYOU
国家：China->Italy
2025-12-13 12:32:00 Arrived At Destination Country Airport 
2025-12-13 06:32:00 Customs Clearance In Process 
2025-12-11 04:57:00 Departed From Port Of Orig...
```
**标注原因**: Arrived At Destination Country Airport 表明已经到达目的国机场

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 轨迹中显示'Arrived At Destination Country Airport'，表明包裹... |
| GPT-5 | 正确 | 0.90 | “Arrived At Destination Country Airport” 表明包裹已抵达目的... |
| Claude-4.5 | **错误** -> IN_TRANSIT_03 | 0.85 | 最新状态显示'Arrived At Destination Country Airport'且'Cu... |

**样本 2:**

```
单号：XSSY00006132922
物流商：XUANSI
2025-12-15 00:30:51 到达目的地机场/港口 
2025-12-12 10:17:23 离开起运地机场/港口 
2025-12-11 10:33:04 到达起飞地机场 
2025-12-11 09:32:01 包裹离开分拣中心 DONGGUAN
2025-12-10 12:34:48 分拣中心已入库 DONGGUAN
20...
```
**标注原因**: 到达目的地机场/港口 表明包裹已经到达目的国

| 模型 | 预测 | 置信度 | 解释 |
|------|------|--------|------|
| Kimi | 正确 | 1.00 | 轨迹显示'到达目的地机场/港口'，表明包裹已经抵达目的国，符合'IN_TRANSIT_06'状态。... |
| GPT-5 | 正确 | 0.86 | 最新轨迹为“到达目的地机场/港口”，表明包裹已抵达目的国；此前有“离开起运地机场/港口”记录... |
| Claude-4.5 | 正确 | 0.95 | "到达目的地机场/港口"表明包裹已抵达目的国... |

---

## 4. 结论

### 模型排名

1. **Claude-4.5** 和 **GPT-5** 并列第一，子状态准确率均为 **73.21%**
2. **Kimi** 准确率 **53.57%**，表现较差

### 主要问题类别

- **ABNORMAL_07**: 5个错误
- **ABNORMAL_05**: 4个错误
- **ABNORMAL_06**: 4个错误
- **DELIVERED_01**: 4个错误
- **IN_TRANSIT_04**: 4个错误
- **WAITING_DELIVERY_01**: 4个错误
- **WAITING_DELIVERY_03**: 4个错误
- **ABNORMAL_03**: 3个错误
- **ABNORMAL_08**: 3个错误
- **DELIVERY_FAILED_04**: 3个错误

### 改进建议

1. 针对高错误率的子状态（如ABNORMAL系列、IN_TRANSIT_04等），增加更多few-shot案例
2. 在prompt中增加对易混淆状态的区分说明
3. 考虑对ABNORMAL类别进行更细致的规则定义