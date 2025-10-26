# AI知识助手 (AI Knowledge Assistant)

## 项目概述

企业级数据资产知识助手，采用"意图识别"与"GraphRAG"相结合的双核驱动架构，基于知识图谱技术实现数据资产的智能检索与问答。

### 技术架构

```
用户查询
   ↓
[意图识别模块] (Qwen2.5-32B 微调)
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





