#!/usr/bin/env python3
"""
캐시 통계 스크립트

사용법:
    python cache_stats.py
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def get_cache_stats():
    """캐시 통계 수집"""
    cache_dir = project_root / "src" / "mcp_kr_legislation" / "utils" / "data" / "legislation_cache"
    
    if not cache_dir.exists():
        print(f"📁 캐시 디렉토리가 없습니다: {cache_dir}")
        return
    
    stats = {
        "total_count": 0,
        "total_size": 0,
        "by_type": defaultdict(lambda: {"count": 0, "size": 0}),
        "expiring_soon": 0,
    }
    
    print(f"📊 캐시 통계: {cache_dir}\n")
    
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
            expires_at = datetime.fromisoformat(metadata.get("expires_at", datetime.now().isoformat()))
            
            # 크기 계산
            size = sum(f.stat().st_size for f in item_cache.rglob('*') if f.is_file())
            
            stats["total_count"] += 1
            stats["total_size"] += size
            stats["by_type"][item_type]["count"] += 1
            stats["by_type"][item_type]["size"] += size
            
            # 만료 예정 (7일 이내)
            days_until_expiry = (expires_at - datetime.now()).days
            if 0 <= days_until_expiry <= 7:
                stats["expiring_soon"] += 1
                
        except Exception as e:
            print(f"⚠️  오류 ({item_cache.name}): {e}")
    
    # 통계 출력
    print(f"📈 전체 통계:")
    print(f"   - 총 캐시 개수: {stats['total_count']}개")
    print(f"   - 총 크기: {stats['total_size'] / 1024 / 1024:.2f} MB")
    print(f"   - 만료 예정 (7일 이내): {stats['expiring_soon']}개")
    
    print(f"\n📋 타입별 통계:")
    for item_type, type_stats in sorted(stats["by_type"].items()):
        print(f"   - {item_type}:")
        print(f"     * 개수: {type_stats['count']}개")
        print(f"     * 크기: {type_stats['size'] / 1024 / 1024:.2f} MB")


def main():
    get_cache_stats()
    sys.exit(0)


if __name__ == "__main__":
    main()
