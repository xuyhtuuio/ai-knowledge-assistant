"""
关系加载器实现
"""

from .base_loader import RelationshipLoader
import pandas as pd
from neo4j import Session
import logging

logger = logging.getLogger(__name__)


class SimpleRelationshipLoader(RelationshipLoader):
    """简单关系加载器（直接连接两个节点）"""
    
    def __init__(self, rel_config: dict, source_id_field: str, target_id_field: str):
        """
        初始化简单关系加载器
        """
        super().__init__(rel_config)
        self.source_id_field = source_id_field
        self.target_id_field = target_id_field
    
    
    
    def load(self, file_path: str, session: Session) -> int:
        """
        加载简单关系
        
        CSV格式：source_id, target_id, [关系属性...]
        """
        
        df = self._read_data(file_path)
        count = 0
        
        for _, row in df.iterrows():
            source_id = row.get(self.source_id_field)
            target_id = row.get(self.target_id_field)
            
            if pd.isna(source_id) or pd.isna(target_id):
                continue
            
            try:
                # 构建Cypher查询
                cypher = f"""
                    MATCH (s:{self.source_type} {{{self.source_id_field}: $source_id}})
                    MATCH (t:{self.target_type} {{{self.target_id_field}: $target_id}})
                    MERGE (s)-[r:{self.rel_type}]->(t)
                """
                
                # 添加关系属性
                rel_props = {}
                for prop_config in self.properties:
                    prop_name = prop_config['name']
                    if prop_name in row and pd.notna(row[prop_name]):
                        rel_props[prop_name] = row[prop_name]
                        cypher += f"\nSET r.{prop_name} = ${prop_name}"
                
                session.run(cypher, source_id=source_id, target_id=target_id, **rel_props)
                count += 1
            except Exception as e:
                logger.warning(f"创建 {self.rel_type} 关系失败: {str(e)}")
        
        logger.info(f"成功创建 {count} 个 {self.rel_type} 关系")
        return count


class AssetUsageLoader(RelationshipLoader):
    """
    资产使用关系加载器（M:M关系，使用中间节点）
    
    处理 Scenario-Asset 的多对多关系
    """
    
    def load(self, file_path: str, session: Session) -> int:
        """
        加载AssetUsage中间节点及其关系
        
        CSV格式：asset_id, scenario_id, role, status, description
        """
        logger.info(f"加载 AssetUsage 关系: {file_path}")
        
        df = self._read_data(file_path)
        count = 0
        
        for idx, row in df.iterrows():
            asset_id = row.get('asset_id')
            scenario_id = row.get('scenario_id')
            
            if pd.isna(asset_id) or pd.isna(scenario_id):
                continue
            
            try:
                usage_id = f"usage_{asset_id}_{scenario_id}_{idx}"
                
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
                    asset_id=asset_id,
                    scenario_id=scenario_id,
                    usage_id=usage_id,
                    role=row.get('role', ''),
                    status=row.get('status', ''),
                    description=row.get('description', '')
                )
                count += 1
            except Exception as e:
                logger.warning(f"创建 AssetUsage 关系失败: {str(e)}")
        
        logger.info(f"成功创建 {count} 个 AssetUsage 关系")
        return count


class UniversalRelationshipLoader(RelationshipLoader):
    """
    通用关系加载器
    
    支持从通用关系表加载（source_type, source_id, target_type, target_id, relationship_type）
    """
    
    def __init__(self, schema_config: dict):
        """
        初始化通用关系加载器
        
        Args:
            schema_config: Schema配置（用于获取节点ID字段映射）
        """
        super().__init__({})
        self.schema_config = schema_config
    
    def load(self, file_path: str, session: Session) -> int:
        """
        加载通用关系
        
        CSV格式：source_type, source_id, target_type, target_id, relationship_type, [properties]
        """
        
        df = self._read_data(file_path)
        count = 0
        
        for _, row in df.iterrows():
            source_type = row['source_type']
            source_id = row['source_id']
            target_type = row['target_type']
            target_id = row['target_id']
            rel_type = row['relationship_type']
            
            # 获取ID字段名
            source_id_field = self._get_id_field(source_type)
            target_id_field = self._get_id_field(target_type)
            
            try:
                cypher = f"""
                    MATCH (s:{source_type} {{{source_id_field}: $source_id}})
                    MATCH (t:{target_type} {{{target_id_field}: $target_id}})
                    MERGE (s)-[r:{rel_type}]->(t)
                """
                
                session.run(cypher, source_id=source_id, target_id=target_id)
                count += 1
            except Exception as e:
                logger.warning(f"创建关系失败 {source_id}->{target_id}: {str(e)}")
        
        logger.info(f"成功创建 {count} 个通用关系")
        return count
    
    def _get_id_field(self, node_type: str) -> str:
        """根据节点类型返回ID字段名"""
        node_config = self.schema_config.get('node_types', {}).get(node_type, {})
        return node_config.get('id_field', f"{node_type.lower()}_id")

