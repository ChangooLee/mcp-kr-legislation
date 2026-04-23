# 운영 모델 — mcp-kr-legislation

## 시스템 아키텍처

```
Claude Desktop / Claude Code
        │
        ▼
FastMCP Server (mcp-kr-legislation)
        │
   ┌────┴────┐
   │         │
   ▼         ▼
197개 도구   캐시 시스템
   │         │
   ▼         ▼
법제처 OPEN API  ~/.cache/mcp-kr-legislation/
(law.go.kr)
```

## 도구 카테고리 매트릭스
| 카테고리 | 도구 수 | 모듈 | 특이사항 |
|---------|---------|------|---------|
| 법령 | 23 | law_tools.py | 법령명/본문 검색, 조문 조회 |
| 법령 비교/이력 | 11 | law_comparison_tools.py | 개정 이력, 연계 |
| 법령 특수검색 | 6 | law_specialized_tools.py | 금융/세무/개인정보 도메인 |
| 최적화 | 4 | optimized_law_tools.py | 캐시 최적화 버전 |
| 자치법규/행정규칙 | 8 | administrative_rule_tools.py | 지방 조례, 훈령 |
| 위원회결정문 | 24 | committee_tools.py | 12개 위원회 |
| 판례 | 8 | precedent_tools.py | 대법원, 헌재, 행정심판 |
| 중앙부처해석 | 68 | ministry_interpretation_tools*.py | 30개 부처 |
| 특별행정심판 | 14 | specialized_tools.py | 8개 기관 |
| 법령용어 | 10 | legal_term_tools.py | AI 검색 포함 |
| 맞춤형 | 6 | custom_tools.py | 연혁, 비교 등 |
| 부가서비스 | 6 | additional_service_tools.py | 별표, 서식 |
| 연계 | 2 | linkage_tools.py | 법령 간 관계 |
| 기타 | 3 | misc_tools.py | 조약, 학칙 |
| **BM25 고도화** | **5** | **search_enhance_tools.py** | **BM25+캐시관리** |

## 검색 흐름 (BM25 포함)

```
사용자: "개인정보 처리 동의 관련 법령"
        │
        ▼
search_law_bm25(query="개인정보 처리 동의")
        │
        ├─ 캐시 확인 (7일 TTL)
        │   └─ HIT: 즉시 반환
        │   └─ MISS: API 호출
        │
        ▼
법제처 API (top-50 결과)
        │
        ▼
BM25 재랭킹 (rank-bm25)
  ┌─ 토크나이저: 공백/구두점 분리, 2자 이상, 불용어 제거
  ├─ BM25Okapi 계산
  └─ 점수 기준 정렬
        │
        ▼
상위 10개 결과 (_bm25_score 포함)
```

## 스웜 사이클

스웜 사이클은 에이전트 간 협업으로 시스템을 유지/개선합니다:

```
orchestrator
    │
    ├─ api-verifier → 법제처 사이트 크롤 → 커버리지 보고
    │
    ├─ tool-developer → 미구현 API → 도구 추가
    │
    ├─ search-engineer → BM25 품질 측정 → 개선
    │
    └─ 검증 사이클 완료 → state/runs/ 에 보고서 저장
```

실행:
```bash
./scripts/run_swarm_cycle.sh
```

## 품질 게이트
1. **도구 로딩**: 서버 시작 시 17/17 모듈 로드
2. **API 응답**: 실제 법제처 API totalCnt > 0
3. **캐시 히트**: 동일 쿼리 재호출 시 캐시 사용
4. **BM25 점수**: 관련 법령이 상위 3위 이내
5. **테스트**: pytest 전체 통과
