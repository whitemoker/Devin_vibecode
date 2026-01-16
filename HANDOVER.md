# 物流状态识别项目交接文档

## 项目概述

本项目实现了基于多LLM集成的物流状态自动分类系统，支持一级状态（6类）和二级状态（28类）的分类。

## 核心功能

### 1. 多模型集成标注

使用4个LLM模型 × 3种Prompt策略 = 12个专家组合进行集成标注：

**模型：**
- GPT-5.2 (最佳，准确率90.7%)
- Grok-4 (准确率84.7%)
- Claude-Opus-4.5 (准确率81.3%)
- Gemini-3 (准确率55.3%，API不稳定)

**Prompt策略：**
- rule_based: 基于优先级规则的分类
- time_based: 基于物流链路时间线的分类
- evidence_based: 基于证据提取的分类

### 2. 一级分类（6类）

| 类目 | 说明 |
|------|------|
| INFO_RECEIVED | 信息已收到，未实际揽收 |
| IN_TRANSIT | 运输中（揽收、分拣、清关、航班等） |
| WAITING_DELIVERY | 待派送（派送中、可自取） |
| DELIVERED | 已签收 |
| DELIVERY_FAILED | 派送失败（有明确失败原因） |
| ABNORMAL | 异常（扣留、丢失、损坏、退回等） |

### 3. 生产级错误处理

`scripts/robust_batch_labeler.py` 实现了：
- 自定义httpx超时（connect=10s, read=45s）
- 每模型熔断器（滑动窗口20条，失败率>20%触发）
- 增量保存（每条结果立即写入文件）
- 心跳线程（每10秒输出进度）
- 错误分类（可恢复/不可恢复/解析错误）
- 优雅退出（信号处理、状态报告）

## 测试结果

基于50样本 × 4模型 × 3prompt = 600次测试（标签修正后）：

| 指标 | 结果 |
|------|------|
| 总体准确率 | **90.4%** (491/543有效预测) |
| Oracle准确率 | 96.0% (理论上限) |
| 简单多数投票 | **94.0%** (47/50) |
| 专家加权投票 | **94.0%** (47/50) |

**模型准确率：**
- GPT-5.2: **94.7%** (142/150)
- Gemini-3: **93.6%** (88/94)
- Grok-4: **89.3%** (133/149)
- Claude-Opus-4.5: **85.3%** (128/150)

**按类别准确率：**
- WAITING_DELIVERY: 100.0%
- INFO_RECEIVED: 99.0%
- DELIVERY_FAILED: 92.6%
- DELIVERED: 92.1%
- ABNORMAL: 80.7%
- IN_TRANSIT: 80.6%

> 注：2个hard case标签已修正，详见 output/ACCURACY_SUMMARY.md

## 关键发现

### Hard Cases（全体专家一致错误）

1. **GM5453527420279432**: WAITING_DELIVERY误判为DELIVERY_FAILED
   - 原因: "ATTEMPTED DELIVERY"被理解为派送失败
   - 修复: 已在prompt中添加说明，"尝试派送"不等于"派送失败"

2. **WS14532782726884605DL**: WAITING_DELIVERY误判为DELIVERED
   - 原因: "Arrived at letterbox"被理解为已签收
   - 状态: 待业务确认letterbox是否算送达

### UNKNOWN分析

- 57个UNKNOWN全部是API错误（http_error）
- 0个是模型主动说"不确定"
- 56/57来自Gemini-3（API不稳定）

## 项目结构

```
Devin_vibecode/
├── scripts/                    # 核心脚本
│   ├── robust_batch_labeler.py # 生产级批量标注器
│   ├── test_primary_classification.py # 一级分类测试
│   ├── expert_coupling_analysis.py # 专家耦合分析
│   └── ensemble_voting.py      # 集成投票策略
├── src/                        # 源代码
│   ├── ensemble_labeler.py     # 集成标注器
│   ├── llm_client.py           # LLM客户端
│   └── ...
├── resources/
│   ├── prompts/                # Prompt模板
│   │   ├── primary_*_v1.yaml   # 一级分类prompt（最新版）
│   │   └── primary_*_v0.yaml   # 一级分类prompt（旧版）
│   └── taxonomy/               # 分类树定义
│       └── taxonomy.json
├── output/                     # 输出结果
│   ├── run_ensemble_50_v1/     # 50样本测试结果
│   ├── expert_coupling_analysis.json
│   ├── ensemble_voting_results.json
│   └── hard_cases_analysis.md
├── goldenset.json              # 测试集（300单号，4082事件）
└── requirements.txt
```

## API配置

- **API Base URL**: https://routellm.abacus.ai/v1
- **API Key**: 需要从Abacus获取
- **模型ID**:
  - grok-4-0709
  - gpt-5.2
  - claude-opus-4-5-20251101
  - gemini-3-pro-preview

## 使用方法

### 运行一级分类测试

```bash
python scripts/test_primary_classification.py \
  --samples 50 \
  --models gpt-5.2 grok-4 claude-opus-4.5 gemini-3 \
  --prompts rule_based time_based evidence_based \
  --output output/test_run
```

### 运行专家耦合分析

```bash
python scripts/expert_coupling_analysis.py \
  --input output/run_ensemble_50_v1/predictions_long_merged.jsonl \
  --output output/expert_coupling_analysis.json
```

### 运行集成投票

```bash
python scripts/ensemble_voting.py \
  --input output/run_ensemble_50_v1/predictions_long_merged.jsonl \
  --output output/ensemble_voting_results.json
```

## 后续建议

1. **模型选择**: 推荐使用GPT-5.2 + Grok-4组合，去掉不稳定的Gemini-3
2. **Prompt优化**: 继续优化WAITING_DELIVERY和ABNORMAL的边界定义
3. **二级分类**: 在一级分类稳定后，开始二级分类的prompt设计
4. **Few-shot**: 可以尝试在prompt中加入典型样例提升准确率

## 联系方式

- GitHub: https://github.com/whitemoker/Devin_vibecode
- 分支: devin/1767344928-logistics-labeling
