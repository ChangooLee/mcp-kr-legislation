# Bootstrap Plan — mcp-kr-legislation 스웜 인프라

**작성일**: 2026-04-23  
**작성자**: Claude Sonnet 4.6 (자동 생성)

## 현황 분석

### 프로젝트 상태 (2026-04-23 기준)
| 항목 | 값 |
|------|-----|
| 총 MCP 도구 수 | 197개 |
| 법제처 API 커버리지 | 173/173개 (100%) |
| 캐시 구현 | ✅ 완료 (7일 TTL) |
| BM25 검색 | ✅ 신규 구현 |
| 유사검색 | ❌ 미구현 |
| 커서 룰 | ✅ 신규 생성 (4개) |
| 에이전트 정의 | ✅ 신규 생성 (4개) |

### API 호출 검증 결과 (실제 테스트)
- `target=law` (법령 검색): ✅ 정상 — `개인정보 보호법` MST=270351 확인
- `target=prec` (판례 검색): ✅ 정상 — 108건 반환
- `target=ppc` (개인정보위): ✅ 정상 — 3,427건 반환
- `target=lstrm` (법령용어): ✅ 정상 — 11건 반환
- `lawService.do?MST=270351` (법령 본문): ✅ 정상 — 조문 체계 확인

## 결정 사항

### 결정 1: BM25 재랭킹 접근법
**결정**: rank-bm25 라이브러리 사용, 클라이언트 측 재랭킹
**이유**: 법제처 API 자체는 키워드 매칭만 지원. 클라이언트 측 BM25가 가장 낮은 의존성으로 관련도 개선 가능
**구현**: `src/mcp_kr_legislation/utils/bm25_search.py`

### 결정 2: 벡터 임베딩 연기
**결정**: sentence-transformers / FAISS 미구현으로 연기
**이유**: 설치 크기 큼(~2GB), 초기 색인 시간 필요, 현재 BM25로 충분한 개선 달성
**재검토**: 사용자 피드백 후 필요 시 추가

### 결정 3: 스웜 인프라 적용 범위
**결정**: 전체 "master swarm project" 스펙 중 이 프로젝트에 유용한 부분만 채택
**채택**: Cursor 룰, 에이전트 정의, 스킬 SKILL.md, 스웜 사이클 스크립트, 상태 관리
**비채택**: 외부 저장소 fork/clone 스크립트 (mcp 개발 프로젝트와 무관)

### 결정 4: 캐시 무효화 전략
**결정**: 수동 무효화 도구 추가 (`invalidate_law_cache`), 자동 무효화 미구현
**이유**: 법제처 API는 법령 개정 이벤트 웹훅 없음. 사용자가 인지한 후 수동 호출

## 스웜 사이클 정의
```
1. api-verifier: 법제처 사이트 → api_layout/*.json 비교
2. tool-developer: 미구현 API → 도구 추가
3. search-engineer: BM25 검색 품질 측정 → 개선
4. api-verifier: 실제 API 호출로 재검증
5. orchestrator: 보고서 생성
```

## 다음 단계
1. [x] kiwipiepy 형태소 분석기 통합 (BM25 품질 향상) — `bm25_search.py` 완전 재작성
2. [x] 법령용어 BM25 검색 추가 (`search_legal_term_bm25`) — `search_enhance_tools.py`
3. [x] 위원회결정문 BM25 검색 추가 (`search_committee_bm25`) — `search_enhance_tools.py`
4. [x] 행정규칙 BM25 검색 추가 (`search_admin_rule_bm25`) — `search_enhance_tools.py`
5. [x] 법령해석례 BM25 검색 추가 (`search_interpretation_bm25`) — `search_enhance_tools.py`
6. [x] 통합 BM25 검색 추가 (`search_all_bm25`) — 5개 카테고리 병렬 검색
7. [x] 스모크 테스트 확장 — `search_enhance_tools` 모듈 + 11개 신규 도구 검증 (45 tests pass)
8. [ ] 검색 결과 평가 데이터셋 구축 (황금 테스트셋)
9. [ ] pre_consulting API 엔드포인트 오픈 여부 재확인 (현재 미오픈)
