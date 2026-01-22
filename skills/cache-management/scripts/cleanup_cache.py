#!/usr/bin/env python3
"""
캐시 정리 스크립트

사용법:
    python cleanup_cache.py [--dry-run]

옵션:
    --dry-run: 삭제 전 미리보기만 (실제 삭제 안 함)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import json

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def cleanup_cache(dry_run: bool = False):
    """만료된 캐시 정리"""
    cache_dir = project_root / "src" / "mcp_kr_legislation" / "utils" / "data" / "legislation_cache"
    
    if not cache_dir.exists():
        print(f"📁 캐시 디렉토리가 없습니다: {cache_dir}")
        return 0
    
    expired_count = 0
    total_size = 0
    
    print(f"🔍 캐시 정리 시작: {cache_dir}\n")
    
    for item_cache in cache_dir.iterdir():
        if not item_cache.is_dir():
            continue
        
        metadata_path = item_cache / "metadata.json"
        if not metadata_path.exists():
            if not dry_run:
                import shutil
                shutil.rmtree(item_cache)
            print(f"🗑️  메타데이터 없음: {item_cache.name}")
            expired_count += 1
            continue
        
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            expires_at = datetime.fromisoformat(metadata["expires_at"])
            if datetime.now() > expires_at:
                # 크기 계산
                size = sum(f.stat().st_size for f in item_cache.rglob('*') if f.is_file())
                total_size += size
                
                if dry_run:
                    print(f"⚠️  만료 예정 삭제: {item_cache.name} ({size / 1024:.1f} KB)")
                else:
                    import shutil
                    shutil.rmtree(item_cache)
                    print(f"🗑️  삭제: {item_cache.name} ({size / 1024:.1f} KB)")
                expired_count += 1
        except Exception as e:
            print(f"❌ 오류 ({item_cache.name}): {e}")
    
    print(f"\n📊 정리 결과:")
    print(f"   - 만료된 캐시: {expired_count}개")
    print(f"   - 총 삭제 크기: {total_size / 1024 / 1024:.2f} MB")
    
    if dry_run:
        print(f"\n💡 실제 삭제하려면 --dry-run 옵션을 제거하세요.")
    
    return expired_count


def main():
    parser = argparse.ArgumentParser(description='캐시 정리')
    parser.add_argument('--dry-run', action='store_true', help='삭제 전 미리보기만')
    args = parser.parse_args()
    
    count = cleanup_cache(dry_run=args.dry_run)
    sys.exit(0)
