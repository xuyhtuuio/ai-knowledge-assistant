
> 本指南记录了从零开始启动Neo4j图谱的完整流程

---

## 📋 目录

1. [环境准备](#环境准备)
2. [Neo4j安装与启动](#neo4j安装与启动)
3. [配置数据库连接](#配置数据库连接)
4. [构建知识图谱](#构建知识图谱)
5. [访问与可视化](#访问与可视化)
6. [测试查询功能](#测试查询功能)
7. [常见问题](#常见问题)

---

## 环境准备

### 系统要求
- Ubuntu 22.04 或其他Linux发行版
- Python 3.9+
- 至少2GB内存
- 5GB磁盘空间

### 安装依赖包

```bash
cd /root/ai-knowledge-assistant

# 安装Python依赖
pip3 install pandas pyyaml neo4j
```

---

## Neo4j安装与启动

### 步骤1: 安装Java运行环境

```bash
# 更新包管理器
sudo apt-get update

# 安装Java 17
sudo apt-get install -y openjdk-17-jre
```

### 步骤2: 安装Neo4j

```bash
# 添加Neo4j GPG密钥
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -

# 添加Neo4j软件源
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# 更新包列表
sudo apt-get update

# 安装Neo4j
sudo apt-get install -y neo4j
```

### 步骤3: 设置初始密码

```bash
# 设置Neo4j初始密码为 neo4j123
neo4j-admin dbms set-initial-password neo4j123
```

### 步骤4: 启动Neo4j服务

```bash
# 启动Neo4j
neo4j start

# 验证服务状态（应该显示已运行）
neo4j status
```

**预期输出**：
```
Neo4j is running at pid XXXXX
```

### 步骤5: 验证服务

```bash
# 访问HTTP接口验证
curl http://localhost:7474

# 应该返回JSON格式的版本信息
```

---

## 配置数据库连接

### 修改配置文件

编辑 `config/config.yaml`：

```yaml
graph:
  database: "neo4j"
  neo4j:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "neo4j123"    # 修改为你设置的密码
    database: "neo4j"
```

### 验证连接

```bash
cd /root/ai-knowledge-assistant

# 测试Neo4j连接
python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4j123'))
with driver.session() as session:
    result = session.run('RETURN 1')
    print('✅ Neo4j连接成功！')
driver.close()
"
```

# 运行构建脚本
python3 -m src.graph_rag.graph_builder
```

**预期输出**：
```
INFO:__main__:成功连接Neo4j: bolt://localhost:7687
INFO:__main__:图谱构建器初始化完成
INFO:__main__:开始构建知识图谱...
INFO:__main__:约束和索引创建完成（支持新Schema）
INFO:__main__:加载资产数据: data/raw/assets/assets.csv
INFO:__main__:成功加载 8 个资产节点
INFO:__main__:加载场景数据: data/raw/scenarios/scenarios.csv
INFO:__main__:成功加载 7 个场景节点
INFO:__main__:加载热点数据: data/raw/hotspots/hotspots.csv
INFO:__main__:成功加载 4 个热点节点
INFO:__main__:加载字段数据: data/raw/fields/fields.csv
INFO:__main__:成功加载 16 个字段节点
INFO:__main__:加载业务域数据: data/raw/domains/domains.csv
INFO:__main__:成功加载 6 个业务域节点
INFO:__main__:加载业务专区数据: data/raw/zones/zones.csv
INFO:__main__:成功加载 5 个业务专区节点
INFO:__main__:加载业务概念数据: data/raw/concepts/concepts.csv
INFO:__main__:成功加载 8 个业务概念节点
INFO:__main__:加载用户数据: data/raw/users/users.csv
INFO:__main__:成功加载 8 个用户节点
INFO:__main__:加载组织数据: data/raw/orgs/orgs.csv
INFO:__main__:成功加载 7 个组织节点
INFO:__main__:加载通用关系: data/raw/relationships/relationships.csv
INFO:__main__:成功创建 58 个关系
INFO:__main__:用户-资产关系已通过通用关系文件加载，跳过
INFO:__main__:加载资产-场景关系: data/raw/relationships/asset_scenario.csv
INFO:__main__:成功创建 12 个资产-场景关系
INFO:__main__:加载热点-资产关系: data/raw/relationships/hotspot_asset.csv
INFO:__main__:成功创建 7 个热点-资产关系
INFO:__main__:知识图谱构建完成！
```