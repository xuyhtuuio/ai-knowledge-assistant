# 🚀 快速启动指南

本指南将帮助您在 30 分钟内启动 AI 知识助手系统。

## 📋 前置检查清单

在开始之前，请确认您的环境满足以下要求：

### 硬件要求

- [ ] **GPU**: NVIDIA GPU，至少 24GB 显存（推荐 A10/A100）
- [ ] **内存**: 至少 64GB RAM
- [ ] **存储**: 至少 150GB 可用空间
- [ ] **网络**: 稳定的网络连接（用于下载模型）

### 软件要求

- [ ] **操作系统**: Linux (Ubuntu 20.04+) 或 macOS
- [ ] **Python**: 3.8 或更高版本
- [ ] **CUDA**: 11.8 或更高版本（如使用 GPU）
- [ ] **Docker**: 用于运行 Neo4j（推荐）

检查命令：

```bash
# 检查 Python 版本
python3 --version

# 检查 CUDA 版本
nvcc --version

# 检查显存
nvidia-smi

# 检查磁盘空间
df -h .
```

---

## 🎯 快速开始（5 步）

### 步骤 1: 克隆项目

```bash
git clone <repository-url>
cd ai-knowledge-assistant
```

### 步骤 2: 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 升级 pip
pip install --upgrade pip

# 安装依赖（约 5-10 分钟）
pip install -r requirements.txt
```

### 步骤 3: 下载模型

⚠️ **重要**: 模型文件总计约 93GB，下载时间取决于您的网速。

#### 方式 A: 国内用户（使用 ModelScope，推荐）

```bash
# 安装 modelscope
pip install modelscope

# 下载模型（约 30-60 分钟，取决于网速）
python3 << EOF
from modelscope import snapshot_download
import os

print("正在下载意图识别模型 (Qwen2.5-32B-Instruct)...")
snapshot_download('qwen/Qwen2.5-32B-Instruct', 
                  cache_dir='./models/intent_recognition/qwen3-32b-sft')
print("✅ 意图识别模型下载完成！")

print("\n正在下载答案生成模型 (Qwen2.5-14B-Instruct)...")
snapshot_download('qwen/Qwen2.5-14B-Instruct',
                  cache_dir='./models/answer_generation/qwen3-14b')
print("✅ 答案生成模型下载完成！")

print("\n🎉 所有模型下载完成！")
EOF
```

#### 方式 B: 国际用户（使用 Hugging Face）

```bash
# 安装 huggingface-cli
pip install -U huggingface_hub

# 下载意图识别模型
huggingface-cli download Qwen/Qwen2.5-32B-Instruct \
  --local-dir ./models/intent_recognition/qwen3-32b-sft

# 下载答案生成模型
huggingface-cli download Qwen/Qwen2.5-14B-Instruct \
  --local-dir ./models/answer_generation/qwen3-14b
```

#### 验证下载

```bash
# 检查模型文件
ls -lh models/intent_recognition/qwen3-32b-sft/
ls -lh models/answer_generation/qwen3-14b/

# 应该看到 .safetensors 或 .bin 文件
```

### 步骤 4: 启动 Neo4j 数据库

#### 使用 Docker（推荐）

```bash
# 启动 Neo4j 容器
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -v $HOME/neo4j/data:/data \
  neo4j:latest

# 等待 30 秒让 Neo4j 完全启动
sleep 30

# 验证 Neo4j 是否启动
docker ps | grep neo4j
curl http://localhost:7474
```

访问 http://localhost:7474 打开 Neo4j Browser，使用以下凭证登录：
- 用户名: `neo4j`
- 密码: `your_password`（首次登录可能需要修改密码）

#### 本地安装（替代方案）

```bash
# macOS
brew install neo4j
neo4j start

# Linux (Ubuntu)
# 参考: https://neo4j.com/docs/operations-manual/current/installation/linux/
```

### 步骤 5: 配置系统

编辑 `config/config.yaml`，设置 Neo4j 密码：

```bash
# 使用你喜欢的编辑器
vim config/config.yaml
# 或
nano config/config.yaml
```

找到 `graph.neo4j.password`，修改为您设置的密码：

```yaml
graph:
  neo4j:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "your_password"  # ⚠️ 修改为实际密码
```

---

## 🏗️ 构建知识图谱

### 验证示例数据

```bash
# 查看示例数据文件
ls -lh data/raw/*/

# 应该看到以下文件：
# - assets/assets.csv (8 条资产)
# - scenarios/scenarios.csv (7 条场景)
# - hotspots/hotspots.csv (4 条热点)
# - fields/fields.csv (16 条字段)
# - domains/domains.csv (6 条业务域)
# - users/users.csv (8 条用户)
# - 等等...
```

### 构建图谱

```bash
# 运行图谱构建脚本
python3 -m src.graph_rag.graph_builder
```

预期输出：

```
INFO:root:开始构建知识图谱...
INFO:root:连接到 Neo4j: bolt://localhost:7687
INFO:root:创建约束和索引...
INFO:root:✅ 约束创建完成
INFO:root:
INFO:root:========== 加载节点数据 ==========
INFO:root:加载资产数据...
INFO:root:✅ 成功加载 8 个资产节点
INFO:root:加载字段数据...
INFO:root:✅ 成功加载 16 个字段节点
INFO:root:加载业务域数据...
INFO:root:✅ 成功加载 6 个业务域节点
...
INFO:root:
INFO:root:========== 图谱构建完成 ==========
INFO:root:
INFO:root:📊 图谱统计:
INFO:root:  - 资产节点: 8
INFO:root:  - 字段节点: 16
INFO:root:  - 业务域节点: 6
INFO:root:  - 业务专区节点: 5
INFO:root:  - 场景节点: 7
INFO:root:  - 业务概念节点: 8
INFO:root:  - 用户节点: 8
INFO:root:  - 组织节点: 7
INFO:root:  - 热点节点: 4
INFO:root:  - 应用实例节点: 12
INFO:root:  - 关系总数: 150+
INFO:root:
INFO:root:✅ 知识图谱构建成功！
```

### 验证图谱构建

在 Neo4j Browser (http://localhost:7474) 中运行以下查询：

```cypher
// 1. 查看所有节点类型统计
MATCH (n) 
RETURN labels(n) as 节点类型, count(n) as 数量 
ORDER BY 数量 DESC
```

```cypher
// 2. 查看新员工入职场景涉及的资产
MATCH (s:Scenario {scenario_id: 'S001'})-[:USES_ASSET]->(a:Asset)
RETURN s.name as 场景, a.name as 资产, a.description as 描述
```

```cypher
// 3. 可视化资产关系
MATCH path = (a:Asset)-[*1..2]-(n)
WHERE a.asset_id = 'A001'
RETURN path
LIMIT 50
```

---

## 🚀 启动 API 服务

### 启动服务

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 启动 API 服务
python3 -m src.api.api_server
```

预期输出：

```
INFO:root:初始化 Orchestrator...
INFO:root:初始化意图识别分类器，设备: cuda
INFO:root:初始化答案生成器，设备: cuda
INFO:root:初始化图查询引擎...
INFO:root:连接到 Neo4j: bolt://localhost:7687
INFO:root:✅ 所有组件初始化完成
 * Serving Flask app 'api_server'
 * Running on http://0.0.0.0:8000
```

⚠️ **首次启动**: 模型加载可能需要 1-2 分钟，请耐心等待。

### 测试 API

打开新的终端窗口（保持 API 服务运行），运行测试：

```bash
# 健康检查
curl http://localhost:8000/health

# 预期输出：
# {"status":"healthy","service":"AI Knowledge Assistant","version":"2.0.0"}
```

```bash
# 测试查询 1: 场景相关资产
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "新员工入职场景需要哪些核心资产？"}'
```

```bash
# 测试查询 2: 资产基础检索
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "M域的所有资产有哪些？"}'
```

```bash
# 测试查询 3: 用户收藏查询
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "张三收藏了哪些资产？"}'
```

```bash
# 查看服务统计
curl http://localhost:8000/api/v1/stats
```

---

## ✅ 验证系统

### 测试 8 大意图

```bash
# Intent 31: 资产基础检索
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "平台上有哪些系统类型的资产？"}'

# Intent 32: 资产元数据查询
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "HR系统的负责人是谁？"}'

# Intent 34: 资产血缘关系查询
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "数据仓库平台的上游依赖有哪些？"}'

# Intent 35: 资产使用与工单查询
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "王五收藏了哪些资产？"}'

# Intent 36: 场景与标签推荐
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "公众智慧运营专区有哪些场景？"}'

# Intent 38: 平台规则与帮助
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "如何创建数据资产？"}'
```

---

## 🎉 恭喜！系统启动成功

您已经成功启动了 AI 知识助手系统。

### 下一步

1. **查看详细文档**
   - `README.md` - 完整项目文档
   - `data/DATA_SUMMARY.md` - 数据格式说明
   - `docs/SETUP_GUIDE.md` - 生产环境部署

2. **添加您的数据**
   - 编辑 `data/raw/*/` 目录下的 CSV 文件
   - 重新运行 `python3 -m src.graph_rag.graph_builder`

3. **微调模型**
   - 准备训练数据：`data/annotated/training_data_extended.jsonl`
   - 运行训练：`python3 -m src.intent_recognition.intent_trainer`

4. **性能优化**
   - 启用模型量化降低显存需求
   - 配置 Redis 缓存提升响应速度
   - 使用 vLLM 加速推理

---

## 🔍 常见问题

### Q1: 模型下载很慢怎么办？

**A**: 
- 国内用户使用 ModelScope（方式 A）会更快
- 可以使用代理加速 Hugging Face 下载
- 考虑使用其他网络环境下载后传输

### Q2: 显存不足怎么办？

**A**: 启用模型量化，编辑 `config/config.yaml`：

```yaml
training:
  intent_recognition:
    use_qlora: true  # 启用 4-bit 量化
```

这将把显存需求从 65GB 降至约 20GB。

### Q3: Neo4j 连接失败

**A**:

```bash
# 检查 Neo4j 是否运行
docker ps | grep neo4j

# 检查端口
lsof -i :7687

# 查看日志
docker logs neo4j

# 重启 Neo4j
docker restart neo4j
```

### Q4: API 响应很慢

**A**:
- 首次调用需要加载模型（1-2分钟）
- 后续调用会快很多
- 考虑启用缓存和模型量化

### Q5: 如何清空图谱重新构建？

**A**: 在 Neo4j Browser 中运行：

```cypher
// 删除所有节点和关系
MATCH (n) DETACH DELETE n
```

然后重新运行 `python3 -m src.graph_rag.graph_builder`

---

## 📚 学习资源

### 文档

- [README.md](README.md) - 完整项目文档
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目总结
- [data/DATA_SUMMARY.md](data/DATA_SUMMARY.md) - 数据格式说明

### 示例

- `data/raw/` - 示例数据
- `data/annotated/training_data_extended.jsonl` - 训练数据示例
- `tests/test_api.py` - API 测试示例

### 配置

- `config/config.yaml` - 主配置文件
- `config/prompt_config.yaml` - Prompt 模板配置

