"""
加载器抽象基类
定义节点和关系加载器的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd
from neo4j import Session
import logging

logger = logging.getLogger(__name__)


class NodeLoader(ABC):
    """节点加载器抽象基类"""
    
    def __init__(self, schema_config: Dict[str, Any]):
        """
        初始化节点加载器
        
        Args:
            schema_config: 节点Schema配置
        """
        self.schema_config = schema_config
        self.node_type = schema_config.get('label', 'Node')
        self.id_field = schema_config.get('id_field', 'id')
        self.properties = schema_config.get('properties', [])
    
    def load(self, file_path: str, session: Session) -> int:
        """
        模板方法：加载节点数据
        
        Args:
            file_path: CSV文件路径
            session: Neo4j会话
            
        Returns:
            加载的节点数量
        """
        logger.info(f"加载 {self.node_type} 节点数据: {file_path}")
        
        # 1. 读取数据
        df = self._read_data(file_path)
        
        # 2. 数据预处理（子类可重写）
        df = self.preprocess_data(df)
        
        # 3. 批量创建节点
        count = 0
        for _, row in df.iterrows():
            if self._create_node(row, session):
                count += 1
        
        # 4. 后处理（如创建关系）
        self.postprocess(df, session)
        
        logger.info(f"成功加载 {count} 个 {self.node_type} 节点")
        return count
    
    def _read_data(self, file_path: str) -> pd.DataFrame:
        """读取CSV数据"""
        return pd.read_csv(file_path)
    
    
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据预处理（子类可重写）
        
        Args:
            df: 原始数据
            
        Returns:
            处理后的数据
        """
        return df
    
    def _create_node(self, row: pd.Series, session: Session) -> bool:
        """
        创建单个节点
        
        Args:
            row: 数据行
            session: Neo4j会话
            
        Returns:
            是否创建成功
        """
        try:
            # 构建属性字典
            props = self._build_properties(row)
            
            # 生成Cypher查询
            cypher = self._build_cypher_query(props)
            
            # 执行查询
            session.run(cypher, **props)
            return True
        except Exception as e:
            logger.warning(f"创建 {self.node_type} 节点失败: {str(e)}")
            return False
    
    def _build_properties(self, row: pd.Series) -> Dict[str, Any]:
        """
        根据Schema配置构建属性字典
        
        Args:
            row: 数据行
            
        Returns:
            属性字典
        """
        props = {}
        for prop_config in self.properties:
            prop_name = prop_config['name']
            prop_type = prop_config.get('type', 'string')
            default_value = prop_config.get('default')
            required = prop_config.get('required', False)
            
            value = row.get(prop_name, default_value)
            
            if required and pd.isna(value):
                raise ValueError(f"必填字段 {prop_name} 缺失")
            
            # 类型转换
            if not pd.isna(value):
                if prop_type == 'int':
                    value = int(value)
                elif prop_type == 'float':
                    value = float(value)
                elif prop_type == 'bool':
                    value = bool(value)
                else:
                    value = str(value)
            else:
                value = default_value if default_value is not None else ''
            
            props[prop_name] = value
        
        return props
    
    def _build_cypher_query(self, props: Dict[str, Any]) -> str:
        """
        构建Cypher查询语句
        
        Args:
            props: 属性字典
            
        Returns:
            Cypher查询语句
        """
        # MERGE语句（基于ID唯一）
        cypher = f"MERGE (n:{self.node_type} {{{self.id_field}: ${self.id_field}}})\n"
        
        # SET语句
        set_clauses = [f"n.{prop} = ${prop}" for prop in props.keys() if prop != self.id_field]
        if set_clauses:
            cypher += "SET " + ", ".join(set_clauses)
        
        return cypher
    
    def postprocess(self, df: pd.DataFrame, session: Session):
        """
        后处理（子类可重写）
        
        Args:
            df: 数据
            session: Neo4j会话
        """
        pass


class RelationshipLoader(ABC):
    """关系加载器抽象基类"""
    
    def __init__(self, rel_config: Dict[str, Any]):
        """
        初始化关系加载器
        
        Args:
            rel_config: 关系配置
        """
        self.rel_config = rel_config
        self.rel_type = rel_config.get('type', 'RELATES_TO')
        self.source_type = rel_config.get('source')
        self.target_type = rel_config.get('target')
        self.properties = rel_config.get('properties', [])
    
    @abstractmethod
    def load(self, file_path: str, session: Session) -> int:
        """
        加载关系数据
        
        Args:
            file_path: CSV文件路径
            session: Neo4j会话
            
        Returns:
            创建的关系数量
        """
        pass
    
    def _read_data(self, file_path: str) -> pd.DataFrame:
        """读取CSV数据"""
        return pd.read_csv(file_path)

