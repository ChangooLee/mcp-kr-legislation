---
name: bm25-search
description: BM25 Okapi 알고리즘을 사용하여 법령/판례 API 결과를 관련도 순으로 재랭킹합니다. search_enhance_tools.py와 bm25_search.py 구현 시 참조.
---

# BM25 검색 스킬

## 언제 사용하나
- 법제처 API 결과의 관련도 순서가 부정확할 때
- 자연어 쿼리로 법령을 검색할 때 (예: "개인정보 처리 동의")
- 키워드 매칭 검색을 넘어서는 품질 개선 필요 시

## 언제 사용하지 않나
- 정확한 법령명으로 검색 시 (기존 `search_law`가 더 빠름)
- 법령 ID/MST로 직접 조회 시

## 아키텍처

```
사용자 쿼리
    │
    ▼
법제처 API (법령명 기반 검색, top-50)
    │
    ▼
BM25 재랭킹 (bm25_search.py)
  - 토크나이저: 공백/구두점 분리, 불용어 제거, 2자 이상 토큰
  - BM25Okapi 계산 (rank-bm25 패키지)
  - 점수 기준 내림차순 정렬
    │
    ▼
상위 K개 반환 (각 항목에 _bm25_score 추가)
```

## 핵심 API (bm25_search.py)

```python
from mcp_kr_legislation.utils.bm25_search import rank_search_results, BM25Ranker

# 간단 사용
ranked = rank_search_results(
    query="개인정보 처리 동의",
    results=api_results,
    text_keys=["법령명한글", "소관부처명"],
    top_k=10,
)

# 세부 제어
ranker = BM25Ranker()
ranked = ranker.rank(
    query="손해배상 과실상계",
    documents=precedents,
    text_keys=["사건명", "법원명"],
    top_k=5,
    score_threshold=0.1,  # 최소 점수 필터
)
```

## 텍스트 키 선택 가이드
| 도구 유형 | text_keys |
|---------|-----------|
| 법령 | `["법령명한글", "소관부처명", "법령구분명"]` |
| 판례 | `["사건명", "법원명", "사건종류명"]` |
| 위원회결정문 | `["사건명", "결정유형명"]` |
| 행정규칙 | `["법령명", "소관부처명"]` |
| 법령용어 | `["법령용어명", "뜻풀이"]` |

## 새 BM25 도구 추가 패턴

```python
# search_enhance_tools.py에 추가
@mcp.tool(name="search_legal_term_bm25", ...)
def search_legal_term_bm25(query: str, top_k: int = 10) -> TextContent:
    cache_key = get_cache_key(f"bm25_lstrm_{query}_50", "bm25")
    cached = load_from_cache(cache_key)
    if not cached:
        data = _raw_search("lstrm", query, display=50)
        items = _extract_list(data, "LstrmSearch")
        save_to_cache(cache_key, items)
    else:
        items = cached
    ranked = rank_search_results(
        query, items,
        text_keys=["법령용어명", "뜻풀이"],
        top_k=top_k
    )
    # 포맷팅 후 반환
```

## 한계 및 향후 개선

| 기능 | 현황 | 개선 방향 |
|------|------|---------|
| 토크나이저 | 공백 분리 | kiwipiepy 형태소 분석 |
| 문서 본문 검색 | 법령명만 | 조문 내용 포함 |
| 의미 기반 검색 | 미구현 | sentence-transformers 추가 |
| 하이브리드 검색 | 미구현 | BM25 + 벡터 결합 |

## 의존성

```toml
# pyproject.toml
dependencies = [
    "rank-bm25>=0.2.2",  # BM25Okapi 구현
]
```

rank-bm25 없으면 자동으로 TF 폴백 사용 (성능 저하 있음).

## 관련 파일
- `src/mcp_kr_legislation/utils/bm25_search.py` — 핵심 구현
- `src/mcp_kr_legislation/tools/search_enhance_tools.py` — MCP 도구
- `.cursor/rules/20-bm25-search-guide.mdc` — Cursor 룰
