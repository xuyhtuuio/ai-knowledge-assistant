#!/bin/bash

# 启动API服务脚本

echo "=========================================="
echo "启动AI知识助手API服务"
echo "=========================================="

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: Python未安装"
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo ""
    echo "激活虚拟环境..."
    source venv/bin/activate
    echo "✓ 虚拟环境已激活"
fi

# 检查配置文件
if [ ! -f "config/config.yaml" ]; then
    echo "错误: 配置文件不存在: config/config.yaml"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 检查端口是否被占用
PORT=8000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "警告: 端口 $PORT 已被占用"
    echo "是否继续? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 启动服务
echo ""
echo "启动API服务..."
echo "  地址: http://0.0.0.0:$PORT"
echo "  日志: logs/api.log"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

python -m src.api.api_server 2>&1 | tee logs/api.log

