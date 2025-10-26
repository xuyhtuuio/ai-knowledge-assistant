"""
知识图谱构建模块
负责将原始数据构建为Neo4j知识图谱
"""

import os
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import yaml

logger = logging.getLogger(__name__)


"""
图谱Schema设计一览

cypher
// ========== 核心实体节点 ==========
// 槽位1：AssetName
(Asset {
  asset_id: string,
  name: string,
  description: string,
  type: string,          // 槽位6：AssetType
  star_level: string,    // 用于FilterCondition
  value_score: int,      // 用于FilterCondition
  update_time: datetime
})

// 槽位3：FieldName
(Field {
  field_id: string,
  name: string,
  data_type: string,
  description: string
})

// 槽位5：BusinessDomain
(BusinessDomain {
  domain_id: string,
  name: string,          // M域、O域、B域
  description: string
})

// 槽位7：BusinessZone
(BusinessZone {
  zone_id: string,
  name: string,          // 公众智慧运营、一线赋能专区
  description: string
})

// 槽位7关联：Scenario（BusinessZone的子节点）
(Scenario {
  scenario_id: string,
  name: string,
  description: string
})

// 槽位4：CoreDataItem
(Concept {
  concept_id: string,
  name: string,          // 5G登网、移网用户是否活跃
  type: string,          // 业务指标、业务概念
  definition: string
})

// 槽位10：User
(User {
  user_id: string,
  name: string,
  role: string,
  org_id: string
})

// 槽位10：Org
(Org {
  org_id: string,
  name: string,
  parent_org_id: string
})

// 槽位2：MetadataItem（用于扩展元数据）
(MetadataItem {
  item_id: string,
  name: string,          // 业务口径、技术口径、简介/用途
  display_name: string,
  data_type: string
})

// ========== 核心关系 ==========
// 资产-字段
(Asset) -[:HAS_FIELD]-> (Field)

// 资产-业务域
(Asset) -[:BELONGS_TO]-> (BusinessDomain)

// 资产-专区-场景（三层结构）
(BusinessZone) -[:CONTAINS_SCENARIO]-> (Scenario)
(Scenario) -[:USES_ASSET]-> (Asset)
// 或者资产直接关联专区（如果是多对多）
(Asset) -[:IN_ZONE]-> (BusinessZone)

// 资产-业务概念（槽位4）
(Concept) -[:IMPLEMENTED_BY]-> (Asset)
(Concept) -[:MAPPED_TO]-> (Field)

// 用户-资产（槽位9：UserStatus）
(User) -[:FAVORITED {time: datetime()}]-> (Asset)
(User) -[:SUBSCRIBED {status: string}]-> (Asset)

// 用户-组织（槽位10）
(User) -[:BELONGS_TO]-> (Org)
(Asset) -[:MANAGED_BY]-> (User)
(Asset) -[:OWNED_BY]-> (Org)

// 血缘关系（中间节点）
(Asset) -[:PRODUCES]-> (LineageEdge) <-[:CONSUMES]- (Asset)
(Field) -[:DERIVED_FROM]-> (FieldLineage) <-[:FEEDS_INTO]- (Field)

// 元数据关系（可选）
(Asset) -[:HAS_METADATA]-> (MetadataValue {type: string, content: string})
(Field) -[:HAS_METADATA]-> (MetadataValue)

// ========== 槽位8：FilterCondition处理 ==========
// 不建模为节点，而是在查询时动态解析为WHERE条件
// 需要一个条件解析引擎（规则或LLM）


比如： 近一周新上线资产有哪些？ 需要匹配时间范围



"""









class GraphBuilder:
    """知识图谱构建器"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化图谱构建器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.graph_config = self.config['graph']
        self.data_config = self.config['data']

        # 连接Neo4j
        self.driver = None
        self.connect_neo4j()

        logger.info("图谱构建器初始化完成")

    def connect_neo4j(self):
        """连接Neo4j数据库"""
        neo4j_config = self.graph_config['neo4j']

        try:
            self.driver = GraphDatabase.driver(
                neo4j_config['uri'],
                auth=(neo4j_config['user'], neo4j_config['password'])
            )
            # 测试连接
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            logger.info(f"成功连接Neo4j: {neo4j_config['uri']}")
        except Exception as e:
            logger.error(f"Neo4j连接失败: {str(e)}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j连接已关闭")

    def clear_graph(self):
        """清空图谱（谨慎使用）"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("图谱已清空")

    def create_constraints(self):
        """
        创建约束和索引
        """
        with self.driver.session() as session:
            # ========== 核心节点约束 ==========
            # 资产节点约束（槽位1: AssetName）
            session.run(
                "CREATE CONSTRAINT asset_id_unique IF NOT EXISTS "
                "FOR (a:Asset) REQUIRE a.asset_id IS UNIQUE"
            )

            # 字段节点约束（槽位3: FieldName）【新增】
            session.run(
                "CREATE CONSTRAINT field_id_unique IF NOT EXISTS "
                "FOR (f:Field) REQUIRE f.field_id IS UNIQUE"
            )

            # 业务域节点约束（槽位5: BusinessDomain）【新增】
            session.run(
                "CREATE CONSTRAINT domain_id_unique IF NOT EXISTS "
                "FOR (d:BusinessDomain) REQUIRE d.domain_id IS UNIQUE"
            )

            # 业务专区节点约束（槽位7: BusinessZone）【新增】
            session.run(
                "CREATE CONSTRAINT zone_id_unique IF NOT EXISTS "
                "FOR (z:BusinessZone) REQUIRE z.zone_id IS UNIQUE"
            )

            # 场景节点约束（保留，用于BusinessZone的子节点）
            session.run(
                "CREATE CONSTRAINT scenario_id_unique IF NOT EXISTS "
                "FOR (s:Scenario) REQUIRE s.scenario_id IS UNIQUE"
            )

            # 业务概念节点约束（槽位4: CoreDataItem）【新增】
            session.run(
                "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS "
                "FOR (c:Concept) REQUIRE c.concept_id IS UNIQUE"
            )

            # 用户节点约束（槽位9: UserStatus）【新增】
            session.run(
                "CREATE CONSTRAINT user_id_unique IF NOT EXISTS "
                "FOR (u:User) REQUIRE u.user_id IS UNIQUE"
            )

            # 组织节点约束（槽位10: OrgName/UserName）【新增】
            session.run(
                "CREATE CONSTRAINT org_id_unique IF NOT EXISTS "
                "FOR (o:Org) REQUIRE o.org_id IS UNIQUE"
            )

            # 热点节点约束（保留，但可能在数据资产场景中不常用）
            session.run(
                "CREATE CONSTRAINT hotspot_id_unique IF NOT EXISTS "
                "FOR (h:Hotspot) REQUIRE h.hotspot_id IS UNIQUE"
            )

            # ========== 索引（提高查询效率）==========
            # 资产名称索引（高频查询）
            session.run(
                "CREATE INDEX asset_name_index IF NOT EXISTS "
                "FOR (a:Asset) ON (a.name)"
            )

            # 字段名称索引（支持字段级查询）
            session.run(
                "CREATE INDEX field_name_index IF NOT EXISTS "
                "FOR (f:Field) ON (f.name)"
            )

            # 业务域名称索引
            session.run(
                "CREATE INDEX domain_name_index IF NOT EXISTS "
                "FOR (d:BusinessDomain) ON (d.name)"
            )

            # 业务专区名称索引
            session.run(
                "CREATE INDEX zone_name_index IF NOT EXISTS "
                "FOR (z:BusinessZone) ON (z.name)"
            )

            # 场景名称索引
            session.run(
                "CREATE INDEX scenario_name_index IF NOT EXISTS "
                "FOR (s:Scenario) ON (s.name)"
            )

            # 业务概念名称索引（用于CoreDataItem全文搜索）
            session.run(
                "CREATE INDEX concept_name_index IF NOT EXISTS "
                "FOR (c:Concept) ON (c.name)"
            )

            # 用户名索引
            session.run(
                "CREATE INDEX user_name_index IF NOT EXISTS "
                "FOR (u:User) ON (u.name)"
            )

            # 组织名称索引
            session.run(
                "CREATE INDEX org_name_index IF NOT EXISTS "
                "FOR (o:Org) ON (o.name)"
            )

            # 热点标题索引
            session.run(
                "CREATE INDEX hotspot_title_index IF NOT EXISTS "
                "FOR (h:Hotspot) ON (h.title)"
            )

            # ========== 复合索引（支持FilterCondition筛选）==========
            # 资产类型+星级索引
            session.run(
                "CREATE INDEX asset_type_star_index IF NOT EXISTS "
                "FOR (a:Asset) ON (a.type, a.star_level)"
            )

            # 资产价值评分索引（支持范围查询）
            session.run(
                "CREATE INDEX asset_value_score_index IF NOT EXISTS "
                "FOR (a:Asset) ON (a.value_score)"
            )

        logger.info("约束和索引创建完成（支持新Schema）")

    def load_assets(self, asset_file: str):
        """
        加载资产数据

        Args:
            asset_file: 资产CSV文件路径
            CSV格式应包含：asset_id, name, description, owner, type, version, status,
                        star_level(星级), value_score(价值评分), update_time(更新时间)等
        """
        logger.info(f"加载资产数据: {asset_file}")

        # 读取CSV
        df = pd.read_csv(asset_file)

        # 批量创建节点
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(
                    """
                    MERGE (a:Asset {asset_id: $asset_id})
                    SET a.name = $name,
                        a.description = $description,
                        a.owner = $owner,
                        a.type = $type,
                        a.version = $version,
                        a.status = $status,
                        a.star_level = $star_level,
                        a.value_score = $value_score,
                        a.update_time = $update_time,
                        a.business_purpose = $business_purpose,
                        a.technical_spec = $technical_spec
                    """,
                    asset_id=row.get('asset_id', ''),
                    name=row.get('name', ''),
                    description=row.get('description', ''),
                    owner=row.get('owner', ''),
                    type=row.get('type', ''),  # 槽位6: AssetType
                    version=row.get('version', ''),
                    status=row.get('status', ''),
                    star_level=row.get('star_level', ''),  # 槽位8: FilterCondition（五星）
                    value_score=row.get('value_score', 0),  # 槽位8: FilterCondition（价值评分）
                    update_time=row.get('update_time', ''),  # 槽位8: FilterCondition（更新时间）
                    business_purpose=row.get('business_purpose', ''),  # 槽位2: MetadataItem（业务口径）
                    technical_spec=row.get('technical_spec', '')  # 槽位2: MetadataItem（技术口径）
                )

        logger.info(f"成功加载 {len(df)} 个资产节点")

    def load_scenarios(self, scenario_file: str):
        """
        加载场景数据

        Args:
            scenario_file: 场景CSV文件路径
        """
        logger.info(f"加载场景数据: {scenario_file}")

        df = pd.read_csv(scenario_file)

        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(
                    """
                    MERGE (s:Scenario {scenario_id: $scenario_id})
                    SET s.name = $name,
                        s.description = $description,
                        s.business_domain = $business_domain,
                        s.status = $status
                    """,
                    scenario_id=row.get('scenario_id', ''),
                    name=row.get('name', ''),
                    description=row.get('description', ''),
                    business_domain=row.get('business_domain', ''),
                    status=row.get('status', '')
                )

        logger.info(f"成功加载 {len(df)} 个场景节点")

    def load_hotspots(self, hotspot_file: str):
        """
        加载热点数据

        Args:
            hotspot_file: 热点CSV文件路径
        """
        logger.info(f"加载热点数据: {hotspot_file}")

        df = pd.read_csv(hotspot_file)

        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(
                    """
                    MERGE (h:Hotspot {hotspot_id: $hotspot_id})
                    SET h.title = $title,
                        h.summary = $summary,
                        h.publish_date = $publish_date,
                        h.source = $source,
                        h.category = $category
                    """,
                    hotspot_id=row.get('hotspot_id', ''),
                    title=row.get('title', ''),
                    summary=row.get('summary', ''),
                    publish_date=row.get('publish_date', ''),
                    source=row.get('source', ''),
                    category=row.get('category', '')
                )

        logger.info(f"成功加载 {len(df)} 个热点节点")

    def load_asset_scenario_relationships(self, relationship_file: str):
        """
        加载资产-场景关系（使用AssetUsage中间节点）

        Args:
            relationship_file: 关系CSV文件路径
                格式: asset_id, scenario_id, role, status, description
        """
        logger.info(f"加载资产-场景关系: {relationship_file}")

        df = pd.read_csv(relationship_file)

        with self.driver.session() as session:
            for idx, row in df.iterrows():
                # 创建AssetUsage中间节点
                usage_id = f"usage_{row['asset_id']}_{row['scenario_id']}_{idx}"

                session.run(
                    """
                    MATCH (a:Asset {asset_id: $asset_id})
                    MATCH (s:Scenario {scenario_id: $scenario_id})
                    MERGE (u:AssetUsage {usage_id: $usage_id})
                    SET u.role = $role,
                        u.status = $status,
                        u.description = $description
                    MERGE (s)-[:INCLUDES_USAGE]->(u)
                    MERGE (a)-[:IS_USED_IN]->(u)
                    """,
                    asset_id=row['asset_id'],
                    scenario_id=row['scenario_id'],
                    usage_id=usage_id,
                    role=row.get('role', ''),
                    status=row.get('status', ''),
                    description=row.get('description', '')
                )

        logger.info(f"成功创建 {len(df)} 个资产-场景关系")

    def load_hotspot_asset_relationships(self, relationship_file: str):
        """
        加载热点-资产关系

        Args:
            relationship_file: 关系CSV文件路径
                格式: hotspot_id, asset_id, impact_type, description
        """
        logger.info(f"加载热点-资产关系: {relationship_file}")

        df = pd.read_csv(relationship_file)

        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(
                    """
                    MATCH (h:Hotspot {hotspot_id: $hotspot_id})
                    MATCH (a:Asset {asset_id: $asset_id})
                    MERGE (h)-[r:DIRECTLY_IMPACTS]->(a)
                    SET r.impact_type = $impact_type,
                        r.description = $description
                    """,
                    hotspot_id=row['hotspot_id'],
                    asset_id=row['asset_id'],
                    impact_type=row.get('impact_type', ''),
                    description=row.get('description', '')
                )

        logger.info(f"成功创建 {len(df)} 个热点-资产关系")

    def build_full_graph(self,
                         asset_file: str,
                         scenario_file: str,
                         hotspot_file: str,
                         asset_scenario_rel_file: str,
                         field_file: str,
                         domain_file: str,
                         zone_file: str,
                         concept_file: str,
                         user_file: str,
                         org_file: str,
                         relationship_file: str,
                         lineage_file: str,
                         hotspot_asset_rel_file: Optional[str] = None):
        """
        构建完整知识图谱

        Args:
            asset_file: 资产文件
            scenario_file: 场景文件
            hotspot_file: 热点文件
            asset_scenario_rel_file: 资产-场景关系文件
            hotspot_asset_rel_file: 热点-资产关系文件
        """
        logger.info("开始构建知识图谱...")

        # 创建约束
        self.create_constraints()

        # 加载节点
        self.load_assets(asset_file)
        self.load_scenarios(scenario_file)
        self.load_hotspots(hotspot_file)
        self.load_fields(field_file)
        self.load_business_domains(domain_file)
        self.load_business_zones(zone_file)
        self.load_concepts(concept_file)
        self.load_users(user_file)
        self.load_orgs(org_file)
        self.load_asset_domain_relationships(relationship_file)
        self.load_user_asset_relationships(relationship_file)
        self.load_lineage_relationships(lineage_file)
        self.load_asset_scenario_relationships(asset_scenario_rel_file)
        self.load_hotspot_asset_relationships(hotspot_asset_rel_file)

        # 加载关系
        self.load_asset_scenario_relationships(asset_scenario_rel_file)

        if hotspot_asset_rel_file and os.path.exists(hotspot_asset_rel_file):
            self.load_hotspot_asset_relationships(hotspot_asset_rel_file)

        logger.info("知识图谱构建完成！")


    def load_fields(self, field_file: str):
        """
        加载字段数据（槽位3: FieldName）
        
        Args:
            field_file: 字段CSV文件路径
            CSV格式：field_id, asset_id, name, data_type, description, business_definition, technical_definition
        """
        logger.info(f"加载字段数据: {field_file}")
        df = pd.read_csv(field_file)
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # 创建Field节点
                session.run(
                    """
                    MERGE (f:Field {field_id: $field_id})
                    SET f.name = $name,
                        f.data_type = $data_type,
                        f.description = $description,
                        f.business_definition = $business_definition,
                        f.technical_definition = $technical_definition
                    """,
                    field_id=row.get('field_id', ''),
                    name=row.get('name', ''),
                    data_type=row.get('data_type', ''),
                    description=row.get('description', ''),
                    business_definition=row.get('business_definition', ''),
                    technical_definition=row.get('technical_definition', '')
                )
                
                # 创建Asset-Field关系
                if 'asset_id' in row and row['asset_id']:
                    session.run(
                        """
                        MATCH (a:Asset {asset_id: $asset_id})
                        MATCH (f:Field {field_id: $field_id})
                        MERGE (a)-[:HAS_FIELD]->(f)
                        """,
                        asset_id=row['asset_id'],
                        field_id=row['field_id']
                    )
        
        logger.info(f"成功加载 {len(df)} 个字段节点")
    
    def load_business_domains(self, domain_file: str):
        """
        加载业务域数据（槽位5: BusinessDomain）
        
        Args:
            domain_file: 业务域CSV文件路径
            CSV格式：domain_id, name, description, parent_domain_id
        """
        logger.info(f"加载业务域数据: {domain_file}")
        df = pd.read_csv(domain_file)
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(
                    """
                    MERGE (d:BusinessDomain {domain_id: $domain_id})
                    SET d.name = $name,
                        d.description = $description
                    """,
                    domain_id=row.get('domain_id', ''),
                    name=row.get('name', ''),
                    description=row.get('description', '')
                )
        
        logger.info(f"成功加载 {len(df)} 个业务域节点")
    
    def load_business_zones(self, zone_file: str):
        """
        加载业务专区数据（槽位7: BusinessZone）
        
        Args:
            zone_file: 业务专区CSV文件路径
            CSV格式：zone_id, name, description
        """
        logger.info(f"加载业务专区数据: {zone_file}")
        df = pd.read_csv(zone_file)
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(
                    """
                    MERGE (z:BusinessZone {zone_id: $zone_id})
                    SET z.name = $name,
                        z.description = $description
                    """,
                    zone_id=row.get('zone_id', ''),
                    name=row.get('name', ''),
                    description=row.get('description', '')
                )
        
        logger.info(f"成功加载 {len(df)} 个业务专区节点")
    
    def load_concepts(self, concept_file: str):
        """
        加载业务概念数据（槽位4: CoreDataItem）
        
        Args:
            concept_file: 业务概念CSV文件路径
            CSV格式：concept_id, name, type, definition, description
        """
        logger.info(f"加载业务概念数据: {concept_file}")
        df = pd.read_csv(concept_file)
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(
                    """
                    MERGE (c:Concept {concept_id: $concept_id})
                    SET c.name = $name,
                        c.type = $type,
                        c.definition = $definition,
                        c.description = $description
                    """,
                    concept_id=row.get('concept_id', ''),
                    name=row.get('name', ''),
                    type=row.get('type', '业务指标'),
                    definition=row.get('definition', ''),
                    description=row.get('description', '')
                )
        
        logger.info(f"成功加载 {len(df)} 个业务概念节点")
    
    def load_users(self, user_file: str):
        """
        加载用户数据（槽位9: UserStatus）
        
        Args:
            user_file: 用户CSV文件路径
            CSV格式：user_id, name, role, org_id
        """
        logger.info(f"加载用户数据: {user_file}")
        df = pd.read_csv(user_file)
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(
                    """
                    MERGE (u:User {user_id: $user_id})
                    SET u.name = $name,
                        u.role = $role,
                        u.org_id = $org_id
                    """,
                    user_id=row.get('user_id', ''),
                    name=row.get('name', ''),
                    role=row.get('role', ''),
                    org_id=row.get('org_id', '')
                )
        
        logger.info(f"成功加载 {len(df)} 个用户节点")
    
    def load_orgs(self, org_file: str):
        """
        加载组织机构数据（槽位10: OrgName/UserName）
        
        Args:
            org_file: 组织CSV文件路径
            CSV格式：org_id, name, parent_org_id, description
        """
        logger.info(f"加载组织数据: {org_file}")
        df = pd.read_csv(org_file)
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(
                    """
                    MERGE (o:Org {org_id: $org_id})
                    SET o.name = $name,
                        o.parent_org_id = $parent_org_id,
                        o.description = $description
                    """,
                    org_id=row.get('org_id', ''),
                    name=row.get('name', ''),
                    parent_org_id=row.get('parent_org_id', ''),
                    description=row.get('description', '')
                )
        
        logger.info(f"成功加载 {len(df)} 个组织节点")
    
    def load_asset_domain_relationships(self, relationship_file: str):
        """
        加载资产-业务域关系
        
        Args:
            relationship_file: 关系CSV文件路径
            CSV格式：asset_id, domain_id
        """
        logger.info(f"加载资产-业务域关系: {relationship_file}")
        df = pd.read_csv(relationship_file)
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(
                    """
                    MATCH (a:Asset {asset_id: $asset_id})
                    MATCH (d:BusinessDomain {domain_id: $domain_id})
                    MERGE (a)-[:BELONGS_TO]->(d)
                    """,
                    asset_id=row['asset_id'],
                    domain_id=row['domain_id']
                )
        
        logger.info(f"成功创建 {len(df)} 个资产-业务域关系")
    
    def load_user_asset_relationships(self, relationship_file: str):
        """
        加载用户-资产关系（收藏、订阅等）
        
        Args:
            relationship_file: 关系CSV文件路径
            CSV格式：user_id, asset_id, relationship_type(FAVORITED/SUBSCRIBED/CREATED), timestamp
        """
        logger.info(f"加载用户-资产关系: {relationship_file}")
        df = pd.read_csv(relationship_file)
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                rel_type = row.get('relationship_type', 'FAVORITED')
                
                session.run(
                    f"""
                    MATCH (u:User {{user_id: $user_id}})
                    MATCH (a:Asset {{asset_id: $asset_id}})
                    MERGE (u)-[r:{rel_type}]->(a)
                    SET r.timestamp = $timestamp
                    """,
                    user_id=row['user_id'],
                    asset_id=row['asset_id'],
                    timestamp=row.get('timestamp', '')
                )
        
        logger.info(f"成功创建 {len(df)} 个用户-资产关系")
    

    # 【TODO】血缘关系相关方法 
    def load_lineage_relationships(self, lineage_file: str):
        """
        【TODO】加载血缘关系（Intent 34: 资产血缘关系查询）
        
        需要实现：
        1. LineageEdge中间节点（存储血缘关系属性）
        2. 支持多级递归查询（可能5-10级）
        3. 支持字段级血缘
        4. DAG结构验证（检测环路）
        
        Args:
            lineage_file: 血缘关系CSV文件路径
            CSV格式：source_asset_id, target_asset_id, lineage_type, 
                    transform_logic, update_frequency, data_volume
        """
        logger.warning("血缘关系加载功能尚未实现，需要实现LineageEdge中间节点和递归查询")
        # TODO: 实现血缘关系加载
        pass

    def get_graph_stats(self) -> Dict[str, int]:
        """
        获取图谱统计信息
        """
        with self.driver.session() as session:
            # 节点数量
            asset_count = session.run("MATCH (a:Asset) RETURN count(a) as count").single()['count']
            field_count = session.run("MATCH (f:Field) RETURN count(f) as count").single()['count']
            domain_count = session.run("MATCH (d:BusinessDomain) RETURN count(d) as count").single()['count']
            zone_count = session.run("MATCH (z:BusinessZone) RETURN count(z) as count").single()['count']
            scenario_count = session.run("MATCH (s:Scenario) RETURN count(s) as count").single()['count']
            concept_count = session.run("MATCH (c:Concept) RETURN count(c) as count").single()['count']
            user_count = session.run("MATCH (u:User) RETURN count(u) as count").single()['count']
            org_count = session.run("MATCH (o:Org) RETURN count(o) as count").single()['count']
            hotspot_count = session.run("MATCH (h:Hotspot) RETURN count(h) as count").single()['count']
            usage_count = session.run("MATCH (u:AssetUsage) RETURN count(u) as count").single()['count']

            # 关系数量
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']

        stats = {
            "资产节点": asset_count,
            "字段节点": field_count,
            "业务域节点": domain_count,
            "业务专区节点": zone_count,
            "场景节点": scenario_count,
            "业务概念节点": concept_count,
            "用户节点": user_count,
            "组织节点": org_count,
            "热点节点": hotspot_count,
            "应用实例节点": usage_count,
            "关系总数": rel_count
        }

        return stats


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    builder = GraphBuilder()

    # 构建图谱
    builder.build_full_graph(
        asset_file="data/raw/assets/assets.csv",
        scenario_file="data/raw/scenarios/scenarios.csv",
        hotspot_file="data/raw/hotspots/hotspots.csv",
        asset_scenario_rel_file="data/raw/relationships/asset_scenario.csv",
        field_file="data/raw/fields/fields.csv",
        domain_file="data/raw/domains/domains.csv",
        zone_file="data/raw/zones/zones.csv",
        concept_file="data/raw/concepts/concepts.csv",
        user_file="data/raw/users/users.csv",
        org_file="data/raw/orgs/orgs.csv",
        relationship_file="data/raw/relationships/relationships.csv",
        lineage_file="data/raw/relationships/lineage.csv",
        hotspot_asset_rel_file="data/raw/relationships/hotspot_asset.csv"
    )

    # 查看统计
    stats = builder.get_graph_stats()
    print("\n图谱统计:")
    for key, value in stats.items():
        print(f"{key}: {value}")

    builder.close()
