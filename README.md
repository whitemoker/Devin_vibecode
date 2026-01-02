# 物流状态自动标注系统 (Logistics Status Auto-Labeling System)

企业级LLM自动标注Pipeline，用于物流轨迹状态识别。

## 特性

- **多模型投票**: 支持多个LLM模型（OpenAI GPT-4o、Claude等）进行投票，提高标注准确性
- **检索式Few-shot**: 根据待标注轨迹动态检索最相似的典型案例作为示例
- **规则校验**: 业务规则兜底，防止明显错误（如出现"Delivered"却标注为运输中）
- **不确定性标记**: 低置信度或模型分歧的样本自动标记为需人工复核
- **断点续跑**: 支持大批量数据的checkpoint机制
- **可审计输出**: 每条标注都包含evidence引用和解释

## 项目结构

```
logistics-labeling/
├── config.py              # 配置管理
├── taxonomy_manager.py    # 分类树管理
├── preprocessor.py        # 数据预处理（清洗、标准化）
├── few_shot_retriever.py  # Few-shot样例检索
├── llm_client.py          # LLM API客户端
├── labeler.py             # 核心标注模块
├── voting.py              # 投票/共识机制
├── pipeline.py            # 主Pipeline编排
├── evaluator.py           # 评估模块
├── demo.py                # 演示脚本
├── run_labeling.py        # 批量标注脚本
├── taxonomy.json          # 分类树定义
├── sample_cases.json      # 典型案例库
└── requirements.txt       # 依赖
```

## 安装

```bash
pip install -r requirements.txt
```

## 配置API Key

设置环境变量：

```bash
# OpenAI
export OPENAI_API_KEY='your-openai-key'

# Anthropic (可选，用于多模型投票)
export ANTHROPIC_API_KEY='your-anthropic-key'
```

## 使用方法

### 1. 运行Demo

```bash
# 单模型测试
python demo.py --mode single

# 多模型投票测试
python demo.py --mode multi

# 评估演示
python demo.py --mode eval
```

### 2. 批量标注

准备输入数据（JSONL格式）：
```json
{"id": "1", "trace": "物流轨迹文本..."}
{"id": "2", "trace": "物流轨迹文本..."}
```

运行标注：
```bash
# 单模型标注
python run_labeling.py --input data.jsonl --model gpt-4o-mini

# 多模型投票标注
python run_labeling.py --input data.jsonl --model all --voting weighted_majority

# 从checkpoint恢复
python run_labeling.py --input data.jsonl --checkpoint my_job --resume

# 标注并评估
python run_labeling.py --input data.jsonl --gold-labels labels.csv
```

### 3. 在代码中使用

```python
from config import PipelineConfig, ModelConfig
from pipeline import LabelingPipeline, LabelingTask

# 配置
config = PipelineConfig(
    models=[
        ModelConfig(
            name="gpt-4o-mini",
            provider="openai",
            model_id="gpt-4o-mini",
            api_key_env="OPENAI_API_KEY",
            temperature=0.0,
            weight=1.0
        ),
    ],
    num_few_shot_examples=3,
    voting_strategy="weighted_majority",
    min_confidence_threshold=0.6,
)

# 初始化Pipeline
pipeline = LabelingPipeline(config, base_dir="/path/to/project")

# 标注单条数据
task = LabelingTask(id="1", trace="物流轨迹文本...")
result = pipeline.label_single(task)

print(f"预测: {result.sub_status}")
print(f"置信度: {result.confidence}")
print(f"解释: {result.explanation}")
print(f"需人工复核: {result.needs_human_review}")
```

## 分类树

系统支持6个主状态、28个子状态：

| 主状态 | 子状态数 | 说明 |
|--------|----------|------|
| In transit/运输途中 | 8 | 包括分拣中心、清关、航空运输等 |
| Out for delivery/派送中 | 3 | 派送途中、自提点等待、二次派送 |
| Delivered/签收 | 4 | 正常签收、自提签收、本人签收、门廊签收 |
| Failed attempt/投递失败 | 4 | 地址问题、不在家、联系不上、其他原因 |
| Exception/可能异常 | 8 | 无人领取、海关扣留、损坏丢失、退件等 |
| Info received/等待揽收 | 1 | 等待揽收 |

## 输出格式

每条标注结果包含：

```json
{
    "task_id": "1",
    "trace": "原始轨迹文本",
    "main_status": "In transit/运输途中",
    "sub_status": "IN_TRANSIT_03",
    "confidence": 0.85,
    "evidence": ["Clearance processing completed - Import"],
    "explanation": "轨迹中出现清关完成的信息",
    "needs_human_review": false,
    "review_reason": "",
    "voting_details": {...},
    "predictions": [
        {"model": "gpt-4o-mini", "sub_status": "IN_TRANSIT_03", "confidence": 0.85}
    ],
    "timestamp": "2025-12-30T18:00:00"
}
```

## 质量控制

1. **规则校验**: 自动检测明显矛盾（如轨迹包含"delivered"但标注为运输中）
2. **置信度阈值**: 低于阈值的样本标记为需人工复核
3. **投票分歧**: 多模型投票分歧大的样本标记为需人工复核
4. **NEEDS_HUMAN标记**: 不确定的样本不强行分类，而是标记出来

## 评估

```python
from evaluator import Evaluator

evaluator = Evaluator()
result = evaluator.evaluate(predictions)

print(result.summary)
# 输出: 准确率、Macro F1、每类P/R/F1、混淆矩阵等
```
