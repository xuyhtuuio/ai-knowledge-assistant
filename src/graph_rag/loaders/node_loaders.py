"""
具体节点加载器实现
每个节点类型一个加载器类
"""

from .base_loader import NodeLoader
import pandas as pd
from neo4j import Session
import logging

logger = logging.getLogger(__name__)


class AssetLoader(NodeLoader):
    """资产节点加载器（槽位1: AssetName）"""
    
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """资产数据预处理"""
        # 确保必填字段存在
        if 'asset_id' not in df.columns or 'name' not in df.columns:
            raise ValueError("资产数据必须包含 asset_id 和 name 字段")
        
        # 填充默认值
        if 'value_score' in df.columns:
            df['value_score'] = df['value_score'].fillna(0)
        
        return df


class FieldLoader(NodeLoader):
    """字段节点加载器（槽位3: FieldName）"""
    
    def postprocess(self, df: pd.DataFrame, session: Session):
        """创建Field与Asset的关系"""
        if 'asset_id' not in df.columns:
            return
        
        count = 0
        for _, row in df.iterrows():
            if pd.notna(row.get('asset_id')):
                try:
                    session.run(
                        """
                        MATCH (a:Asset {asset_id: $asset_id})
                        MATCH (f:Field {field_id: $field_id})
                        MERGE (a)-[:HAS_FIELD]->(f)
                        """,
                        asset_id=row['asset_id'],
                        field_id=row['field_id']
                    )
                    count += 1
                except Exception as e:
                    logger.warning(f"创建Asset-Field关系失败: {str(e)}")
        
        logger.info(f"成功创建 {count} 个Asset-Field关系")


class BusinessDomainLoader(NodeLoader):
    """业务域节点加载器（槽位5: BusinessDomain）"""
    pass


class BusinessZoneLoader(NodeLoader):
    """业务专区节点加载器（槽位7: BusinessZone）"""
    pass


class ScenarioLoader(NodeLoader):
    """场景节点加载器"""
    pass


class ConceptLoader(NodeLoader):
    """业务概念节点加载器（槽位4: CoreDataItem）"""
    pass


class UserLoader(NodeLoader):
    """用户节点加载器（槽位9: UserStatus）"""
    pass


class OrgLoader(NodeLoader):
    """组织节点加载器（槽位10: OrgName/UserName）"""
    pass


class HotspotLoader(NodeLoader):
    """热点节点加载器"""
    pass

