# AI知识助手 (AI Knowledge Assistant)

## 项目概述

企业级数据资产知识助手，采用"意图识别"与"GraphRAG"相结合的双核驱动架构，基于知识图谱技术实现数据资产的智能检索与问答。

### 技术架构

```
用户查询
   ↓
[意图识别模块] (Qwen2.5-32B 微调)  
   ↓
[路由控制器] （目前为8大意图， 10大槽位）
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

### 快速了解Schema ->  graph_schema_config.yaml

## 硬件要求

**重要**: 本项目使用大型语言模型，需要较高的硬件配置。

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

### 若要整个流程但先不想加入模型可以运行demo_intent31.py文件


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

### 关于GraphRAG启动部分可以去看GraphRAG快速启动.md



### GraphRAG的核心数据示例

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

#### 关于模型的详细设置包括优化器选择等，代码里有详细注释


#### 使用 vLLM 加速推理

```bash
pip install vllm

# 修改模型加载方式使用 vLLM
```

优化效果：
- **吞吐量**: 提升 2-5 倍
- **批量处理**: 显著提升效率





