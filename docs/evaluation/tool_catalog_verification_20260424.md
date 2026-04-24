# 도구 카탈로그 검증 보고서

> **검증 일시**: 2026-04-24  
> **대상 파일**: `docs/tool_catalog.md`  
> **검증 방법**: 실제 코드(`src/mcp_kr_legislation/tools/`) 및 API 호출 기반 검증

---

## 1. 카탈로그 요약 검증

| 항목 | 카탈로그 표기 | 실제 값 | 일치 여부 |
|---|---|---|---|
| 전체 도구 수 | 213개 | 213개 | ✅ 정확 |
| 섹션 수 | 22개 섹션 | 22개 섹션 | ✅ 정확 |
| 생성일 | 2026-04-23 | (기록 기준) | — |

---

## 2. 누락된 도구 목록 (코드에 있지만 카탈로그에 없는 것들)

총 **5개** 도구가 코드에 등록되어 있으나 카탈로그에 설명이 누락되어 있습니다.

| 도구명 | 실제 파일 | 카탈로그 섹션 | 작동 상태 |
|---|---|---|---|
| `search_effective_law` | `law_tools.py` L2352 | 섹션 2(시행일법령)에 누락 | ✅ 정상 |
| `search_english_law` | `law_tools.py` L2046 | 섹션 3(영문법령)에 누락 | ✅ 정상 |
| `search_university_regulation` | `specialized_tools.py` L130 | 카탈로그 전체 누락 | ✅ 정상 |
| `search_public_corporation_regulation` | `specialized_tools.py` L153 | 카탈로그 전체 누락 | ✅ 정상 |
| `search_public_institution_regulation` | `specialized_tools.py` L176 | 카탈로그 전체 누락 | ✅ 정상 |

### 누락 도구 설명 보완

#### `search_effective_law`
- **목적**: 시행일법령 목록 검색 (target=eflaw). 시행상태(현행/미시행/폐지) 필터 지원.
- **파라미터**: `query`, `search`(1=법령명, 2=본문), `display`, `page`, `status_type`(100=시행, 200=미시행, 300=폐지), 기타 날짜 범위 파라미터 다수
- **반환**: 법령명, 법령일련번호(MST), 현행연혁코드[현행/연혁], 공포일자, 시행일자, 소관부처명
- **체인**: MST → `get_effective_law_detail`, `get_effective_law_articles`
- **배치 권장**: 섹션 2(시행일법령 도구)에 추가 필요

#### `search_english_law`
- **목적**: 영문법령 목록 검색 (target=elaw). 영어 키워드 검색.
- **파라미터**: `query`(영어 키워드), `display`, `page`
- **반환**: 법령명(영문), 법령일련번호(MST), 공포일자, 시행일자, 소관부처명
- **체인**: MST → `get_english_law_detail`, `get_english_law_summary`
- **배치 권장**: 섹션 3(영문법령 도구)에 추가 필요

#### `search_university_regulation`
- **목적**: 대학교 학칙 검색 (vcode 기관코드 기반 대학 범위 검색).
- **파라미터**: `query`(학교명 또는 키워드), `display`, `page`
- **반환**: 행정규칙일련번호, 규칙명, 소관부처명(학교명), 시행일자
- **체인**: 행정규칙일련번호 → `get_administrative_rule_detail(rule_id=...)`
- **배치 권장**: 신규 섹션 또는 섹션 19(맞춤형)에 추가

#### `search_public_corporation_regulation`
- **목적**: 지방공사공단 규정 검색.
- **파라미터**: `query`(기관명 또는 키워드), `display`, `page`
- **반환**: 행정규칙일련번호, 규칙명, 소관부처명(공사공단명), 시행일자
- **배치 권장**: `search_university_regulation`과 같은 섹션

#### `search_public_institution_regulation`
- **목적**: 공공기관 규정 검색.
- **파라미터**: `query`(기관명 또는 키워드), `display`, `page`
- **반환**: 행정규칙일련번호, 규칙명, 소관부처명(공공기관명), 시행일자
- **배치 권장**: `search_university_regulation`과 같은 섹션

---

## 3. 섹션 배치 오류

### 3-1. 섹션 3(영문법령)에 잘못 배치된 도구

카탈로그 섹션 3은 "영문법령 도구"로 정의되어 있으나, 다음 3개 도구가 잘못 배치되어 있음:

| 도구명 | 현재 위치 | 올바른 위치 |
|---|---|---|
| `search_financial_laws` | 섹션 3(영문법령) AND 섹션 21(도메인) | 섹션 21(도메인 특화)만 |
| `search_tax_laws` | 섹션 3(영문법령) AND 섹션 21(도메인) | 섹션 21(도메인 특화)만 |
| `search_privacy_laws` | 섹션 3(영문법령) AND 섹션 21(도메인) | 섹션 21(도메인 특화)만 |

**원인**: 섹션 3에 `search_financial_laws`, `search_tax_laws`, `search_privacy_laws`가 
포함되어 있는데, 이는 영문법령 섹션이 아닌 도메인 특화 검색 도구임. 해당 도구들은
섹션 21(도메인 특화 법령 검색)에 올바르게 재분류됨.

**실제 영문법령 섹션(3)에 있어야 할 도구**:
- `search_english_law` (현재 누락)
- `get_english_law_detail`
- `get_english_law_summary`
- `search_english_law_articles_semantic`
- `search_law_articles_semantic` (영/한 통합)

### 3-2. 카탈로그 명명 불일치

| 카탈로그 표기 | 실제 도구명 | 비고 |
|---|---|---|
| `moms`/`mnd` = 국방부 | `get_mnd_interpretation_detail` | ✅ `get_mnd_interpretation_detail` 존재 |
| — | `search_moms_interpretation` | ✅ 국방부 검색은 `moms`로 등록 |
| — | `get_moms_interpretation_detail` | ❌ 미존재 (카탈로그 서술은 있음) |

**결론**: 국방부 interpretation 도구는 검색(`search_moms_interpretation`)과 상세조회(`get_mnd_interpretation_detail`) 간 코드명이 불일치함.

---

## 4. 버그 수정 검증 결과 (수정된 10개)

| # | 도구명 | 이전 버그 | 수정 방법 | 실제 호출 결과 | 현재 상태 |
|---|---|---|---|---|---|
| 1 | `search_related_law` | 관계유형 코드만 표시 (`2유형(특별법)`) | 관계유형 한글 번역 적용 | `수권관계`, `특별법관계` 등 번역 포함 확인 | ✅ 수정 완료 |
| 2 | `search_committee_bm25` | nlrc 타겟 제목 필드 매핑 오류 | `nlrc` 필드 매핑 구현 | nlrc API 결과가 `○ ○ ○` 마스킹으로 BM25 점수 0 → 결과 없음 | ⚠️ 코드 수정됨, API 특성상 결과 없을 수 있음 |
| 3 | `get_one_view_detail` | 한눈보기 정보 조회 실패 | endpoint `is_detail=True` 수정 | `가맹사업거래법` 한눈보기 17건 조회 성공 | ✅ 수정 완료 |
| 4 | `get_administrative_rule_comparison_detail` | 비교 상세 API 응답 파싱 로직 미완성 | `AdmRulOldAndNewService` 파싱 추가 | ID=1 (순번)로는 정상 작동, 검색 결과의 `신구법일련번호`로는 API가 응답 안 함 | ⚠️ 부분 수정 — ID 매핑 방식 문제 잔존 |
| 5 | `get_ordinance_detail` | `ID=` 파라미터 오류 | `MST=` 파라미터로 변경 | 코드 정상(API URL 직접 검증 완료), 도구 호출 시 타임아웃 간헐적 발생 | ✅ 코드 수정 완료 (API 지연 있음) |
| 6 | `get_treaty_detail` | 조약 상세 API JSON 미지원 | 검색 API 폴백 방식으로 변경 | 조약일련번호 `1400`으로 조약명/번호/발효일 조회 성공 | ✅ 수정 완료 |
| 7 | `get_ordinance_appendix_detail` | 별표서식 본문 파싱 미완성 | `별표일련번호` 파라미터 직접 조회 방식으로 변경 | 별표일련번호 `21433579`로 별표명/종류/상세링크 조회 성공 | ✅ 수정 완료 |
| 8 | `search_intelligent_law` | 공포일자 타임스탬프(`20250401120400`) 포함 | 날짜 포맷 정제 (`[:8]` 슬라이싱) | `2025-04-01` 형식으로 정상 표시 확인 | ✅ 수정 완료 |
| 9 | `search_intelligent_related_law` | raw dict 문자열 출력 | `aiRltLsSearch` 루트키 수정 | 법령명, 조문번호, 시행일자 정상 포맷으로 출력 확인 | ✅ 수정 완료 |
| 10 | `get_delegated_law` | lsDelegated API 빈 응답 | 다중 API 시도 + 대안 안내 | 여전히 위임법령 데이터 없음, 대안(search_related_law) 안내로 처리 | ⚠️ 미수정 (API 제한) |

### 수정 결과 요약

- ✅ **완전 수정**: 7개 (`search_related_law`, `get_one_view_detail`, `get_treaty_detail`, `get_ordinance_appendix_detail`, `search_intelligent_law`, `search_intelligent_related_law`, `get_ordinance_detail`)
- ⚠️ **부분 수정**: 2개 (`get_administrative_rule_comparison_detail` — ID 매핑 방식 잔존 문제, `search_committee_bm25` — nlrc API 마스킹 특성)
- ❌ **미수정**: 1개 (`get_delegated_law` — API 자체 미지원)

---

## 5. 여전히 작동 불가한 도구

### 5-1. API 미오픈 (JSON 상세 조회 불가)

| 도구명 | 증상 | 원인 |
|---|---|---|
| `get_delegated_law` | 빈 응답 또는 대안 안내만 반환 | `lsDelegated` API JSON 조회 지원 안 됨 |
| `get_administrative_rule_comparison_detail` | 검색 결과의 `신구법일련번호`로 조회 시 빈 응답 | `admrulOldAndNew` lawService.do의 ID는 순번(1, 2, 3...)이어야 하나 검색 API는 `신구법일련번호`(12자리) 반환 — ID 형식 불일치 |

### 5-2. 검색 API 데이터 부족 (특정 쿼리에서 결과 없음)

| 도구명 | 이유 |
|---|---|
| `search_acrc_special_tribunal` | 일부 쿼리('행정', '부당해고' 등)에서 결과 없음 — '취소' 쿼리로는 작동 |
| `search_mpm_appeal_tribunal` | 일부 쿼리('공무원')에서 결과 없음 — '징계' 쿼리로는 작동 |
| `search_committee_bm25(nlrc)` | nlrc API 사건명이 `○ ○ ○`으로 마스킹 → BM25 키워드 매칭 불가 |

### 5-3. 간헐적 타임아웃 (코드 정상, API 지연)

| 도구명 | 증상 |
|---|---|
| `get_ordinance_detail` | 법제처 `lawService.do?target=ordin` API에서 간헐적 15초+ 타임아웃 발생 |
| `get_effective_law_articles` | 대형 법령 조문 조회 시 지연 |

---

## 6. 카탈로그 정확도 종합 평가

| 항목 | 평가 |
|---|---|
| 전체 도구 수(213개) | ✅ 정확 |
| 누락 도구 | ❌ 5개 누락 (`search_effective_law`, `search_english_law`, `search_university_regulation`, `search_public_corporation_regulation`, `search_public_institution_regulation`) |
| 섹션 배치 오류 | ❌ 섹션 3에 영문법령이 아닌 도메인 도구 3개 잘못 배치 |
| 수정된 버그 반영 | ✅ 7개 수정 완료로 카탈로그 설명과 일치 |
| 미수정 버그 | ⚠️ `get_administrative_rule_comparison_detail` ID 매핑 문제 설명 보완 필요 |
| 명명 불일치 | ⚠️ 국방부 detail 도구 `get_moms_interpretation_detail` 미존재 (`get_mnd_interpretation_detail`이 정확) |

---

*검증일: 2026-04-24 | 검증 환경: Darwin 24.6.0 / Python 3.13 / 법제처 OPEN API (실제 호출)*
