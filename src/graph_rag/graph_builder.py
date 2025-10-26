"""
知识图谱构建器 
"""

import os
import logging
from typing import Dict, Any, Optional
from neo4j import GraphDatabase
import yaml

from .loaders import LoaderFactory

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    知识图谱构建器
    
    """
    
    def __init__(self, 
                 config_path: str = "config/config.yaml",
                 schema_config_path: str = "config/graph_schema_config.yaml"):
        """
        初始化图谱构建器
        """
        # 加载主配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 加载Schema配置
        with open(schema_config_path, 'r', encoding='utf-8') as f:
            self.schema_config = yaml.safe_load(f)
        
        self.graph_config = self.config['graph']
        self.data_config = self.config['data']
        
        # 连接Neo4j
        self.driver = None
        self.connect_neo4j()
        
        logger.info("图谱构建器 V2.0 初始化完成")
    
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
        """清空图谱"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("图谱已清空")
    
    def create_constraints_and_indexes(self):
        """根据Schema配置创建约束和索引"""
        
        with self.driver.session() as session:
            # 创建节点唯一约束
            for node_type, node_config in self.schema_config['node_types'].items():
                id_field = node_config['id_field']
                try:
                    session.run(
                        f"CREATE CONSTRAINT {node_type.lower()}_{id_field}_unique IF NOT EXISTS "
                        f"FOR (n:{node_type}) REQUIRE n.{id_field} IS UNIQUE"
                    )
                except Exception as e:
                    logger.warning(f"创建约束失败 {node_type}.{id_field}: {str(e)}")
            
            # 创建索引
            for index_config in self.schema_config.get('indexes', []):
                node_type = index_config['node_type']
                fields = index_config['fields']
                index_type = index_config.get('type', 'index')
                
                try:
                    if len(fields) == 1:
                        # 单字段索引
                        session.run(
                            f"CREATE INDEX {node_type.lower()}_{fields[0]}_index IF NOT EXISTS "
                            f"FOR (n:{node_type}) ON (n.{fields[0]})"
                        )
                    elif index_type == 'composite_index':
                        # 复合索引
                        field_str = ', '.join([f"n.{f}" for f in fields])
                        session.run(
                            f"CREATE INDEX {node_type.lower()}_{'_'.join(fields)}_index IF NOT EXISTS "
                            f"FOR (n:{node_type}) ON ({field_str})"
                        )
                except Exception as e:
                    logger.warning(f"创建索引失败: {str(e)}")
        
        logger.info("约束和索引创建完成")
    
    def load_node(self, node_type: str, file_path: str) -> int:
        """
        加载指定类型的节点
        
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在，跳过: {file_path}")
            return 0
        
        # 获取节点Schema配置
        node_config = self.schema_config['node_types'].get(node_type)
        if not node_config:
            logger.error(f"未找到节点类型 {node_type} 的配置")
            return 0
        
        # 创建加载器
        loader = LoaderFactory.create_node_loader(node_type, node_config)
        
        # 执行加载
        with self.driver.session() as session:
            return loader.load(file_path, session)
    
    def load_relationship(self, rel_type: str, file_path: str) -> int:
        """
        加载指定类型的关系
        
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在，跳过: {file_path}")
            return 0
        
        # 特殊处理：AssetUsage（M:M中间节点）
        if rel_type == 'AssetUsage':
            rel_config = self.schema_config['special_relationships'].get('AssetUsage', {})
        # 通用关系表
        elif rel_type == 'Universal':
            loader = LoaderFactory.create_relationship_loader('Universal', {}, self.schema_config)
            with self.driver.session() as session:
                return loader.load(file_path, session)
        # 普通关系
        else:
            rel_config = self.schema_config['relationship_types'].get(rel_type)
            if not rel_config:
                logger.error(f"未找到关系类型 {rel_type} 的配置")
                return 0
        
        # 创建加载器
        loader = LoaderFactory.create_relationship_loader(rel_type, rel_config, self.schema_config)
        
        # 执行加载
        with self.driver.session() as session:
            return loader.load(file_path, session)
    
    def build_full_graph(self, data_files: Dict[str, str]):
        """
        构建完整知识图谱
        
        """
        
        # 1. 创建约束和索引
        self.create_constraints_and_indexes()
        
        # 2. 加载节点
        node_files = data_files.get('nodes', {})
        for node_type, file_path in node_files.items():
            self.load_node(node_type, file_path)
        
        # 3. 加载关系
        rel_files = data_files.get('relationships', {})
        for rel_type, file_path in rel_files.items():
            self.load_relationship(rel_type, file_path)
        
        # 4. 显示统计
        stats = self.get_graph_stats()
        
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
    
    def get_graph_stats(self) -> Dict[str, int]:
        """获取图谱统计信息"""
        stats = {}
        
        with self.driver.session() as session:
            # 统计各类节点数量
            for node_type in self.schema_config['node_types'].keys():
                try:
                    count = session.run(
                        f"MATCH (n:{node_type}) RETURN count(n) as count"
                    ).single()['count']
                    stats[f"{node_type}节点"] = count
                except:
                    stats[f"{node_type}节点"] = 0
            
            # 统计关系总数
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            stats["关系总数"] = rel_count
        
        return stats


if __name__ == "__main__":

    # 初始化图谱构建器
    builder = GraphBuilder()
    
    # 配置数据文件
    data_files = {
        'nodes': {
            'Asset': 'data/raw/assets/assets.csv',
            'Field': 'data/raw/fields/fields.csv',
            'BusinessDomain': 'data/raw/domains/domains.csv',
            'BusinessZone': 'data/raw/zones/zones.csv',
            'Scenario': 'data/raw/scenarios/scenarios.csv',
            'Concept': 'data/raw/concepts/concepts.csv',
            'User': 'data/raw/users/users.csv',
            'Org': 'data/raw/orgs/orgs.csv',
            'Hotspot': 'data/raw/hotspots/hotspots.csv'
        },
        'relationships': {
            'AssetUsage': 'data/raw/relationships/asset_scenario.csv',
            'DIRECTLY_IMPACTS': 'data/raw/relationships/hotspot_asset.csv',
            'Universal': 'data/raw/relationships/relationships.csv'
        }
    }
    
    # 构建图谱
    builder.build_full_graph(data_files)
    
    builder.close()

