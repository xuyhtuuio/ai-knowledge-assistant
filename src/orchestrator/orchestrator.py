"""
核心编排服务
实现"路由-检索-生成"架构
整合：意图识别模块、GraphRAG模块、答案生成模块
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from ..intent_recognition.intent_classifier import IntentClassifier
from ..intent_recognition.intent_config import IntentType
from ..graph_rag.graph_query import GraphQuery
from ..answer_generation.answer_generator import AnswerGenerator

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    核心编排服务
    负责协调整个AI知识助手的工作流
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化编排器

        Args:
            config_path: 配置文件路径
        """
        logger.info("正在初始化编排服务...")

        # 初始化各个模块
        self.intent_classifier = IntentClassifier(config_path)
        self.graph_query = GraphQuery(config_path)
        self.answer_generator = AnswerGenerator(config_path)

        # 统计信息
        self.request_count = 0
        self.start_time = datetime.now()

        logger.info("编排服务初始化完成")

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        处理用户查询（核心方法）

        工作流程：
        1. 意图识别 (Intent Recognition)
        2. 路由控制 (Routing)
        3. 图谱检索 (GraphRAG) - 如果是知识查询
        4. 答案生成 (Generation)

        Args:
            user_query: 用户查询

        Returns:
            包含答案和元信息的字典
        """
        start_time = time.time()
        self.request_count += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"处理查询 #{self.request_count}: {user_query}")
        logger.info(f"{'='*60}")

        try:
            # ========== 步骤1: 意图识别 ==========
            logger.info("[步骤1] 意图识别中...")
            intent_start = time.time()
            
            intent_result = self.intent_classifier.predict(user_query)
            
            intent_time = time.time() - intent_start
            logger.info(f"[步骤1] 意图识别完成 (耗时: {intent_time:.2f}s)")
            logger.info(f"  - 意图: {intent_result.intent}")
            logger.info(f"  - 槽位列表: {intent_result.slots}")
            

            # ========== 步骤2: 路由控制 ==========
            logger.info("[步骤2] 路由控制中...")
            logger.info(f"  - 意图: {intent_result.intent.value}")

            context = ""
            graph_results = []

            # 判断是否为平台帮助（Intent 38）
            if intent_result.intent == IntentType.PLATFORM_HELP:
                logger.info("  - 路由: Intent 38 (平台帮助) -> 直接生成帮助响应")
                
                # 直接生成平台帮助响应
                generation_start = time.time()
                # 可以从prompt_config.yaml读取帮助模板，这里简化处理
                answer_result = self.answer_generator.generate_ood_response(user_query)
                generation_time = time.time() - generation_start

                total_time = time.time() - start_time

                return {
                    "query": user_query,
                    "answer": answer_result['answer'],
                    "intent": intent_result.intent.value,
                    "entities": [
                        {"type": e.type.value, "value": e.value}
                        for e in intent_result.entities
                    ],
                    "context": "",
                    "graph_results": [],
                    "has_context": False,
                    "is_platform_help": True,
                    "timing": {
                        "intent_recognition": intent_time,
                        "graph_query": 0,
                        "answer_generation": generation_time,
                        "total": total_time
                    },
                    "metadata": {
                        "request_id": self.request_count,
                        "timestamp": datetime.now().isoformat()
                    }
                }

            else:
                # 其他7个意图都需要GraphRAG查询
                logger.info(f"  - 路由: {intent_result.intent.value} -> GraphRAG模块")

                # ========== 步骤3: GraphRAG检索 ==========
                logger.info("[步骤3] GraphRAG检索中...")
                graph_start = time.time()

                try:
                    # 生成并执行Cypher查询
                    graph_results = self.graph_query.query(intent_result)
                    
                    # 格式化为上下文
                    context = self.graph_query.format_context(
                        graph_results, 
                        intent_result.intent
                    )
                    
                    graph_time = time.time() - graph_start
                    logger.info(f"[步骤3] GraphRAG检索完成 (耗时: {graph_time:.2f}s)")
                    logger.info(f"  - 检索结果数: {len(graph_results)}")
                    logger.info(f"  - 上下文长度: {len(context)} 字符")

                except Exception as e:
                    logger.error(f"GraphRAG检索失败: {str(e)}")
                    graph_time = time.time() - graph_start
                    context = "知识库中暂无相关信息。"

                # ========== 步骤4: 答案生成 ==========
                logger.info("[步骤4] 答案生成中...")
                generation_start = time.time()

                answer_result = self.answer_generator.generate_answer(
                    user_query=user_query,
                    context=context,
                    intent=intent_result.intent.value
                )

                generation_time = time.time() - generation_start
                logger.info(f"[步骤4] 答案生成完成 (耗时: {generation_time:.2f}s)")

                total_time = time.time() - start_time
                logger.info(f"\n总耗时: {total_time:.2f}s")

                # 构建完整响应
                response = {
                    "query": user_query,
                    "answer": answer_result['answer'],
                    "intent": intent_result.intent.value,
                    "intent_name": self._get_intent_name(intent_result.intent),
                    "entities": [
                        {"type": e.type.value, "value": e.value}
                        for e in intent_result.entities
                    ],
                    "context": context,
                    "graph_results": graph_results,
                    "has_context": answer_result['has_context'],
                    "is_platform_help": False,
                    "timing": {
                        "intent_recognition": intent_time,
                        "graph_query": graph_time,
                        "answer_generation": generation_time,
                        "total": total_time
                    },
                    "metadata": {
                        "request_id": self.request_count,
                        "timestamp": datetime.now().isoformat()
                    }
                }

                return response

        except Exception as e:
            logger.error(f"查询处理失败: {str(e)}", exc_info=True)
            
            # 返回错误响应
            return {
                "query": user_query,
                "answer": "抱歉，处理您的查询时遇到了错误。请稍后重试或联系管理员。",
                "error": str(e),
                "intent": "ERROR",
                "entities": [],
                "context": "",
                "graph_results": [],
                "has_context": False,
                "is_ood": False,
                "timing": {
                    "total": time.time() - start_time
                },
                "metadata": {
                    "request_id": self.request_count,
                    "timestamp": datetime.now().isoformat()
                }
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息

        Returns:
            统计信息字典
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "request_count": self.request_count,
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_uptime(uptime),
            "start_time": self.start_time.isoformat(),
            "avg_requests_per_minute": (self.request_count / uptime * 60) if uptime > 0 else 0
        }

    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"

    def _get_intent_name(self, intent: IntentType) -> str:
        """
        获取意图的中文名称
        【新增】支持8大意图的名称映射
        """
        intent_names = {
            IntentType.ASSET_BASIC_SEARCH: "资产基础检索",
            IntentType.ASSET_METADATA_QUERY: "资产元数据查询",
            IntentType.ASSET_QUALITY_VALUE_QUERY: "资产质量与价值查询",
            IntentType.ASSET_LINEAGE_QUERY: "资产血缘关系查询",
            IntentType.ASSET_USAGE_QUERY: "资产使用与工单查询",
            IntentType.SCENARIO_RECOMMENDATION: "场景与标签推荐",
            IntentType.ASSET_COMPARISON: "资产复合对比与筛选",
            IntentType.PLATFORM_HELP: "平台规则与帮助"
        }
        return intent_names.get(intent, "未知意图")

    def close(self):
        """关闭服务，释放资源"""
        logger.info("正在关闭编排服务...")
        
        # 关闭图数据库连接
        self.graph_query.close()
        
        logger.info("编排服务已关闭")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 初始化编排器
    orchestrator = Orchestrator()

    # 测试查询列表
    test_queries = [
        "XX系统的负责人是谁？",
        "新员工入职流程怎么走？",
        "最近的数据安全法更新了什么？",
        "客户管理系统应用在哪些场景？",
        "数据安全法更新对客户管理系统有什么影响？",
        "今天天气怎么样？",  # OOD问题
    ]

    print("\n" + "="*80)
    print("AI知识助手测试")
    print("="*80)

    for query in test_queries:
        # 处理查询
        result = orchestrator.process_query(query)
        
        # 显示结果
        print(f"\n问题: {result['query']}")
        print(f"意图: {result['intent']}")
        print(f"实体: {result['entities']}")
        print(f"答案: {result['answer']}")
        print(f"耗时: {result['timing']['total']:.2f}s")
        print("-" * 80)

    # 显示统计信息
    stats = orchestrator.get_stats()
    print("\n服务统计:")
    print(f"  总请求数: {stats['request_count']}")
    print(f"  运行时间: {stats['uptime_formatted']}")
    print(f"  平均QPS: {stats['avg_requests_per_minute']:.2f} req/min")

    # 关闭服务
    orchestrator.close()

