# AI知识助手 - 部署指南

## 目录

1. [环境要求](#环境要求)
2. [Neo4j安装配置](#neo4j安装配置)
3. [模型准备](#模型准备)
4. [数据准备](#数据准备)
5. [系统配置](#系统配置)
6. [启动服务](#启动服务)
7. [验证测试](#验证测试)

## 环境要求

### 硬件要求

- **CPU**: 8核以上
- **内存**: 32GB以上
- **GPU**: 
  - Qwen3-32B: 至少24GB显存 (建议使用A100/A6000)
  - Qwen3-14B: 至少16GB显存 (可使用RTX 4090/A5000)
- **存储**: 100GB以上可用空间

### 软件要求

- Python 3.9+
- CUDA 11.8+ (如果使用GPU)
- Neo4j 5.x
- Git

## Neo4j安装配置

### 方式一：Docker安装（推荐）

```bash
# 拉取Neo4j镜像
docker pull neo4j:5.14

# 启动Neo4j容器
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -v $HOME/neo4j/data:/data \
  -v $HOME/neo4j/logs:/logs \
  neo4j:5.14

# 访问Web界面
# http://localhost:7474
```

### 方式二：本地安装

#### Ubuntu/Debian

```bash
# 添加Neo4j仓库
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# 安装Neo4j
sudo apt-get update
sudo apt-get install neo4j

# 启动服务
sudo systemctl start neo4j
sudo systemctl enable neo4j
```

#### MacOS

```bash
# 使用Homebrew安装
brew install neo4j

# 启动服务
neo4j start
```

### 配置Neo4j

编辑 `/etc/neo4j/neo4j.conf`:

```properties
# 启用远程连接
dbms.default_listen_address=0.0.0.0

# 调整内存设置
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=4g
dbms.memory.pagecache.size=2g
```

## 模型准备

### 1. 下载Qwen3模型

```bash
# 创建模型目录
mkdir -p models

# 下载Qwen3-32B (意图识别)
cd models
git lfs install
git clone https://huggingface.co/Qwen/Qwen2.5-32B-Instruct qwen3-32b

# 下载Qwen3-14B (答案生成)
git clone https://huggingface.co/Qwen/Qwen2.5-14B-Instruct qwen3-14b
```

### 2. 模型微调 (可选)

如果需要对意图识别模型进行SFT：

```bash
# 准备训练数据
python -m src.data_tools.data_augmentation

# 训练模型
python -m src.intent_recognition.intent_trainer \
  --base_model models/qwen3-32b \
  --train_file data/processed/training/train.jsonl \
  --output_dir models/intent_recognition_sft \
  --num_epochs 3 \
  --batch_size 4 \
  --learning_rate 2e-5
```

## 数据准备

### 1. 准备原始数据

创建以下CSV文件：

```
data/raw/
├── assets/
│   └── assets.csv
├── scenarios/
│   └── scenarios.csv
├── hotspots/
│   └── hotspots.csv
└── relationships/
    ├── asset_scenario.csv
    └── hotspot_asset.csv
```

### 2. 资产数据示例 (assets.csv)

```csv
asset_id,name,description,owner,type,version,status
A001,HR系统,人力资源管理系统,张三,系统,v2.0,已上线
A002,OA系统,办公自动化系统,李四,系统,v3.1,已上线
A003,客户管理系统,CRM客户关系管理,王五,系统,v1.5,已上线
```

### 3. 场景数据示例 (scenarios.csv)

```csv
scenario_id,name,description,business_domain,status
S001,新员工入职,新员工入职全流程管理,人力资源,已上线
S002,月度数据上报,月度业务数据统计上报,财务管理,已上线
S003,客户信息维护,客户基本信息的录入和更新,客户服务,已上线
```

### 4. 热点数据示例 (hotspots.csv)

```csv
hotspot_id,title,summary,publish_date,source,category
H001,数据安全法更新,最新数据安全法规要求企业加强数据保护...,2024-01-15,官方,政策法规
H002,AIGC技术报告,人工智能生成内容技术发展趋势...,2024-02-01,行业报告,技术趋势
```

### 5. 关系数据示例 (asset_scenario.csv)

```csv
asset_id,scenario_id,role,status,description
A001,S001,核心依赖,已上线,新员工入职的核心系统
A002,S001,辅助支持,已上线,提供办公权限和账号
A003,S003,核心依赖,已上线,客户信息的主要管理系统
```

### 6. 构建知识图谱

```bash
python -m src.graph_rag.graph_builder
```

## 系统配置

### 1. 编辑配置文件 config/config.yaml

```yaml
# 模型配置
models:
  intent_recognition:
    model_name: "Qwen3-32B-SFT"
    model_path: "/absolute/path/to/models/intent_recognition_sft"  # 使用绝对路径
    device: "cuda"
    max_length: 512
    temperature: 0.1
    top_p: 0.9
  
  answer_generation:
    model_name: "Qwen3-14B"
    model_path: "/absolute/path/to/models/qwen3-14b"  # 使用绝对路径
    device: "cuda"
    max_length: 1024
    temperature: 0.7
    top_p: 0.9
    repetition_penalty: 1.1

# 图数据库配置
graph:
  neo4j:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "your_password"  # 修改为实际密码
    database: "neo4j"

# 数据路径配置
data:
  raw_data_dir: "data/raw"
  processed_data_dir: "data/processed"
  training_data_dir: "data/processed/training"
```

### 2. 编辑Prompt配置 config/prompt_config.yaml

根据实际业务需求调整System Prompt。

## 启动服务

### 1. 启动API服务

```bash
# 开发模式
python -m src.api.api_server

# 生产模式（使用gunicorn）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "src.api.api_server:create_app()"
```

### 2. 后台运行

```bash
# 使用nohup
nohup python -m src.api.api_server > logs/api.log 2>&1 &

# 或使用systemd
sudo cp deploy/ai-knowledge-assistant.service /etc/systemd/system/
sudo systemctl start ai-knowledge-assistant
sudo systemctl enable ai-knowledge-assistant
```

## 验证测试

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

预期输出：
```json
{
  "status": "healthy",
  "service": "AI Knowledge Assistant"
}
```

### 2. 测试查询

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "新员工入职场景需要哪些核心资产？"
  }'
```

### 3. 批量测试

```bash
python tests/test_api.py
```

### 4. 性能测试

```bash
# 安装wrk
sudo apt-get install wrk

# 压力测试
wrk -t4 -c100 -d30s --latency \
  -s tests/wrk_script.lua \
  http://localhost:8000/api/v1/query
```

## 常见问题

### 1. CUDA Out of Memory

**解决方案**：
- 使用模型量化 (4-bit/8-bit)
- 减少batch_size
- 使用CPU推理（性能会下降）

```python
# 在配置中设置
device: "cpu"
```

### 2. Neo4j连接超时

**解决方案**：
- 检查Neo4j服务状态: `sudo systemctl status neo4j`
- 验证端口是否开放: `netstat -tlnp | grep 7687`
- 检查防火墙设置

### 3. 模型加载缓慢

**解决方案**：
- 预先加载模型（warm up）
- 使用本地模型缓存
- 考虑使用vLLM进行推理优化

### 4. 图谱查询性能差

**解决方案**：
- 确保已创建索引
- 优化Cypher查询语句
- 考虑增加Neo4j内存配置

## 监控和日志

### 1. 日志配置

```python
# 在启动脚本中配置
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### 2. 性能监控

```bash
# 查看GPU使用情况
nvidia-smi -l 1

# 查看系统资源
htop
```

### 3. Neo4j监控

访问 http://localhost:7474 查看数据库状态

## 安全建议

1. **更改默认密码**: Neo4j和API的默认密码
2. **启用HTTPS**: 在生产环境使用SSL证书
3. **访问控制**: 使用防火墙限制API访问
4. **日志审计**: 记录所有API请求
5. **定期备份**: 备份Neo4j数据库和模型文件

## 后续优化

1. 使用Redis缓存高频查询
2. 部署Nginx作为反向代理
3. 配置负载均衡
4. 实现分布式部署
5. 添加监控告警系统

## 技术支持

如遇到问题，请：
1. 查看日志文件
2. 阅读常见问题
3. 提交Issue
4. 联系技术支持团队

