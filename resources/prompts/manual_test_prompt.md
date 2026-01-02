================================================================================
【系统提示词 - System Prompt】
（如果网页版支持设置系统提示词，请粘贴以下内容）
================================================================================

你是一个物流状态分类专家。根据物流轨迹信息，判断包裹当前的状态。

## 分类规则

### In transit/运输途中
- IN_TRANSIT_01: 包裹正在运输途中
- IN_TRANSIT_02: 包裹已到达分拣中心
- IN_TRANSIT_03: 包裹已完成海关清关
- IN_TRANSIT_04: 包裹已封装，即将送往机场
- IN_TRANSIT_05: 包裹已交航空公司，运往目的国
- IN_TRANSIT_06: 包裹已抵达目的国
- IN_TRANSIT_07: 包裹已到达当地网点，即将派送
- IN_TRANSIT_08: 包裹已上飞机，航班已起飞

### Out for delivery/派送中
- WAITING_DELIVERY_01: 包裹正在派送途中
- WAITING_DELIVERY_02: 包裹已到自提点，等待领取
- WAITING_DELIVERY_03: 收件人要求延迟派送或投递失败后等待二次派送

### Delivered/签收
- DELIVERED_01: 包裹已成功送达
- DELIVERED_02: 收件人在自提点已领取包裹
- DELIVERED_03: 包裹已签收（客户本人）
- DELIVERED_04: 包裹已投递至收件人地址，可能由房主、门卫、家人、邻居代收，或放置在家门口、门廊（Front Door / Porch）或其他安全位置。

### Failed attempt/投递失败
- DELIVERY_FAILED_01: 因地址问题派送失败
- DELIVERY_FAILED_02: 因收件人不在家派送失败
- DELIVERY_FAILED_03: 因无法联系上收件人派送失败
- DELIVERY_FAILED_04: 因其他原因派送失败

### Exception/可能异常
- ABNORMAL_01: 包裹无人领取
- ABNORMAL_02: 包裹被海关扣留
- ABNORMAL_03: 包裹损坏、丢失或被丢弃
- ABNORMAL_04: 订单已取消
- ABNORMAL_05: 收件人拒绝签收
- ABNORMAL_06: 退回包裹已被发件人接收
- ABNORMAL_07: 包裹正在返回发件人途中
- ABNORMAL_08: 其他异常情况

### Info received/等待揽收
- INFO_RECEIVED_01: 承运方已收到发件人请求，正在揽件

## 输出格式

请用JSON格式输出：
{"sub_status": "状态代码", "confidence": 0.0-1.0, "explanation": "简短解释，引用1-2个关键证据片段"}

可选状态代码：IN_TRANSIT_01, IN_TRANSIT_02, IN_TRANSIT_03, IN_TRANSIT_04, IN_TRANSIT_05, IN_TRANSIT_06, IN_TRANSIT_07, IN_TRANSIT_08, WAITING_DELIVERY_01, WAITING_DELIVERY_02, WAITING_DELIVERY_03, DELIVERED_01, DELIVERED_02, DELIVERED_03, DELIVERED_04, DELIVERY_FAILED_01, DELIVERY_FAILED_02, DELIVERY_FAILED_03, DELIVERY_FAILED_04, ABNORMAL_01, ABNORMAL_02, ABNORMAL_03, ABNORMAL_04, ABNORMAL_05, ABNORMAL_06, ABNORMAL_07, ABNORMAL_08, INFO_RECEIVED_01


================================================================================
【用户提示词 - User Prompt】
（直接粘贴到对话框发送）
================================================================================

## 参考案例

案例1:
轨迹: 单号：LI354832813LT
物流商：Lithuania Post
国家：Lithuania->未知
2025-12-16 01:05:00 Siunta sulaikyta gavimo šalies muitinėje Jungtinės Amerikos Valstijos
2025-12-15 01:06:00 Siunta pateikta gavėjo šalies muitinei Jungtinės Amerikos Valstijos
...
状态: ABNORMAL_02
原因: Siunta sulaikyta gavimo šalies muitinėje 表明包裹在海关被扣留

案例2:
轨迹: 单号：LZ348277808CN
物流商：China Post
国家：China->未知
2025-12-17 03:48:53 邮件离开【广州市国际互换局】，正在发往下一站 广东省,广州市
2025-12-16 23:03:06 【广州市国际互换局】已出口直封 广东省,广州市
...
状态: IN_TRANSIT_04
原因: 【广州市国际互换局】已出口直封 ，表明包裹已经封装好，即将出口了

案例3:
轨迹: 单号：UK754362568YP
物流商：Yanwen
2025-12-17 07:34:00 Processing information input
2025-12-17 00:20:42 Yanwen Pickup Scan
2025-12-16 15:20:07 Order processed by shipper
...
状态: IN_TRANSIT_01
原因: Processing information input .就属于比较宽泛的运输中状态

## 待分类轨迹

单号：ZC53472203799
物流商：China Post
2025-12-16 22:26:25 邮件离开【东莞市国际公司直属国际营业部】，正在发往【广商中心】 广东省,东莞市
2025-12-16 22:15:30 邮件已在【东莞市国际公司直属国际营业部】完成分拣，准备发出 广东省,东莞市
2025-12-16 19:08:59 快件离开处理中心【东莞市】 东莞市
2025-12-16 19:06:38 快件到达处理中心【东莞市】 东莞市
2025-12-16 18:28:57 中国邮政已收取快件 广东省,东莞市
==========================================
Powered by www.track123.com

请输出JSON结果：


================================================================================
【正确答案】: IN_TRANSIT_01
================================================================================


================================================================================
【更多测试用例 - 替换上面的"待分类轨迹"部分】
================================================================================

--- 测试用例2 (正确答案: IN_TRANSIT_03) ---
单号：JCY1128052543DH
物流商：JCEX
国家：China->USA
2025-12-13 00:15:30 US,Customs clearance completed US
2025-12-11 07:02:43 US,Arrived at US Airport US
2025-12-09 11:25:11 HK,Departure From HK Center HK
2025-12-06 13:45:04 Arrived at HK CENTER HK
2025-12-06 01:45:04 Departed from origin facility to airport CN
2025-12-05 21:45:04 Item outbound in sorting center CN
2025-12-05 04:54:19 Arrive at the delivery point CN
2025-11-28 10:17:41 预报订单信息已收到
==========================================
Powered by www.track123.com

--- 测试用例3 (正确答案: DELIVERED_01) ---
单号：9214490357610124896670
物流商：USPS
国家：USA->USA
2025-12-17 14:30:00 Delivered, In/At Mailbox SYRACUSE,NY
2025-12-17 08:15:00 Out for Delivery SYRACUSE,NY
2025-12-16 13:50:00 Arrived at USPS Facility SYRACUSE NY DISTRIBUTION CENTER
2025-12-16 07:53:00 Departed Post Office QUEENS NY DISTRIBUTION CENTER
2025-12-15 23:00:00 Processed through USPS Facility QUEENS NY DISTRIBUTION CENTER
==========================================
Powered by www.track123.com

--- 测试用例4 (正确答案: ABNORMAL_02) ---
单号：LI354832813LT
物流商：Lithuania Post
国家：Lithuania->未知
2025-12-16 01:05:00 Siunta sulaikyta gavimo šalies muitinėje Jungtinės Amerikos Valstijos
2025-12-15 01:06:00 Siunta pateikta gavėjo šalies muitinei Jungtinės Amerikos Valstijos
2025-12-14 01:06:00 Siunta atvyko į gavėjo šalį Jungtinės Amerikos Valstijos
2025-12-11 01:05:00 Siunta išvyko iš kilmės šalies Lietuva
2025-12-10 01:05:00 Siunta pateikta kilmės šalies muitinei Lietuva
==========================================
Powered by www.track123.com

--- 测试用例5 (正确答案: DELIVERY_FAILED_01) ---
单号：92419903032582543402551286
物流商：UPS
国家：未知->未知
2025-12-17 15:30:00 Delivery attempted - Incorrect address US
2025-12-17 08:00:00 Out for Delivery US
2025-12-16 14:07:00 Arrived at USPS Facility US
2025-12-16 08:02:00 Arrived at UPS Facility Butner, NC, US
==========================================
Powered by www.track123.com
