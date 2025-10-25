#!/bin/bash

# 构建知识图谱脚本

echo "=========================================="
echo "开始构建知识图谱"
echo "=========================================="

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: Python未安装"
    exit 1
fi

# 检查Neo4j是否运行
echo ""
echo "检查Neo4j服务..."
if ! nc -z localhost 7687 2>/dev/null; then
    echo "错误: Neo4j服务未启动"
    echo "请先启动Neo4j: sudo systemctl start neo4j"
    exit 1
fi
echo "✓ Neo4j服务正常"

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo ""
    echo "激活虚拟环境..."
    source venv/bin/activate
    echo "✓ 虚拟环境已激活"
fi

# 检查数据文件
echo ""
echo "检查数据文件..."
DATA_DIR="data/raw"
REQUIRED_FILES=(
    "$DATA_DIR/assets/assets.csv"
    "$DATA_DIR/scenarios/scenarios.csv"
    "$DATA_DIR/hotspots/hotspots.csv"
    "$DATA_DIR/relationships/asset_scenario.csv"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "错误: 缺少数据文件: $file"
        exit 1
    fi
    echo "✓ $file"
done

# 构建图谱
echo ""
echo "开始构建图谱..."
python -m src.graph_rag.graph_builder

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "图谱构建完成！"
    echo "=========================================="
    echo ""
    echo "可以通过以下方式访问Neo4j:"
    echo "  浏览器: http://localhost:7474"
    echo "  Bolt: bolt://localhost:7687"
else
    echo ""
    echo "错误: 图谱构建失败"
    exit 1
fi

