#!/usr/bin/env python3
"""
数据验证脚本
验证所有CSV数据文件的格式和内容是否正确
"""

import os
import pandas as pd
from pathlib import Path

def validate_csv(file_path, required_columns):
    """验证CSV文件"""
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    try:
        df = pd.read_csv(file_path)
        
        # 检查必需列
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            return False, f"缺少列: {missing_cols}"
        
        # 检查数据行数
        if len(df) == 0:
            return False, "文件为空"
        
        return True, f"✓ 验证通过 ({len(df)} 行数据)"
    
    except Exception as e:
        return False, f"读取失败: {str(e)}"


def main():
    print("=" * 60)
    print("知识图谱数据验证")
    print("=" * 60)
    
    base_dir = Path(__file__).parent.parent / "data" / "raw"
    
    # 定义需要验证的文件和必需列
    files_to_validate = {
        "assets/assets.csv": ["asset_id", "name", "description", "owner", "type"],
        "scenarios/scenarios.csv": ["scenario_id", "name", "description"],
        "hotspots/hotspots.csv": ["hotspot_id", "title", "summary"],
        "fields/fields.csv": ["field_id", "asset_id", "name", "data_type"],
        "domains/domains.csv": ["domain_id", "name"],
        "zones/zones.csv": ["zone_id", "name", "description"],
        "concepts/concepts.csv": ["concept_id", "name", "type"],
        "users/users.csv": ["user_id", "name", "role"],
        "orgs/orgs.csv": ["org_id", "name"],
        "relationships/asset_scenario.csv": ["asset_id", "scenario_id"],
        "relationships/hotspot_asset.csv": ["hotspot_id", "asset_id"],
        "relationships/relationships.csv": ["source_type", "source_id", "target_type", "target_id"],
        "relationships/lineage.csv": ["source_asset_id", "target_asset_id"],
    }
    
    all_valid = True
    stats = {}
    
    print("\n文件验证结果:\n")
    
    for file_path, required_cols in files_to_validate.items():
        full_path = base_dir / file_path
        valid, message = validate_csv(full_path, required_cols)
        
        status = "✓" if valid else "✗"
        print(f"{status} {file_path:45s} {message}")
        
        if not valid:
            all_valid = False
        else:
            # 统计数据量
            df = pd.read_csv(full_path)
            file_key = file_path.split('/')[-1].replace('.csv', '')
            stats[file_key] = len(df)
    
    print("\n" + "=" * 60)
    
    if all_valid:
        print("✓ 所有数据文件验证通过！\n")
        
        print("数据统计:")
        print(f"  资产节点: {stats.get('assets', 0)}")
        print(f"  场景节点: {stats.get('scenarios', 0)}")
        print(f"  热点节点: {stats.get('hotspots', 0)}")
        print(f"  字段节点: {stats.get('fields', 0)}")
        print(f"  业务域节点: {stats.get('domains', 0)}")
        print(f"  业务专区节点: {stats.get('zones', 0)}")
        print(f"  业务概念节点: {stats.get('concepts', 0)}")
        print(f"  用户节点: {stats.get('users', 0)}")
        print(f"  组织节点: {stats.get('orgs', 0)}")
        print(f"  资产-场景关系: {stats.get('asset_scenario', 0)}")
        print(f"  热点-资产关系: {stats.get('hotspot_asset', 0)}")
        print(f"  通用关系: {stats.get('relationships', 0)}")
        print(f"  血缘关系: {stats.get('lineage', 0)}")
        
        print("\n可以开始构建图谱了！运行:")
        print("  python -m src.graph_rag.graph_builder")
        print("  或")
        print("  bash scripts/build_graph.sh")
    else:
        print("✗ 数据验证失败，请修复上述问题后重试")
        return 1
    
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())

