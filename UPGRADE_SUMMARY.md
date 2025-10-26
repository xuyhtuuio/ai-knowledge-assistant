# 代码更新总结 - 升级至8大意图和10大槽位体系

## 📅 更新时间
2025-10-26

## 🎯 更新目标
将原有的5意图4实体体系升级为**数据资产助手**的**8大意图和10大槽位**体系。

---

## ✅ 已完成的更新

### 1. ✅ 意图和槽位定义（`src/intent_recognition/intent_config.py`）

**更新内容：**
- 将5个意图替换为8个意图（Intent 31-38）
- 将4个实体类型扩展为10个槽位类型
- 新增详细的意图和槽位描述字典
- 新增同义词映射配置（MetadataItem）

**8大意图：**
```python
IntentType.ASSET_BASIC_SEARCH = "31"              # 资产基础检索
IntentType.ASSET_METADATA_QUERY = "32"            # 资产元数据查询
IntentType.ASSET_QUALITY_VALUE_QUERY = "33"       # 资产质量与价值查询
IntentType.ASSET_LINEAGE_QUERY = "34"             # 资产血缘关系查询
IntentType.ASSET_USAGE_QUERY = "35"               # 资产使用与工单查询
IntentType.SCENARIO_RECOMMENDATION = "36"         # 场景与标签推荐
IntentType.ASSET_COMPARISON = "37"                # 资产复合对比与筛选
IntentType.PLATFORM_HELP = "38"                   # 平台规则与帮助
```

**10大槽位：**
```python
SlotType.ASSET_NAME = "AssetName"                 # 核心资产名
SlotType.METADATA_ITEM = "MetadataItem"           # 查询元数据项
SlotType.FIELD_NAME = "FieldName"                 # 字段名称
SlotType.CORE_DATA_ITEM = "CoreDataItem"         # 核心数据项
SlotType.BUSINESS_DOMAIN = "BusinessDomain"       # 业务/数据域
SlotType.ASSET_TYPE = "AssetType"                 # 资产类型
SlotType.BUSINESS_ZONE = "BusinessZone"           # 业务专区
SlotType.FILTER_CONDITION = "FilterCondition"     # 筛选条件
SlotType.USER_STATUS = "UserStatus"               # 用户操作属性
SlotType.ORG_USER_NAME = "OrgName/UserName"       # 机构/人员名
```

---

### 2. ✅ 图谱Schema设计（`src/graph_rag/graph_builder.py`）

**新增节点类型：**
- `Field` 节点：支持字段级查询（槽位3）
- `BusinessDomain` 节点：业务域分类（槽位5）
- `BusinessZone` 节点：业务专区（槽位7）
- `Concept` 节点：业务概念/数据项（槽位4）
- `User` 节点：用户信息（槽位9）
- `Org` 节点：组织机构（槽位10）

**新增关系类型：**
- `HAS_FIELD`: Asset → Field（资产包含字段）
- `BELONGS_TO`: Asset → BusinessDomain（资产属于域）
- `CONTAINS_SCENARIO`: BusinessZone → Scenario（专区包含场景）
- `USES_ASSET`: Scenario → Asset（场景使用资产）
- `IMPLEMENTED_BY`: Concept → Asset（概念由资产实现）
- `FAVORITED/SUBSCRIBED`: User → Asset（用户收藏/订阅）
- `MANAGED_BY`: Asset → User（资产管理者）

**新增方法：**
- `load_fields()`: 加载字段数据
- `load_business_domains()`: 加载业务域
- `load_business_zones()`: 加载业务专区
- `load_concepts()`: 加载业务概念
- `load_users()`: 加载用户数据
- `load_orgs()`: 加载组织数据
- `load_asset_domain_relationships()`: 资产-域关系
- `load_user_asset_relationships()`: 用户-资产关系

**新增约束和索引：**
- 为所有新节点创建唯一性约束
- 为高频查询字段创建索引
- 为FilterCondition相关属性创建复合索引

---

### 3. ✅ 图谱查询逻辑（`src/graph_rag/graph_query.py`）

**完全重写，支持8大意图的Cypher生成：**

| 意图 | 方法 | 支持的槽位 | 查询特点 |
|------|------|----------|---------|
| Intent 31 | `_generate_basic_search_cypher()` | AssetName, AssetType, BusinessDomain, FieldName, FilterCondition | 支持多条件组合查询 |
| Intent 32 | `_generate_metadata_query_cypher()` | AssetName, FieldName, MetadataItem | 支持资产级和字段级元数据 |
| Intent 33 | `_generate_quality_value_cypher()` | AssetName, MetadataItem | 查询价值评分和星级 |
| Intent 34 | `_generate_lineage_query_cypher()` | AssetName, FieldName | 简化版血缘查询（TODO：需LineageEdge） |
| Intent 35 | `_generate_usage_query_cypher()` | AssetName, UserStatus | 支持个性化查询 |
| Intent 36 | `_generate_scenario_recommendation_cypher()` | BusinessZone, CoreDataItem, AssetType | 场景化推荐 |
| Intent 37 | `_generate_comparison_cypher()` | AssetName（多个）, MetadataItem | 资产对比和复合筛选 |
| Intent 38 | （不需要查询） | - | 直接返回帮助信息 |

**新增辅助方法：**
- `_extract_slots()`: 从意图结果中提取槽位
- 更新`format_context()`: 支持新意图的结果格式化

---

### 4. ✅ 提示词配置（`config/prompt_config.yaml`）

**更新内容：**

1. **意图识别System Prompt**
   - 详细描述8大意图和示例
   - 详细描述10大槽位和识别规则
   - 强调AssetName完整性、MetadataItem同义词规范化
   - 严格的JSON输出格式要求

2. **答案生成System Prompt**
   - 针对数据资产领域优化
   - 为不同意图提供不同的回答风格指导
   - 强调专业术语的准确性

3. **新增平台帮助模板**
   - 替换原来的OOD模板
   - 提供数据资产平台的使用指导

4. **Cypher生成说明**
   - 移除旧的Prompt生成方式
   - 添加代码实现的Cypher示例

---

### 5. ✅ 编排器路由逻辑（`src/orchestrator/orchestrator.py`）

**更新内容：**
- 更新路由逻辑：将OOD判断替换为Intent 38（平台帮助）判断
- 其他7个意图统一走GraphRAG流程
- 新增`_get_intent_name()`方法：返回意图的中文名称
- 返回结果中新增`intent_name`字段
- 将`is_ood`改为`is_platform_help`

---

### 6. ✅ 主配置文件（`config/config.yaml`）

**更新内容：**

1. **系统配置**
   - 系统名称：AI知识助手 → 数据资产助手
   - 版本号：1.0.0 → 2.0.0
   - 新增系统描述

2. **意图标签配置**
   - 将5个意图替换为8个意图（"31"-"38"）
   - 添加详细注释

3. **槽位标签配置**
   - 新增`slot_labels`配置（10个槽位）
   - 保留`entity_labels`别名用于向后兼容

4. **图谱Schema配置**
   - 更新节点列表（新增6个节点类型）
   - 更新关系列表（新增10+种关系）
   - 添加详细注释标明槽位对应关系
   - 添加TODO标记未实现的血缘关系

---

## ⚠️ 未实现的功能（已添加TODO注释）

### 1. 血缘关系（LineageEdge）- TODO #7

**位置：** `src/graph_rag/graph_builder.py::load_lineage_relationships()`

**需要实现：**
```python
def load_lineage_relationships(self, lineage_file: str):
    """
    【TODO】加载血缘关系（Intent 34: 资产血缘关系查询）
    
    需要实现：
    1. LineageEdge中间节点（存储血缘关系属性）
    2. 支持多级递归查询（可能5-10级）
    3. 支持字段级血缘
    4. DAG结构验证（检测环路）
    """
    pass
```

**技术难点：**
- 需要设计LineageEdge中间节点存储血缘属性
- 需要支持递归查询（APOC插件或手动递归）
- 需要处理复杂的多路径血缘关系
- 性能优化（大规模血缘图的查询）

---

### 2. 同义词映射引擎 - TODO #8

**位置：** `src/graph_rag/graph_query.py::_generate_metadata_query_cypher()`

**当前实现：** 在代码中硬编码了部分同义词映射
```python
metadata_mapping = {
    '业务解释': 'business_purpose',
    '技术口径': 'technical_spec',
    # ...
}
```

**需要改进：**
1. 将同义词映射独立为配置文件或数据库
2. 支持动态添加新的同义词
3. 支持模糊匹配和相似度计算
4. 与MetadataItem的recognition_rule集成

**建议方案：**
```python
class SynonymMapper:
    def __init__(self):
        self.mappings = self.load_from_config()
    
    def normalize(self, user_input: str) -> str:
        """将用户输入规范化为标准值"""
        # 1. 精确匹配
        # 2. 模糊匹配
        # 3. 语义匹配（可选，使用embedding）
        pass
```

---

### 3. 三元组自动生成 - TODO #9

**相关位置：** 文档1提到的NLU结果到知识图谱三元组的转换

**需要明确：**
- 三元组的用途：是用于构建图谱还是记录查询日志？
- 生成规则：如何从NLU的槽位生成有意义的三元组？
- 应用场景：在哪个环节使用这些三元组？

**疑问点（需要确认）：**
```
NLU输出：{"intent": "32", "slots": {"AssetName": "XX资产", "MetadataItem": "业务口径"}}

应该生成什么三元组？
选项A: (XX资产, 查询元数据项, 业务口径)  ← 文档1的示例
选项B: (XX资产, 有属性, 业务口径)
选项C: 不生成三元组，直接转Cypher查询  ← 目前的实现
```

**建议：** 如果需要实现，请先明确三元组的用途和格式规范。

---

## 📊 代码修改统计

| 文件 | 修改类型 | 行数变化 | 主要内容 |
|------|---------|---------|---------|
| `intent_config.py` | 重写 | +370 / -100 | 8意图+10槽位定义 |
| `graph_builder.py` | 扩展 | +350 / -50 | 新增6种节点加载方法 |
| `graph_query.py` | 重写 | +500 / -150 | 8大意图Cypher生成 |
| `prompt_config.yaml` | 更新 | +100 / -60 | 新Prompt模板 |
| `orchestrator.py` | 更新 | +30 / -20 | 路由逻辑调整 |
| `config.yaml` | 更新 | +80 / -30 | Schema和标签配置 |
| **总计** | - | **+1430 / -410** | **净增加约1020行** |

---

## 🔄 向后兼容性

为了确保向后兼容，我们保留了以下内容：

1. **类型别名：**
   ```python
   EntityType = SlotType  # 向后兼容
   get_entity_by_name = get_slot_by_name  # 向后兼容
   ```

2. **配置别名：**
   ```yaml
   entity_labels:  # 保留旧名称
     - "AssetName"
     - "FieldName"
     # ...
   ```

3. **IntentResult数据类：**
   ```python
   @property
   def slots(self) -> List[Entity]:
       """槽位列表（别名）"""
       return self.entities  # entities和slots都支持
   ```

---

## 🚀 如何使用更新后的系统

### 1. 更新依赖（如有新增）
```bash
pip install -r requirements.txt
```

### 2. 更新Neo4j图谱Schema
```python
from src.graph_rag.graph_builder import GraphBuilder

builder = GraphBuilder()
builder.create_constraints()  # 创建新的约束和索引
```

### 3. 加载新的节点数据
```python
# 加载字段数据
builder.load_fields("data/raw/fields/fields.csv")

# 加载业务域
builder.load_business_domains("data/raw/domains/domains.csv")

# 加载业务专区
builder.load_business_zones("data/raw/zones/zones.csv")

# 加载业务概念
builder.load_concepts("data/raw/concepts/concepts.csv")

# 加载用户和组织
builder.load_users("data/raw/users/users.csv")
builder.load_orgs("data/raw/orgs/orgs.csv")

# 加载关系
builder.load_asset_domain_relationships("data/raw/relationships/asset_domain.csv")
builder.load_user_asset_relationships("data/raw/relationships/user_asset.csv")
```

### 4. 重新训练意图识别模型
```python
# 使用新的8大意图和10大槽位标注数据进行SFT训练
python -m src.intent_recognition.intent_trainer \
  --train_file data/processed/training/train_v2.jsonl \
  --output_dir models/intent_recognition_v2 \
  --base_model /path/to/qwen3-32b
```

### 5. 测试新的查询
```python
from src.orchestrator.orchestrator import Orchestrator

orchestrator = Orchestrator()

# Intent 31: 基础检索
result = orchestrator.process_query("平台上有哪些五星资产？")

# Intent 32: 元数据查询
result = orchestrator.process_query("XX资产的业务口径是什么？")

# Intent 33: 质量价值查询
result = orchestrator.process_query("XX资产的价值评估分数是多少？")

# Intent 36: 场景推荐
result = orchestrator.process_query("公众智慧运营专区有哪些资产？")

# Intent 37: 资产对比
result = orchestrator.process_query("XX资产和YY资产有什么关系？")

print(result['answer'])
print(result['intent_name'])  # 新增字段：意图中文名称
```

---

## 📝 数据准备指南

### CSV文件格式要求

#### 1. fields.csv（字段数据）
```csv
field_id,asset_id,name,data_type,description,business_definition,technical_definition
field_001,asset_001,user_id,STRING,用户唯一标识,业务主键,varchar(32)
field_002,asset_001,order_id,STRING,订单ID,订单标识,varchar(64)
```

#### 2. business_domains.csv（业务域）
```csv
domain_id,name,description
domain_m,M域,移动网络域
domain_o,O域,运营支撑域
domain_b,B域,业务应用域
```

#### 3. business_zones.csv（业务专区）
```csv
zone_id,name,description
zone_001,公众智慧运营,面向公众客户的智能运营专区
zone_002,一线赋能专区,支持一线员工的数据赋能
```

#### 4. concepts.csv（业务概念）
```csv
concept_id,name,type,definition,description
concept_001,5G登网,业务指标,用户是否登录5G网络,标识用户5G使用情况
concept_002,用户活跃度,业务指标,用户活跃程度,综合评估用户活跃度
```

#### 5. users.csv（用户）
```csv
user_id,name,role,org_id
user_001,张三,数据管理员,org_001
user_002,李四,数据分析师,org_002
```

#### 6. orgs.csv（组织）
```csv
org_id,name,parent_org_id,description
org_001,总部-数据部,,总部数据管理部门
org_002,营销中心,org_001,营销业务部门
```

#### 7. asset_domain.csv（资产-域关系）
```csv
asset_id,domain_id
asset_001,domain_m
asset_002,domain_o
```

#### 8. user_asset.csv（用户-资产关系）
```csv
user_id,asset_id,relationship_type,timestamp
user_001,asset_001,FAVORITED,2025-10-26 10:00:00
user_001,asset_002,SUBSCRIBED,2025-10-26 11:00:00
```

---

## ✅ 测试检查清单

- [ ] **意图识别测试**
  - [ ] 测试8个意图是否能正确识别
  - [ ] 测试10个槽位是否能正确抽取
  - [ ] 测试同义词是否能正确映射

- [ ] **图谱查询测试**
  - [ ] Intent 31: 基础检索（多条件组合）
  - [ ] Intent 32: 元数据查询（资产级+字段级）
  - [ ] Intent 33: 质量价值查询
  - [ ] Intent 34: 血缘查询（简化版）
  - [ ] Intent 35: 使用查询（个性化）
  - [ ] Intent 36: 场景推荐
  - [ ] Intent 37: 资产对比和复合筛选
  - [ ] Intent 38: 平台帮助

- [ ] **图谱数据测试**
  - [ ] 新节点（Field, BusinessZone, Concept等）是否创建成功
  - [ ] 新关系（HAS_FIELD, FAVORITED等）是否创建成功
  - [ ] 索引和约束是否生效

- [ ] **端到端测试**
  - [ ] 完整查询流程是否正常
  - [ ] 返回结果格式是否正确
  - [ ] 性能是否满足要求

---

## 🐛 已知问题

1. **FilterCondition解析简化**
   - 当前实现：简单的字符串匹配
   - 问题：无法处理复杂条件（如"价值评估>80分且最近一周更新"）
   - 建议：实现专门的条件解析器

2. **UserStatus的用户ID获取**
   - 当前实现：硬编码为"current_user"
   - 问题：需要从session或context获取真实用户ID
   - 建议：集成用户认证系统

3. **血缘查询未完整实现**
   - 当前实现：只支持直接上下游查询
   - 问题：无法递归查询多级血缘
   - 建议：实现LineageEdge中间节点

---

## 📚 相关文档

- 原技术文档：`/path/to/original_tech_doc.md`
- 新需求文档1：数据资产助手意图识别方案
- 新需求文档2：10大槽位定义
- 图谱Schema设计：`config/config.yaml` (graph.schema部分)
- Prompt配置：`config/prompt_config.yaml`

---

## 👥 联系方式

如有问题，请联系：
- 项目负责人：[姓名]
- Email：[邮箱]

---

## 📜 更新日志

### v2.0.0 (2025-10-26)
- ✅ 升级为8大意图和10大槽位体系
- ✅ 扩展图谱Schema（新增6种节点类型）
- ✅ 重写图谱查询逻辑（支持8大意图）
- ✅ 更新所有提示词配置
- ⚠️ 血缘关系、同义词映射、三元组生成待实现

### v1.0.0 (2024-xx-xx)
- 初始版本：5意图4实体体系

---

**更新完成！🎉**

