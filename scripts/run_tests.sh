#!/bin/bash

# 运行测试脚本

echo "=========================================="
echo "运行API测试"
echo "=========================================="

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: Python未安装"
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 检查API服务是否运行
echo ""
echo "检查API服务..."
if ! nc -z localhost 8000 2>/dev/null; then
    echo "错误: API服务未启动"
    echo "请先启动API服务: ./scripts/start_api.sh"
    exit 1
fi
echo "✓ API服务正常"

# 运行测试
echo ""
echo "开始运行测试..."
echo "=========================================="
python tests/test_api.py

echo ""
echo "测试完成"

