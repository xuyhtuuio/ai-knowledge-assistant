"""
加载器工厂
根据配置创建相应的加载器实例
"""

from typing import Dict, Any
from .base_loader import NodeLoader, RelationshipLoader
from .node_loaders import (
    AssetLoader,
    FieldLoader,
    BusinessDomainLoader,
    BusinessZoneLoader,
    ScenarioLoader,
    ConceptLoader,
    UserLoader,
    OrgLoader,
    HotspotLoader
)
from .relationship_loaders import (
    SimpleRelationshipLoader,
    AssetUsageLoader,
    UniversalRelationshipLoader
)
import logging

logger = logging.getLogger(__name__)


class LoaderFactory:
    """加载器工厂类"""
    
    # 节点加载器映射
    NODE_LOADERS = {
        'Asset': AssetLoader,
        'Field': FieldLoader,
        'BusinessDomain': BusinessDomainLoader,
        'BusinessZone': BusinessZoneLoader,
        'Scenario': ScenarioLoader,
        'Concept': ConceptLoader,
        'User': UserLoader,
        'Org': OrgLoader,
        'Hotspot': HotspotLoader
    }
    
    @classmethod
    def create_node_loader(cls, node_type: str, schema_config: Dict[str, Any]) -> NodeLoader:
        """
        创建节点加载器
        
        Args:
            node_type: 节点类型（如 'Asset'）
            schema_config: 节点Schema配置
            
        Returns:
            节点加载器实例
        """
        loader_class = cls.NODE_LOADERS.get(node_type)
        
        if not loader_class:
            # 如果没有专门的加载器，使用基类
            logger.warning(f"节点类型 {node_type} 没有专门的加载器，使用通用加载器")
            loader_class = NodeLoader
        
        return loader_class(schema_config)
    
    @classmethod
    def create_relationship_loader(cls, 
                                   rel_type: str, 
                                   rel_config: Dict[str, Any],
                                   schema_config: Dict[str, Any] = None) -> RelationshipLoader:
        """
        创建关系加载器
        
        Returns:
            关系加载器实例
        """
        # 特殊关系：AssetUsage（M:M中间节点）
        if rel_type == 'AssetUsage':
            return AssetUsageLoader(rel_config)
        
        # 通用关系加载器
        if rel_type == 'Universal':
            return UniversalRelationshipLoader(schema_config)
        
        # 简单关系加载器
        source_type = rel_config.get('source')
        target_type = rel_config.get('target')
        
        # 获取ID字段名
        source_id_field = cls._get_id_field(source_type, schema_config)
        target_id_field = cls._get_id_field(target_type, schema_config)
        
        return SimpleRelationshipLoader(rel_config, source_id_field, target_id_field)
    
    @staticmethod
    def _get_id_field(node_type: str, schema_config: Dict[str, Any]) -> str:
        """根据节点类型返回ID字段名"""
        if not schema_config:
            return f"{node_type.lower()}_id"
        
        node_config = schema_config.get('node_types', {}).get(node_type, {})
        return node_config.get('id_field', f"{node_type.lower()}_id")

