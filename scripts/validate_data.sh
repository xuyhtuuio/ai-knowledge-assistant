#!/bin/bash
# 数据验证脚本 - 检查所有CSV文件是否存在且有内容

echo "============================================================"
echo "知识图谱数据验证"
echo "============================================================"
echo ""

BASE_DIR="data/raw"
ALL_VALID=true

# 定义需要检查的文件
declare -a FILES=(
    "$BASE_DIR/assets/assets.csv"
    "$BASE_DIR/scenarios/scenarios.csv"
    "$BASE_DIR/hotspots/hotspots.csv"
    "$BASE_DIR/fields/fields.csv"
    "$BASE_DIR/domains/domains.csv"
    "$BASE_DIR/zones/zones.csv"
    "$BASE_DIR/concepts/concepts.csv"
    "$BASE_DIR/users/users.csv"
    "$BASE_DIR/orgs/orgs.csv"
    "$BASE_DIR/relationships/asset_scenario.csv"
    "$BASE_DIR/relationships/hotspot_asset.csv"
    "$BASE_DIR/relationships/relationships.csv"
    "$BASE_DIR/relationships/lineage.csv"
)

echo "文件验证结果:"
echo ""

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        # 统计行数（减去标题行）
        lines=$(tail -n +2 "$file" | grep -v '^$' | wc -l | tr -d ' ')
        echo "✓ $file (${lines} 行数据)"
    else
        echo "✗ $file (文件不存在)"
        ALL_VALID=false
    fi
done

echo ""
echo "============================================================"

if [ "$ALL_VALID" = true ]; then
    echo "✓ 所有数据文件验证通过！"
    echo ""
    echo "数据统计:"
    echo "  资产节点: $(tail -n +2 $BASE_DIR/assets/assets.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  场景节点: $(tail -n +2 $BASE_DIR/scenarios/scenarios.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  热点节点: $(tail -n +2 $BASE_DIR/hotspots/hotspots.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  字段节点: $(tail -n +2 $BASE_DIR/fields/fields.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  业务域节点: $(tail -n +2 $BASE_DIR/domains/domains.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  业务专区节点: $(tail -n +2 $BASE_DIR/zones/zones.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  业务概念节点: $(tail -n +2 $BASE_DIR/concepts/concepts.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  用户节点: $(tail -n +2 $BASE_DIR/users/users.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  组织节点: $(tail -n +2 $BASE_DIR/orgs/orgs.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  资产-场景关系: $(tail -n +2 $BASE_DIR/relationships/asset_scenario.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  热点-资产关系: $(tail -n +2 $BASE_DIR/relationships/hotspot_asset.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  通用关系: $(tail -n +2 $BASE_DIR/relationships/relationships.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo "  血缘关系: $(tail -n +2 $BASE_DIR/relationships/lineage.csv | grep -v '^$' | wc -l | tr -d ' ')"
    echo ""
    echo "📖 详细数据说明请查看: data/DATA_SUMMARY.md"
    echo ""
    echo "🚀 可以开始构建图谱了！运行:"
    echo "  bash scripts/build_graph.sh"
    echo "  或"
    echo "  python3 -m src.graph_rag.graph_builder"
else
    echo "✗ 数据验证失败，请检查缺失的文件"
    exit 1
fi

echo "============================================================"

