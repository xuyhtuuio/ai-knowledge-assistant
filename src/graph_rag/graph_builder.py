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
        """创建约束和索引"""
        with self.driver.session() as session:
            # 资产节点约束
            session.run(
                "CREATE CONSTRAINT asset_id_unique IF NOT EXISTS "
                "FOR (a:Asset) REQUIRE a.asset_id IS UNIQUE"
            )

            # 场景节点约束
            session.run(
                "CREATE CONSTRAINT scenario_id_unique IF NOT EXISTS "
                "FOR (s:Scenario) REQUIRE s.scenario_id IS UNIQUE"
            )

            # 热点节点约束
            session.run(
                "CREATE CONSTRAINT hotspot_id_unique IF NOT EXISTS "
                "FOR (h:Hotspot) REQUIRE h.hotspot_id IS UNIQUE"
            )

            # 创建name索引（提高查询效率）
            session.run(
                "CREATE INDEX asset_name_index IF NOT EXISTS "
                "FOR (a:Asset) ON (a.name)"
            )

            session.run(
                "CREATE INDEX scenario_name_index IF NOT EXISTS "
                "FOR (s:Scenario) ON (s.name)"
            )

            session.run(
                "CREATE INDEX hotspot_title_index IF NOT EXISTS "
                "FOR (h:Hotspot) ON (h.title)"
            )

        logger.info("约束和索引创建完成")

    def load_assets(self, asset_file: str):
        """
        加载资产数据

        Args:
            asset_file: 资产CSV文件路径
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
                        a.status = $status
                    """,
                    asset_id=row.get('asset_id', ''),
                    name=row.get('name', ''),
                    description=row.get('description', ''),
                    owner=row.get('owner', ''),
                    type=row.get('type', ''),
                    version=row.get('version', ''),
                    status=row.get('status', '')
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
                         hotspot_asset_rel_file: Optional[str] = None):
        """
        构建完整知识图谱

        Args:
            asset_file: 资产文件
            scenario_file: 场景文件
            hotspot_file: 热点文件
            asset_scenario_rel_file: 资产-场景关系文件
            hotspot_asset_rel_file: 热点-资产关系文件（可选）
        """
        logger.info("开始构建知识图谱...")

        # 创建约束
        self.create_constraints()

        # 加载节点
        self.load_assets(asset_file)
        self.load_scenarios(scenario_file)
        self.load_hotspots(hotspot_file)

        # 加载关系
        self.load_asset_scenario_relationships(asset_scenario_rel_file)

        if hotspot_asset_rel_file and os.path.exists(hotspot_asset_rel_file):
            self.load_hotspot_asset_relationships(hotspot_asset_rel_file)

        logger.info("知识图谱构建完成！")

    def get_graph_stats(self) -> Dict[str, int]:
        """获取图谱统计信息"""
        with self.driver.session() as session:
            # 节点数量
            asset_count = session.run("MATCH (a:Asset) RETURN count(a) as count").single()['count']
            scenario_count = session.run("MATCH (s:Scenario) RETURN count(s) as count").single()['count']
            hotspot_count = session.run("MATCH (h:Hotspot) RETURN count(h) as count").single()['count']
            usage_count = session.run("MATCH (u:AssetUsage) RETURN count(u) as count").single()['count']

            # 关系数量
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']

        stats = {
            "资产节点": asset_count,
            "场景节点": scenario_count,
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
        hotspot_asset_rel_file="data/raw/relationships/hotspot_asset.csv"
    )

    # 查看统计
    stats = builder.get_graph_stats()
    print("\n图谱统计:")
    for key, value in stats.items():
        print(f"{key}: {value}")

    builder.close()
