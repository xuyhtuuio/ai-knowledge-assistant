"""
API服务器
基于Flask提供RESTful API接口
"""

import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Any

from ..orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


def create_app(config_path: str = "config/config.yaml") -> Flask:
    """
    创建Flask应用

    Args:
        config_path: 配置文件路径

    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    CORS(app)  # 允许跨域

    # 初始化编排器
    orchestrator = Orchestrator(config_path)
    logger.info("API服务初始化完成")

    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({
            "status": "healthy",
            "service": "AI Knowledge Assistant"
        }), 200

    @app.route('/api/v1/query', methods=['POST'])
    def query():
        """
        主查询接口
        
        请求体:
        {
            "query": "用户查询文本"
        }
        
        响应:
        {
            "success": true,
            "data": {
                "query": "...",
                "answer": "...",
                "intent": "...",
                "entities": [...],
                "context": "...",
                "has_context": true/false,
                ...
            }
        }
        """
        try:
            # 获取请求数据
            data = request.get_json()
            
            if not data or 'query' not in data:
                return jsonify({
                    "success": False,
                    "error": "缺少必需参数: query"
                }), 400

            user_query = data['query'].strip()
            
            if not user_query:
                return jsonify({
                    "success": False,
                    "error": "查询内容不能为空"
                }), 400

            # 处理查询
            result = orchestrator.process_query(user_query)

            # 返回响应
            return jsonify({
                "success": True,
                "data": result
            }), 200

        except Exception as e:
            logger.error(f"查询处理失败: {str(e)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"服务器错误: {str(e)}"
            }), 500

    @app.route('/api/v1/stats', methods=['GET'])
    def get_stats():
        """
        获取服务统计信息
        
        响应:
        {
            "success": true,
            "data": {
                "request_count": 123,
                "uptime_seconds": 3600,
                ...
            }
        }
        """
        try:
            stats = orchestrator.get_stats()
            return jsonify({
                "success": True,
                "data": stats
            }), 200

        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/v1/batch_query', methods=['POST'])
    def batch_query():
        """
        批量查询接口
        
        请求体:
        {
            "queries": ["查询1", "查询2", ...]
        }
        
        响应:
        {
            "success": true,
            "data": {
                "results": [...]
            }
        }
        """
        try:
            data = request.get_json()
            
            if not data or 'queries' not in data:
                return jsonify({
                    "success": False,
                    "error": "缺少必需参数: queries"
                }), 400

            queries = data['queries']
            
            if not isinstance(queries, list):
                return jsonify({
                    "success": False,
                    "error": "queries必须是列表"
                }), 400

            # 批量处理
            results = []
            for query in queries:
                if isinstance(query, str) and query.strip():
                    result = orchestrator.process_query(query.strip())
                    results.append(result)

            return jsonify({
                "success": True,
                "data": {
                    "count": len(results),
                    "results": results
                }
            }), 200

        except Exception as e:
            logger.error(f"批量查询处理失败: {str(e)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return jsonify({
            "success": False,
            "error": "接口不存在"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        return jsonify({
            "success": False,
            "error": "服务器内部错误"
        }), 500

    # 清理资源
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """应用上下文结束时清理资源"""
        pass

    return app


def run_server(host: str = "0.0.0.0", 
               port: int = 8000, 
               debug: bool = False,
               config_path: str = "config/config.yaml"):
    """
    运行API服务器

    Args:
        host: 主机地址
        port: 端口号
        debug: 是否开启调试模式
        config_path: 配置文件路径
    """
    app = create_app(config_path)
    
    logger.info(f"启动API服务器: http://{host}:{port}")
    logger.info("接口列表:")
    logger.info("  GET  /health              - 健康检查")
    logger.info("  POST /api/v1/query        - 单个查询")
    logger.info("  POST /api/v1/batch_query  - 批量查询")
    logger.info("  GET  /api/v1/stats        - 服务统计")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行服务器
    run_server(
        host="0.0.0.0",
        port=8000,
        debug=True
    )

