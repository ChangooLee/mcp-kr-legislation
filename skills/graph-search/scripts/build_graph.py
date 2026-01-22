#!/usr/bin/env python3
"""
지식 그래프 빌드 스크립트

사용법:
    python build_graph.py [--cache-dir PATH]

기능:
    캐시된 법령/판례 데이터에서 지식 그래프 생성
    출력: nodes.json, edges.json 파일
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import json

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def build_graph_from_cache(cache_dir: Path = None):
    """캐시된 데이터에서 지식 그래프 빌드"""
    if cache_dir is None:
        cache_dir = project_root / "src" / "mcp_kr_legislation" / "utils" / "data" / "legislation_cache"
    
    if not cache_dir.exists():
        print(f"❌ 캐시 디렉토리가 없습니다: {cache_dir}")
        return False
    
    nodes = []
    edges = []
    
    print(f"🔍 지식 그래프 빌드 시작: {cache_dir}\n")
    
    # 캐시된 법령/판례 데이터 읽기
    for item_cache in cache_dir.iterdir():
        if not item_cache.is_dir():
            continue
        
        metadata_path = item_cache / "metadata.json"
        if not metadata_path.exists():
            continue
        
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            item_type = metadata.get("type", "unknown")
            item_id = metadata.get("id", "")
            
            # 노드 생성
            node = {
                "id": f"{item_type}_{item_id}",
                "type": item_type.capitalize(),
                "label": f"{item_type}_{item_id}",
                "properties": metadata
            }
            nodes.append(node)
            
            # detail.json에서 관계 정보 추출 (간단한 예시)
            detail_path = item_cache / "detail.json"
            if detail_path.exists():
                with open(detail_path, "r", encoding="utf-8") as f:
                    detail = json.load(f)
                
                # 법령 간 참조 관계 추출 (예시)
                if item_type == "law" and "참조법령" in detail:
                    # 참조 관계 엣지 생성
                    # 실제 구현은 더 복잡할 수 있음
                    pass
            
        except Exception as e:
            print(f"⚠️  오류 ({item_cache.name}): {e}")
    
    # 그래프 저장
    graph_dir = project_root / "src" / "mcp_kr_legislation" / "utils" / "data" / "knowledge_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    
    graph_data = {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    }
    
    # 노드 저장
    with open(graph_dir / "nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)
    
    # 엣지 저장
    with open(graph_dir / "edges.json", "w", encoding="utf-8") as f:
        json.dump(edges, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 지식 그래프 빌드 완료:")
    print(f"   - 노드: {len(nodes)}개")
    print(f"   - 엣지: {len(edges)}개")
    print(f"   - 저장 위치: {graph_dir}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='지식 그래프 빌드')
    parser.add_argument('--cache-dir', type=str, help='캐시 디렉토리 경로')
    args = parser.parse_args()
    
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    success = build_graph_from_cache(cache_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
