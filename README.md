# AI知识助手 (AI Knowledge Assistant)

## 项目概述

企业级AI知识助手，采用"意图识别"与"GraphRAG"相结合的双核驱动架构，解决企业内部知识（资产、场景、热点）分散、关联性弱、检索效率低下的核心问题。

### 核心特性

- 🎯 **精准意图识别**: 基于Qwen3-32B SFT的高精度意图识别和实体抽取
- 🕸️ **知识图谱检索**: GraphRAG技术，深度挖掘资产-场景-热点之间的关联关系
- 💬 **忠实答案生成**: 基于Qwen3-14B的RAG答案生成，杜绝知识幻觉
- 📊 **数据增强工具**: 三种策略快速扩充训练数据（同义改写、实体置换、负样本生成）
- 🚀 **高性能API**: RESTful API接口，支持单个/批量查询

### 技术架构

```
用户查询
   ↓
[意图识别模块] (Qwen3-32B SFT)
   ↓
[路由控制器]
   ├─→ [OOD] → 通用对话
   └─→ [知识查询] → [GraphRAG模块]
                      ↓
                   [图数据库检索]
                      ↓
                   [上下文组装]
                      ↓
                   [答案生成] (Qwen3-14B)
                      ↓
                   返回答案
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd ai-knowledge-assistant

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件

编辑 `config/config.yaml`，设置：

```yaml
models:
  intent_recognition:
    model_path: "/path/to/qwen3-32b-sft"  # 意图识别模型路径
  
  answer_generation:
    model_path: "/path/to/qwen3-14b"  # 答案生成模型路径

graph:
  neo4j:
    uri: "bolt://localhost:7687"  # Neo4j连接地址
    user: "neo4j"
    password: "your_password"
```

### 3. 构建知识图谱

```bash
# 准备数据文件
# - data/raw/assets/assets.csv
# - data/raw/scenarios/scenarios.csv
# - data/raw/hotspots/hotspots.csv
# - data/raw/relationships/asset_scenario.csv

# 运行图谱构建
python -m src.graph_rag.graph_builder
```

### 4. 启动API服务

```bash
python -m src.api.api_server
```

服务将在 `http://localhost:8000` 启动

### 5. 测试查询

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "新员工入职场景需要哪些核心资产？"}'
```

## 项目结构

```
ai-knowledge-assistant/
├── config/                      # 配置文件
│   ├── config.yaml             # 主配置
│   └── prompt_config.yaml      # Prompt配置
├── data/                        # 数据目录
│   ├── raw/                    # 原始数据
│   │   ├── assets/            # 资产数据
│   │   ├── scenarios/         # 场景数据
│   │   ├── hotspots/          # 热点数据
│   │   └── relationships/     # 关系数据
│   └── processed/              # 处理后数据
│       ├── training/          # 训练数据
│       └── entity_catalog.json # 实体目录
├── src/                         # 源代码
│   ├── intent_recognition/     # 意图识别模块
│   │   ├── intent_classifier.py
│   │   ├── intent_config.py
│   │   └── intent_trainer.py
│   ├── graph_rag/              # GraphRAG模块
│   │   ├── graph_builder.py   # 图谱构建
│   │   └── graph_query.py     # 图谱查询
│   ├── answer_generation/      # 答案生成模块
│   │   └── answer_generator.py
│   ├── data_tools/             # 数据工具
│   │   └── data_augmentation.py
│   ├── orchestrator/           # 编排服务
│   │   └── orchestrator.py
│   └── api/                    # API服务
│       └── api_server.py
├── tests/                       # 测试代码
├── docs/                        # 文档
├── requirements.txt             # 依赖包
└── README.md                    # 本文件
```

## 核心模块说明

### 1. 意图识别模块

**文件**: `src/intent_recognition/intent_classifier.py`

使用Qwen3-32B SFT模型，识别5种意图：
- `Query_Asset`: 查询资产
- `Query_Scenario`: 查询场景
- `Query_Hotspot`: 查询热点
- `Find_Relationship`: 查找关联关系（核心）
- `OOD`: 域外问题

**使用示例**:

```python
from src.intent_recognition.intent_classifier import IntentClassifier

classifier = IntentClassifier()
result = classifier.predict("客户管理系统应用在哪些场景？")

print(f"意图: {result.intent}")
print(f"实体: {result.entities}")
```

### 2. GraphRAG模块

**文件**: `src/graph_rag/graph_query.py`

将意图和实体转换为Cypher查询，从Neo4j检索知识子图。

**知识图谱Schema**:

节点类型:
- `Asset`: 资产节点
- `Scenario`: 场景节点
- `Hotspot`: 热点节点
- `AssetUsage`: 资产应用实例（中间节点）

关系类型:
- `INCLUDES_USAGE`: 场景包含资产应用
- `IS_USED_IN`: 资产用于应用实例
- `DIRECTLY_IMPACTS`: 热点直接影响资产

**使用示例**:

```python
from src.graph_rag.graph_query import GraphQuery

query_engine = GraphQuery()
results = query_engine.query(intent_result)
context = query_engine.format_context(results, intent_result.intent)
```

### 3. 答案生成模块

**文件**: `src/answer_generation/answer_generator.py`

基于Qwen3-14B，使用GraphRAG检索到的上下文生成答案。

**特点**:
- 关闭CoT模式，直接生成答案
- 严格基于上下文，防止知识幻觉
- 针对OOD问题提供友好引导

**使用示例**:

```python
from src.answer_generation.answer_generator import AnswerGenerator

generator = AnswerGenerator()
result = generator.generate_answer(
    user_query="新员工入职需要哪些资产？",
    context=graph_context
)

print(result['answer'])
```

### 4. 数据增强工具

**文件**: `src/data_tools/data_augmentation.py`

三种数据扩充策略：

1. **同义改写**: 使用LLM生成查询的多种表达方式
2. **实体置换**: 基于实体目录批量生成训练样本
3. **负样本生成**: 系统性生成OOD和边界样本

**使用示例**:

```python
from src.data_tools.data_augmentation import DataAugmentation

augmentor = DataAugmentation()
augmented_data = augmentor.augment_dataset(
    original_samples=samples,
    entity_catalog_file="data/processed/entity_catalog.json",
    output_file="data/processed/training/train.jsonl"
)
```

### 5. 编排服务

**文件**: `src/orchestrator/orchestrator.py`

核心路由控制器，整合所有模块，实现完整的查询处理流程。

**工作流程**:
1. 意图识别
2. 路由控制（OOD vs 知识查询）
3. GraphRAG检索（如适用）
4. 答案生成
5. 返回结果

## API接口文档

### 1. 单个查询

**接口**: `POST /api/v1/query`

**请求体**:
```json
{
  "query": "新员工入职场景需要哪些核心资产？"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "query": "新员工入职场景需要哪些核心资产？",
    "answer": "根据知识库信息，新员工入职场景需要以下核心资产...",
    "intent": "Find_Relationship",
    "entities": [
      {"type": "Scenario", "value": "新员工入职"}
    ],
    "has_context": true,
    "timing": {
      "intent_recognition": 0.5,
      "graph_query": 0.2,
      "answer_generation": 1.2,
      "total": 1.9
    }
  }
}
```

### 2. 批量查询

**接口**: `POST /api/v1/batch_query`

**请求体**:
```json
{
  "queries": [
    "查询1",
    "查询2"
  ]
}
```

### 3. 健康检查

**接口**: `GET /health`

### 4. 服务统计

**接口**: `GET /api/v1/stats`

## 数据准备

### 资产数据格式 (assets.csv)

```csv
asset_id,name,description,owner,type,version,status
A001,HR系统,人力资源管理系统,张三,系统,v2.0,已上线
A002,OA系统,办公自动化系统,李四,系统,v3.1,已上线
```

### 场景数据格式 (scenarios.csv)

```csv
scenario_id,name,description,business_domain,status
S001,新员工入职,新员工入职全流程,人力资源,已上线
S002,月度数据上报,月度业务数据上报流程,财务管理,已上线
```

### 热点数据格式 (hotspots.csv)

```csv
hotspot_id,title,summary,publish_date,source,category
H001,数据安全法更新,最新数据安全法规要求...,2024-01-01,官方,政策法规
```

### 关系数据格式 (asset_scenario.csv)

```csv
asset_id,scenario_id,role,status,description
A001,S001,核心依赖,已上线,新员工入职的核心系统
A002,S001,辅助支持,已上线,提供办公权限
```

## 模型训练

### 意图识别模型训练

```bash
# 1. 准备训练数据（使用数据增强）
python -m src.data_tools.data_augmentation

# 2. 训练模型
python -m src.intent_recognition.intent_trainer \
  --train_file data/processed/training/train.jsonl \
  --output_dir models/intent_recognition_sft \
  --base_model /path/to/qwen3-32b
```

## 性能优化建议

1. **模型量化**: 使用QLoRA (4-bit)降低显存消耗
2. **批量推理**: 使用vLLM提升推理吞吐量
3. **缓存策略**: 对高频查询结果进行缓存
4. **图查询优化**: 建立合适的索引，优化Cypher查询

## 注意事项

1. **关闭CoT模式**: 两个模型都关闭思考链模式，确保输出稳定可控
2. **知识忠实度**: 14B模型严格基于GraphRAG上下文生成答案
3. **数据质量**: 高质量的标注数据是SFT成功的关键
4. **M:M关系**: 使用AssetUsage中间节点处理资产-场景多对多关系

## 故障排查

### 常见问题

1. **Neo4j连接失败**
   - 检查Neo4j是否启动
   - 验证config.yaml中的连接配置

2. **模型加载失败**
   - 确认模型路径正确
   - 检查显存是否充足

3. **JSON解析错误**
   - 检查SFT模型输出格式
   - 可能需要重新训练或调整temperature

## 后续优化方向

- [ ] 支持流式输出
- [ ] 集成向量数据库实现混合检索
- [ ] 添加用户反馈回流机制
- [ ] 多轮对话支持
- [ ] 前端Web界面

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

[指定许可证]

## 联系方式

- 项目负责人: [姓名]
- Email: [邮箱]
- 技术支持: [联系方式]

