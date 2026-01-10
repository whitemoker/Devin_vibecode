# Hard Cases 分析

共找到 2 个Hard Case（全体专家一致错误）

## Hard Case 1

- **Sample ID**: GM5453527420279432
- **Tracking No**: GM5453527420279432
- **真实标签**: WAITING_DELIVERY
- **预测标签**: DELIVERY_FAILED (全部 11 个专家一致)

### 完整轨迹 (16 条事件)

**1. [INFO_RECEIVED_01]**
```
[2025-12-09 10:46:55] LABEL CREATED
```

**2. [INFO_RECEIVED_01]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
```

**3. [INFO_RECEIVED_01]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
```

**4. [IN_TRANSIT_02]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
```

**5. [IN_TRANSIT_02]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
```

**6. [IN_TRANSIT_02]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
```

**7. [IN_TRANSIT_02]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
[2025-12-10 13:17:34] PROCESSING COMPLETED AT ORIGIN
```

**8. [IN_TRANSIT_02]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
[2025-12-10 13:17:34] PROCESSING COMPLETED AT ORIGIN
[2025-12-10 13:17:37] SCANNED INTO SACK/CONTAINER
```

**9. [IN_TRANSIT_07]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
[2025-12-10 13:17:34] PROCESSING COMPLETED AT ORIGIN
[2025-12-10 13:17:37] SCANNED INTO SACK/CONTAINER
[2025-12-11 10:22:00] SHIPMENT ACCEPTED BY USPS
```

**10. [IN_TRANSIT_07]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
[2025-12-10 13:17:34] PROCESSING COMPLETED AT ORIGIN
[2025-12-10 13:17:37] SCANNED INTO SACK/CONTAINER
[2025-12-11 10:22:00] SHIPMENT ACCEPTED BY USPS
[2025-12-11 11:37:00] PROCESSED THROUGH SORT FACILITY
```

**11. [IN_TRANSIT_07]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
[2025-12-10 13:17:34] PROCESSING COMPLETED AT ORIGIN
[2025-12-10 13:17:37] SCANNED INTO SACK/CONTAINER
[2025-12-11 10:22:00] SHIPMENT ACCEPTED BY USPS
[2025-12-11 11:37:00] PROCESSED THROUGH SORT FACILITY
[2025-12-11 11:38:00] ARRIVED AT EXPORT FACILITY
```

**12. [IN_TRANSIT_07]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
[2025-12-10 13:17:34] PROCESSING COMPLETED AT ORIGIN
[2025-12-10 13:17:37] SCANNED INTO SACK/CONTAINER
[2025-12-11 10:22:00] SHIPMENT ACCEPTED BY USPS
[2025-12-11 11:37:00] PROCESSED THROUGH SORT FACILITY
[2025-12-11 11:38:00] ARRIVED AT EXPORT FACILITY
[2025-12-11 11:58:00] PROCESSED AT EXPORT FACILITY
```

**13. [IN_TRANSIT_01]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
[2025-12-10 13:17:34] PROCESSING COMPLETED AT ORIGIN
[2025-12-10 13:17:37] SCANNED INTO SACK/CONTAINER
[2025-12-11 10:22:00] SHIPMENT ACCEPTED BY USPS
[2025-12-11 11:37:00] PROCESSED THROUGH SORT FACILITY
[2025-12-11 11:38:00] ARRIVED AT EXPORT FACILITY
[2025-12-11 11:58:00] PROCESSED AT EXPORT FACILITY
[2025-12-15 14:59:00] PROCESSED AT LOCAL DISTRIBUTION CENTER
```

**14. [IN_TRANSIT_01]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
[2025-12-10 13:17:34] PROCESSING COMPLETED AT ORIGIN
[2025-12-10 13:17:37] SCANNED INTO SACK/CONTAINER
[2025-12-11 10:22:00] SHIPMENT ACCEPTED BY USPS
[2025-12-11 11:37:00] PROCESSED THROUGH SORT FACILITY
[2025-12-11 11:38:00] ARRIVED AT EXPORT FACILITY
[2025-12-11 11:58:00] PROCESSED AT EXPORT FACILITY
[2025-12-15 14:59:00] PROCESSED AT LOCAL DISTRIBUTION CENTER
[2025-12-15 14:59:00] ARRIVED AT CUSTOMS
```

**15. [IN_TRANSIT_07]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
[2025-12-10 13:17:34] PROCESSING COMPLETED AT ORIGIN
[2025-12-10 13:17:37] SCANNED INTO SACK/CONTAINER
[2025-12-11 10:22:00] SHIPMENT ACCEPTED BY USPS
[2025-12-11 11:37:00] PROCESSED THROUGH SORT FACILITY
[2025-12-11 11:38:00] ARRIVED AT EXPORT FACILITY
[2025-12-11 11:58:00] PROCESSED AT EXPORT FACILITY
[2025-12-15 14:59:00] PROCESSED AT LOCAL DISTRIBUTION CENTER
[2025-12-15 14:59:00] ARRIVED AT CUSTOMS
[2025-12-15 16:14:00] CLEARED CUSTOMS
```

**16. >>> LATEST: [WAITING_DELIVERY_01]**
```
[2025-12-09 10:46:55] LABEL CREATED
[2025-12-09 16:22:30] EN ROUTE TO DHL ECOMMERCE OR AWAITING PROCESSING
[2025-12-10 00:00:00] ELECTRONIC SHIPPING INFO RECEIVED
[2025-12-10 08:31:30] PROCESSED
[2025-12-10 12:06:29] CLOSE BAG
[2025-12-10 13:17:28] MANIFESTED FOR OUTBOUND TRANSPORTATION
[2025-12-10 13:17:34] PROCESSING COMPLETED AT ORIGIN
[2025-12-10 13:17:37] SCANNED INTO SACK/CONTAINER
[2025-12-11 10:22:00] SHIPMENT ACCEPTED BY USPS
[2025-12-11 11:37:00] PROCESSED THROUGH SORT FACILITY
[2025-12-11 11:38:00] ARRIVED AT EXPORT FACILITY
[2025-12-11 11:58:00] PROCESSED AT EXPORT FACILITY
[2025-12-15 14:59:00] PROCESSED AT LOCAL DISTRIBUTION CENTER
[2025-12-15 14:59:00] ARRIVED AT CUSTOMS
[2025-12-15 16:14:00] CLEARED CUSTOMS
[2025-12-18 15:23:00] ATTEMPTED DELIVERY
```

### 专家解释

**gpt-5.2_rule_based**:
> 最新事件为“ATTEMPTED DELIVERY”（已尝试派送但未成功），符合优先级3【派送失败】；轨迹中无退回（RTS/RTO/return to sender等）强证据，也未出现最终签收/妥投事件，因此不判为DELIVERED。

**gpt-5.2_time_based**:
> 最新事件为“ATTEMPTED DELIVERY”（已尝试派送但未显示成功签收/妥投），属于发生派送尝试未完成交付的状态。此前已清关完成，说明包裹已进入末端派送环节。

**gpt-5.2_evidence_based**:
> 最新轨迹为“ATTEMPTED DELIVERY”，属于已尝试派送但未完成签收的派送失败类证据；同时存在清关/分拣等运输链路事件，但没有交付完成证据（delivered）或强退回证据，因此判定为 DELIVERY_FAILED。

**claude-opus-4.5_rule_based**:
> 最新事件为'ATTEMPTED DELIVERY'（尝试派送），表明派送尝试但未成功完成，符合优先级3 DELIVERY_FAILED规则。无退回证据，无签收证据。

**claude-opus-4.5_time_based**:
> 最新事件为'ATTEMPTED DELIVERY'，表明已尝试派送但未成功交付，属于派送失败状态。

**claude-opus-4.5_evidence_based**:
> 最新事件为ATTEMPTED DELIVERY（尝试投递），表明派送失败，无交付完成或退回证据

**gemini-3_rule_based**:
> The latest event is 'ATTEMPTED DELIVERY', which directly matches the criteria for Priority 3: DELIVERY_FAILED (evidence of failed delivery attempt, no one home, or unable to contact). There is no evidence of final delivery or a strong return process.

**grok-4_rule_based**:
> 最新事件为'ATTEMPTED DELIVERY'，表示派送尝试失败，匹配DELIVERY_FAILED规则的投递失败证据；轨迹无退回或异常证据覆盖优先级更高的分类

**gemini-3_time_based**:
> The latest event 'ATTEMPTED DELIVERY' indicates that a delivery attempt was made but was not successful (e.g., recipient not home), which falls directly under the definition of DELIVERY_FAILED.

**grok-4_time_based**:
> Latest event 'ATTEMPTED DELIVERY' indicates a delivery attempt was made but not completed successfully, with no evidence of delivery or abnormalities.

**grok-4_evidence_based**:
> 最新事件'ATTEMPTED DELIVERY'表示投递尝试失败，属于派送失败证据；轨迹中存在多个运输链路证据如'PROCESSED'、'CLEARED CUSTOMS'等，但无交付完成证据或异常阻断证据，因此分类为DELIVERY_FAILED。

---

## Hard Case 2

- **Sample ID**: WS14532782726884605DL
- **Tracking No**: WS14532782726884605DL
- **真实标签**: WAITING_DELIVERY
- **预测标签**: DELIVERED (全部 12 个专家一致)

### 完整轨迹 (19 条事件)

**1. [INFO_RECEIVED_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
```

**2. [INFO_RECEIVED_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
```

**3. [IN_TRANSIT_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
```

**4. [IN_TRANSIT_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
```

**5. [IN_TRANSIT_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
```

**6. [IN_TRANSIT_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
```

**7. [IN_TRANSIT_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
```

**8. [IN_TRANSIT_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
```

**9. [IN_TRANSIT_08]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
```

**10. [IN_TRANSIT_08]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
[2025-12-03 00:49:34] Arrived at International airport
```

**11. [IN_TRANSIT_03]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
[2025-12-03 00:49:34] Arrived at International airport
[2025-12-03 23:46:22] Released from customs
```

**12. [IN_TRANSIT_03]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
[2025-12-03 00:49:34] Arrived at International airport
[2025-12-03 23:46:22] Released from customs
[2025-12-04 03:00:00] Arrive transithub
```

**13. [IN_TRANSIT_03]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
[2025-12-03 00:49:34] Arrived at International airport
[2025-12-03 23:46:22] Released from customs
[2025-12-04 03:00:00] Arrive transithub
[2025-12-04 09:01:36] We've received this parcel at the hub and will be sorted to the customers delivery depot
```

**14. [IN_TRANSIT_03]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
[2025-12-03 00:49:34] Arrived at International airport
[2025-12-03 23:46:22] Released from customs
[2025-12-04 03:00:00] Arrive transithub
[2025-12-04 09:01:36] We've received this parcel at the hub and will be sorted to the customers delivery depot
[2025-12-04 09:02:36] Parcel processed at the hub
```

**15. [IN_TRANSIT_03]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
[2025-12-03 00:49:34] Arrived at International airport
[2025-12-03 23:46:22] Released from customs
[2025-12-04 03:00:00] Arrive transithub
[2025-12-04 09:01:36] We've received this parcel at the hub and will be sorted to the customers delivery depot
[2025-12-04 09:02:36] Parcel processed at the hub
[2025-12-04 22:46:22] Collected by Evri
```

**16. [IN_TRANSIT_03]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
[2025-12-03 00:49:34] Arrived at International airport
[2025-12-03 23:46:22] Released from customs
[2025-12-04 03:00:00] Arrive transithub
[2025-12-04 09:01:36] We've received this parcel at the hub and will be sorted to the customers delivery depot
[2025-12-04 09:02:36] Parcel processed at the hub
[2025-12-04 22:46:22] Collected by Evri
[2025-12-06 08:06:58] Parcel processed at the depot
```

**17. [WAITING_DELIVERY_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
[2025-12-03 00:49:34] Arrived at International airport
[2025-12-03 23:46:22] Released from customs
[2025-12-04 03:00:00] Arrive transithub
[2025-12-04 09:01:36] We've received this parcel at the hub and will be sorted to the customers delivery depot
[2025-12-04 09:02:36] Parcel processed at the hub
[2025-12-04 22:46:22] Collected by Evri
[2025-12-06 08:06:58] Parcel processed at the depot
[2025-12-10 15:31:43] Out for delivery
```

**18. [WAITING_DELIVERY_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
[2025-12-03 00:49:34] Arrived at International airport
[2025-12-03 23:46:22] Released from customs
[2025-12-04 03:00:00] Arrive transithub
[2025-12-04 09:01:36] We've received this parcel at the hub and will be sorted to the customers delivery depot
[2025-12-04 09:02:36] Parcel processed at the hub
[2025-12-04 22:46:22] Collected by Evri
[2025-12-06 08:06:58] Parcel processed at the depot
[2025-12-10 15:31:43] Out for delivery
[2025-12-10 18:18:12] ETA of delivery
```

**19. >>> LATEST: [WAITING_DELIVERY_01]**
```
[2025-11-24 05:59:00] Carrier Receipt
[2025-11-24 13:02:17] Shipping Label Created
[2025-11-25 19:10:05] Picked up from shipper
[2025-11-25 20:10:05] Arrived at SHA Depot
[2025-11-25 20:30:05] Departed from Original Depot
[2025-11-25 20:40:05] Arrived at operation center
[2025-11-25 20:50:05] Departed from operation center
[2025-11-27 20:47:15] Arrived at original airport
[2025-12-01 06:05:34] Departed from original airport
[2025-12-03 00:49:34] Arrived at International airport
[2025-12-03 23:46:22] Released from customs
[2025-12-04 03:00:00] Arrive transithub
[2025-12-04 09:01:36] We've received this parcel at the hub and will be sorted to the customers delivery depot
[2025-12-04 09:02:36] Parcel processed at the hub
[2025-12-04 22:46:22] Collected by Evri
[2025-12-06 08:06:58] Parcel processed at the depot
[2025-12-10 15:31:43] Out for delivery
[2025-12-10 18:18:12] ETA of delivery
[2025-12-10 23:40:31] This parcel has been Arrived at the customers letterbox
```

### 专家解释

**gpt-5.2_rule_based**:
> 最新事件为“This parcel has been Arrived at the customers letterbox”，属于已妥投/放入信箱的交付完成证据，符合优先级1（DELIVERED）。轨迹中未出现任何强退回证据（RTS/RTO/return to sender等）或其他需覆盖签收的异常证据。

**gpt-5.2_time_based**:
> 最新事件显示包裹“已到达收件人信箱（Arrived at the customers letterbox）”，且此前有“Out for delivery”派送动作，轨迹中未出现退回/异常强证据，因此判定为已妥投签收（DELIVERED）。

**gpt-5.2_evidence_based**:
> 最新状态显示包裹已投递至客户信箱（Arrived at the customers letterbox），属于交付完成证据；此前有Out for delivery的末端派送流程，且全程无退回链路或异常阻断/派送失败类强证据，因此判定为DELIVERED。

**claude-opus-4.5_rule_based**:
> 最新事件'Arrived at the customers letterbox'表示包裹已投递至收件人信箱，属于签收/妥投证据。轨迹中无退回或异常证据，符合优先级1 DELIVERED规则。

**claude-opus-4.5_time_based**:
> 最新事件显示包裹已到达客户信箱（letterbox），表示成功投递，无退回或异常证据。

**claude-opus-4.5_evidence_based**:
> 最新事件显示包裹已投递至客户信箱，无退回或异常证据，判定为成功签收

**gemini-3_rule_based**:
> The latest event 'Arrived at the customers letterbox' indicates a successful delivery to a specific location (letterbox). There are no keywords suggesting return, refusal, or damage in the history, satisfying the Priority 1 rule for DELIVERED.

**grok-4_rule_based**:
> 最新事件'This parcel has been Arrived at the customers letterbox'表示包裹已放置于客户的信箱，符合DELIVERED的证据（放置于指定位置），轨迹中无退回或异常证据，满足优先级1规则。

**gemini-3_time_based**:
> The latest event 'Arrived at the customers letterbox' indicates that the parcel has been successfully delivered to the recipient's location. There are no signs of return or abnormal issues in the tracking history.

**grok-4_time_based**:
> The latest event states the parcel has arrived at the customer's letterbox, indicating successful delivery with no evidence of returns or abnormalities in the trace.

**gemini-3_evidence_based**:
> 轨迹最新状态显示包裹已到达客户信箱（Arrived at the customers letterbox），这属于明确的交付完成证据。此前虽有运输和派送过程，但无任何异常阻断或退回证据，因此判定为正常签收。

**grok-4_evidence_based**:
> 轨迹显示从预报到运输链路，再到末端派送，最终以'Arrived at the customers letterbox'作为交付完成证据，无任何异常阻断或退回链路证据，因此分类为DELIVERED。

---

