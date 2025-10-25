"""
意图识别配置模块
定义意图类别、实体类型及其描述
"""

from enum import Enum
from typing import List, Dict
from dataclasses import dataclass


class IntentType(str, Enum):
    """意图类型枚举"""
    QUERY_ASSET = "Query_Asset"  # 查询资产
    QUERY_SCENARIO = "Query_Scenario"  # 咨询场景
    QUERY_HOTSPOT = "Query_Hotspot"  # 了解热点
    FIND_RELATIONSHIP = "Find_Relationship"  # 查找关联关系
    OOD = "OOD"  # 域外问题


class EntityType(str, Enum):
    """实体类型枚举"""
    ASSET = "Asset"  # 资产
    SCENARIO = "Scenario"  # 场景
    HOTSPOT = "Hotspot"  # 热点
    ATTRIBUTE = "Attribute"  # 属性


@dataclass
class Entity:
    """实体数据类"""
    type: EntityType
    value: str
    confidence: float = 1.0  # 置信度


@dataclass
class IntentResult:
    """意图识别结果数据类"""
    intent: IntentType
    entities: List[Entity]
    confidence: float = 1.0  # 置信度
    raw_output: str = ""  # 模型原始输出


# 意图描述字典（用于标注指引）
INTENT_DESCRIPTIONS = {
    IntentType.QUERY_ASSET: {
        "name": "查询资产",
        "description": "用户想要了解某个资产的详细信息",
        "examples": [
            "XX系统的详情是什么？",
            "资产A的负责人是谁？",
            "客户关系管理系统是做什么的？",
            "告诉我XX数据平台的版本号"
        ],
        "keywords": ["是什么", "详情", "介绍", "负责人", "版本", "状态"]
    },
    IntentType.QUERY_SCENARIO: {
        "name": "咨询场景",
        "description": "用户想要了解某个业务场景的流程或信息",
        "examples": [
            "新员工入职流程怎么走？",
            "介绍一下季度财报分析场景",
            "月度数据上报的步骤是什么？"
        ],
        "keywords": ["流程", "步骤", "怎么走", "场景", "业务"]
    },
    IntentType.QUERY_HOTSPOT: {
        "name": "了解热点",
        "description": "用户想要了解行业热点、政策或最新动态",
        "examples": [
            "最近的行业热点有哪些？",
            "XX政策文件的解读",
            "数据安全法更新了什么内容？",
            "AIGC行业报告讲了什么？"
        ],
        "keywords": ["热点", "最近", "政策", "法规", "行业", "动态"]
    },
    IntentType.FIND_RELATIONSHIP: {
        "name": "查找关联关系",
        "description": "用户想要了解不同实体之间的关联关系（核心功能）",
        "examples": [
            "资产A应用在哪些场景？",
            "热点B影响了哪些资产？",
            "场景C需要哪些资产支持？",
            "新员工入职场景用到了哪些系统？",
            "数据安全法对客户管理系统有什么影响？"
        ],
        "keywords": [
            "应用在", "用到", "需要", "支持", "影响", "关联",
            "哪些", "相关", "涉及", "依赖"
        ]
    },
    IntentType.OOD: {
        "name": "域外问题",
        "description": "与资产、场景、热点无关的问题或闲聊",
        "examples": [
            "今天天气怎么样？",
            "帮我写个笑话",
            "你叫什么名字？",
            "1+1等于几？"
        ],
        "keywords": ["天气", "笑话", "名字", "闲聊"]
    }
}


# 实体描述字典
ENTITY_DESCRIPTIONS = {
    EntityType.ASSET: {
        "name": "资产",
        "description": "企业内部的系统、平台、接口、数据等资产",
        "examples": [
            "XX数据平台V3.0",
            "客户关系管理系统",
            "统一认证系统",
            "数据接口API"
        ]
    },
    EntityType.SCENARIO: {
        "name": "场景",
        "description": "业务场景或流程",
        "examples": [
            "新员工入职",
            "月度数据上报",
            "季度财报分析",
            "供应商准入"
        ]
    },
    EntityType.HOTSPOT: {
        "name": "热点",
        "description": "行业热点、政策法规、技术动态等",
        "examples": [
            "数据安全法更新",
            "AIGC行业报告",
            "隐私计算白皮书",
            "XX政策解读"
        ]
    },
    EntityType.ATTRIBUTE: {
        "name": "属性",
        "description": "资产、场景、热点的属性字段",
        "examples": [
            "负责人",
            "版本号",
            "状态",
            "影响范围",
            "角色",
            "发布日期"
        ]
    }
}


def get_intent_by_name(intent_name: str) -> IntentType:
    """根据字符串获取意图类型"""
    try:
        return IntentType(intent_name)
    except ValueError:
        return IntentType.OOD


def get_entity_by_name(entity_name: str) -> EntityType:
    """根据字符串获取实体类型"""
    try:
        return EntityType(entity_name)
    except ValueError:
        raise ValueError(f"Unknown entity type: {entity_name}")


def validate_intent_result(result: Dict) -> bool:
    """验证意图识别结果格式是否正确"""
    if "intent" not in result:
        return False
    if "entities" not in result:
        return False
    if not isinstance(result["entities"], list):
        return False

    # 检查intent是否合法
    try:
        IntentType(result["intent"])
    except ValueError:
        return False

    # 检查entities格式
    for entity in result["entities"]:
        if not isinstance(entity, dict):
            return False
        if "type" not in entity or "value" not in entity:
            return False
        try:
            EntityType(entity["type"])
        except ValueError:
            return False

    return True
