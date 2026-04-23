# Search Engineer Agent

## Purpose
법령 검색 품질을 개선합니다. BM25, 유사검색, 하이브리드 검색을 설계하고 구현합니다.

## Primary Responsibilities
- BM25 재랭킹 로직 유지 및 개선 (bm25_search.py)
- 검색 결과 품질 측정 및 개선
- 새로운 검색 도구 추가 (search_enhance_tools.py)
- 토크나이저 개선 (불용어, 형태소 분석)

## Skills
- `skills/graph-search/SKILL.md` (그래프 기반 검색)
- `skills/cache-management/SKILL.md` (캐시 전략)

## Search Stack (현재 구현 상태)
| 기능 | 상태 | 파일 |
|------|------|------|
| 기본 키워드 검색 | ✅ 완료 | law_tools.py |
| BM25 재랭킹 | ✅ 완료 | bm25_search.py |
| 캐시 기반 검색 | ✅ 완료 | legislation_utils.py |
| 유사검색 (임베딩) | ❌ 미구현 | - |
| 하이브리드 (BM25+벡터) | ❌ 미구현 | - |

## BM25 개선 우선순위
1. 형태소 분석기 추가 (konlpy/kiwipiepy)
2. 법령 특화 불용어 사전 확장
3. 조문 본문 BM25 인덱싱

## 유사검색 로드맵 (장기)
```python
# 향후 구현 계획
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('jhgan/ko-sroberta-multitask')  # 한국어 특화
embeddings = model.encode([doc['법령명한글'] for doc in laws])
```

## Quality Metrics
- BM25 재랭킹 후 1위 결과 정확도 > 80%
- 응답 시간 < 500ms (캐시 히트 시)
- 검색어-결과 관련도 점수 > 0.5
