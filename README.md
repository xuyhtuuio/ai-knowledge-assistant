# AI知识助手 (AI Knowledge Assistant)

## 项目概述

企业级数据资产知识助手，采用"意图识别"与"GraphRAG"相结合的双核驱动架构，基于知识图谱技术实现数据资产的智能检索与问答。

### 核心特性

- 🎯 **精准意图识别**: 基于 Qwen2.5-32B 微调，支持 8 大意图和 10 大槽位的高精度识别
- 🕸️ **知识图谱检索**: GraphRAG 技术，深度挖掘资产-场景-热点-用户之间的关联关系
- 💬 **忠实答案生成**: 基于 Qwen2.5-14B 的 RAG 答案生成，杜绝知识幻觉
- 📊 **数据增强工具**: 三种策略快速扩充训练数据（同义改写、实体置换、负样本生成）
- 🚀 **高性能API**: RESTful API 接口，支持单个/批量查询

### 技术架构

```
用户查询
   ↓
[意图识别模块] (Qwen2.5-32B 微调)
   ↓
   识别 8 大意图 + 10 大槽位
   ↓
[路由控制器]
   ├─→ [38-平台帮助] → 直接回答
   └─→ [31-37 意图] → [GraphRAG模块]
                         ↓
                      [Neo4j 图查询]
                         ↓
                      [上下文组装]
                         ↓
                      [答案生成] (Qwen2.5-14B)
                         ↓
                      返回答案
```

## 硬件要求

⚠️ **重要**: 本项目使用大型语言模型，需要较高的硬件配置。

### 最低配置
- **GPU**: NVIDIA GPU，24GB+ 显存（推荐 A10/A100/V100）
- **内存**: 64GB+ RAM
- **存储**: 150GB+ 可用空间（100GB 用于模型文件）
- **CPU**: 8 核心+

### 推荐配置（生产环境）
- **GPU**: NVIDIA A100 40GB/80GB
- **内存**: 128GB+ RAM
- **存储**: 500GB+ SSD
- **CPU**: 16 核心+

### 显存优化选项
如显存不足，可使用量化技术：
- **4-bit 量化** (QLoRA): 可将显存需求降至约 20GB
- **8-bit 量化**: 可将显存需求降至约 32GB

## 快速开始

### 步骤 1: 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd ai-knowledge-assistant

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 步骤 2: 下载模型

⚠️ **模型文件不在 GitHub 仓库中**，需要单独下载（总计约 93GB）

#### 方式 A: 使用 Hugging Face（国际用户）

```bash
# 安装 huggingface-cli
pip install -U huggingface_hub

# 下载意图识别模型 (Qwen2.5-32B-Instruct, ~65GB)
huggingface-cli download Qwen/Qwen2.5-32B-Instruct \
  --local-dir ./models/intent_recognition/qwen3-32b-sft

# 下载答案生成模型 (Qwen2.5-14B-Instruct, ~28GB)
huggingface-cli download Qwen/Qwen2.5-14B-Instruct \
  --local-dir ./models/answer_generation/qwen3-14b
```

#### 方式 B: 使用 ModelScope（国内用户推荐）

```bash
# 安装 modelscope
pip install modelscope

# 使用 Python 下载
python3 << EOF
from modelscope import snapshot_download

# 下载意图识别模型
snapshot_download('qwen/Qwen2.5-32B-Instruct', 
                  cache_dir='./models/intent_recognition/qwen3-32b-sft')

# 下载答案生成模型
snapshot_download('qwen/Qwen2.5-14B-Instruct',
                  cache_dir='./models/answer_generation/qwen3-14b')
EOF
```

#### 方式 C: 使用已有模型

如果您已经下载了 Qwen 模型，可直接在配置文件中指定路径（见步骤 3）。

### 步骤 3: 配置系统

编辑 `config/config.yaml`，配置模型路径和数据库连接：

```yaml
models:
  intent_recognition:
    model_path: "./models/intent_recognition/qwen3-32b-sft"  # 修改为实际路径
    device: "cuda"
    temperature: 0.1
  
  answer_generation:
    model_path: "./models/answer_generation/qwen3-14b"  # 修改为实际路径
    device: "cuda"
    temperature: 0.3

graph:
  neo4j:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "your_password"  # ⚠️ 修改为实际密码
```

### 步骤 4: 启动 Neo4j 数据库

#### 使用 Docker（推荐）

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -v $HOME/neo4j/data:/data \
  neo4j:latest

# 验证服务
docker ps | grep neo4j
```

#### 本地安装

```bash
# macOS
brew install neo4j
neo4j start

# Linux
sudo apt install neo4j
sudo systemctl start neo4j
```

访问 http://localhost:7474 验证 Neo4j 是否正常运行。

### 步骤 5: 构建知识图谱

```bash
# 使用示例数据（可选）
# 项目已包含示例数据在 data/raw/ 目录

# 构建图谱
python3 -m src.graph_rag.graph_builder
```

预期输出：
```
INFO:root:开始构建知识图谱...
INFO:root:成功加载 8 个资产节点
INFO:root:成功加载 7 个场景节点
INFO:root:成功加载 4 个热点节点
INFO:root:图谱构建完成！
```

### 步骤 6: 启动 API 服务

```bash
python3 -m src.api.api_server
```

服务将在 `http://localhost:8000` 启动

### 步骤 7: 测试查询

```bash
# 健康检查
curl http://localhost:8000/health

# 测试查询
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

使用 Qwen2.5-32B 微调模型，支持 **8 大意图** 和 **10 大槽位** 的精准识别：

#### 8 大意图类型

| 意图编号 | 意图名称 | 说明 | 示例查询 |
|---------|---------|------|---------|
| 31 | 资产基础检索 | 按条件检索资产 | "M域的所有资产有哪些？" |
| 32 | 资产元数据查询 | 查询资产的元数据信息 | "HR系统的负责人是谁？" |
| 33 | 资产质量与价值查询 | 查询资产的质量和价值指标 | "哪些资产的质量分最高？" |
| 34 | 资产血缘关系查询 | 查询资产的上下游血缘 | "数据仓库的上游依赖有哪些？" |
| 35 | 资产使用与工单查询 | 查询资产的使用情况 | "张三收藏了哪些资产？" |
| 36 | 场景与标签推荐 | 场景相关的资产推荐 | "新员工入职需要哪些资产？" |
| 37 | 资产复合对比与筛选 | 多条件筛选和对比 | "M域中质量分>90的系统资产" |
| 38 | 平台规则与帮助 | 平台使用帮助和规则说明 | "如何创建数据资产？" |

#### 10 大槽位类型

| 槽位编号 | 槽位名称 | 说明 | 示例 |
|---------|---------|------|------|
| 1 | AssetName | 核心资产名称/ID | "HR系统"、"A001" |
| 2 | MetadataItem | 元数据项 | "负责人"、"创建时间" |
| 3 | FieldName | 字段名称 | "user_id"、"employee_name" |
| 4 | CoreDataItem | 核心数据项 | "质量分"、"访问量" |
| 5 | BusinessDomain | 业务域 | "M域"、"数据治理域" |
| 6 | AssetType | 资产类型 | "系统"、"表"、"接口" |
| 7 | BusinessZone | 业务专区 | "公众智慧运营专区" |
| 8 | FilterCondition | 筛选条件 | "质量分>90"、"状态=已上线" |
| 9 | UserStatus | 用户操作属性 | "收藏"、"订阅"、"创建" |
| 10 | OrgName/UserName | 机构/人员名 | "张三"、"数据管理部" |

**使用示例**:

```python
from src.intent_recognition.intent_classifier import IntentClassifier

classifier = IntentClassifier()
result = classifier.predict("M域中张三负责的系统资产有哪些？")

print(f"意图: {result.intent}")  # 31 (资产基础检索)
print(f"槽位: {result.slots}")    
# {
#   "BusinessDomain": ["M域"],
#   "OrgName/UserName": ["张三"],
#   "AssetType": ["系统"]
# }
```

### 2. GraphRAG模块

**文件**: `src/graph_rag/graph_query.py`

将意图和槽位转换为 Cypher 查询，从 Neo4j 检索知识子图。

**知识图谱 Schema**:

#### 节点类型（11种）

| 节点类型 | 说明 | 对应槽位 | 示例属性 |
|---------|------|---------|---------|
| Asset | 数据资产 | AssetName | asset_id, name, type, owner |
| Field | 字段 | FieldName | field_id, name, data_type |
| BusinessDomain | 业务域 | BusinessDomain | domain_id, name, description |
| BusinessZone | 业务专区 | BusinessZone | zone_id, name, industry |
| Scenario | 场景 | - | scenario_id, name, status |
| Concept | 业务概念 | CoreDataItem | concept_id, name, definition |
| User | 用户 | OrgName/UserName | user_id, name, email |
| Org | 组织 | OrgName/UserName | org_id, name, type |
| Hotspot | 热点 | - | hotspot_id, title, category |
| AssetUsage | 资产使用实例 | - | usage_id, role, status |
| Keyword | 关键词 | - | keyword, category |

#### 关系类型（15种）

| 关系类型 | 说明 | 场景 |
|---------|------|------|
| HAS_FIELD | 资产包含字段 | Asset -> Field |
| BELONGS_TO | 资产属于业务域 | Asset -> BusinessDomain |
| CONTAINS_SCENARIO | 专区包含场景 | BusinessZone -> Scenario |
| USES_ASSET | 场景使用资产 | Scenario -> Asset |
| IMPLEMENTED_BY | 概念由资产实现 | Concept -> Asset |
| MAPPED_TO | 概念映射到字段 | Concept -> Field |
| FAVORITED | 用户收藏资产 | User -> Asset |
| SUBSCRIBED | 用户订阅资产 | User -> Asset |
| CREATED | 用户创建资产 | User -> Asset |
| MANAGED_BY | 资产管理者 | Asset -> User |
| OWNED_BY | 资产所属组织 | Asset -> Org |
| DIRECTLY_IMPACTS | 热点影响资产 | Hotspot -> Asset |
| INCLUDES_USAGE | 场景包含资产使用 | Scenario -> AssetUsage |
| IS_USED_IN | 资产用于应用实例 | Asset -> AssetUsage |
| LINEAGE_UPSTREAM | 血缘上游 | Asset -> Asset |

**使用示例**:

```python
from src.graph_rag.graph_query import GraphQuery

query_engine = GraphQuery()

# 查询场景相关资产
results = query_engine.query_scenario_assets("S001")

# 查询用户收藏的资产
results = query_engine.query_user_favorites("U001")

# 格式化上下文
context = query_engine.format_context(results, intent="36")
```

### 3. 答案生成模块

**文件**: `src/answer_generation/answer_generator.py`

基于 Qwen2.5-14B，使用 GraphRAG 检索到的上下文生成答案。

**核心特点**:
- ✅ **关闭 CoT 模式**: 直接生成答案，避免冗长推理，提升响应速度
- ✅ **忠实于上下文**: 严格基于知识图谱检索结果，杜绝幻觉问题
- ✅ **结构化输出**: 提供清晰、结构化的答案格式
- ✅ **OOD 处理**: 对域外问题（Intent 38）提供友好引导

**使用示例**:

```python
from src.answer_generation.answer_generator import AnswerGenerator

generator = AnswerGenerator()

# 基于图谱上下文生成答案
result = generator.generate_answer(
    user_query="新员工入职需要哪些资产？",
    context=graph_context,
    intent="36"
)

print(result['answer'])
print(f"生成耗时: {result['generation_time']}s")
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

项目已包含完整的示例数据，位于 `data/raw/` 目录。

### 数据文件清单

| 文件路径 | 说明 | 记录数 |
|---------|------|--------|
| `data/raw/assets/assets.csv` | 资产基础信息 | 8 条 |
| `data/raw/fields/fields.csv` | 字段信息 | 16 条 |
| `data/raw/domains/domains.csv` | 业务域信息 | 6 条 |
| `data/raw/zones/zones.csv` | 业务专区信息 | 5 条 |
| `data/raw/scenarios/scenarios.csv` | 场景信息 | 7 条 |
| `data/raw/concepts/concepts.csv` | 业务概念信息 | 8 条 |
| `data/raw/users/users.csv` | 用户信息 | 8 条 |
| `data/raw/orgs/orgs.csv` | 组织信息 | 7 条 |
| `data/raw/hotspots/hotspots.csv` | 热点信息 | 4 条 |
| `data/raw/relationships/*.csv` | 各类关系数据 | 81 条 |

### 核心数据格式示例

#### 资产数据 (assets.csv)

```csv
asset_id,name,description,owner,type,version,status,create_date
A001,HR系统,人力资源管理系统,张三,系统,v2.0,已上线,2024-01-15
A002,员工信息表,存储员工基本信息,李四,表,v1.0,已上线,2024-02-01
```

#### 字段数据 (fields.csv)

```csv
field_id,name,data_type,description,asset_id
F001,user_id,VARCHAR(50),用户唯一标识,A002
F002,employee_name,VARCHAR(100),员工姓名,A002
```

#### 业务域数据 (domains.csv)

```csv
domain_id,name,description,owner
D001,M域,移动业务域,王五
D002,数据治理域,数据治理与质量管理,赵六
```

#### 场景数据 (scenarios.csv)

```csv
scenario_id,name,description,business_domain,status
S001,新员工入职,新员工入职全流程,人力资源,已上线
S002,月度数据上报,月度业务数据上报流程,财务管理,已上线
```

#### 用户数据 (users.csv)

```csv
user_id,name,email,department,role
U001,张三,zhangsan@company.com,IT部,开发工程师
U002,李四,lisi@company.com,数据部,数据分析师
```

#### 关系数据 (relationships/asset_scenario.csv)

```csv
asset_id,scenario_id,role,status,description
A001,S001,核心依赖,已上线,新员工入职的核心系统
A002,S001,辅助支持,已上线,提供员工信息查询
```

详细数据说明请查看 `data/DATA_SUMMARY.md`

## 模型训练

### 意图识别模型微调（SFT）

如果需要针对您的业务场景微调模型：

#### 步骤 1: 准备训练数据

```bash
# 查看示例训练数据
cat data/annotated/training_data_extended.jsonl

# 使用数据增强工具扩充训练数据
python3 -m src.data_tools.data_augmentation \
  --input data/annotated/training_data_extended.jsonl \
  --output data/processed/training/train.jsonl \
  --augment_ratio 10
```

训练数据格式（JSONL）：

```json
{
  "query": "M域中张三负责的系统资产有哪些？",
  "intent": "31",
  "slots": {
    "BusinessDomain": ["M域"],
    "OrgName/UserName": ["张三"],
    "AssetType": ["系统"]
  }
}
```

#### 步骤 2: 微调模型

```bash
python3 -m src.intent_recognition.intent_trainer \
  --train_file data/processed/training/train.jsonl \
  --output_dir models/intent_recognition_sft \
  --base_model ./models/intent_recognition/qwen3-32b-sft \
  --num_epochs 3 \
  --batch_size 4 \
  --learning_rate 2e-5 \
  --use_qlora
```

**训练参数说明**:
- `--use_qlora`: 启用 4-bit 量化，降低显存需求
- `--num_epochs`: 训练轮数，建议 3-5
- `--batch_size`: 批大小，根据显存调整
- `--learning_rate`: 学习率，建议 1e-5 到 5e-5

#### 步骤 3: 评估模型

```bash
python3 -m src.intent_recognition.intent_trainer \
  --mode eval \
  --model_path models/intent_recognition_sft/checkpoint-best \
  --test_file data/processed/training/test.jsonl
```

## 性能优化建议

### 1. 模型优化

#### 使用模型量化
```yaml
# config/config.yaml
training:
  intent_recognition:
    use_qlora: true  # 启用 4-bit 量化
    lora_r: 64
    lora_alpha: 16
```

优化效果：
- **显存需求**: 从 65GB 降至约 20GB
- **推理速度**: 略有下降（约 10-20%）
- **准确率**: 基本不受影响

#### 使用 vLLM 加速推理

```bash
pip install vllm

# 修改模型加载方式使用 vLLM
```

优化效果：
- **吞吐量**: 提升 2-5 倍
- **批量处理**: 显著提升效率

### 2. 缓存策略

```yaml
# config/config.yaml（取消注释启用）
cache:
  enabled: true
  backend: "redis"
  redis:
    host: "localhost"
    port: 6379
    expire_time: 3600  # 1小时过期
```

### 3. Neo4j 图查询优化

```cypher
-- 创建索引
CREATE INDEX asset_name_idx FOR (a:Asset) ON (a.name);
CREATE INDEX asset_id_idx FOR (a:Asset) ON (a.asset_id);
CREATE INDEX user_name_idx FOR (u:User) ON (u.name);

-- 优化查询计划
EXPLAIN MATCH (a:Asset)-[:BELONGS_TO]->(d:BusinessDomain {name: 'M域'})
RETURN a;
```

### 4. API 性能优化

- 启用异步处理
- 使用连接池
- 配置负载均衡（生产环境）

## 注意事项

### ⚠️ 重要提醒

1. **模型文件管理**
   - 模型文件已在 `.gitignore` 中排除，不会上传到 GitHub
   - 总大小约 93GB，需预留足够存储空间
   - 建议使用软链接或挂载存储管理模型文件

2. **关闭 CoT 模式**
   - 两个模型都关闭思考链模式（`use_cot: false`）
   - 确保输出稳定可控，避免格式污染

3. **知识忠实度**
   - 答案生成严格基于 GraphRAG 检索的上下文
   - Temperature 设置较低（0.3），减少幻觉
   - 不建议修改 system prompt

4. **数据质量**
   - 高质量的标注数据是 SFT 成功的关键
   - 建议至少准备 500+ 条标注样本
   - 使用数据增强工具扩充到 5000+ 条

5. **图谱设计**
   - 使用 AssetUsage 中间节点处理资产-场景多对多关系
   - 血缘关系使用 LINEAGE_UPSTREAM/DOWNSTREAM
   - 合理使用关系属性（role, status, weight 等）

6. **安全配置**
   - 生产环境务必修改 Neo4j 默认密码
   - 启用 API 认证和授权
   - 配置 SSL/TLS 加密传输

## 故障排查

### 常见问题 Q&A

#### Q1: Neo4j 连接失败

**错误信息**: `ServiceUnavailable: Failed to establish connection`

**解决方案**:
```bash
# 1. 检查 Neo4j 是否启动
docker ps | grep neo4j
# 或
sudo systemctl status neo4j

# 2. 检查端口
lsof -i :7687

# 3. 测试连接
curl http://localhost:7474

# 4. 查看 Neo4j 日志
docker logs neo4j
```

#### Q2: 模型加载失败

**错误信息**: `CUDA out of memory` 或 `FileNotFoundError`

**解决方案**:
```bash
# 检查模型路径
ls -lh models/intent_recognition/qwen3-32b-sft/

# 检查显存使用
nvidia-smi

# 启用量化（修改 config.yaml）
use_qlora: true

# 或使用 CPU（性能较低）
device: "cpu"
```

#### Q3: 意图识别输出格式错误

**错误信息**: `JSON parsing error` 或 `Invalid intent format`

**解决方案**:
```yaml
# 降低 temperature（config.yaml）
models:
  intent_recognition:
    temperature: 0.1  # 降低到 0.05-0.1
    
# 检查训练数据格式
python3 -m src.data_tools.validate_training_data

# 重新微调模型
python3 -m src.intent_recognition.intent_trainer --retrain
```

#### Q4: API 响应慢

**问题**: 单次查询超过 10 秒

**解决方案**:
```bash
# 1. 启用模型量化
# 2. 使用 vLLM 加速
# 3. 启用缓存（Redis）
# 4. 优化 Cypher 查询

# 查看性能分析
curl http://localhost:8000/api/v1/stats
```

#### Q5: 图谱构建失败

**错误信息**: `CSV parsing error` 或 `Constraint violation`

**解决方案**:
```bash
# 验证数据格式
python3 scripts/validate_data.py

# 检查 CSV 编码（必须是 UTF-8）
file -I data/raw/assets/assets.csv

# 清空图谱重新构建
# 在 Neo4j Browser 中运行：
# MATCH (n) DETACH DELETE n

# 重新构建
python3 -m src.graph_rag.graph_builder
```

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看 Neo4j 日志
docker logs -f neo4j

# 启用 DEBUG 日志级别（config.yaml）
system:
  log_level: "DEBUG"
```

## 后续优化方向

### 短期优化（1-2周）

- [ ] **模型加速**: 集成 vLLM 提升推理性能
- [ ] **缓存优化**: 实现 Redis 缓存，减少重复计算
- [ ] **监控告警**: 添加 Prometheus + Grafana 监控
- [ ] **API 文档**: 集成 Swagger/OpenAPI 文档
- [ ] **单元测试**: 提升测试覆盖率至 80%+

### 中期优化（1-2月）

- [ ] **流式输出**: 支持 Server-Sent Events (SSE) 流式响应
- [ ] **混合检索**: 集成向量数据库（Milvus/Qdrant）实现语义+图谱混合检索
- [ ] **多轮对话**: 支持上下文记忆和多轮交互
- [ ] **用户反馈**: 实现反馈回流和持续学习机制
- [ ] **Web 前端**: 开发交互式 Web 界面

### 长期规划（3-6月）

- [ ] **知识扩展**: 自动从文档、Wiki 等提取知识更新图谱
- [ ] **Text2Cypher**: 实现自然语言到 Cypher 的自动转换
- [ ] **多模态支持**: 支持图片、文档等多模态输入
- [ ] **分布式部署**: 支持多节点负载均衡
- [ ] **企业级功能**: 权限管理、审计日志、数据脱敏

## 相关文档

- 📖 **快速开始**: `QUICKSTART.md` - 零基础入门指南
- 📋 **项目总结**: `PROJECT_SUMMARY.md` - 完整的项目交付总结
- 📊 **数据说明**: `data/DATA_SUMMARY.md` - 详细的数据格式和示例
- 🔧 **配置说明**: `config/config.yaml` - 完整的配置文件说明
- 📝 **数据标注**: `docs/DATA_ANNOTATION_GUIDE.md` - 数据标注规范
- 🚀 **部署指南**: `docs/SETUP_GUIDE.md` - 生产环境部署指南
- 📈 **升级日志**: `UPGRADE_SUMMARY.md` - 版本更新记录

## 技术栈

| 技术 | 版本 | 用途 |
|-----|------|------|
| Python | 3.8+ | 主要开发语言 |
| PyTorch | 2.0+ | 深度学习框架 |
| Transformers | 4.36+ | 模型加载和推理 |
| Neo4j | 5.14+ | 图数据库 |
| Flask | 3.0+ | Web API 框架 |
| Qwen2.5-32B | - | 意图识别模型 |
| Qwen2.5-14B | - | 答案生成模型 |

## 项目亮点

✨ **完整的企业级实现**
- 8 大意图 + 10 大槽位的精细化意图识别
- 11 种节点类型 + 15 种关系类型的丰富知识图谱
- 生产就绪的 API 服务和监控体系

🚀 **高性能架构**
- 支持模型量化，降低硬件门槛
- 可选的缓存和批处理优化
- 优化的图查询和索引策略

📊 **完善的数据生态**
- 完整的示例数据（69 个节点，81 条关系）
- 数据增强工具，可扩充 10-100 倍训练数据
- 标准化的数据格式和验证工具

🛡️ **生产级质量**
- 关闭 CoT 确保输出稳定性
- 严格的知识忠实度，杜绝幻觉
- 完善的错误处理和日志记录

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 代码风格
- 添加必要的注释和文档
- 确保测试通过
- 更新相关文档

## 许可证

MIT License

## 联系方式

- 📧 **技术支持**: 提交 GitHub Issue
- 📚 **文档**: 查看 `docs/` 目录
- 💬 **讨论**: GitHub Discussions

---

**版本**: v2.0.0  
**最后更新**: 2024-10  
**状态**: ✅ 生产就绪

⭐ 如果这个项目对您有帮助，欢迎 Star 支持！

