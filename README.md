# 物流状态自动标注系统 (Logistics Status Auto-Labeling System)

基于多LLM集成的物流轨迹状态自动分类系统。

## 项目概述

本项目使用4个LLM模型 × 3种Prompt策略 = 12个专家组合进行集成标注，实现物流状态的自动分类。

## 特性

- **多模型集成**: 支持GPT-5.2、Grok-4、Claude-Opus-4.5、Gemini-3等模型
- **多Prompt策略**: rule_based、time_based、evidence_based三种分类视角
- **集成投票**: 简单多数投票、加权投票、置信度加权投票
- **生产级错误处理**: 熔断器、增量保存、心跳监控、优雅退出
- **专家耦合分析**: 识别冗余专家组合，优化模型选择

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
│   ├── hierarchical_labeler.py # 分层标注器
│   └── anonymizer.py           # 人名脱敏
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
├── HANDOVER.md                 # 交接文档
└── requirements.txt
```

## 安装

```bash
pip install -r requirements.txt
```

## 配置API Key

```bash
export ABACUS_API_KEY='your-abacus-key'
```

## 一级分类（6类）

| 类目 | 说明 |
|------|------|
| INFO_RECEIVED | 信息已收到，未实际揽收 |
| IN_TRANSIT | 运输中（揽收、分拣、清关、航班等） |
| WAITING_DELIVERY | 待派送（派送中、可自取） |
| DELIVERED | 已签收 |
| DELIVERY_FAILED | 派送失败（有明确失败原因） |
| ABNORMAL | 异常（扣留、丢失、损坏、退回等） |

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

## 测试结果

基于50样本 × 4模型 × 3prompt = 600次测试：

| 指标 | 结果 |
|------|------|
| 总体准确率 | 78.0% |
| Oracle准确率 | 94.0% |
| 简单多数投票 | 90.0% |
| 加权投票 | 90.0% |

**模型准确率排名：**
1. GPT-5.2: 90.7%
2. Grok-4: 84.7%
3. Claude-Opus-4.5: 81.3%
4. Gemini-3: 55.3% (API不稳定)

## API配置

- **API Base URL**: https://routellm.abacus.ai/v1
- **模型ID**:
  - grok-4-0709
  - gpt-5.2
  - claude-opus-4-5-20251101
  - gemini-3-pro-preview

## 详细文档

请参阅 [HANDOVER.md](HANDOVER.md) 获取完整的项目交接文档。
