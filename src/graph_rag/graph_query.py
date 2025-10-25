"""
图谱查询模块
负责将意图和实体转换为Cypher查询，并执行检索
"""

import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import yaml

from ..intent_recognition.intent_config import IntentType, IntentResult, Entity, EntityType

logger = logging.getLogger(__name__)


class GraphQuery:
    """图谱查询器"""

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

        logger.info("图谱查询器初始化完成")

    def connect_neo4j(self):
        """连接Neo4j数据库"""
        neo4j_config = self.graph_config['neo4j']

        try:
            self.driver=GraphDatabase.driver(
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

    def generate_cypher(self, intent_result: IntentResult) -> str:
        """
        根据意图和实体生成Cypher查询

        Args:
            intent_result: 意图识别结果

        Returns:
            Cypher查询语句
        """
        intent = intent_result.intent
        entities = intent_result.entities

        # 提取实体值
        assets = [e.value for e in entities if e.type == EntityType.ASSET]
        scenarios = [e.value for e in entities if e.type == EntityType.SCENARIO]
        hotspots = [e.value for e in entities if e.type == EntityType.HOTSPOT]
        attributes = [e.value for e in entities if e.type == EntityType.ATTRIBUTE]

        cypher = ""

        if intent == IntentType.QUERY_ASSET:
            # 查询资产
            if assets:
                asset_name = assets[0]
                cypher = f"""
                MATCH (a:Asset {{name: "{asset_name}"}})
                RETURN a.name AS name, a.description AS description,
                       a.owner AS owner, a.type AS type,
                       a.version AS version, a.status AS status
                """

        elif intent == IntentType.QUERY_SCENARIO:
            # 查询场景
            if scenarios:
                scenario_name = scenarios[0]
                cypher = f"""
                MATCH (s:Scenario {{name: "{scenario_name}"}})
                RETURN s.name AS name, s.description AS description,
                       s.business_domain AS business_domain, s.status AS status
                """

        elif intent == IntentType.QUERY_HOTSPOT:
            # 查询热点
            if hotspots:
                hotspot_title = hotspots[0]
                cypher = f"""
                MATCH (h:Hotspot {{title: "{hotspot_title}"}})
                RETURN h.title AS title, h.summary AS summary,
                       h.publish_date AS publish_date, h.source AS source
                """

        elif intent == IntentType.FIND_RELATIONSHIP:
            # 查找关联关系（核心功能）
            if scenarios and assets:
                # 场景-资产关系（带AssetUsage中间节点）
                scenario_name = scenarios[0]
                asset_name = assets[0] if assets else None

                if asset_name:
                    cypher = f"""
                    MATCH (s:Scenario {{name: "{scenario_name}"}})
                    -[:INCLUDES_USAGE]-> (u:AssetUsage)
                    <-[:IS_USED_IN]- (a:Asset {{name: "{asset_name}"}})
                    RETURN a.name AS asset_name, s.name AS scenario_name,
                           u.role AS role, u.status AS status, u.description AS description
                    """
                else:
                    # 查询场景的所有资产
                    cypher = f"""
                    MATCH (s:Scenario {{name: "{scenario_name}"}})
                    -[:INCLUDES_USAGE]-> (u:AssetUsage)
                    <-[:IS_USED_IN]- (a:Asset)
                    RETURN a.name AS asset_name, a.description AS asset_description,
                           u.role AS role, u.status AS status
                    ORDER BY u.role
                    """

            elif scenarios and not assets:
                # 查询场景的所有资产
                scenario_name = scenarios[0]
                cypher = f"""
                MATCH (s:Scenario {{name: "{scenario_name}"}})
                -[:INCLUDES_USAGE]-> (u:AssetUsage)
                <-[:IS_USED_IN]- (a:Asset)
                RETURN a.name AS asset_name, a.description AS asset_description,
                       u.role AS role, u.status AS status
                ORDER BY u.role
                """

            elif assets and not scenarios:
                # 查询资产应用在哪些场景
                asset_name = assets[0]
                cypher = f"""
                MATCH (a:Asset {{name: "{asset_name}"}})
                -[:IS_USED_IN]-> (u:AssetUsage)
                <-[:INCLUDES_USAGE]- (s:Scenario)
                RETURN s.name AS scenario_name, s.description AS scenario_description,
                       u.role AS role, u.status AS status
                ORDER BY s.name
                """

            elif hotspots and assets:
                # 热点对资产的影响
                hotspot_title = hotspots[0]
                asset_name = assets[0]
                cypher = f"""
                MATCH (h:Hotspot {{title: "{hotspot_title}"}})
                -[r:DIRECTLY_IMPACTS]-> (a:Asset {{name: "{asset_name}"}})
                RETURN h.title AS hotspot_title, a.name AS asset_name,
                       r.impact_type AS impact_type, r.description AS description
                """

            elif hotspots and not assets:
                # 热点影响的所有资产
                hotspot_title = hotspots[0]
                cypher = f"""
                MATCH (h:Hotspot {{title: "{hotspot_title}"}})
                -[r:DIRECTLY_IMPACTS]-> (a:Asset)
                RETURN a.name AS asset_name, a.description AS asset_description,
                       r.impact_type AS impact_type, r.description AS impact_description
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

        if intent == IntentType.QUERY_ASSET:
            for record in query_results:
                context_lines.append(f"资产名称: {record.get('name', 'N/A')}")
                context_lines.append(f"描述: {record.get('description', 'N/A')}")
                context_lines.append(f"负责人: {record.get('owner', 'N/A')}")
                context_lines.append(f"类型: {record.get('type', 'N/A')}")
                context_lines.append(f"版本: {record.get('version', 'N/A')}")
                context_lines.append(f"状态: {record.get('status', 'N/A')}")

        elif intent == IntentType.QUERY_SCENARIO:
            for record in query_results:
                context_lines.append(f"场景名称: {record.get('name', 'N/A')}")
                context_lines.append(f"描述: {record.get('description', 'N/A')}")
                context_lines.append(f"业务域: {record.get('business_domain', 'N/A')}")
                context_lines.append(f"状态: {record.get('status', 'N/A')}")

        elif intent == IntentType.QUERY_HOTSPOT:
            for record in query_results:
                context_lines.append(f"热点标题: {record.get('title', 'N/A')}")
                context_lines.append(f"摘要: {record.get('summary', 'N/A')}")
                context_lines.append(f"发布日期: {record.get('publish_date', 'N/A')}")
                context_lines.append(f"来源: {record.get('source', 'N/A')}")

        elif intent == IntentType.FIND_RELATIONSHIP:
            for idx, record in enumerate(query_results, 1):
                context_lines.append(f"\n关系 {idx}:")
                for key, value in record.items():
                    if value:
                        context_lines.append(f"  {key}: {value}")

        context = "\n".join(context_lines)
        return context


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    from ..intent_recognition.intent_config import IntentType, Entity, EntityType, IntentResult

    query_engine = GraphQuery()

    # 测试查询
    test_intent = IntentResult(
        intent=IntentType.FIND_RELATIONSHIP,
        entities=[
            Entity(type=EntityType.SCENARIO, value="新员工入职"),
        ]
    )

    results = query_engine.query(test_intent)
    print("\n查询结果:")
    print(results)

    context = query_engine.format_context(results, test_intent.intent)
    print("\n格式化上下文:")
    print(context)

    query_engine.close()
