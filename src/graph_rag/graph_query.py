"""
图谱查询模块
负责将意图和槽位转换为Cypher查询，并执行检索
"""

import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import yaml

from ..intent_recognition.intent_config import IntentType, IntentResult, Entity, SlotType

logger = logging.getLogger(__name__)


class GraphQuery:
    """
    图谱查询器数据资产助手的8大意图
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化图谱查询器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.graph_config = self.config['graph']

        # 连接Neo4j
        self.driver = None
        self.connect_neo4j()

        logger.info("图谱查询器初始化完成（支持8大意图）")

    def connect_neo4j(self):
        """连接Neo4j数据库"""
        neo4j_config = self.graph_config['neo4j']

        try:
            self.driver = GraphDatabase.driver(
                neo4j_config['uri'],
                auth=(neo4j_config['user'], neo4j_config['password'])
            )
            logger.info(f"成功连接Neo4j: {neo4j_config['uri']}")
        except Exception as e:
            logger.error(f"Neo4j连接失败: {str(e)}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j连接已关闭")

    def _extract_slots(self, intent_result: IntentResult) -> Dict[str, List[str]]:
        """
        从意图结果中提取槽位值
        
        Args:
            intent_result: 意图识别结果
        
        Returns:
            槽位字典 {槽位类型: [值列表]}
        """
        slots = {}
        for entity in intent_result.entities:
            slot_type = entity.type.value
            if slot_type not in slots:
                slots[slot_type] = []
            slots[slot_type].append(entity.value)
        return slots

    def generate_cypher(self, intent_result: IntentResult) -> str:
        """
        根据意图和槽位生成Cypher查询

        Args:
            intent_result: 意图识别结果

        Returns:
            Cypher查询语句
        """
        intent = intent_result.intent
        slots = self._extract_slots(intent_result)

        # 根据意图类型生成不同的Cypher
        if intent == IntentType.ASSET_BASIC_SEARCH:
            return self._generate_basic_search_cypher(slots)
        
        elif intent == IntentType.ASSET_METADATA_QUERY:
            return self._generate_metadata_query_cypher(slots)
        
        elif intent == IntentType.ASSET_QUALITY_VALUE_QUERY:
            return self._generate_quality_value_cypher(slots)
        
        elif intent == IntentType.ASSET_LINEAGE_QUERY:
            return self._generate_lineage_query_cypher(slots)
        
        elif intent == IntentType.ASSET_USAGE_QUERY:
            return self._generate_usage_query_cypher(slots)
        
        elif intent == IntentType.SCENARIO_RECOMMENDATION:
            return self._generate_scenario_recommendation_cypher(slots)
        
        elif intent == IntentType.ASSET_COMPARISON:
            return self._generate_comparison_cypher(slots)
        
        elif intent == IntentType.PLATFORM_HELP:
            return ""  # 平台帮助不需要查询图谱
        
        else:
            logger.warning(f"未知意图类型: {intent}")
            return ""

    # Intent 31: 资产基础检索
    def _generate_basic_search_cypher(self, slots: Dict[str, List[str]]) -> str:
        """
        生成基础检索Cypher
        支持槽位：AssetName, AssetType, BusinessDomain, FieldName, FilterCondition
        """
        conditions = []
        
        # 槽位1: AssetName
        if 'AssetName' in slots:
            asset_name = slots['AssetName'][0]
            conditions.append(f'a.name = "{asset_name}"')
        
        # 槽位6: AssetType
        if 'AssetType' in slots:
            asset_type = slots['AssetType'][0]
            conditions.append(f'a.type = "{asset_type}"')
        
        # 槽位8: FilterCondition（示例：五星、价值评分）
        if 'FilterCondition' in slots:
            filter_cond = slots['FilterCondition'][0]
            # TODO: 需要实现FilterCondition解析器
            
            
            
            if '五星' in filter_cond:
                conditions.append('a.star_level = "五星"')
            elif '>' in filter_cond or '<' in filter_cond:
                # 简单解析数值条件
                conditions.append(f'a.value_score {filter_cond.split("价值评估")[1].strip()}')
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 槽位5: BusinessDomain
        if 'BusinessDomain' in slots:
            domain_name = slots['BusinessDomain'][0]
            cypher = f"""
            MATCH (a:Asset)-[:BELONGS_TO]->(d:BusinessDomain {{name: "{domain_name}"}})
            WHERE {where_clause}
            RETURN a.name AS name, a.description AS description,
                   a.type AS type, a.star_level AS star_level,
                   a.value_score AS value_score, d.name AS domain
            LIMIT 50
            """
        # 槽位3: FieldName（查询包含特定字段的资产）
        elif 'FieldName' in slots:
            field_name = slots['FieldName'][0]
            cypher = f"""
            MATCH (a:Asset)-[:HAS_FIELD]->(f:Field {{name: "{field_name}"}})
            WHERE {where_clause}
            RETURN a.name AS name, a.description AS description,
                   a.type AS type, f.name AS field_name
            LIMIT 50
            """
        else:
            # 基础查询
            cypher = f"""
            MATCH (a:Asset)
            WHERE {where_clause}
            RETURN a.name AS name, a.description AS description,
                   a.type AS type, a.star_level AS star_level,
                   a.value_score AS value_score
            LIMIT 50
            """
        
        return cypher.strip()

    # Intent 32: 资产元数据查询
    def _generate_metadata_query_cypher(self, slots: Dict[str, List[str]]) -> str:
        """
        生成元数据查询Cypher
        支持槽位：AssetName, FieldName, MetadataItem
        """
        # 槽位1: AssetName
        if 'AssetName' in slots:
            asset_name = slots['AssetName'][0]
            
            # 槽位2: MetadataItem
            metadata_item = slots.get('MetadataItem', ['所有'])[0]
            
            # TODO: 同义词映射（将"业务解释"映射为"business_purpose"）
            metadata_mapping = {
                '业务口径': 'business_purpose',
                '技术口径': 'technical_spec',
                '简介': 'description',
                '用途': 'description',
                '负责人': 'owner',
                '版本': 'version',
                '状态': 'status'
            }
            
            if metadata_item in metadata_mapping:
                field_name = metadata_mapping[metadata_item]
                cypher = f"""
                MATCH (a:Asset {{name: "{asset_name}"}})
                RETURN a.name AS name, a.{field_name} AS {metadata_item}
                """
            else:
                # 返回所有元数据
                cypher = f"""
                MATCH (a:Asset {{name: "{asset_name}"}})
                RETURN a.name AS name, a.description AS description,
                       a.business_purpose AS business_purpose,
                       a.technical_spec AS technical_spec,
                       a.owner AS owner, a.type AS type,
                       a.version AS version, a.status AS status
                """
        
        # 槽位3: FieldName（字段级元数据查询）
        elif 'FieldName' in slots:
            field_name = slots['FieldName'][0]
            metadata_item = slots.get('MetadataItem', ['所有'])[0]
            
            metadata_mapping = {
                '业务口径': 'business_definition',
                '技术口径': 'technical_definition',
                '数据类型': 'data_type'
            }
            
            if metadata_item in metadata_mapping:
                field_prop = metadata_mapping[metadata_item]
                cypher = f"""
                MATCH (a:Asset)-[:HAS_FIELD]->(f:Field {{name: "{field_name}"}})
                RETURN a.name AS asset_name, f.name AS field_name,
                       f.{field_prop} AS {metadata_item}
                """
            else:
                cypher = f"""
                MATCH (a:Asset)-[:HAS_FIELD]->(f:Field {{name: "{field_name}"}})
                RETURN a.name AS asset_name, f.name AS field_name,
                       f.data_type AS data_type,
                       f.business_definition AS business_definition,
                       f.technical_definition AS technical_definition
                """
        else:
            cypher = ""
        
        return cypher.strip()

    # Intent 33: 资产质量与价值查询
    def _generate_quality_value_cypher(self, slots: Dict[str, List[str]]) -> str:
        """
        生成质量价值查询Cypher
        支持槽位：AssetName, MetadataItem（价值评分、星级等）
        """
        if 'AssetName' in slots:
            asset_name = slots['AssetName'][0]
            
            cypher = f"""
            MATCH (a:Asset {{name: "{asset_name}"}})
            RETURN a.name AS name,
                   a.star_level AS star_level,
                   a.value_score AS value_score,
                   a.status AS status
            """
        else:
            # 如果没有指定资产，返回高价值资产排行
            cypher = """
            MATCH (a:Asset)
            WHERE a.value_score IS NOT NULL
            RETURN a.name AS name,
                   a.star_level AS star_level,
                   a.value_score AS value_score
            ORDER BY a.value_score DESC
            LIMIT 20
            """
        
        return cypher.strip()

    # Intent 34: 资产血缘关系查询
    def _generate_lineage_query_cypher(self, slots: Dict[str, List[str]]) -> str:
        """
        【TODO】生成血缘查询Cypher
        
        需要实现：
        1. 查询资产的上游依赖（递归）
        2. 查询资产的下游应用（递归）
        3. 查询字段级血缘
        4. 血缘路径分析
        
        目前返回简化版本（仅支持直接血缘）
        """
        logger.warning("血缘关系查询尚未完整实现，目前只支持简化查询")
        
        if 'AssetName' in slots:
            asset_name = slots['AssetName'][0]
            
            # 简化版：只查询直接上下游（需要LineageEdge才能完整实现）
            cypher = f"""
            // TODO: 实现完整的血缘查询（需要LineageEdge中间节点）
            MATCH (a:Asset {{name: "{asset_name}"}})
            OPTIONAL MATCH (a)-[:DEPENDS_ON]->(upstream:Asset)
            OPTIONAL MATCH (a)<-[:DEPENDS_ON]-(downstream:Asset)
            RETURN a.name AS asset_name,
                   collect(DISTINCT upstream.name) AS upstream_assets,
                   collect(DISTINCT downstream.name) AS downstream_assets
            """
        else:
            cypher = ""
        
        return cypher.strip()

    # Intent 35: 资产使用与工单查询
    def _generate_usage_query_cypher(self, slots: Dict[str, List[str]]) -> str:
        """
        生成使用情况查询Cypher
        支持槽位：AssetName, UserStatus（我收藏的、我订阅的）
        """
        # 槽位9: UserStatus
        if 'UserStatus' in slots:
            user_status = slots['UserStatus'][0]
            
            # TODO: 需要获取当前用户ID（从session或context）
            user_id = "current_user"  # 占位符
            
            if '收藏' in user_status:
                cypher = f"""
                MATCH (u:User {{user_id: "{user_id}"}})-[:FAVORITED]->(a:Asset)
                RETURN a.name AS name, a.description AS description,
                       a.star_level AS star_level
                """
            elif '订阅' in user_status:
                cypher = f"""
                MATCH (u:User {{user_id: "{user_id}"}})-[:SUBSCRIBED]->(a:Asset)
                RETURN a.name AS name, a.description AS description,
                       a.status AS status
                """
            else:
                cypher = ""
        elif 'AssetName' in slots:
            # 查询特定资产的使用情况
            asset_name = slots['AssetName'][0]
            cypher = f"""
            MATCH (u:User)-[r:SUBSCRIBED|FAVORITED]->(a:Asset {{name: "{asset_name}"}})
            RETURN type(r) AS relationship_type,
                   count(u) AS user_count
            """
        else:
            cypher = ""
        
        return cypher.strip()

    # Intent 36: 场景与标签推荐
    def _generate_scenario_recommendation_cypher(self, slots: Dict[str, List[str]]) -> str:
        """
        生成场景推荐Cypher
        支持槽位：BusinessZone, CoreDataItem, AssetType
        """
        # 槽位7: BusinessZone
        if 'BusinessZone' in slots:
            zone_name = slots['BusinessZone'][0]
            
            cypher = f"""
            MATCH (z:BusinessZone {{name: "{zone_name}"}})-[:CONTAINS_SCENARIO]->(s:Scenario)
            -[:USES_ASSET]->(a:Asset)
            RETURN DISTINCT a.name AS name, a.description AS description,
                   a.type AS type, s.name AS scenario_name
            LIMIT 20
            """
        # 槽位4: CoreDataItem（业务概念检索）
        elif 'CoreDataItem' in slots:
            concept_name = slots['CoreDataItem'][0]
            
            # 方式1：通过Concept节点
            cypher = f"""
            MATCH (c:Concept {{name: "{concept_name}"}})-[:IMPLEMENTED_BY]->(a:Asset)
            RETURN a.name AS name, a.description AS description,
                   a.type AS type, c.definition AS concept_definition
            """
            
            # 方式2（备用）：全文搜索description
            # cypher = f"""
            # MATCH (a:Asset)
            # WHERE a.description CONTAINS "{concept_name}"
            # RETURN a.name AS name, a.description AS description
            # LIMIT 10
            # """
        # 槽位6: AssetType
        elif 'AssetType' in slots:
            asset_type = slots['AssetType'][0]
            
            cypher = f"""
            MATCH (a:Asset {{type: "{asset_type}"}})
            RETURN a.name AS name, a.description AS description,
                   a.star_level AS star_level
            ORDER BY a.value_score DESC
            LIMIT 20
            """
        else:
            cypher = ""
        
        return cypher.strip()

    # Intent 37: 资产复合对比与筛选
    def _generate_comparison_cypher(self, slots: Dict[str, List[str]]) -> str:
        """
        生成对比查询Cypher
        支持槽位：AssetName（多个）, MetadataItem
        
        注意：对比查询需要多次执行，这里只生成第一个资产的查询
        完整的对比逻辑需要在调用层实现
        """
        if 'AssetName' in slots and len(slots['AssetName']) >= 2:
            asset_names = slots['AssetName'][:2]  # 取前两个
            
            # 查询两个资产的所有属性，便于对比
            cypher = f"""
            MATCH (a1:Asset {{name: "{asset_names[0]}"}})
            MATCH (a2:Asset {{name: "{asset_names[1]}"}})
            RETURN a1.name AS asset1_name,
                   a1.description AS asset1_description,
                   a1.value_score AS asset1_value_score,
                   a1.star_level AS asset1_star_level,
                   a2.name AS asset2_name,
                   a2.description AS asset2_description,
                   a2.value_score AS asset2_value_score,
                   a2.star_level AS asset2_star_level
            """
            
            # TODO: 查询两个资产的关系
            # OPTIONAL MATCH (a1)-[r]-(a2)
            # RETURN type(r) AS relationship
        else:
            # 复合筛选（多条件AND）
            conditions = []
            if 'AssetType' in slots:
                conditions.append(f'a.type = "{slots["AssetType"][0]}"')
            if 'BusinessDomain' in slots:
                conditions.append(f'd.name = "{slots["BusinessDomain"][0]}"')
            if 'FilterCondition' in slots:
                filter_cond = slots['FilterCondition'][0]
                if '五星' in filter_cond:
                    conditions.append('a.star_level = "五星"')
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cypher = f"""
            MATCH (a:Asset)-[:BELONGS_TO]->(d:BusinessDomain)
            WHERE {where_clause}
            RETURN a.name AS name, a.description AS description,
                   a.type AS type, a.star_level AS star_level,
                   d.name AS domain
            LIMIT 50
            """
        
        return cypher.strip()

    def execute_query(self, cypher: str) -> List[Dict[str, Any]]:
        """
        执行Cypher查询

        Args:
            cypher: Cypher查询语句

        Returns:
            查询结果列表
        """
        if not cypher:
            logger.warning("Cypher查询为空")
            return []

        logger.info(f"执行Cypher查询:\n{cypher}")

        try:
            with self.driver.session() as session:
                result = session.run(cypher)
                records = [dict(record) for record in result]

            logger.info(f"查询返回 {len(records)} 条结果")
            return records

        except Exception as e:
            logger.error(f"Cypher查询执行失败: {str(e)}")
            return []

    def query(self, intent_result: IntentResult) -> List[Dict[str, Any]]:
        """
        根据意图结果查询图谱

        Args:
            intent_result: 意图识别结果

        Returns:
            查询结果
        """
        # 生成Cypher
        cypher = self.generate_cypher(intent_result)

        if not cypher:
            logger.warning(f"无法为意图 {intent_result.intent} 生成Cypher查询")
            return []

        # 执行查询
        results = self.execute_query(cypher)

        return results

    def format_context(self, query_results: List[Dict[str, Any]], intent: IntentType) -> str:
        """
        将查询结果格式化为上下文文本

        Args:
            query_results: 查询结果
            intent: 意图类型

        Returns:
            格式化的上下文文本
        """
        if not query_results:
            return "知识库中暂无相关信息。"

        context_lines = []

        # Intent 31/36: 基础检索/场景推荐
        if intent in [IntentType.ASSET_BASIC_SEARCH, IntentType.SCENARIO_RECOMMENDATION]:
            context_lines.append("检索到以下资产：\n")
            for idx, record in enumerate(query_results, 1):
                context_lines.append(f"{idx}. 资产名称: {record.get('name', 'N/A')}")
                if 'description' in record:
                    context_lines.append(f"   描述: {record.get('description', 'N/A')}")
                if 'type' in record:
                    context_lines.append(f"   类型: {record.get('type', 'N/A')}")
                if 'star_level' in record:
                    context_lines.append(f"   星级: {record.get('star_level', 'N/A')}")
                context_lines.append("")

        # Intent 32: 元数据查询
        elif intent == IntentType.ASSET_METADATA_QUERY:
            for record in query_results:
                context_lines.append("资产元数据信息：")
                for key, value in record.items():
                    if value:
                        context_lines.append(f"  {key}: {value}")

        # Intent 33: 质量价值查询
        elif intent == IntentType.ASSET_QUALITY_VALUE_QUERY:
            context_lines.append("资产质量与价值信息：\n")
            for idx, record in enumerate(query_results, 1):
                context_lines.append(f"{idx}. {record.get('name', 'N/A')}")
                context_lines.append(f"   星级: {record.get('star_level', 'N/A')}")
                context_lines.append(f"   价值评分: {record.get('value_score', 'N/A')}")
                context_lines.append("")

        # Intent 34: 血缘查询
        elif intent == IntentType.ASSET_LINEAGE_QUERY:
            for record in query_results:
                context_lines.append(f"资产: {record.get('asset_name', 'N/A')}")
                if 'upstream_assets' in record:
                    context_lines.append(f"  上游资产: {', '.join(record['upstream_assets']) if record['upstream_assets'] else '无'}")
                if 'downstream_assets' in record:
                    context_lines.append(f"  下游资产: {', '.join(record['downstream_assets']) if record['downstream_assets'] else '无'}")

        # Intent 35: 使用查询
        elif intent == IntentType.ASSET_USAGE_QUERY:
            context_lines.append("资产使用情况：\n")
            for idx, record in enumerate(query_results, 1):
                context_lines.append(f"{idx}. {record.get('name', record)}")
                for key, value in record.items():
                    if key != 'name' and value:
                        context_lines.append(f"   {key}: {value}")
                context_lines.append("")

        # Intent 37: 对比查询
        elif intent == IntentType.ASSET_COMPARISON:
            if any('asset1_name' in record for record in query_results):
                # 资产对比
                for record in query_results:
                    context_lines.append("资产对比结果：")
                    context_lines.append(f"\n资产1: {record.get('asset1_name', 'N/A')}")
                    context_lines.append(f"  描述: {record.get('asset1_description', 'N/A')}")
                    context_lines.append(f"  价值评分: {record.get('asset1_value_score', 'N/A')}")
                    context_lines.append(f"\n资产2: {record.get('asset2_name', 'N/A')}")
                    context_lines.append(f"  描述: {record.get('asset2_description', 'N/A')}")
                    context_lines.append(f"  价值评分: {record.get('asset2_value_score', 'N/A')}")
            else:
                # 复合筛选
                context_lines.append("筛选结果：\n")
                for idx, record in enumerate(query_results, 1):
                    context_lines.append(f"{idx}. {record.get('name', 'N/A')}")
                    for key, value in record.items():
                        if key != 'name' and value:
                            context_lines.append(f"   {key}: {value}")
                    context_lines.append("")

        else:
            # 通用格式
            for idx, record in enumerate(query_results, 1):
                context_lines.append(f"\n结果 {idx}:")
                for key, value in record.items():
                    if value:
                        context_lines.append(f"  {key}: {value}")

        context = "\n".join(context_lines)
        return context


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)

    from ..intent_recognition.intent_config import IntentType, Entity, SlotType, IntentResult

    query_engine = GraphQuery()

    # 测试查询：Intent 31 (基础检索)
    test_intent = IntentResult(
        intent=IntentType.ASSET_BASIC_SEARCH,
        entities=[
            Entity(type=SlotType.ASSET_TYPE, value="标签"),
            Entity(type=SlotType.FILTER_CONDITION, value="五星")
        ]
    )

    results = query_engine.query(test_intent)
    print("\n查询结果:")
    print(results)

    context = query_engine.format_context(results, test_intent.intent)
    print("\n格式化上下文:")
    print(context)

    query_engine.close()
