# 🚀 快速启动指南

## ✅ 数据准备完成

所有知识图谱初始数据已生成并验证通过！

### 📊 数据概览

- **节点数据**：69个节点
  - 资产节点: 8个
  - 场景节点: 7个
  - 热点节点: 4个
  - 字段节点: 16个
  - 业务域节点: 6个
  - 业务专区节点: 5个
  - 业务概念节点: 8个
  - 用户节点: 8个
  - 组织节点: 7个

- **关系数据**：81条关系
  - 资产-场景关系: 12条
  - 热点-资产关系: 7条
  - 通用关系: 58条（包含多种类型）
  - 血缘关系: 4条

📖 **详细数据说明**: 查看 `data/DATA_SUMMARY.md`

---

## 🔧 下一步操作

### 步骤1: 配置Neo4j数据库

#### 方式A: 使用Docker（推荐）

```bash
# 启动Neo4j容器
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/yourpassword \
  -v $HOME/neo4j/data:/data \
  neo4j:latest

# 查看容器状态
docker ps | grep neo4j
```

#### 方式B: 本地安装

```bash
# macOS
brew install neo4j
neo4j start

# Linux
sudo systemctl start neo4j
```

#### 验证Neo4j服务

访问浏览器：http://localhost:7474
- 默认用户名: `neo4j`
- 默认密码: `neo4j`（首次登录需要修改）

---

### 步骤2: 更新配置文件

编辑 `config/config.yaml`，设置Neo4j连接信息：

```yaml
graph:
  neo4j:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "yourpassword"  # ⚠️ 修改为你设置的密码
```

---

### 步骤3: 构建知识图谱

#### 方式A: 使用脚本（推荐）

```bash
# 检查数据（可选）
bash scripts/validate_data.sh

# 构建图谱
bash scripts/build_graph.sh
```

#### 方式B: 直接运行Python

```bash
python3 -m src.graph_rag.graph_builder
```

#### 预期输出

构建成功后会看到类似输出：

```
INFO:root:开始构建知识图谱...
INFO:root:创建约束...
INFO:root:加载资产数据...
INFO:root:成功加载 8 个资产节点
INFO:root:加载场景数据...
INFO:root:成功加载 7 个场景节点
...
INFO:root:图谱构建完成！

图谱统计:
资产节点: 8
字段节点: 16
业务域节点: 6
业务专区节点: 5
场景节点: 7
业务概念节点: 8
用户节点: 8
组织节点: 7
热点节点: 4
应用实例节点: 12
关系总数: 150+
```

---

### 步骤4: 验证图谱构建

#### 在Neo4j Browser中运行查询

访问 http://localhost:7474，运行以下Cypher查询：

**1. 查看所有节点类型**
```cypher
MATCH (n) 
RETURN labels(n) as 节点类型, count(n) as 数量 
ORDER BY 数量 DESC
```

**2. 查看所有关系类型**
```cypher
MATCH ()-[r]->() 
RETURN type(r) as 关系类型, count(r) as 数量 
ORDER BY 数量 DESC
```

**3. 查看新员工入职场景涉及的资产**
```cypher
MATCH (s:Scenario {scenario_id: 'S001'})-[:USES_ASSET]->(a:Asset)
RETURN s.name as 场景, a.name as 资产, a.description as 描述
```

**4. 查看数据仓库的上游血缘**
```cypher
MATCH (source:Asset)-[r:LINEAGE_UPSTREAM]->(target:Asset {asset_id: 'A005'})
RETURN source.name as 上游资产, 
       r.transform_logic as 转换逻辑, 
       r.update_frequency as 更新频率
```

**5. 查看用户收藏的资产**
```cypher
MATCH (u:User)-[:FAVORITED]->(a:Asset)
RETURN u.name as 用户, collect(a.name) as 收藏的资产
```

**6. 查看M域的所有资产**
```cypher
MATCH (a:Asset)-[:BELONGS_TO]->(d:BusinessDomain {domain_id: 'D001'})
RETURN a.name as 资产名称, a.type as 资产类型, a.description as 描述
```

**7. 可视化：新员工入职场景的关系图**
```cypher
MATCH path = (s:Scenario {scenario_id: 'S001'})-[*1..2]-(n)
RETURN path
LIMIT 50
```

---

## 🎯 测试意图查询

图谱构建完成后，可以测试各种意图查询：

### Intent 31: 资产基础检索
```
"M域的所有资产有哪些？"
"包含user_id字段的资产"
"平台上有哪些系统类型的资产？"
```

### Intent 32: 资产元数据查询
```
"HR系统的负责人是谁？"
"数据仓库平台是干什么用的？"
"employee_id字段是什么类型？"
```

### Intent 34: 资产血缘关系查询
```
"数据仓库平台的上游依赖有哪些？"
"HR系统的下游应用是什么？"
```

### Intent 35: 资产使用与工单查询
```
"王五收藏了哪些资产？"
"张三负责管理的资产有哪些？"
```

### Intent 36: 场景与标签推荐
```
"公众智慧运营专区有哪些场景？"
"5G登网相关的数据有哪些？"
"新员工入职需要哪些资产？"
```

---

## 🔍 常见问题

### Q1: Neo4j连接失败怎么办？

**A:** 检查以下几点：
1. Neo4j服务是否启动：`docker ps` 或 `systemctl status neo4j`
2. 端口7687是否被占用：`lsof -i :7687`
3. 配置文件中的密码是否正确
4. 防火墙是否允许7687端口

### Q2: 构建过程中出现错误怎么办？

**A:** 常见错误处理：
- `ModuleNotFoundError`: 安装依赖 `pip install -r requirements.txt`
- `Authentication error`: 检查Neo4j用户名密码
- `CSV parsing error`: 检查CSV文件格式，确保UTF-8编码

### Q3: 如何清空图谱重新构建？

**A:** 在Neo4j Browser中运行：
```cypher
// 删除所有节点和关系
MATCH (n) DETACH DELETE n
```
然后重新运行构建脚本。

### Q4: 如何添加更多数据？

**A:** 
1. 编辑对应的CSV文件（如 `data/raw/assets/assets.csv`）
2. 保持CSV格式和字段名一致
3. 重新运行构建脚本（会自动合并新数据）

---

## 📚 相关文档

- **项目整体介绍**: `README.md`
- **数据详细说明**: `data/DATA_SUMMARY.md`
- **配置说明**: `config/config.yaml`
- **升级日志**: `UPGRADE_SUMMARY.md`

---

## 🎉 下一步

图谱构建完成后，可以：

1. **启动API服务**
```bash
python3 -m src.api.api_server
```

2. **测试查询接口**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "新员工入职场景需要哪些核心资产？"}'
```

3. **训练意图识别模型**
```bash
# 生成训练数据
python3 -m src.data_tools.data_augmentation

# 训练模型
python3 -m src.intent_recognition.intent_trainer
```

---

## 💡 提示

- 首次构建可能需要几秒到几十秒，取决于数据量
- 建议定期备份Neo4j数据目录
- 生产环境请修改默认密码并启用SSL
- 大规模数据（10万+节点）建议使用批量导入工具

---

**祝你使用愉快！** 🚀

如有问题，请查看日志文件或提Issue。

