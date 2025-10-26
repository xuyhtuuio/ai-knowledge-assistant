"""
Intent 31 (资产基础检索) 完整流程模拟

模拟从大模型意图识别 -> Cypher生成 -> 执行查询的完整过程
"""

from neo4j import GraphDatabase
import json

#  模拟大模型意图识别输出
def simulate_llm_intent_recognition(user_query: str):
    """
    模拟大模型对用户查询进行意图识别和槽位提取实际项目中，这里会调用Qwen3-32B SFT模型
    """
    
    # 定义几个测试用例
    test_cases = {
        "M域的所有资产有哪些？": {
            "intent": "31",  # ASSET_BASIC_SEARCH
            "slots": {
                "BusinessDomain": ["M域"]
            }
        },
        "包含user_id字段的资产": {
            "intent": "31",
            "slots": {
                "FieldName": ["user_id"]
            }
        },
        "平台上有哪些系统类型的资产？": {
            "intent": "31",
            "slots": {
                "AssetType": ["系统"]
            }
        },
        "M域的系统类型资产": {
            "intent": "31",
            "slots": {
                "BusinessDomain": ["M域"],
                "AssetType": ["系统"]
            }
        },
        "HR系统": {
            "intent": "31",
            "slots": {
                "AssetName": ["HR系统"]
            }
        }
    }
    
    # 查找匹配的测试用例
    for query, result in test_cases.items():
        if query in user_query or user_query in query:
            return result
    
    # 默认返回
    return test_cases["M域的所有资产有哪些？"]



def generate_cypher_for_intent31(slots: dict) -> str:
    """
    根据槽位生成Intent 31的Cypher查询
    
    支持的槽位：
    - AssetName (槽位1): 资产名称
    - AssetType (槽位6): 资产类型
    - BusinessDomain (槽位5): 业务域
    - FieldName (槽位3): 字段名称
    - FilterCondition (槽位8): 筛选条件
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
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # 情况1: 查询特定业务域的资产
    if 'BusinessDomain' in slots:
        domain_name = slots['BusinessDomain'][0]
        cypher = f"""
MATCH (a:Asset)-[:BELONGS_TO]->(d:BusinessDomain)
WHERE d.name = "{domain_name}" AND {where_clause}
RETURN a.asset_id AS asset_id,
       a.name AS name, 
       a.description AS description,
       a.type AS type, 
       a.owner AS owner,
       a.status AS status,
       d.name AS domain
ORDER BY a.name
LIMIT 50
        """.strip()
    
    # 情况2: 查询包含特定字段的资产
    elif 'FieldName' in slots:
        field_name = slots['FieldName'][0]
        cypher = f"""
MATCH (a:Asset)-[:HAS_FIELD]->(f:Field)
WHERE f.name = "{field_name}" AND {where_clause}
RETURN a.asset_id AS asset_id,
       a.name AS name, 
       a.description AS description,
       a.type AS type,
       f.name AS field_name,
       f.data_type AS field_type
ORDER BY a.name
LIMIT 50
        """.strip()
    
    # 情况3: 基础资产查询
    else:
        cypher = f"""
MATCH (a:Asset)
WHERE {where_clause}
RETURN a.asset_id AS asset_id,
       a.name AS name,
       a.description AS description,
       a.type AS type,
       a.owner AS owner,
       a.status AS status
ORDER BY a.name
LIMIT 50
        """.strip()
    
    return cypher


def execute_cypher(cypher: str):
    """执行Cypher查询并返回结果"""
    
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "neo4j123")
    )
    
    try:
        with driver.session() as session:
            result = session.run(cypher)
            records = [dict(record) for record in result]
            return records
    finally:
        driver.close()




# 完整流程演示
def demo_intent31_pipeline(user_query: str):
    """
    完整演示Intent 31的处理流程
    """    
    # 1: 用户输入
    print(f"\n【用户查询】\n{user_query}\n")
    
    # 2: 模拟大模型意图识别
    print("【步骤1: 意图识别】")
    print("调用 Qwen3-32B SFT 模型...")
    intent_result = simulate_llm_intent_recognition(user_query)
    print(f"识别结果:")
    print(f"  Intent: {intent_result['intent']} (ASSET_BASIC_SEARCH)")
    print(f"  Slots: {json.dumps(intent_result['slots'], ensure_ascii=False, indent=8)}")
    
    # 步骤3: 生成Cypher查询
    print("\n【步骤2: 生成Cypher查询】")
    cypher = generate_cypher_for_intent31(intent_result['slots'])
    
    # 步骤4: 执行查询
    print("\n【步骤3: 执行Neo4j查询】")
    print("连接到 bolt://localhost:7687...")
    try:
        records = execute_cypher(cypher)
        print(f"查询成功，返回 {len(records)} 条记录")
    except Exception as e:
        print(f"查询失败: {str(e)}")
        return
    

    # 5: JSON结果（供调试）
    print("【原始JSON结果】")
    print(json.dumps(records, ensure_ascii=False, indent=2))
    


# 主程序
if __name__ == "__main__":
    
    # 1: 查询业务
    print("测试用例 1: 查询M域的资产")
    demo_intent31_pipeline("M域的所有资产有哪些？")
    
    # 2: 查询字段
    print("测试用例 2: 查询包含特定字段的资产")
    demo_intent31_pipeline("包含user_id字段的资产")
    
    # 3: 查询资产类型
    print("测试用例 3: 查询资产类型")
    demo_intent31_pipeline("平台上有哪些系统类型的资产？")
    
    # 4: 复合条件查询
    print("测试用例 4: 复合条件查询")
    demo_intent31_pipeline("M域的系统类型资产")
    
    # 5: 精确查询
    print("测试用例 5: 精确资产名称")
    demo_intent31_pipeline("HR系统")

