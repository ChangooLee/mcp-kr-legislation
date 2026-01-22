# 캐시 구현 코드

## 캐시 저장

```python
from pathlib import Path
import json
from datetime import datetime, timedelta

def save_legislation_cache(
    item_id: str,
    item_type: str,
    data: dict,
    cache_dir: Path = None
) -> Path:
    """
    법령 데이터 캐싱
    
    Args:
        item_id: 법령/판례 ID
        item_type: 'law', 'precedent', 'committee', etc.
        data: 캐시할 데이터
        cache_dir: 캐시 디렉토리 경로
    """
    if cache_dir is None:
        cache_dir = Path(__file__).parent.parent / "utils" / "data" / "legislation_cache"
    
    cache_path = cache_dir / f"{item_type}_{item_id}"
    cache_path.mkdir(parents=True, exist_ok=True)
    
    # 메타데이터 저장
    metadata = {
        "id": item_id,
        "type": item_type,
        "cached_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
    }
    
    with open(cache_path / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # 데이터 저장
    with open(cache_path / "detail.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return cache_path
```

## 캐시 로드

```python
def load_legislation_cache(
    item_id: str,
    item_type: str,
    cache_dir: Path = None
) -> Optional[dict]:
    """
    캐시된 법령 데이터 로드
    
    Returns:
        캐시된 데이터 또는 None (캐시 없음/만료)
    """
    if cache_dir is None:
        cache_dir = Path(__file__).parent.parent / "utils" / "data" / "legislation_cache"
    
    cache_path = cache_dir / f"{item_type}_{item_id}"
    
    if not cache_path.exists():
        return None
    
    # 메타데이터 확인
    metadata_path = cache_path / "metadata.json"
    if not metadata_path.exists():
        return None
    
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    # 만료 확인
    expires_at = datetime.fromisoformat(metadata["expires_at"])
    if datetime.now() > expires_at:
        return None
    
    # 데이터 로드
    detail_path = cache_path / "detail.json"
    if not detail_path.exists():
        return None
    
    with open(detail_path, "r", encoding="utf-8") as f:
        return json.load(f)
```

## 캐시 무효화

```python
def invalidate_cache(item_id: str, item_type: str):
    """
    특정 캐시 무효화
    """
    cache_path = Path(__file__).parent.parent / "utils" / "data" / "legislation_cache"
    item_cache = cache_path / f"{item_type}_{item_id}"
    
    if item_cache.exists():
        import shutil
        shutil.rmtree(item_cache)
        logger.info(f"캐시 무효화: {item_type}_{item_id}")

def cleanup_expired_cache(cache_dir: Path = None):
    """
    만료된 캐시 자동 정리
    """
    if cache_dir is None:
        cache_dir = Path(__file__).parent.parent / "utils" / "data" / "legislation_cache"
    
    if not cache_dir.exists():
        return
    
    for item_cache in cache_dir.iterdir():
        metadata_path = item_cache / "metadata.json"
        if not metadata_path.exists():
            continue
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        expires_at = datetime.fromisoformat(metadata["expires_at"])
        if datetime.now() > expires_at:
            import shutil
            shutil.rmtree(item_cache)
            logger.info(f"만료된 캐시 삭제: {item_cache.name}")
```
