# 법제처 MCP 도구 카탈로그 (213개)

실제 API 응답 결과를 기반으로 작성된 도구 설명서. 다중 도구 연계(Multi-Tool Orchestration)를 위한 참조 문서.

---

## 목차

1. [핵심 패턴: Search → Detail 체인](#핵심-패턴)
2. [현행법령 도구 (Core Law)](#1-현행법령-도구)
3. [시행일법령 도구 (Effective Date Law)](#2-시행일법령-도구)
4. [영문법령 도구 (English Law)](#3-영문법령-도구)
5. [판례 · 결정례 도구 (Case Law)](#4-판례--결정례-도구)
6. [행정심판 도구 (Administrative Trial)](#5-행정심판-도구)
7. [행정규칙 도구 (Administrative Rule)](#6-행정규칙-도구)
8. [자치법규 도구 (Local Ordinance)](#7-자치법규-도구)
9. [조약 도구 (Treaty)](#8-조약-도구)
10. [법령해석 도구 – 법제처/부처별 (Interpretation)](#9-법령해석-도구)
11. [위원회 결정문 도구 (Committee)](#10-위원회-결정문-도구)
12. [특별행정심판 도구 (Special Tribunal)](#11-특별행정심판-도구)
13. [법령용어 도구 (Legal Term)](#12-법령용어-도구)
14. [법령비교 도구 (Law Comparison)](#13-법령비교-도구)
15. [별표서식 도구 (Appendix/Form)](#14-별표서식-도구)
16. [법령연혁 도구 (Amendment History)](#15-법령연혁-도구)
17. [연계정보 도구 (Linkage)](#16-연계정보-도구)
18. [지능형 검색 도구 (AI Search)](#17-지능형-검색-도구)
19. [BM25 재랭킹 도구 (BM25 Search)](#18-bm25-재랭킹-도구)
20. [맞춤형 도구 (Custom)](#19-맞춤형-도구)
21. [지식베이스 / 상담 도구 (Knowledge Base)](#20-지식베이스--상담-도구)
22. [도메인 특화 법령 검색 (Domain-Specific)](#21-도메인-특화-법령-검색)
23. [캐시 · 유틸리티 도구 (Utility)](#22-캐시--유틸리티-도구)
24. [다중 도구 연계 패턴](#다중-도구-연계-패턴)

---

## 핵심 패턴

### Search → Detail 체인 전체 맵

| Search 도구 | 반환 ID 필드 | Detail 도구 | Detail ID 파라미터 |
|---|---|---|---|
| `search_law_unified` | 법령일련번호 (MST) | `get_law_detail` | `mst` |
| `search_law_unified` | 법령일련번호 (MST) | `get_law_article_by_key` | `mst` |
| `search_law_unified` | 법령일련번호 (MST) | `get_law_articles_range` | `mst` |
| `search_law_unified` | 법령일련번호 (MST) | `get_effective_law_detail` | `mst` |
| `search_law_unified` | 법령일련번호 (MST) | `get_law_system_diagram_detail` | `mst_id` |
| `search_precedent` | 판례일련번호 | `get_precedent_detail` | `case_id` |
| `search_constitutional_court` | 결정례일련번호 | `get_constitutional_court_detail` | `decision_id` |
| `search_legal_interpretation` | 해석례일련번호 | `get_legal_interpretation_detail` | `interpretation_id` |
| `search_administrative_trial` | 행정심판재결례일련번호 | `get_administrative_trial_detail` | `trial_id` |
| `search_administrative_rule` | 행정규칙ID | `get_administrative_rule_detail` | `rule_id` |
| `search_administrative_rule_comparison` | 비교일련번호 | `get_administrative_rule_comparison_detail` | `comparison_id` |
| `search_local_ordinance` | 자치법규일련번호 (MST) | `get_local_ordinance_detail` | `ordinance_id` |
| `search_local_ordinance` | 자치법규일련번호 (MST) | `get_ordinance_detail` | `ordinance_id` |
| `search_ordinance_appendix` | 별표일련번호 | `get_ordinance_appendix_detail` | `appendix_id` |
| `search_treaty` | 조약일련번호 | `get_treaty_detail` | `treaty_id` |
| `search_law_amendment_history` | 법령일련번호 | `get_law_amendment_history_detail` | `law_id` |
| `search_old_and_new_law` | 법령일련번호 | `get_old_and_new_law_detail` | `law_id` |
| `search_three_way_comparison` | 법령일련번호 | `get_three_way_comparison_detail` | `law_id` |
| `search_one_view` | 법령일련번호 | `get_one_view_detail` | `law_id` |
| `search_law_appendix` | 별표일련번호 | `get_law_appendix_detail` | `appendix_id` |
| `search_legal_term` | 용어일련번호 | `get_legal_term_detail` | `term_id` |
| `search_tax_tribunal` | 결정례일련번호 | `get_tax_tribunal_detail` | `tribunal_id` |
| `search_maritime_safety_tribunal` | 결정례일련번호 | `get_maritime_safety_tribunal_detail` | `tribunal_id` |
| `search_acrc_special_tribunal` | 재결례일련번호 | `get_acrc_special_tribunal_detail` | `tribunal_id` |
| `search_mpm_appeal_tribunal` | 재결례일련번호 | `get_mpm_appeal_tribunal_detail` | `tribunal_id` |
| `search_bai_preconsulting` | 의견서일련번호 | `get_bai_preconsulting_detail` | `opinion_id` |
| 각 부처 `search_*_interpretation` | 해석례일련번호 | 각 `get_*_interpretation_detail` | `interpretation_id` |
| 각 `search_*_committee` | 결정문번호 | 각 `get_*_committee_detail` | `decision_id` |

---

## 1. 현행법령 도구

현행 시행 중인 법률·시행령·시행규칙 등을 검색·조회.

### `search_law_unified`
**목적**: 법령명 또는 키워드로 현행법령을 검색. 가장 범용적인 법령 검색 진입점.  
**파라미터**: `query`(검색어), `target`("law"|"eflaw"|"elaw", 기본="law"), `display`(결과수), `page`  
**실제 반환 필드**: 법령일련번호(MST), 법령명한글, 법령명영문, 공포일자(YYYYMMDD), 시행일자, 소관부처명, 법령구분명  
**체인**: MST → `get_law_detail`, `get_law_article_by_key`, `get_law_articles_range`  
**특이사항**: target="eflaw"이면 시행일법령, "elaw"이면 영문법령 검색

### `search_law`
**목적**: 법령 목록 검색 (구 API 직접 호출, 내부용). `search_law_unified` 사용 권장.  
**파라미터**: `query`, `target`("law"|"eflaw"|"elaw"), `display`, `page`  
**반환**: 법령일련번호(MST), 법령명, 공포일자, 시행일자

### `get_law_detail`
**목적**: MST로 법령 전문(全文) 조회. 기본정보 + 모든 조문 + 부칙 포함.  
**파라미터**: `mst`(법령일련번호, 필수)  
**실제 반환 구조**: 법령기본정보{법령명, 공포번호, 공포일자, 시행일자, 소관부처명}, 조문{제1조~마지막조, 각 조의 항·호·목}, 부칙  
**특이사항**: 대형 법령(수백 조)은 응답이 길어질 수 있음. 특정 조문만 필요하면 `get_law_article_by_key` 사용

### `get_law_article_by_key`
**목적**: 특정 조문(예: "제15조")의 내용만 조회.  
**파라미터**: `mst`(법령일련번호), `target`("law"|"eflaw"), `article_key`(예: "제15조", "15", "제3조제1항")  
**실제 반환**: 조문번호, 조문제목, 조문내용, 하위 항·호·목  
**특이사항**: 조문 번호 표현 유연. "제15조", "15", "15조" 모두 인식

### `get_law_articles_range`
**목적**: 연속된 여러 조문을 한 번에 조회 (범위 지정).  
**파라미터**: `mst`, `target`, `start_article`(시작조 번호), `count`(조문 수), `include_details`  
**반환**: 지정 범위 조문 목록, 각 조의 항·호·목

### `get_law_summary`
**목적**: 법령의 요약 정보 조회 (기본정보 + 주요 조문 목차).  
**파라미터**: `mst`(법령일련번호) 또는 `law_name`(법령명)  
**반환**: 법령명, 공포일자, 시행일자, 소관부처명, 조문 수, 조문 목차

### `get_law_article_detail`
**목적**: 조문 상세 내용 조회 (get_law_article_by_key와 유사, 최적화 버전).  
**파라미터**: `mst`, `article_key`

### `get_law_articles_summary_tool`
**목적**: 법령의 조문 목차(조제목 목록) 요약 조회.  
**파라미터**: `mst`  
**반환**: 조문번호-조제목 목록 (본문 미포함, 빠름)

### `search_law_with_cache`
**목적**: 캐시를 활용한 법령 검색 (7일 캐시).  
**파라미터**: `query`

### `search_law_nickname`
**목적**: 법령 약칭 검색 (예: "민법" → 민법, "형법" → 형법).  
**파라미터**: `query`(약칭 검색어), `display`, `page`  
**반환**: 약칭, 법령명, MST

### `search_deleted_law_data`
**목적**: 폐지·삭제된 법령 데이터 검색.  
**파라미터**: `query`, `display`, `page`  
**반환**: 법령명, 폐지일자, 법령일련번호

### `search_law_articles`
**목적**: 조문 내용 키워드 검색 (법령 내 특정 조문 탐색).  
**파라미터**: `query`(키워드), `target`("law"|"eflaw"), `display`, `page`  
**반환**: 법령명, 조문번호, 조문내용 일치 결과

---

## 2. 시행일법령 도구

특정 시행일 기준의 법령 조문 조회.

### `get_effective_law_articles`
**목적**: 특정 시행일 기준 법령의 조항호목 목록 조회.  
**파라미터**: `mst`(법령일련번호), `efdate`(시행일자 YYYYMMDD, 선택)  
**반환**: 조문번호, 조문제목, 해당 시행일의 조문 상태(신설/개정/현행)

### `search_effective_law_articles_raw`
**목적**: 공포일 기준 시행일법령의 조항호목 메타데이터 직접 조회.  
**파라미터**: `mst`, `display`, `page`  
**반환**: 조문번호, 조문제목, 공포일자 (목차 수준, 본문 미포함)

### `get_effective_law_detail`
**목적**: 시행일법령 전문 조회 (eflaw target).  
**파라미터**: `mst`(법령일련번호), `efdate`(시행일자, 선택)  
**반환**: get_law_detail과 동일 구조, 시행일 기준 조문

---

## 3. 영문법령 도구

영어로 번역된 법령 검색·조회.

### `get_english_law_detail`
**목적**: 영문 법령 전문 조회.  
**파라미터**: `mst`(법령일련번호)  
**반환**: 법령명(영문), 조문(영문), 공포일자, 시행일자  
**특이사항**: 영문법령은 번역된 법령만 존재. MST는 한국어 법령과 동일.

### `search_financial_laws`
**목적**: 금융 분야 법령 전문 검색 (금융위원회, 금융감독원 관련 법령).  
**파라미터**: `query`, `include_regulations`(시행령 포함 여부), `display`, `page`  
**반환**: 법령명, MST, 공포일자, 소관부처명  
**특이사항**: 금융 도메인 키워드로 필터링된 법령 목록

### `search_tax_laws`
**목적**: 세무·조세 분야 법령 전문 검색.  
**파라미터**: `query`, `include_regulations`, `display`, `page`  
**반환**: 법령명, MST, 공포일자, 소관부처명

### `search_privacy_laws`
**목적**: 개인정보보호 분야 법령 전문 검색.  
**파라미터**: `query`, `include_regulations`, `display`, `page`  
**반환**: 법령명, MST, 공포일자, 소관부처명

### `search_law_articles_semantic`
**목적**: 법령 조문 의미 기반 검색 (키워드 매칭 + 의미 유사도).  
**파라미터**: `query`, `law_name`(특정 법령명), `display`  
**반환**: 법령명, 조문번호, 조문내용

### `search_english_law_articles_semantic`
**목적**: 영문법령 조문 의미 기반 검색.  
**파라미터**: `query`(영어), `law_name`(영문법령명), `display`  
**반환**: 법령명(영문), 조문번호, 조문내용(영문)

### `get_english_law_summary`
**목적**: 영문법령 요약 정보 조회.  
**파라미터**: `law_name`(영문법령명) 또는 `mst`  
**반환**: 법령명(영문), 공포일자, 시행일자, 조문 수

---

## 4. 판례 · 결정례 도구

대법원 판례, 헌법재판소 결정례.

### `search_precedent`
**목적**: 대법원 판례 검색.  
**파라미터**: `query`(키워드/사건명), `display`, `page`  
**실제 반환 필드**: 판례일련번호, 사건명, 법원명, 선고일자, 사건종류명, 판결유형  
**체인**: 판례일련번호 → `get_precedent_detail(case_id=판례일련번호)`

### `get_precedent_detail`
**목적**: 판례 상세 조회 (판결 요지 + 이유 + 참조 조문).  
**파라미터**: `case_id`(판례일련번호)  
**실제 반환**: 판결요지, 판결이유, 참조조문(법령명+조문번호), 참조판례, 원심판결  
**특이사항**: 국세청 판례는 JSON 미지원 → HTML 링크만 제공

### `search_constitutional_court`
**목적**: 헌법재판소 결정례 검색.  
**파라미터**: `query`, `display`, `page`  
**실제 반환 필드**: 결정례일련번호, 사건명, 사건번호, 선고일자, 결정유형  
**체인**: 결정례일련번호 → `get_constitutional_court_detail(decision_id=결정례일련번호)`

### `get_constitutional_court_detail`
**목적**: 헌법재판소 결정례 상세 조회.  
**파라미터**: `decision_id`(결정례일련번호)  
**반환**: 결정요지, 결정이유, 관련 법령 조문, 재판관 의견

---

## 5. 행정심판 도구

중앙행정심판위원회 행정심판 재결례.

### `search_administrative_trial`
**목적**: 행정심판 재결례 검색.  
**파라미터**: `query`, `search`(1=사건명검색, 2=본문검색, 기본=1), `display`, `page`  
**실제 반환 필드**: 행정심판재결례일련번호, 사건명, 결정유형명, 재결일자, 청구유형  
**체인**: 행정심판재결례일련번호 → `get_administrative_trial_detail(trial_id=...)`

### `get_administrative_trial_detail`
**목적**: 행정심판 재결례 상세 조회 (재결 이유 + 관련 법령).  
**파라미터**: `trial_id`(행정심판재결례일련번호)  
**반환**: 사건명, 재결요지, 재결이유, 관련 법령, 청구취지

---

## 6. 행정규칙 도구

각 부처의 행정규칙(훈령·예규·고시 등) 검색·조회.

### `search_administrative_rule`
**목적**: 행정규칙(훈령, 예규, 고시, 지침) 검색.  
**파라미터**: `query`, `search`(1=규칙명, 2=본문, 기본=2), `display`, `page`  
**실제 반환 필드**: 행정규칙ID, 행정규칙명, 발령일자, 시행일자, 소관부처명, 제개정구분명  
**체인**: 행정규칙ID → `get_administrative_rule_detail(rule_id=행정규칙ID)`

### `get_administrative_rule_detail`
**목적**: 행정규칙 전문 조회.  
**파라미터**: `rule_id`(행정규칙ID)  
**반환**: 행정규칙기본정보{행정규칙명, 발령번호, 발령일자, 시행일자, 소관부처명}, 조문 내용

### `search_administrative_rule_comparison`
**목적**: 행정규칙 신구조문 비교 목록 검색 (개정 전후 비교).  
**파라미터**: `query`, `display`, `page`  
**반환**: 행정규칙명, 비교일련번호, 발령일자  
**체인**: 비교일련번호 → `get_administrative_rule_comparison_detail(comparison_id=...)`

### `get_administrative_rule_comparison_detail`
**목적**: 행정규칙 신구조문 비교 본문 조회.  
**파라미터**: `comparison_id`(비교일련번호)  
**실제 반환 구조**: AdmRulOldAndNewService → 신조문_기본정보{행정규칙명, 발령일자, 시행일자}, 구조문_기본정보, 신조문목록[], 구조문목록[]  
**특이사항**: 직전 버그 수정 완료. 신/구 조문 대비 형식으로 출력

### `search_admin_rule_appendix`
**목적**: 행정규칙 별표서식 검색.  
**파라미터**: `query`, `display`, `page`  
**반환**: 별표명, 별표일련번호, 관련 행정규칙명

---

## 7. 자치법규 도구

지방자치단체 조례·규칙 검색·조회.

### `search_local_ordinance`
**목적**: 자치법규(조례·규칙) 검색.  
**파라미터**: `query`, `search`(1=법규명, 2=본문, 기본=2), `display`, `page`  
**실제 반환 필드**: 자치법규일련번호(MST), 자치법규명, 지자체기관명, 공포일자, 시행일자, 제개정구분  
**체인**: 자치법규일련번호 → `get_local_ordinance_detail(ordinance_id=...)` 또는 `get_ordinance_detail(ordinance_id=...)`

### `get_local_ordinance_detail`
**목적**: 자치법규 전문 조회 (lawService.do MST= 파라미터 사용).  
**파라미터**: `ordinance_id`(자치법규일련번호)  
**반환**: 자치법규기본정보{자치법규명, 지자체기관명, 공포일자, 시행일자}, 조문, 부칙

### `get_ordinance_detail`
**목적**: 자치법규 상세 조회 (misc_tools.py 버전, get_local_ordinance_detail과 동일 기능).  
**파라미터**: `ordinance_id`(자치법규일련번호)  
**특이사항**: 수정 이력 — `ID=` → `MST=` 파라미터로 버그 수정 완료

### `search_ordinance_appendix`
**목적**: 자치법규 별표서식 검색.  
**파라미터**: `query`, `display`, `page`  
**반환**: 별표명, 별표일련번호, 관련 자치법규명, 지자체기관명  
**체인**: 별표일련번호 → `get_ordinance_appendix_detail(appendix_id=...)`

### `get_ordinance_appendix_detail`
**목적**: 자치법규 별표서식 상세 조회.  
**파라미터**: `appendix_id`(별표일련번호)  
**반환**: 별표명, 별표종류, 관련 자치법규명, 상세링크, 서식파일링크

### `search_linked_ordinance`
**목적**: 이미 법령ID(knd) 또는 자치법규ID(OID)를 알 때 연계 자치법규 목록 조회.  
**파라미터**: `law_id`(knd, 법령키), `ordinance_id`(OID, 자치법규ID), `display`, `page`  
**반환**: 연계된 자치법규명, 자치법규일련번호, 지자체기관명  
**특이사항**: 법령명만 있을 때는 `search_ordinance_law_link` 사용

### `search_custom_ordinance`
**목적**: 맞춤형 자치법규 검색 (vcode로 특정 지자체 범위 설정).  
**파라미터**: `vcode`(지자체코드, 선택), `query`, `display`, `page`

### `search_custom_ordinance_articles`
**목적**: 맞춤형 자치법규 조문 검색.  
**파라미터**: `vcode`, `query`, `display`, `page`

---

## 8. 조약 도구

국제조약·협정 검색·조회.

### `search_treaty`
**목적**: 한국이 체결한 국제조약·협정 검색.  
**파라미터**: `query`, `display`, `page`  
**실제 반환 필드**: 조약일련번호, 조약명, 조약번호, 서명일자, 발효일자, 조약구분명  
**체인**: 조약일련번호 → `get_treaty_detail(treaty_id=조약일련번호)`

### `get_treaty_detail`
**목적**: 조약 상세 정보 조회.  
**파라미터**: `treaty_id`(조약일련번호)  
**반환**: 조약명, 조약번호, 조약구분명, 서명일자, 발효일자, 관보게재일자, 조약상세링크  
**특이사항**: JSON 직접 상세 API 미지원 → 검색 API로 상세정보 취득 후 링크 제공

---

## 9. 법령해석 도구

법제처 및 각 부처의 법령해석례.

### 법제처

#### `search_legal_interpretation`
**목적**: 법제처 법령해석례 검색.  
**파라미터**: `query`, `display`, `page`  
**실제 반환 필드**: 해석례일련번호, 제목, 회답일자, 질의요지, 의뢰기관명  
**체인**: 해석례일련번호 → `get_legal_interpretation_detail(interpretation_id=...)`

#### `get_legal_interpretation_detail`
**목적**: 법제처 법령해석례 본문 조회.  
**파라미터**: `interpretation_id`(해석례일련번호)  
**반환**: 질의요지, 회답, 이유, 관련 법령 조문

### 부처별 법령해석 (각 38개 = search 19 + detail 19)

패턴: `search_{청약코드}_interpretation(query, display, page)` → 해석례일련번호 반환  
→ `get_{청약코드}_interpretation_detail(interpretation_id)` 로 본문 조회

| 도구 코드 | 기관명 |
|---|---|
| `moef` | 기획재정부 |
| `molit` | 국토교통부 |
| `moel` | 고용노동부 |
| `mof` | 해양수산부 |
| `mohw` | 보건복지부 |
| `moe` | 교육부 |
| `mote` / `motie` | 산업통상자원부 |
| `maf` / `mafra` | 농림축산식품부 |
| `moms` / `mnd` | 국방부 |
| `sme` / `mss` | 중소벤처기업부 |
| `nfa` / `kfs` | 산림청 |
| `nts` | 국세청 |
| `kcs` | 관세청 |
| `mois` | 행정안전부 |
| `me` | 환경부(기후에너지환경부) |
| `mcst` | 문화체육관광부 |
| `moj` | 법무부 |
| `mogef` | 성평등가족부(구 여성가족부) |
| `mofa` | 외교부 |
| `unikorea` | 통일부 |
| `moleg` | 법제처 (별도 expc 타겟) |
| `mfds` | 식품의약품안전처 |
| `mpm` | 인사혁신처 |
| `kma` | 기상청 |
| `cha` | 국가유산청 |
| `rda` | 농촌진흥청 |
| `police` | 경찰청 |
| `dapa` | 방위사업청 |
| `mma` | 병무청 |
| `fire_agency` | 소방청 |
| `pps` | 조달청 |
| `kdca` | 질병관리청 |
| `kcg` | 해양경찰청 |
| `mpva` | 국가보훈부 |
| `kostat` | 국가데이터처 |
| `kipo` | 지식재산처 |
| `naacc` | 행정중심복합도시건설청 |
| `msit` | 과학기술정보통신부 |
| `oka` | 재외동포청 |

**공통 반환 필드**: 해석례일련번호, 제목(또는 질의요지), 회답일자, 소관부처명  
**공통 Detail 반환**: 질의요지, 회답, 이유, 관련 법령

---

## 10. 위원회 결정문 도구

각 행정위원회의 결정문 검색·상세 조회.

패턴: `search_{위원회코드}_committee(query, display, page)` → 결정문번호 반환  
→ `get_{위원회코드}_committee_detail(decision_id)` 로 본문 조회

| 도구 코드 | 기관명 | API target |
|---|---|---|
| `privacy` | 개인정보보호위원회 | `ppc` |
| `financial` | 금융위원회 | `fsc` |
| `monopoly` | 공정거래위원회 | `ftc` |
| `anticorruption` | 국민권익위원회 | `acr` |
| `labor` | 노동위원회 | `nlrc` |
| `environment` | 중앙환경분쟁조정위원회 | `ecc` |
| `securities` | 증권선물위원회 | `sfc` |
| `human_rights` | 국가인권위원회 | `nhrck` |
| `broadcasting` | 방송통신위원회 | `kcc` |
| `industrial_accident` | 산업재해보상보험 재심사위원회 | `iaciac` |
| `land_tribunal` | 중앙토지수용위원회 | `oclt` |
| `employment_insurance` | 고용보험심사위원회 | (별도) |

**공통 반환 필드**: 결정문번호(ID), 사건명(또는 제목), 결정일자(또는 의결일)  
**노동위원회(nlrc) 특이사항**: 반환 필드명이 `제목` (사건명 아님), 사건번호 별도 제공  
**상세 반환**: 결정 요지, 결정 이유, 관련 법령

---

## 11. 특별행정심판 도구

조세·해양·국민권익·인사혁신처 특별행정심판.

### `search_tax_tribunal` / `get_tax_tribunal_detail`
**목적**: 조세심판원 특별행정심판례 검색·상세.  
**반환(search)**: 결정례일련번호, 사건명, 결정일  
**체인**: 결정례일련번호 → `get_tax_tribunal_detail(tribunal_id=...)`

### `search_maritime_safety_tribunal` / `get_maritime_safety_tribunal_detail`
**목적**: 해양안전심판원 특별행정심판례 검색·상세.

### `search_acrc_special_tribunal` / `get_acrc_special_tribunal_detail`
**목적**: 국민권익위원회 특별행정심판 재결례 검색·상세.

### `search_mpm_appeal_tribunal` / `get_mpm_appeal_tribunal_detail`
**목적**: 인사혁신처 소청심사위원회 특별행정심판 재결례 검색·상세.

### `search_bai_preconsulting` / `get_bai_preconsulting_detail`
**목적**: 감사원 사전컨설팅 의견서 검색·상세.  
**파라미터(search)**: `query`, `display`, `page`  
**반환(search)**: 의견서일련번호, 제목, 의결일자  
**체인**: 의견서일련번호 → `get_bai_preconsulting_detail(opinion_id=...)`

---

## 12. 법령용어 도구

법률 전문용어 정의 및 일상용어-법령용어 연계.

### `search_legal_term`
**목적**: 법령용어 검색 (용어명 또는 정의 내 키워드).  
**파라미터**: `query`, `display`, `page`  
**실제 반환 필드**: 용어일련번호, 용어명, 정의, 관련 법령명, 관련 조문  
**체인**: 용어일련번호 → `get_legal_term_detail(term_id=용어일련번호)`

### `search_legal_term_ai`
**목적**: AI 기반 법령용어 검색 (의미 유사도).  
**파라미터**: `query`, `display`, `page`  
**반환**: 용어명, AI 해설, 관련 법령

### `get_legal_term_detail`
**목적**: 법령용어 상세 정의 조회.  
**파라미터**: `term_id`(용어일련번호)  
**반환**: 용어명, 정의, 용례, 관련 조문, 관련 용어

### `search_daily_legal_term_link`
**목적**: 일상용어 → 법령용어 연계 정보 검색 (평이한 표현으로 법률 용어 찾기).  
**파라미터**: `query`(일상 표현), `display`, `page`  
**반환**: 일상용어, 연계 법령용어명, 용어일련번호

### `search_legal_term_article_link`
**목적**: 법령용어 → 관련 조문 연계 검색.  
**파라미터**: `term_id`(용어일련번호), `display`, `page`  
**반환**: 법령명, 조문번호, 용어가 등장하는 조문

### `search_article_legal_term_link`
**목적**: 조문 → 법령용어 연계 검색 (특정 조문에 등장하는 법령용어 목록).  
**파라미터**: `mst`(법령일련번호), `jo`(조문번호), `display`, `page`  
**반환**: 용어명, 용어일련번호, 정의

### `search_daily_term`
**목적**: 일상용어 검색 (법령용어와 대응되는 쉬운 표현 탐색).  
**파라미터**: `query`, `display`, `page`

### `search_legal_daily_term_link`
**목적**: 법령용어 → 일상용어 연계 검색 (법률 용어의 평이한 표현 찾기).  
**파라미터**: `term_id`(용어일련번호), `display`, `page`

---

## 13. 법령비교 도구

개정 전후 법령 조문 비교.

### `search_old_and_new_law`
**목적**: 신구법비교 목록 검색 (개정 전후 비교 가능 법령 목록).  
**파라미터**: `query`, `display`, `page`  
**반환**: 법령명, 법령일련번호, 비교일자  
**체인**: 법령일련번호 → `get_old_and_new_law_detail(law_id=...)`

### `get_old_and_new_law_detail`
**목적**: 신구법비교 본문 조회 (개정 전후 조문 대비).  
**파라미터**: `law_id`(법령일련번호)  
**반환**: 신조문, 구조문, 개정 내용 표시

### `search_three_way_comparison`
**목적**: 3단비교 목록 검색 (법령·시행령·시행규칙 3단 대조 목록).  
**파라미터**: `query`, `display`, `page`  
**반환**: 법령명, 법령일련번호  
**체인**: 법령일련번호 → `get_three_way_comparison_detail(law_id=...)`

### `get_three_way_comparison_detail`
**목적**: 3단비교 본문 조회 (법률·시행령·시행규칙 3단 대조).  
**파라미터**: `law_id`(법령일련번호)  
**반환**: 법률 조문, 시행령 조문, 시행규칙 조문 3단 대조

### `search_one_view`
**목적**: 한눈보기 목록 검색 (법령의 체계를 한눈에 볼 수 있는 뷰 목록).  
**파라미터**: `query`, `display`, `page`  
**체인**: 법령일련번호 → `get_one_view_detail(law_id=...)`

### `get_one_view_detail`
**목적**: 한눈보기 본문 조회.  
**파라미터**: `law_id`(법령일련번호)  
**반환**: 법령 조문을 계층 구조로 시각화한 정보

### `compare_law_versions`
**목적**: 법령의 이전 버전과 현재 버전 자동 비교 (현행 vs. 직전 개정).  
**파라미터**: `law_name`(법령명)  
**반환**: 변경된 조문 목록, 신설/개정/삭제 현황

---

## 14. 별표서식 도구

법령·행정규칙·자치법규에 첨부된 별표·서식.

### `search_law_appendix`
**목적**: 법령(시행령·시행규칙 포함) 별표서식 검색.  
**파라미터**: `query`, `law_name`(법령명 필터), `display`, `page`  
**실제 반환 필드**: 별표일련번호, 별표명, 별표종류, 관련 법령명, 서식파일링크  
**체인**: 별표일련번호 → `get_law_appendix_detail(appendix_id=별표일련번호)`

### `get_law_appendix_detail`
**목적**: 법령 별표서식 상세 정보 조회.  
**파라미터**: `appendix_id`(별표일련번호)  
**반환**: 별표명, 별표종류, 관련 법령명, 서식파일링크, 별표 상세링크

---

## 15. 법령연혁 도구

법령의 제정·개정 이력.

### `search_law_amendment_history`
**목적**: 법령 개정 이력 검색 (특정 법령의 제정·개정 연혁 목록).  
**파라미터**: `query`(법령명), `display`, `page`  
**실제 반환 필드**: 법령일련번호, 법령명, 개정일자, 공포번호, 제개정구분명  
**체인**: 법령일련번호 → `get_law_amendment_history_detail(law_id=...)`

### `get_law_amendment_history_detail`
**목적**: 특정 개정 시점의 법령 전문 조회.  
**파라미터**: `law_id`(법령일련번호) 또는 `mst`  
**반환**: 해당 시점의 법령 전문 (과거 버전)

### `search_article_change_history`
**목적**: 특정 조문의 상세 변경 이력 조회 (정책적 배경 포함).  
**파라미터**: `mst`(법령일련번호), `article_no`(조문번호, 예: "제15조"), `display`, `page`  
**반환**: 개정일자, 개정 전 조문, 개정 후 조문, 개정 이유

### `search_law_change_history`
**목적**: 특정 날짜 기준 법령 변경이력 검색 (당일 개정된 법령 목록).  
**파라미터**: `change_date`(날짜 YYYYMMDD, 필수), `org`(소관부처), `display`, `page`  
**반환**: 법령명, 공포일자, 제개정구분명  
**특이사항**: 대용량 API — 응답 시간이 오래 걸릴 수 있음

---

## 16. 연계정보 도구

법령·자치법규·관련법령 간 연계 관계.

### `search_related_law`
**목적**: 관련법령 검색 (위임·수권·부속관계 등 법령 간 관계 조회).  
**파라미터**: `query`(법령명), `display`, `page`  
**실제 반환 필드**: 법령명, 법령일련번호, 관계유형(1~4유형 + 번역 표시), 관련 법령명  
**관계유형 코드**: 1유형=수권관계(상위→하위), 2유형=특별법관계, 3유형=부속법령관계, 4유형=위임관계

### `search_ordinance_law_link`
**목적**: 자치법규와 연계된 법령 목록 검색 (법령명으로 연계 조례 탐색).  
**파라미터**: `query`(법령명), `display`, `page`  
**반환**: 법령명, 자치법규명, 자치법규일련번호, 지자체기관명

### `search_law_ordinance_status`
**목적**: 특정 법령에 연계된 자치법규 현황 조회.  
**파라미터**: `query`(법령명), `display`, `page`  
**반환**: 법령명, 연계 자치법규 수, 자치법규 목록

### `get_delegated_law`
**목적**: 법령의 위임 사항 조회 (상위 법령 → 하위 법령 위임 관계).  
**파라미터**: `mst`(법령일련번호)  
**특이사항**: lsDelegated API 항상 빈 응답 → 대안으로 `search_related_law` 사용 안내

### `search_law_system_diagram`
**목적**: 법령 체계도 검색 (상위·하위 법령 계층 관계 다이어그램).  
**파라미터**: `query`, `display`, `page`  
**반환**: 법령명, 법령일련번호, 상위법령명  
**체인**: 법령일련번호 → `get_law_system_diagram_detail(mst_id=...)`

### `get_law_system_diagram_detail`
**목적**: 법령 체계도 요약 정보 조회 (대용량으로 요약본 제공).  
**파라미터**: `mst_id`(법령일련번호)  
**반환**: 법령명, 상위법령명, 하위법령 목록, 계층 관계 구조  
**특이사항**: 전체 체계도 데이터는 대용량 — 요약 정보만 제공

---

## 17. 지능형 검색 도구

AI 기반 법령·관련법령 검색.

### `search_intelligent_law`
**목적**: AI/NLP 기반 지능형 법령 검색 (의미 유사도 + 연관 법령 추천).  
**파라미터**: `query`, `display`, `page`  
**실제 반환 필드**: 법령일련번호, 법령명, 시행일자(YYYY-MM-DD 형식으로 포맷), 소관부처명  
**특이사항**: aiSearch API 사용. 공포일자 포맷 수정 완료 (버그 수정됨)

### `search_intelligent_related_law`
**목적**: AI 기반 관련법령 조문 검색 (특정 키워드와 관련된 법령 조문 추천).  
**파라미터**: `query`, `display`, `page`  
**실제 반환 필드**: 법령명, 조문번호, 조문내용  
**실제 API 구조**: `aiRltLsSearch.법령조문[]` → 법령조문번호, 법령조문명, 법령명, 시행일자  
**특이사항**: aiRltLsSearch 루트키 수정 완료 (버그 수정됨). 이전에는 원시 dict를 title로 출력하는 버그 있었음

---

## 18. BM25 재랭킹 도구

BM25 알고리즘 기반 검색 품질 개선.

### `search_law_bm25`
**목적**: 법령 BM25 재랭킹 검색 (관련도 높은 결과 우선 정렬).  
**파라미터**: `query`, `top_k`(반환 수, 기본=10), `display`(API 후보 수)  
**특이사항**: 내부적으로 search_law_unified 후 BM25로 재정렬

### `search_precedent_bm25`
**목적**: 판례 BM25 재랭킹 검색.  
**파라미터**: `query`, `top_k`, `display`

### `search_legal_term_bm25`
**목적**: 법령용어 BM25 재랭킹 검색.  
**파라미터**: `query`, `top_k`, `display`

### `search_committee_bm25`
**목적**: 위원회 결정문 BM25 재랭킹 검색 (다수 위원회 통합 검색).  
**파라미터**: `query`, `committee`(위원회 코드, 선택), `top_k`, `display`  
**특이사항**: nlrc(노동위원회)는 `제목` 필드 사용으로 수정 완료 (버그 수정됨)

### `search_admin_rule_bm25`
**목적**: 행정규칙 BM25 재랭킹 검색.  
**파라미터**: `query`, `top_k`, `display`

### `search_interpretation_bm25`
**목적**: 법령해석례 BM25 재랭킹 검색 (다수 부처 통합 검색).  
**파라미터**: `query`, `ministry`(부처 코드, 선택), `top_k`, `display`

### `search_all_bm25`
**목적**: 전체 법제처 DB 통합 BM25 재랭킹 검색 (법령·판례·해석례·행정규칙 통합).  
**파라미터**: `query`, `targets`(대상 목록, 선택), `top_k`, `display`

### `explain_bm25_tokenize`
**목적**: BM25 토큰화 결과 설명 (검색어가 어떻게 분석되는지 디버깅).  
**파라미터**: `query`  
**반환**: 토큰 목록, BM25 점수 계산 설명

---

## 19. 맞춤형 도구

vcode(기관코드)로 범위를 제한한 맞춤형 검색.

### `search_custom_law`
**목적**: 맞춤형 법령 검색 (특정 vcode 기관 범위로 제한).  
**파라미터**: `vcode`(기관코드, 선택), `query`, `display`, `page`

### `search_custom_law_articles`
**목적**: 맞춤형 법령 조문 검색.  
**파라미터**: `vcode`, `query`, `display`, `page`

### `search_custom_administrative_rule`
**목적**: 맞춤형 행정규칙 검색.  
**파라미터**: `vcode`, `query`, `display`, `page`

### `search_custom_administrative_rule_articles`
**목적**: 맞춤형 행정규칙 조문 목록 조회.  
**파라미터**: `vcode`, `query`, `display`, `page`

---

## 20. 지식베이스 · 상담 도구

법제처 FAQ, 질의응답, 상담 사례.

### `search_knowledge_base`
**목적**: 법령 관련 지식베이스 검색 (법제처 지식 DB).  
**파라미터**: `query`, `display`, `page`

### `search_faq`
**목적**: 자주 묻는 질문(FAQ) 검색.  
**파라미터**: `query`, `display`, `page`

### `search_qna`
**목적**: 질의응답(QNA) 검색.  
**파라미터**: `query`, `display`, `page`

### `search_counsel`
**목적**: 상담 사례 검색 (법률 상담 Q&A).  
**파라미터**: `query`, `display`, `page`

### `search_precedent_counsel`
**목적**: 판례 상담 검색 (판례 기반 법률 상담).  
**파라미터**: `query`, `display`, `page`

### `search_civil_petition`
**목적**: 민원 사례 검색.  
**파라미터**: `query`, `display`, `page`

### `search_all_legal_documents`
**목적**: 법령·판례·해석례·행정규칙·자치법규 등 전체 통합 검색.  
**파라미터**: `query`, `targets`(대상 유형 목록), `display`, `page`

---

## 21. 도메인 특화 법령 검색

특정 법률 도메인에 최적화된 통합 검색.

### `search_financial_laws`
**목적**: 금융·은행·자본시장 관련 법령 검색.  
**반환**: 법령명, MST, 소관부처(금융위원회, 기획재정부 등)

### `search_tax_laws`
**목적**: 조세·세무 관련 법령 검색.  
**반환**: 법령명, MST, 소관부처(국세청, 기획재정부 등)

### `search_privacy_laws`
**목적**: 개인정보·데이터보호 관련 법령 검색.  
**반환**: 법령명, MST, 소관부처(개인정보보호위원회 등)

---

## 22. 캐시 · 유틸리티 도구

캐시 관리 및 기타 유틸리티.

### `get_cache_status`
**목적**: 현재 캐시 상태 확인 (캐시된 항목 수, 크기, 마지막 업데이트).  
**파라미터**: 없음  
**반환**: 캐시 디렉토리 경로, 캐시 파일 수, 총 캐시 크기

### `cleanup_cache_tool`
**목적**: 만료된 캐시 파일 정리 (7일 이상 된 캐시 삭제).  
**파라미터**: `force`(강제 전체 삭제 여부, 기본=False)

### `invalidate_law_cache`
**목적**: 특정 법령의 캐시 무효화 (법령 개정 후 최신 데이터 조회용).  
**파라미터**: `law_name`(법령명) 또는 `mst`(법령일련번호)

---

## 다중 도구 연계 패턴

### 패턴 1: 법령 전문 조회 체인
```
query → search_law_unified(query, target="law")
     → [법령일련번호(MST)] → get_law_detail(mst)
     → [조문번호] → get_law_article_by_key(mst, article_key="제15조")
```

### 패턴 2: 법령 + 관련 하위 법령 체인
```
query → search_law_unified(query)
     → [MST, 법령명] → search_related_law(query=법령명)
                      → [하위법령 MST] → get_law_detail(mst)
     → [MST] → search_law_system_diagram(query=법령명)
             → get_law_system_diagram_detail(mst_id)
```

### 패턴 3: 법령 + 연계 자치법규 체인
```
query → search_law_unified(query)
     → [법령명] → search_ordinance_law_link(query=법령명)
                → [자치법규일련번호] → get_local_ordinance_detail(ordinance_id)
```

### 패턴 4: 판례 + 관련 법령 연계
```
query → search_precedent(query)
     → [판례일련번호] → get_precedent_detail(case_id)
     → [참조조문의 법령명] → search_law_unified(query=법령명)
                           → get_law_article_by_key(mst, article_key=참조조문)
```

### 패턴 5: 법령해석 + 법령 원문 체인
```
query → search_legal_interpretation(query) (또는 부처별 interpretation)
     → [해석례일련번호] → get_legal_interpretation_detail(interpretation_id)
     → [관련법령명] → search_law_unified(query=법령명)
                    → get_law_article_by_key(mst, article_key=관련조문)
```

### 패턴 6: 법령 개정 이력 분석
```
query → search_law_amendment_history(query=법령명)
     → [법령일련번호 목록] → get_law_amendment_history_detail(law_id) [각 버전]
     → search_old_and_new_law(query=법령명)
     → [법령일련번호] → get_old_and_new_law_detail(law_id)
```

### 패턴 7: 법령 조문 + 용어 풀이
```
mst → get_law_article_by_key(mst, article_key)
    → [조문 내 전문용어] → search_article_legal_term_link(mst, jo=조문번호)
                         → [용어일련번호] → get_legal_term_detail(term_id)
```

### 패턴 8: 행정규칙 개정 전후 비교
```
query → search_administrative_rule(query)
     → [행정규칙ID] → get_administrative_rule_detail(rule_id)
     → search_administrative_rule_comparison(query)
     → [비교일련번호] → get_administrative_rule_comparison_detail(comparison_id)
```

### 패턴 9: 위원회 결정 + 관련 법령 체인
```
query → search_{committee}_committee(query)
     → [결정문번호] → get_{committee}_committee_detail(decision_id)
     → [관련법령명] → search_law_unified(query=법령명)
                    → get_law_detail(mst)
```

### 패턴 10: BM25 정밀 검색 → 상세 조회
```
query → search_all_bm25(query)         # 전체 통합 BM25 재랭킹
     → [상위 결과 type 확인]
     → (type=law) → get_law_detail(mst)
     → (type=prec) → get_precedent_detail(case_id)
     → (type=expc) → get_legal_interpretation_detail(interpretation_id)
     → (type=admrul) → get_administrative_rule_detail(rule_id)
```

### 패턴 11: 법령용어 → 일상용어 → 법령 조문 체인
```
일상표현 → search_daily_legal_term_link(query=일상표현)
         → [용어일련번호] → get_legal_term_detail(term_id)
                          → [관련 법령명, 조문번호] → get_law_article_by_key(mst, article_key)
```

---

*생성일: 2026-04-23 | 도구 수: 213개 | 기반: 실제 API 응답 구조 분석*
