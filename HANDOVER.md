# 物流状态标注项目交接文档

## 项目概述

本项目是一个基于LLM的物流轨迹状态自动标注系统，用于将物流轨迹文本分类到28个子状态（6个主状态）。

## 项目位置

- **本地路径**: `/home/ubuntu/repos/logistics-labeling`
- **GitHub仓库**: https://github.com/whitemoker/Devin_vibecode
- **分支**: `devin/1767344928-logistics-labeling`

## API密钥

用户提供了以下API密钥（请从环境变量或用户处获取）：

- **Abacus.ai API Key**: 用于GPT-5.2, Grok-4等模型
  - Base URL: `https://routellm.abacus.ai/v1`
  - 支持模型: `gpt-5.2`, `grok-4-0709`, `claude-sonnet-4-20250514`
  
- **Kimi (Moonshot) API Key**: 用于Kimi模型
  - Base URL: `https://api.moonshot.cn/v1`
  - 模型: `moonshot-v1-128k`

## 项目结构

```
Devin_vibecode/
├── src/                          # 核心代码
│   ├── llm_client.py            # LLM客户端（Moonshot, Abacus）
│   ├── simple_labeler.py        # 单阶段28分类标注器
│   ├── hierarchical_labeler.py  # 分层分类标注器（两阶段）
│   ├── ensemble_labeler.py      # 多角度*多模型集成标注器 [NEW]
│   └── anonymizer.py            # 多语言NER人名脱敏
├── resources/
│   ├── taxonomy/
│   │   └── taxonomy.json        # 分类树（6主状态，28子状态）
│   ├── datasets/
│   │   ├── fewshot.json         # Few-shot样本（28条，每类1条）
│   │   └── test.json            # 测试集（56条，每类2条）
│   └── prompts/
│       ├── prompt_template.yaml # 单阶段prompt模板
│       ├── main_stage.yaml      # 分层Stage1模板（主状态）
│       ├── sub_stage.yaml       # 分层Stage2模板（子状态）
│       ├── rule_based.yaml      # 规则优先角度模板 [NEW]
│       ├── time_based.yaml      # 时间优先角度模板 [NEW]
│       └── evidence_based.yaml  # 证据优先角度模板 [NEW]
├── scripts/
│   ├── evaluate_all_models.py   # 综合评估脚本
│   ├── evaluate_models.py       # 单阶段评估脚本
│   ├── evaluate_hierarchical.py # 分层评估脚本
│   ├── evaluate_ensemble.py     # 集成标注评估脚本 [NEW]
│   └── generate_error_analysis.py # 错误分析报告生成
├── output/                       # 评估结果输出
│   ├── full_comparison_report.md # 完整对比报告（含混淆矩阵）
│   ├── *_single_results.json    # 单阶段评估结果
│   └── *_hierarchical_results.json # 分层评估结果
└── tests/                        # 测试代码
    └── fixtures/
        └── test_data_with_names.json # 脱敏测试数据
```

## 分类体系

6个主状态，28个子状态：

| 主状态 | 子状态数量 | 说明 |
|--------|-----------|------|
| IN_TRANSIT | 8 | 运输中（揽收、出口清关、航班、到达目的国等） |
| OUT_FOR_DELIVERY | 3 | 派送中（派送中、派送失败、重新派送） |
| DELIVERED | 4 | 已签收（本人签收、代签、自提、拒收后退回） |
| DELIVERY_FAILED | 3 | 投递失败（地址错误、收件人不在、拒收） |
| RETURNED | 5 | 退回（退回中、已退回、退回失败等） |
| ABNORMAL | 5 | 异常（海关扣留、包裹损坏、丢失等） |

## 当前评估结果

### 单阶段（28分类）准确率

| 模型 | 子状态准确率 | 主状态准确率 |
|------|-------------|-------------|
| GPT-5.2 | 75.00% (42/56) | 85.71% |
| Grok-4 | 76.79% (43/56) | 87.50% |
| Kimi | 53.57% (30/56) | 67.86% |
| Claude-4.5 | 73.21% (41/56) | 85.71% |
| GPT-5 | 73.21% (41/56) | 85.71% |

### 分层分类准确率

| 模型 | 子状态准确率 | 主状态准确率 |
|------|-------------|-------------|
| GPT-5.2 | 75.00% (42/56) | 85.71% |
| Grok-4 | 73.21% (41/56) | 85.71% |
| Kimi | 42.86% (24/56) | 57.14% |

### 错误共性分析

- **所有模型都正确**: 26/56 (46.4%)
- **所有模型都错误（共性错误）**: 7/56 (12.5%)
- **仅部分模型错误（投票可解决）**: 23/56 (41.1%)
- **投票有效性**: 76.7%的错误可通过多模型投票解决

## 关键发现

1. **单阶段 vs 分层**: 对于强模型（GPT-5.2），两种方案效果相当；对于弱模型（Kimi），分层方案反而降低准确率（级联错误）

2. **最佳模型**: Grok-4在单阶段表现最好（76.79%）

3. **多模型投票**: 建议采用GPT-5.2 + Grok-4双模型投票策略，可解决76.7%的错误

4. **共性错误**: 7个样本所有模型都判断错误，可能需要业务层面的规则澄清

## 运行评估

```bash
# 设置环境变量
export ABACUS_API_KEY="your_abacus_key"
export KIMI_API_KEY="your_kimi_key"

# 运行综合评估
cd /home/ubuntu/repos/logistics-labeling
python scripts/evaluate_all_models.py

# 仅生成报告（从已有JSON结果）
python scripts/generate_error_analysis.py
```

## 多角度*多模型集成标注 [NEW]

### 设计思路

基于多prompt方法的研究，实现了多角度*多模型集成标注框架：

1. **多模型**: 支持GPT-5.2、Grok-4、Kimi等多个LLM模型
2. **多角度**: 支持不同的prompt视角（规则优先、时间优先、证据优先）
3. **加权投票**: 使用 `model_weight * prompt_weight * f(confidence)` 进行加权投票
4. **人工复核标记**: 当模型分歧大或置信度低时，自动标记需要人工复核

### Prompt角度

| 角度 | 文件 | 说明 |
|------|------|------|
| rule_based | rule_based.yaml | 严格按优先级规则判断（签收>异常>失败>派送>运输>预报） |
| time_based | time_based.yaml | 仅关注最新1-3条事件判断当前状态 |
| evidence_based | evidence_based.yaml | 先提取关键证据，再基于证据分类 |
| hierarchical | main_stage.yaml + sub_stage.yaml | 两阶段分类（主状态→子状态） |

### 使用方法

```bash
# 设置环境变量
export ABACUS_API_KEY="your_abacus_key"
export KIMI_API_KEY="your_kimi_key"

# 运行集成标注评估
python scripts/evaluate_ensemble.py --models gpt-5.2 grok-4 --angles rule_based time_based evidence_based

# Dry-run模式（无需API Key）
python scripts/evaluate_ensemble.py --dry-run --limit 5
```

### 核心类

- `EnsembleLabeler`: 集成标注器，管理多模型多角度的预测和投票
- `PromptVariant`: Prompt角度配置
- `ModelConfig`: 模型配置
- `EnsembleResult`: 集成结果，包含投票详情和审计轨迹

## 待完成任务

1. ~~**多模型投票实现**~~: 已完成，见 `src/ensemble_labeler.py`
2. **200k数据标注**: 使用最佳方案进行大规模标注
3. **共性错误分析**: 与业务方确认7个共性错误样本的正确标签
4. **Prompt优化**: 根据bad case分析优化prompt
5. **集成标注评估**: 等待新API Key后运行评估，对比单模型效果

## 用户偏好

- 报告使用Markdown格式（.md），不要用txt
- 代码结构要规范，相关文件放在一起
- 改完代码及时推送到GitHub
- 测试要自动运行，不要问用户
- Bad case分析要包含每个模型的预测结果

## 联系方式

用户GitHub: @sunjun-ai (whitemoker)
用户邮箱: sunjun@lingxing.com
