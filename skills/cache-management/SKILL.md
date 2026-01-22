---
name: cache-management
description: 법령/판례 캐시 데이터 관리 시 사용. 캐시 저장/로드, 만료 처리, 지식 그래프 동기화. 성능 최적화 및 API 호출 최소화를 위해 캐싱 구현 시 참조.
---

# 캐시 관리 가이드

법령, 판례, 위원회결정문 등의 데이터를 캐싱하여 성능을 향상시키고 API 호출을 최소화합니다.

## 캐시 구조

### 디렉토리 레이아웃

```
utils/data/
├── legislation_cache/
│   ├── law_{law_id}/          # 법령 캐시
│   │   ├── metadata.json
│   │   ├── detail.json
│   │   └── articles/
│   ├── precedent_{prec_no}/   # 판례 캐시
│   │   ├── metadata.json
│   │   ├── detail.json
│   │   └── summary.json
│   └── committee_{decision_id}/ # 위원회결정문 캐시
│       ├── metadata.json
│       └── detail.json
└── knowledge_graph/
    ├── nodes.json
    ├── edges.json
    └── synonyms/
```

### 캐시 메타데이터

```json
{
  "id": "law_12345",
  "type": "law",
  "cached_at": "2025-12-31T12:00:00Z",
  "expires_at": "2026-01-07T12:00:00Z",
  "source": "lawSearch.do",
  "version": "1.0"
}
```

## 기본 사용법

### 캐시 확인 후 API 호출

```python
# 캐시 확인
cached = load_legislation_cache(law_id, "law")
if cached:
    return cached

# API 호출
result = client.service("law", {"ID": law_id})

# 캐시 저장
if result.get("status") == "000":
    save_legislation_cache(law_id, "law", result)
```

## 캐시 무효화

- **자동 만료**: `expires_at` 기준으로 자동 삭제
- **수동 무효화**: `invalidate_cache(item_id, item_type)`
- **법령 개정 시**: 관련 캐시 자동 무효화 권장

## 유틸리티 스크립트

캐시 정리:
```bash
python scripts/cleanup_cache.py [--dry-run]
```

캐시 통계:
```bash
python scripts/cache_stats.py
```

## 상세 구현

구현 코드는 [implementation.md](implementation.md) 참조.

## 주의사항

1. **캐시 디렉토리 권한**: 프로젝트 디렉토리에 쓰기 권한 필요
2. **캐시 크기 관리**: 주기적으로 만료된 캐시 정리
3. **지식 그래프 동기화**: 캐시 저장 시 그래프도 함께 업데이트

## 관련 파일

- [src/mcp_kr_legislation/utils/data/](../../src/mcp_kr_legislation/utils/data/) - 캐시 디렉토리
- [skills/graph-search/](graph-search/) - 지식 그래프 검색
