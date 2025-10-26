# 知识图谱初始数据汇总

## 📊 数据概览

本项目已生成完整的知识图谱初始数据，支持8大意图和10大槽位体系。

### 数据文件清单

```
data/raw/
├── assets/
│   └── assets.csv                # 8个资产节点
├── scenarios/
│   └── scenarios.csv             # 7个场景节点
├── hotspots/
│   └── hotspots.csv              # 4个热点节点
├── fields/
│   └── fields.csv                # 16个字段节点
├── domains/
│   └── domains.csv               # 6个业务域节点
├── zones/
│   └── zones.csv                 # 5个业务专区节点
├── concepts/
│   └── concepts.csv              # 8个业务概念节点
├── users/
│   └── users.csv                 # 8个用户节点
├── orgs/
│   └── orgs.csv                  # 7个组织节点
└── relationships/
    ├── asset_scenario.csv        # 资产-场景关系
    ├── hotspot_asset.csv         # 热点-资产关系
    ├── relationships.csv         # 通用关系（包含多种类型）
    └── lineage.csv               # 血缘关系
```

---

## 📦 节点数据详情

### 1. 资产节点 (Asset) - 8个

| asset_id | name | type | owner | description |
|----------|------|------|-------|-------------|
| A001 | HR系统 | 系统 | 张三 | 人力资源管理系统 |
| A002 | OA系统 | 系统 | 李四 | 办公自动化系统 |
| A003 | 客户关系管理系统 | 系统 | 王五 | CRM系统 |
| A004 | 统一认证系统 | 系统 | 赵六 | 企业统一身份认证平台 |
| A005 | 数据仓库平台 | 平台 | 孙七 | 企业级数据仓库 |
| A006 | 财务管理系统 | 系统 | 周八 | 财务核算、报表系统 |
| A007 | 供应商管理平台 | 平台 | 吴九 | 供应商准入、评估平台 |
| A008 | 数据接口服务 | 接口 | 郑十 | 统一数据接口服务 |

### 2. 场景节点 (Scenario) - 7个

| scenario_id | name | business_domain | status |
|-------------|------|-----------------|--------|
| S001 | 新员工入职 | 人力资源 | 已上线 |
| S002 | 月度数据上报 | 财务管理 | 已上线 |
| S003 | 客户信息维护 | 客户服务 | 已上线 |
| S004 | 供应商准入 | 供应链 | 已上线 |
| S005 | 季度财报分析 | 财务管理 | 已上线 |
| S006 | 员工考勤管理 | 人力资源 | 已上线 |
| S007 | 销售机会跟进 | 销售管理 | 已上线 |

### 3. 热点节点 (Hotspot) - 4个

| hotspot_id | title | category | publish_date |
|------------|-------|----------|--------------|
| H001 | 数据安全法更新 | 政策法规 | 2024-01-15 |
| H002 | AIGC技术报告 | 技术趋势 | 2024-02-01 |
| H003 | 隐私保护新规 | 政策法规 | 2024-01-20 |
| H004 | 数字化转型白皮书 | 战略规划 | 2024-02-10 |

### 4. 字段节点 (Field) - 16个

涵盖HR系统、CRM系统、数据仓库、财务系统的核心字段：
- **HR系统字段**: employee_id, employee_name, department, hire_date, salary
- **CRM系统字段**: customer_id, customer_name, contact_phone, registration_date
- **数据仓库字段**: user_id, is_active, 5g_registered, star_level
- **财务系统字段**: transaction_id, amount, transaction_date

### 5. 业务域节点 (BusinessDomain) - 6个

| domain_id | name | description |
|-----------|------|-------------|
| D001 | M域 | 市场域，用户行为和市场数据 |
| D002 | O域 | 运营域，业务运营和流程数据 |
| D003 | B域 | 业务域，核心业务数据 |
| D004 | 技术域 | 技术平台和基础设施 |
| D005 | 财务域 | 财务管理和核算数据 |
| D006 | 供应链域 | 供应链协同数据 |

### 6. 业务专区节点 (BusinessZone) - 5个

| zone_id | name | description |
|---------|------|-------------|
| Z001 | 公众智慧运营 | 面向公众客户的智慧化运营专区 |
| Z002 | 一线赋能专区 | 面向一线业务人员的赋能工具 |
| Z003 | 客户洞察 | 客户行为分析、客户价值评估 |
| Z004 | 5G用户分析 | 5G用户发展、行为分析（Z001子专区） |
| Z005 | 数据治理 | 企业数据质量管理、数据标准化 |

### 7. 业务概念节点 (Concept) - 8个

| concept_id | name | type | related_domain |
|------------|------|------|----------------|
| C001 | 5G登网 | 业务指标 | M域 |
| C002 | 移网用户是否活跃 | 业务指标 | M域 |
| C003 | 用户星级 | 业务指标 | 客户域 |
| C004 | 宽带提质 | 业务概念 | O域 |
| C005 | 新星级长高用户 | 业务概念 | 客户域 |
| C006 | 用户活跃度 | 业务指标 | M域 |
| C007 | 价值评估分数 | 业务指标 | 通用 |
| C008 | 五星资产 | 业务概念 | 通用 |

### 8. 用户节点 (User) - 8个

| user_id | name | role | org_id |
|---------|------|------|--------|
| U001 | 张三 | 数据管理员 | ORG001 |
| U002 | 李四 | 系统管理员 | ORG002 |
| U003 | 王五 | 业务分析师 | ORG003 |
| U004 | 赵六 | 技术架构师 | ORG004 |
| U005 | 孙七 | 数据工程师 | ORG001 |
| U006 | 周八 | 财务分析师 | ORG005 |
| U007 | 吴九 | 供应链专员 | ORG006 |
| U008 | 郑十 | 接口开发工程师 | ORG004 |

### 9. 组织节点 (Org) - 7个

| org_id | name | level | parent_org_id |
|--------|------|-------|---------------|
| ORG001 | 总部-数据部 | 1 | - |
| ORG002 | 总部-信息技术部 | 1 | - |
| ORG003 | 营销中心 | 2 | ORG001 |
| ORG004 | 技术中心 | 2 | ORG002 |
| ORG005 | 财务部 | 1 | - |
| ORG006 | 供应链管理部 | 1 | - |
| ORG007 | 客户服务中心 | 1 | - |

---

## 🔗 关系数据详情

### 1. 资产-场景关系 (INCLUDES_USAGE / IS_USED_IN)

共13条关系，典型示例：
- S001(新员工入职) 使用 A001(HR系统) - 核心依赖
- S001(新员工入职) 使用 A002(OA系统) - 辅助支持
- S003(客户信息维护) 使用 A003(CRM系统) - 核心依赖
- S007(销售机会跟进) 使用 A003(CRM系统) - 核心依赖

### 2. 热点-资产关系 (DIRECTLY_IMPACTS)

共7条关系，典型示例：
- H001(数据安全法更新) → A003(CRM系统) - 合规要求
- H001(数据安全法更新) → A005(数据仓库平台) - 合规要求
- H004(数字化转型白皮书) → A005(数据仓库平台) - 战略指引

### 3. 通用关系 (relationships.csv)

包含多种关系类型（共59条）：

#### 3.1 资产-业务域关系 (BELONGS_TO) - 8条
- A001 → D001(M域)
- A003 → D003(B域)
- 等

#### 3.2 资产-字段关系 (HAS_FIELD) - 16条
- A001 → F001(employee_id)
- A001 → F002(employee_name)
- A003 → F006(customer_id)
- 等

#### 3.3 业务概念-字段关系 (MAPPED_TO) - 3条
- C001(5G登网) → F012(5g_registered)
- C002(移网用户是否活跃) → F011(is_active)
- C003(用户星级) → F013(star_level)

#### 3.4 业务专区-场景关系 (CONTAINS_SCENARIO) - 7条
- Z001(公众智慧运营) → S007(销售机会跟进)
- Z002(一线赋能专区) → S001(新员工入职)
- 等

#### 3.5 用户-资产关系 - 11条
- U001 FAVORITED A005 (收藏)
- U003 SUBSCRIBED A005 (订阅)
- U005 CREATED A005 (创建)

#### 3.6 资产管理关系 - 16条
- A001 MANAGED_BY U001 (管理员)
- A001 OWNED_BY ORG001 (所属组织)
- 等

### 4. 血缘关系 (LINEAGE_UPSTREAM / LINEAGE_DOWNSTREAM)

共4条血缘关系：
- A005(数据仓库) ← A001(HR系统) - 每日抽取，10000条
- A005(数据仓库) ← A003(CRM系统) - 每小时同步，50000条
- A008(数据接口) ← A005(数据仓库) - 实时调用
- A006(财务系统) ← A001(HR系统) - 每月流转，1000条

---

## 🎯 支持的意图查询示例

### Intent 31: 资产基础检索
- ✅ "M域的所有资产有哪些？" → 可查询 D001
- ✅ "包含user_id字段的资产" → 可查询 F010
- ✅ "平台上有哪些系统类型的资产？" → 可查询type=系统

### Intent 32: 资产元数据查询
- ✅ "HR系统的负责人是谁？" → 可查询 A001 MANAGED_BY U001
- ✅ "数据仓库平台是干什么用的？" → 可查询 A005.description
- ✅ "employee_id字段是什么类型？" → 可查询 F001.data_type

### Intent 33: 资产质量与价值查询
- ✅ "数据仓库平台的价值评估分数" → 可扩展资产属性
- ✅ "哪些资产的星级是五星？" → 可扩展资产属性

### Intent 34: 资产血缘关系查询
- ✅ "数据仓库平台的上游依赖有哪些？" → 可查询lineage关系
- ✅ "HR系统的下游应用是什么？" → 可查询lineage关系

### Intent 35: 资产使用与工单查询
- ✅ "我收藏的资产有哪些？" → 可查询 User FAVORITED Asset
- ✅ "王五订阅了哪些资产？" → 可查询 U003 SUBSCRIBED

### Intent 36: 场景与标签推荐
- ✅ "公众智慧运营专区有哪些场景？" → 可查询 Z001 CONTAINS_SCENARIO
- ✅ "5G登网相关的数据有哪些？" → 可查询 C001 MAPPED_TO

### Intent 37: 资产复合对比与筛选
- ✅ "HR系统和OA系统有什么关系？" → 可查询共同场景
- ✅ "M域且系统类型的资产" → 可复合查询

### Intent 38: 平台规则与帮助
- ✅ "数据安全法更新有什么影响？" → 可查询 H001 DIRECTLY_IMPACTS

---

## 🚀 快速开始

### 1. 检查Neo4j服务

```bash
# 启动Neo4j（如果未启动）
sudo systemctl start neo4j
# 或者使用Docker
docker run -d -p 7474:7474 -p 7687:7687 --name neo4j \
  -e NEO4J_AUTH=neo4j/your_password neo4j:latest
```

### 2. 配置数据库密码

编辑 `config/config.yaml`，设置Neo4j密码：

```yaml
graph:
  neo4j:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "your_password"  # 修改为你的密码
```

### 3. 运行图谱构建

```bash
# 方式1：使用脚本
bash scripts/build_graph.sh

# 方式2：直接运行Python
python -m src.graph_rag.graph_builder
```

### 4. 验证图谱

构建完成后，访问 Neo4j Browser:
- URL: http://localhost:7474
- 用户名: neo4j
- 密码: your_password

运行Cypher查询验证：

```cypher
// 查看所有节点类型和数量
MATCH (n) RETURN labels(n), count(n)

// 查看所有关系类型和数量
MATCH ()-[r]->() RETURN type(r), count(r)

// 查看新员工入职场景涉及的资产
MATCH (s:Scenario {scenario_id: 'S001'})-[:USES_ASSET]->(a:Asset)
RETURN s.name, a.name, a.description

// 查看数据仓库的血缘关系
MATCH (source:Asset)-[r:LINEAGE_UPSTREAM]->(target:Asset {asset_id: 'A005'})
RETURN source.name, r.transform_logic, r.update_frequency
```

---

## 📈 预期图谱统计

构建完成后应该有：

```
资产节点: 8
字段节点: 16
业务域节点: 6
业务专区节点: 5
场景节点: 7
业务概念节点: 8
用户节点: 8
组织节点: 7
热点节点: 4
应用实例节点: 13 (AssetUsage中间节点)
关系总数: 约100+
```

---

## 🔧 扩展建议

### 1. 增加资产属性
在 `assets.csv` 中添加：
- `star_level`: 星级评分（1-5星）
- `value_score`: 价值评估分数（0-100）
- `quality_status`: 质量状态
- `update_time`: 更新时间

### 2. 增加元数据项
创建 `metadata_items.csv` 支持槽位2：
- 业务口径、技术口径
- 简介/用途、负责人
- 价值评估、质量稽核

### 3. 增加热点标签
为热点增加关键词提取，支持语义检索

### 4. 完善血缘关系
- 增加更多层级的血缘链路
- 添加字段级血缘
- 支持血缘影响分析

---

## 📝 注意事项

1. **数据质量**: 当前为示例数据，实际使用时请替换为真实业务数据
2. **密码安全**: 请修改 `config.yaml` 中的 Neo4j 密码
3. **性能优化**: 大规模数据（10万+节点）建议批量导入和建立索引
4. **扩展性**: Schema设计支持动态扩展，可按需添加新节点和关系类型

---

生成时间: 2025-10-26

