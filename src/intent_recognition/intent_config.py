"""
意图识别配置模块
定义意图类别、槽位类型及其描述
【更新】支持数据资产助手的8大意图和10大槽位体系
"""

from enum import Enum
from typing import List, Dict
from dataclasses import dataclass


class IntentType(str, Enum):
    """
    意图类型枚举（8大意图）
    基于数据资产助手的用户故事设计
    """
    # Intent 31: 资产基础检索（US 1: 高效发现资产）
    ASSET_BASIC_SEARCH = "31"
    
    # Intent 32: 资产元数据查询（US 3: 深度理解资产-基础元数据）
    ASSET_METADATA_QUERY = "32"
    
    # Intent 33: 资产质量与价值查询（US 3: 深度理解资产-质量/价值）
    ASSET_QUALITY_VALUE_QUERY = "33"
    
    # Intent 34: 资产血缘关系查询（US 3: 深度理解资产-血缘）
    ASSET_LINEAGE_QUERY = "34"
    
    # Intent 35: 资产使用与工单查询
    ASSET_USAGE_QUERY = "35"
    
    # Intent 36: 场景与标签推荐（US 1: 高效发现资产-场景化）
    SCENARIO_RECOMMENDATION = "36"
    
    # Intent 37: 资产复合对比与筛选（US 2: 智能对比资产）
    ASSET_COMPARISON = "37"
    
    # Intent 38: 平台规则与帮助
    PLATFORM_HELP = "38"


class SlotType(str, Enum):
    """
    槽位类型枚举（10大槽位）
    用于从用户查询中抽取关键信息
    """
    # 槽位1: 核心资产/ID/英文名
    ASSET_NAME = "AssetName"
    
    # 槽位2: 查询元数据项（如：业务口径、技术口径、简介/用途等）
    METADATA_ITEM = "MetadataItem"
    
    # 槽位3: 字段名称
    FIELD_NAME = "FieldName"
    
    # 槽位4: 核心数据项（如：5G登网、移网用户是否活跃）
    CORE_DATA_ITEM = "CoreDataItem"
    
    # 槽位5: 业务/数据域（如：M域、O域、B域）
    BUSINESS_DOMAIN = "BusinessDomain"
    
    # 槽位6: 资产类型（如：标签、模型资产、数据表、指标）
    ASSET_TYPE = "AssetType"
    
    # 槽位7: 业务专区（如：公众智慧运营、一线赋能专区）
    BUSINESS_ZONE = "BusinessZone"
    
    # 槽位8: 筛选/限定条件（如：五星、价值评估>80分）
    FILTER_CONDITION = "FilterCondition"
    
    # 槽位9: 用户操作属性（如：我收藏的、我订阅的）
    USER_STATUS = "UserStatus"
    
    # 槽位10: 机构/人员名（如：总部-数据部、张三）
    ORG_USER_NAME = "OrgName/UserName"


# 为了向后兼容，保留EntityType别名
EntityType = SlotType


@dataclass
class Entity:
    """
    实体/槽位数据类
    【更新】支持新的SlotType
    """
    type: SlotType  # 槽位类型
    value: str      # 槽位值


@dataclass
class IntentResult:
    """
    意图识别结果数据类
    """
    intent: IntentType           # 意图类型
    entities: List[Entity]       # 槽位列表（原来的entities改名为slots更准确，但为了兼容性保留）
    raw_output: str = ""         # 模型原始输出
    
    @property
    def slots(self) -> List[Entity]:
        """槽位列表（别名）"""
        return self.entities


# ========================================
# 8大意图描述字典（用于标注和SFT训练）
# ========================================
INTENT_DESCRIPTIONS = {
    IntentType.ASSET_BASIC_SEARCH: {
        "code": "31",
        "name": "资产基础检索",
        "description": "基于名称、ID、字段、域、时效等单一或组合条件进行资产定位",
        "user_story": "US 1: 高效发现资产",
        "examples": [
            "查询'宽带提质速率(月)'资产",
            "平台上有哪些五星资产？",
            "M域的所有标签资产",
            "包含user_id字段的资产有哪些？"
        ],
        "keywords": ["查询", "有哪些", "所有", "包含", "列出"],
        "main_slots": ["AssetName", "AssetType", "BusinessDomain", "FieldName", "FilterCondition"]
    },
    IntentType.ASSET_METADATA_QUERY: {
        "code": "32",
        "name": "资产元数据查询",
        "description": "查询资产的基本信息、业务口径、字段详情、技术属性等",
        "user_story": "US 3: 深度理解资产（基础元数据）",
        "examples": [
            "'宽带提质速率(月)'这个资产是干什么用的？",
            "user_id字段的技术口径是什么？",
            "这个资产的业务解释是什么？",
            "XX资产的负责人是谁？"
        ],
        "keywords": ["是什么", "详情", "介绍", "口径", "负责人", "用途"],
        "main_slots": ["AssetName", "FieldName", "MetadataItem", "OrgName/UserName"]
    },
    IntentType.ASSET_QUALITY_VALUE_QUERY: {
        "code": "33",
        "name": "资产质量与价值查询",
        "description": "查询资产的价值评分、质量稽核问题、星级、价值趋势等",
        "user_story": "US 3: 深度理解资产（质量/价值）",
        "examples": [
            "'新星级长高用户清单(月)'的价值评估分数是多少？",
            "这个资产的质量稽核有什么问题？",
            "XX资产的星级是多少？",
            "最近哪些资产的价值评分上升了？"
        ],
        "keywords": ["价值", "评分", "星级", "质量", "稽核", "趋势"],
        "main_slots": ["AssetName", "MetadataItem", "FilterCondition"]
    },
    IntentType.ASSET_LINEAGE_QUERY: {
        "code": "34",
        "name": "资产血缘关系查询",
        "description": "查询资产的上游依赖、下游应用、血缘图等",
        "user_story": "US 3: 深度理解资产（血缘）",
        "examples": [
            "XX资产的上游依赖有哪些？",
            "这个资产的下游应用是什么？",
            "给我看看XX资产的血缘图",
            "user_id字段的数据来源是哪里？"
        ],
        "keywords": ["上游", "下游", "血缘", "依赖", "来源", "应用"],
        "main_slots": ["AssetName", "FieldName", "MetadataItem"]
    },
    IntentType.ASSET_USAGE_QUERY: {
        "code": "35",
        "name": "资产使用与工单查询",
        "description": "查询资产的订阅、工单进度、收藏等使用信息",
        "user_story": "使用情况追踪",
        "examples": [
            "我订阅的资产有哪些？",
            "XX资产的工单进度如何？",
            "我收藏的五星资产",
            "这个资产有多少人订阅？"
        ],
        "keywords": ["订阅", "工单", "收藏", "使用", "进度"],
        "main_slots": ["AssetName", "UserStatus", "FilterCondition"]
    },
    IntentType.SCENARIO_RECOMMENDATION: {
        "code": "36",
        "name": "场景与标签推荐",
        "description": "基于业务场景、专区、标签名或复杂业务描述，推荐相关资产",
        "user_story": "US 1: 高效发现资产（场景化）",
        "examples": [
            "公众智慧运营专区有哪些资产？",
            "5G用户分析场景需要什么数据？",
            "一线赋能相关的资产推荐",
            "关于用户活跃度的数据有哪些？"
        ],
        "keywords": ["专区", "场景", "推荐", "相关", "关于"],
        "main_slots": ["BusinessZone", "CoreDataItem", "AssetType"]
    },
    IntentType.ASSET_COMPARISON: {
        "code": "37",
        "name": "资产复合对比与筛选",
        "description": "对比两个以上资产的关系或属性，或进行多条件复合筛选",
        "user_story": "US 2: 智能对比资产",
        "examples": [
            "'宽带提质速率(月)'和'新星级长高用户清单(月)'有什么关系？",
            "对比这两个资产的价值评分",
            "五星且M域的标签资产",
            "XX资产和YY资产的字段有什么不同？"
        ],
        "keywords": ["对比", "比较", "关系", "不同", "区别", "和"],
        "main_slots": ["AssetName", "MetadataItem", "FilterCondition"]
    },
    IntentType.PLATFORM_HELP: {
        "code": "38",
        "name": "平台规则与帮助",
        "description": "询问平台的操作流程、名词解释、联系人等基础帮助信息",
        "user_story": "平台使用指导",
        "examples": [
            "如何订阅资产？",
            "什么是数据资产？",
            "平台的联系人是谁？",
            "如何提交工单？"
        ],
        "keywords": ["如何", "怎么", "什么是", "联系人", "帮助"],
        "main_slots": ["MetadataItem"]
    }
}


# ========================================
# 10大槽位描述字典（用于标注和抽取）
# ========================================
SLOT_DESCRIPTIONS = {
    SlotType.ASSET_NAME: {
        "code": "槽位1",
        "name": "核心资产/ID/英文名",
        "description": "识别完整的资产名称（必须带上下文的复合名称）",
        "examples": [
            "[在线公司]终端激活信息(日)",
            "宽带提质速率(月)",
            "新星级长高用户清单(月)",
            "客户关系管理系统"
        ],
        "recognition_rule": "必须识别完整的、带上下文的复合名称，不要只识别部分"
    },
    SlotType.METADATA_ITEM: {
        "code": "槽位2",
        "name": "查询元数据项",
        "description": "用户想查询的元数据项及其别名（需要规范化）",
        "examples": [
            "业务口径（别名：业务解释、业务定义）",
            "技术口径（别名：技术定义）",
            "简介/用途（别名：是干什么的、作用）",
            "价值评估分数（别名：价值分数、评分）",
            "负责人（别名：管理员、Owner）"
        ],
        "recognition_rule": "必须识别别名并规范化到核心值",
        "synonym_mapping": {
            "业务解释": "业务口径",
            "业务定义": "业务口径",
            "技术定义": "技术口径",
            "是干什么的": "简介/用途",
            "作用": "简介/用途",
            "价值分数": "价值评估分数",
            "评分": "价值评估分数",
            "管理员": "负责人",
            "Owner": "负责人"
        }
    },
    SlotType.FIELD_NAME: {
        "code": "槽位3",
        "name": "字段名称",
        "description": "数据表中的字段名或数据项名称",
        "examples": [
            "user_id",
            "order_id",
            "是否长高用户",
            "5G登网标识"
        ],
        "recognition_rule": "精确识别字段名，区分大小写和下划线"
    },
    SlotType.CORE_DATA_ITEM: {
        "code": "槽位4",
        "name": "核心数据项",
        "description": "用户想要的业务概念或数据内容描述",
        "examples": [
            "5G登网",
            "移网用户是否活跃",
            "用户星级",
            "宽带提质"
        ],
        "recognition_rule": "识别业务概念，可能跨资产存在"
    },
    SlotType.BUSINESS_DOMAIN: {
        "code": "槽位5",
        "name": "业务/数据域",
        "description": "资产所属的业务域或数据域",
        "examples": [
            "M域",
            "O域",
            "B域",
            "客户域",
            "营销域"
        ],
        "recognition_rule": "识别域的缩写和全称"
    },
    SlotType.ASSET_TYPE: {
        "code": "槽位6",
        "name": "资产类型",
        "description": "资产的形态分类",
        "examples": [
            "标签",
            "模型资产",
            "数据表",
            "指标",
            "API接口"
        ],
        "recognition_rule": "识别资产的类型分类"
    },
    SlotType.BUSINESS_ZONE: {
        "code": "槽位7",
        "name": "业务专区",
        "description": "业务场景或专区名称",
        "examples": [
            "公众智慧运营",
            "一线赋能专区",
            "5G用户分析",
            "客户洞察"
        ],
        "recognition_rule": "识别场景化的业务专区名称"
    },
    SlotType.FILTER_CONDITION: {
        "code": "槽位8",
        "name": "筛选/限定条件",
        "description": "非其他槽位的筛选条件，需要动态解析",
        "examples": [
            "五星",
            "价值评估 > 80分",
            "最近一周更新的",
            "已上线的"
        ],
        "recognition_rule": "识别筛选条件，可能需要转换为WHERE子句"
    },
    SlotType.USER_STATUS: {
        "code": "槽位9",
        "name": "用户操作属性",
        "description": "识别用户的个人状态或操作",
        "examples": [
            "我收藏的",
            "我订阅的",
            "我创建的",
            "我负责的"
        ],
        "recognition_rule": "识别与用户相关的个性化查询"
    },
    SlotType.ORG_USER_NAME: {
        "code": "槽位10",
        "name": "机构/人员名",
        "description": "资产的管理机构或人员",
        "examples": [
            "总部-数据部",
            "张三",
            "营销中心",
            "李四"
        ],
        "recognition_rule": "识别组织机构名和人员姓名"
    }
}

# 向后兼容：保留旧的ENTITY_DESCRIPTIONS
ENTITY_DESCRIPTIONS = SLOT_DESCRIPTIONS


def get_intent_by_name(intent_name: str) -> IntentType:
    """
    根据字符串获取意图类型
    """
    try:
        return IntentType(intent_name)
    except ValueError:
        # 默认返回平台帮助意图（不再返回OOD）
        return IntentType.PLATFORM_HELP


def get_slot_by_name(slot_name: str) -> SlotType:
    """根据字符串获取槽位类型"""
    try:
        return SlotType(slot_name)
    except ValueError:
        raise ValueError(f"Unknown slot type: {slot_name}")


# 向后兼容
get_entity_by_name = get_slot_by_name


def validate_intent_result(result: Dict) -> bool:
    """
    验证意图识别结果格式是否正确

    """
    if "intent" not in result:
        return False
    if "entities" not in result and "slots" not in result:
        return False
    
    # 兼容entities和slots两种字段名
    entities = result.get("entities") or result.get("slots", [])
    if not isinstance(entities, list):
        return False

    # 检查intent是否合法
    try:
        IntentType(result["intent"])
    except ValueError:
        return False

    # 检查槽位格式
    for entity in entities:
        if not isinstance(entity, dict):
            return False
        if "type" not in entity or "value" not in entity:
            return False
        try:
            SlotType(entity["type"])
        except ValueError:
            return False

    return True
