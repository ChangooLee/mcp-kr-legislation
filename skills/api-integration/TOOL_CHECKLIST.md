# MCP 도구 구현 현황 (api_layout 기준)

> 마지막 업데이트: 2026-01-23

---

## ⚠️ 중요 원칙

**이 문서는 진행 상황 추적용입니다. API의 근거가 아닙니다.**

### 데이터 기준점 (Source of Truth)

| 항목 | 경로 | 역할 |
|------|------|------|
| **API 레이아웃** | `src/mcp_kr_legislation/utils/api_layout/*.json` | API 정의의 유일한 기준점 |
| **공식 가이드** | https://open.law.go.kr/LSO/openApi/guideList.do | API 레이아웃의 원본 소스 |
| **TOOL_CHECKLIST.md** | 이 파일 | 구현 진행 추적 (업데이트만, 근거 아님) |

### 워크플로우

```
공식 가이드 → api_crawler.py → api_layout/*.json → 도구 개발 → TOOL_CHECKLIST.md 업데이트
              (크롤링)           (기준점)          (구현)        (추적)
```

**도구 개발 시 항상 `api_layout/*.json` 파일을 참조하세요.**

---

> api_layout 기준: 16개 구분, 173개 API

## 구현 현황 요약

| 구분 | API 수 | 구현 | 구현율 | 도구 파일 |
|------|--------|------|--------|----------|
| 법령 | 26 | 26 | 100% | law_tools.py, optimized_law_tools.py |
| 중앙부처 1차 해석 | 76 | 76 | 100% | ministry_interpretation_tools*.py |
| 위원회 결정문 | 24 | 24 | 100% | committee_tools.py |
| 법령정보 지식베이스 | 9 | 9 | 100% | legal_term_tools.py, additional_service_tools.py |
| 특별행정심판 | 8 | 8 | 100% | specialized_tools.py |
| 맞춤형 | 6 | 6 | 100% | custom_tools.py |
| 행정규칙 | 4 | 4 | 100% | administrative_rule_tools.py |
| 자치법규 | 3 | 3 | 100% | legislation_tools.py |
| 별표ㆍ서식 | 3 | 3 | 100% | law_tools.py |
| 판례 | 2 | 2 | 100% | precedent_tools.py |
| 헌재결정례 | 2 | 2 | 100% | precedent_tools.py |
| 법령해석례 | 2 | 2 | 100% | precedent_tools.py |
| 행정심판례 | 2 | 2 | 100% | precedent_tools.py |
| 조약 | 2 | 2 | 100% | specialized_tools.py |
| 학칙ㆍ공단ㆍ공공기관 | 2 | 2 | 100% | specialized_tools.py |
| 법령용어 | 2 | 2 | 100% | legal_term_tools.py |
| **총계** | **173** | **173** | **100%** | |

---

## 도구 개발 원칙

**`api_layout/*.json`의 `sample_urls` 필드가 개발 필요 여부를 결정합니다.**

| sample_urls 상태 | 개발 방식 |
|------------------|-----------|
| JSON 포함 | ✅ JSON API 직접 호출하여 도구 개발 |
| HTML만 | ❌ **도구 개발 불필요** (JSON 미지원) |

> **원칙**: `sample_urls`에 JSON URL이 없으면 해당 API는 도구 개발 대상이 아닙니다.

---

## 상태 범례

- ✅ 완료: sample_urls에 JSON 있음 → JSON API 호출 도구
- ⚠️ 경고: 특수 파라미터 필요 또는 0건 반환
- 📄 HTML: sample_urls에 HTML만 있음 → **도구 개발 불필요**
- ❌ 미구현: JSON 지원이지만 도구 없음

---

## 1. 법령 - 26개 API

**평가일**: 2026-01-23 | **도구 파일**: `law_tools.py` (39개), `optimized_law_tools.py` (7개)

### 평가 결과

- **전수 테스트**: 46개 도구 전체 재테스트 완료 (2026-01-23)
- **API 테스트**: 핵심 API 정상 동작 확인
- **품질**: 응답 포맷팅 ✅, 에러 처리 ✅, 빈 결과 처리 ✅, 정확 매치 정렬 ✅
- **캐시**: ~/.cache/mcp-kr-legislation (7일 유효)
- **HTML 전용**: drlaw, lsHstInf, lsJoHstInf, lnkLs, oneview - JSON 미지원으로 도구 개발 불필요

### 전체 테스트 결과 (2026-01-23, 46개 전수 테스트)

| 결과 | 도구 수 | 비율 |
|------|--------|------|
| 성공 | 43개 | 93.5% |
| 경고 | 2개 | 4.3% |
| 실패 | 1개 | 2.2% |

**문제 도구 상세**:

| 도구 | 상태 | 원인 |
|------|------|------|
| get_law_appendix_detail | 실패 | JSON 미지원 API (HTML만 반환) |
| get_three_way_comparison_detail | 경고 | 특정 ID에서만 동작 |
| get_current_law_articles | 경고 | lawjosub API 파라미터 제한 |

### 개선 완료 (2026-01-22)

| 도구 | 문제 | 수정 내용 |
|------|------|----------|
| search_law | 정확 매치 결과가 뒤로 밀림 | 정확 매치 우선 정렬 추가 |
| search_english_law | HTML 태그(`<strong>`) 포함 | HTML 태그 제거 필터 추가 |
| get_law_article_by_key | 항/호/목 번호 중복 출력 | 중복 번호 제거 로직 수정 |

### 개선 완료 (2026-01-23)

| 도구 | 문제 | 수정 내용 |
|------|------|----------|
| search_law_with_cache | "상호저축은행법" 우선 반환 | 정확 매치 우선 정렬, display=10으로 확대 |
| get_law_articles_summary | 법령명 불일치 ("유통단지개발촉진법") | 하드코딩 제거, API 검색 + 정확 매치 |
| search_law_system_diagram | MST 누락 | LsStmdSearch 루트 키 지원 추가 |
| search_old_and_new_law | 잘못된 law_id="1" | 신구법일련번호 사용으로 변경 |
| search_deleted_law_data | 제목 "법령"만 표시 | "삭제된 {구분명} (일련번호: XXX)" 형식 |
| search_law_nickname | 약칭명 미표시 | 법령약칭명 필드 추가, break 버그 수정 |
| get_delegated_law | MST 누락 | 실제 API 키 (법령일련번호, 법령ID) 사용 |
| compare_article_before_after | 조문 제목만 추출 | 항 데이터에서 항내용 추출 로직 추가 |
| get_law_article_detail | 이전/이후 조문 "제000000조" 표시 | 무의미한 값 필터링 추가 |
| get_law_summary | 조문 인덱스 중복 ("제1조: 제1조(목적)") | 조문번호/내용 중복 제거 로직 개선 |

### API target 오류 수정 (2026-01-23)

> 잘못된 API target으로 인해 데이터가 반환되지 않던 도구들 수정

| 도구 | 문제 | 수정 내용 |
|------|------|----------|
| search_deleted_history | 잘못된 target (datDelHstGuide) | delHst로 수정 ✅ |
| search_one_view | 잘못된 target (oneViewListGuide) | oneview로 수정 ✅ |
| search_ordinance_law_link | 잘못된 target (ordinLsConListGuide) | lnkLs로 수정 ✅ |
| search_three_way_comparison | params에 불필요한 target | params 정리 ✅ |
| search_law_appendix | params에 불필요한 target | params 정리 ✅ |

### 품질 개선 (2026-01-23)

| 항목 | 내용 |
|------|------|
| 이모지 제거 | law_tools.py, optimized_law_tools.py에서 불필요한 이모지 제거 완료 |
| search_related_law | query 필수, 타임아웃 60초, 캐시 지원으로 개선 |

### Description 개선 (2026-01-23)

> LLM이 문장 형태로 query를 입력하는 문제 해결을 위해 사용법 가이드 추가

| 도구 | 개선 내용 |
|------|----------|
| search_law | "[중요] query 입력 가이드" 추가, 문장 금지 명시 |
| get_law_detail | mst 입력 가이드 추가, 숫자만 입력 명시 |
| get_law_article_by_key | article_key 형식 가이드, "제15조" 형식만 허용 |
| search_related_law | 법령명만 입력 가이드 추가 |
| search_english_law | 영문 키워드만 입력 가이드 추가 |

### API 제한 사항

| 도구 | 상태 | 비고 |
|------|------|------|
| lawjosub (get_current_law_articles) | ⚠️ | API 파라미터 제한 - 일부 MST에서 동작 안함 |

### API-도구 매핑

| API 제목 | target | 도구명 | 상태 | 비고 |
|---------|--------|-------|------|------|
| 현행법령(공포일) 목록 조회 | law | search_law | ✅ | 핵심, 테스트 완료 |
| 현행법령(공포일) 본문 조회 | law | get_law_detail | ✅ | 테스트 완료, 캐시 적용 |
| 현행법령(시행일) 목록 조회 | eflaw | search_effective_law | ✅ | 테스트 완료 |
| 현행법령(시행일) 본문 조회 | eflaw | get_effective_law_detail | ✅ | 테스트 완료, 캐시 적용 |
| 법령 연혁 목록 조회 | lsHistory | search_law_change_history | 📄 | HTML 전용 |
| 법령 연혁 본문 조회 | lsHistory | - | 📄 | HTML 전용 |
| 현행법령(공포일) 본문 조항호목 조회 | lawjosub | get_current_law_articles | ⚠️ | API 파라미터 제한 |
| 현행법령(시행일) 본문 조항호목 조회 | eflawjosub | get_effective_law_articles | ✅ | |
| 영문 법령 목록 조회 | elaw | search_english_law | ✅ | 테스트 완료 |
| 영문 법령 본문 조회 | elaw | get_english_law_detail | ✅ | |
| 법령 변경이력 목록 조회 | lsHstInf | search_law_change_history | 📄 | HTML 전용 |
| 일자별 조문 개정 이력 목록 조회 | lsJoHstInf | search_daily_article_revision | 📄 | HTML 전용 |
| 조문별 변경 이력 목록 조회 | lsJoHstInf | search_article_change_history | 📄 | HTML 전용 |
| 법령 기준 자치법규 연계 관련 목록 조회 | lnkLs | search_law_ordinance_link | 📄 | HTML 전용 |
| 법령-자치법규 연계현황 조회 | drlaw | - | 📄 | HTML 전용, 도구 개발 불필요 |
| 위임법령 조회 | lsDelegated | get_delegated_law | ✅ | lawService.do+ID 필수 |
| 법령 체계도 목록 조회 | lsStmd | search_law_system_diagram | 📄 | HTML 전용 |
| 법령 체계도 본문 조회 | lsStmd | get_law_system_diagram_detail | ✅ | 캐시 적용 |
| 신구법 목록 조회 | oldAndNew | search_old_and_new_law | ⚠️ | ID 필요 |
| 신구법 본문 조회 | oldAndNew | get_old_and_new_law_detail | ⚠️ | ID 필요 |
| 3단 비교 목록 조회 | thdCmp | search_three_way_comparison | ⚠️ | ID 필요 |
| 3단 비교 본문 조회 | thdCmp | get_three_way_comparison_detail | ⚠️ | ID 필요 |
| 법률명 약칭 조회 | lsAbrv | search_law_nickname | ⚠️ | 특수 파라미터 |
| 삭제 데이터 목록 조회 | delHst | search_deleted_law_data | ⚠️ | 특수 파라미터 |
| 한눈보기 목록 조회 | oneview | search_one_view | 📄 | HTML 전용 |
| 한눈보기 본문 조회 | oneview | get_one_view_detail | 📄 | HTML 전용 |

### 추가 도구 (law_tools.py)

- `search_law_unified`: 통합 검색 (키워드 매핑)
- `get_law_article_by_key`: 특정 조문 조회
- `compare_law_versions`: 법령 버전 비교
- `search_financial_laws`, `search_tax_laws`, `search_privacy_laws`: 분야별 검색

---

## 2. 중앙부처 1차 해석 - 76개 API

**도구 파일**: `ministry_interpretation_tools.py`, `ministry_interpretation_tools_extended.py`

### 목록 조회 도구 (38개)

| 부처 | target | 도구명 | 상태 | 데이터 건수 |
|------|--------|-------|------|-----------|
| 고용노동부 | moelCgmExpc | search_moel_interpretation | ✅ | 9,573 |
| 국토교통부 | molitCgmExpc | search_molit_interpretation | ✅ | 5,660 |
| 기획재정부 | moefCgmExpc | search_moef_interpretation | ✅ | 2,297 |
| 해양수산부 | mofCgmExpc | search_mof_interpretation | ✅ | 547 |
| 행정안전부 | moisCgmExpc | search_mois_interpretation | ✅ | 4,039 |
| 기후에너지환경부 | meCgmExpc | search_me_interpretation | ✅ | 2,291 |
| 관세청 | kcsCgmExpc | search_kcs_interpretation | ✅ | 1,279 |
| 국세청 | ntsCgmExpc | search_nts_interpretation | ✅ | 135,765 |
| 교육부 | moeCgmExpc | search_moe_interpretation | ✅ | 40+ |
| 국가보훈부 | mpvaCgmExpc | search_mpva_interpretation | ✅ | 116 |
| 국방부 | mndCgmExpc | search_moms_interpretation | ✅ | 40 |
| 농림축산식품부 | mafraCgmExpc | search_maf_interpretation | ✅ | 32 |
| 문화체육관광부 | mcstCgmExpc | search_mcst_interpretation | ✅ | 44 |
| 법무부 | mojCgmExpc | search_moj_interpretation | ✅ | 1+ |
| 보건복지부 | mohwCgmExpc | search_mohw_interpretation | ✅ | 142+ |
| 산업통상부 | motieCgmExpc | search_mote_interpretation | ✅ | 32 |
| 성평등가족부 | mogefCgmExpc | search_mogef_interpretation | ✅ | 4+ |
| 외교부 | mofaCgmExpc | search_mofa_interpretation | ✅ | 17 |
| 중소벤처기업부 | mssCgmExpc | search_sme_interpretation | ✅ | 4 |
| 통일부 | mouCgmExpc | search_unikorea_interpretation | ✅ | 6 |
| 법제처 | molegCgmExpc | search_moleg_interpretation | ✅ | 17 |
| 식품의약품안전처 | mfdsCgmExpc | search_mfds_interpretation | ✅ | 1,216 |
| 인사혁신처 | mpmCgmExpc | search_mpm_interpretation | ✅ | 10 |
| 기상청 | kmaCgmExpc | search_kma_interpretation | ✅ | 21 |
| 국가유산청 | khsCgmExpc | search_cha_interpretation | ⚠️ | 0건 |
| 농촌진흥청 | rdaCgmExpc | search_rda_interpretation | ✅ | 6 |
| 경찰청 | npaCgmExpc | search_police_interpretation | ⚠️ | 0건 |
| 방위사업청 | dapaCgmExpc | search_dapa_interpretation | ✅ | 46 |
| 병무청 | mmaCgmExpc | search_mma_interpretation | ✅ | 1+ |
| 산림청 | kfsCgmExpc | search_nfa_interpretation | ✅ | 623 |
| 소방청 | nfaCgmExpc | search_fire_agency_interpretation | ✅ | 328 |
| 재외동포청 | okaCgmExpc | search_oka_interpretation | ✅ | - |
| 조달청 | ppsCgmExpc | search_pps_interpretation | ✅ | 23 |
| 질병관리청 | kdcaCgmExpc | search_kdca_interpretation | ⚠️ | 0건 |
| 국가데이터처 | kostatCgmExpc | search_kostat_interpretation | ✅ | 4 |
| 지식재산처 | kipoCgmExpc | search_kipo_interpretation | ✅ | 186 |
| 해양경찰청 | kcgCgmExpc | search_kcg_interpretation | ⚠️ | 0건 |
| 과학기술정보통신부 | msitCgmExpc | search_msit_interpretation | ✅ | - |
| 행정중심복합도시건설청 | naaccCgmExpc | search_naacc_interpretation | ✅ | 37 |

### 본문 조회 도구 (38개)

각 목록 조회 도구에 대응하는 `get_*_interpretation_detail` 도구가 존재

---

## 3. 위원회 결정문 - 24개 API

**도구 파일**: `committee_tools.py`

| 위원회 | target | 목록 도구 | 상세 도구 | 상태 |
|-------|--------|----------|----------|------|
| 개인정보보호위원회 | ppc | search_privacy_committee | get_privacy_committee_detail | ✅ |
| 고용보험심사위원회 | eiac | search_employment_insurance_committee | get_employment_insurance_committee_detail | ✅ |
| 공정거래위원회 | ftc | search_monopoly_committee | get_monopoly_committee_detail | ✅ |
| 국민권익위원회 | acr | search_anticorruption_committee | get_anticorruption_committee_detail | ✅ |
| 금융위원회 | fsc | search_financial_committee | get_financial_committee_detail | ✅ |
| 노동위원회 | nlrc | search_labor_committee | get_labor_committee_detail | ✅ |
| 방송통신위원회 | kcc | search_broadcasting_committee | get_broadcasting_committee_detail | ✅ |
| 산업재해보상보험재심사위원회 | iaciac | search_industrial_accident_committee | get_industrial_accident_committee_detail | ✅ |
| 중앙토지수용위원회 | oclt | search_land_tribunal | get_land_tribunal_detail | ✅ |
| 중앙환경분쟁조정위원회 | ecc | search_environment_committee | get_environment_committee_detail | ✅ |
| 증권선물위원회 | sfc | search_securities_committee | get_securities_committee_detail | ✅ |
| 국가인권위원회 | nhrck | search_human_rights_committee | get_human_rights_committee_detail | ✅ |

---

## 4. 법령정보 지식베이스 - 9개 API

**도구 파일**: `legal_term_tools.py`, `additional_service_tools.py`

| API 제목 | target | 도구명 | 상태 | 비고 |
|---------|--------|-------|------|------|
| 법령용어 조회 | lstrmAI | search_legal_term_ai | ⚠️ | 데이터 없음 |
| 일상용어 조회 | dlytrm | search_daily_term | 📄 | HTML 전용 |
| 법령용어-일상용어 연계 조회 | lstrmRlt | search_legal_daily_term_link | 📄 | HTML 전용 |
| 일상용어-법령용어 연계 조회 | dlytrmRlt | search_daily_legal_term_link | 📄 | HTML 전용 |
| 법령용어-조문 연계 조회 | lstrmRltJo | search_legal_term_article_link | 📄 | ID 필요 |
| 조문-법령용어 연계 조회 | joRltLstrm | search_article_legal_term_link | 📄 | ID 필요 |
| 관련법령 조회 | lsRlt | search_related_law | ✅ | query 필수, 캐시 지원 |
| 지능형 법령검색 시스템 검색 API | aiSearch | search_legal_ai | ✅ | AI 통합 |
| 지능형 법령검색 시스템 연관법령 API | aiRltLs | - | ⚠️ | 별도 도구 필요 |

---

## 5. 특별행정심판 - 8개 API

**도구 파일**: `specialized_tools.py`

| 기관 | target | 목록 도구 | 상세 도구 | 상태 |
|-----|--------|----------|----------|------|
| 조세심판원 | ttSpecialDecc | search_tax_tribunal | get_tax_tribunal_detail | ✅ |
| 해양안전심판원 | kmstSpecialDecc | search_maritime_safety_tribunal | get_maritime_safety_tribunal_detail | ✅ |
| 국민권익위원회 | acrSpecialDecc | search_acrc_special_tribunal | get_acrc_special_tribunal_detail | ✅ |
| 인사혁신처 소청심사위원회 | adapSpecialDecc | search_mpm_appeal_tribunal | get_mpm_appeal_tribunal_detail | ✅ |

---

## 6. 맞춤형 - 6개 API

**도구 파일**: `custom_tools.py`

| API 제목 | target | 도구명 | 상태 | 비고 |
|---------|--------|-------|------|------|
| 맞춤형 법령 목록 조회 | couseLs | search_custom_law | ✅ | vcode 필수 |
| 맞춤형 법령 조문 목록 조회 | couseLs | search_custom_law_articles | ✅ | vcode 필수 |
| 맞춤형 행정규칙 목록 조회 | couseAdmrul | search_custom_administrative_rule | ✅ | vcode 필수 |
| 맞춤형 행정규칙 조문 목록 조회 | couseAdmrul | - | ⚠️ | 별도 도구 필요 |
| 맞춤형 자치법규 목록 조회 | couseOrdin | search_custom_ordinance | ✅ | vcode 필수 |
| 맞춤형 자치법규 조문 목록 조회 | couseOrdin | search_custom_ordinance_articles | ✅ | vcode 필수 |

---

## 7. 행정규칙 - 4개 API

**도구 파일**: `administrative_rule_tools.py`

| API 제목 | target | 도구명 | 상태 |
|---------|--------|-------|------|
| 행정규칙 목록 조회 | admrul | search_administrative_rule | ✅ |
| 행정규칙 본문 조회 | admrul | get_administrative_rule_detail | ✅ |
| 행정규칙 신구법 비교 목록 조회 | admrulOldAndNew | search_administrative_rule_comparison | ⚠️ |
| 행정규칙 신구법 비교 본문 조회 | admrulOldAndNew | get_administrative_rule_comparison_detail | ⚠️ |

---

## 8. 자치법규 - 3개 API

**도구 파일**: `legislation_tools.py`

| API 제목 | target | 도구명 | 상태 |
|---------|--------|-------|------|
| 자치법규 목록 조회 | ordin | search_local_ordinance | ✅ |
| 자치법규 본문 조회 | ordin | get_local_ordinance_detail | ✅ |
| 자치법규 기준 법령 연계 관련 목록 조회 | lnkOrd | search_linked_ordinance | ⚠️ |

---

## 9. 별표ㆍ서식 - 3개 API

**도구 파일**: `law_tools.py`

| API 제목 | target | 도구명 | 상태 |
|---------|--------|-------|------|
| 법령 별표ㆍ서식 목록 조회 | licbyl | search_law_appendix | ✅ |
| 행정규칙 별표ㆍ서식 목록 조회 | admbyl | search_administrative_rule_appendix | ✅ |
| 자치법규 별표ㆍ서식 목록 조회 | ordinbyl | search_ordinance_appendix | ⚠️ |

---

## 10. 판례 - 2개 API

**도구 파일**: `precedent_tools.py`

| API 제목 | target | 도구명 | 상태 |
|---------|--------|-------|------|
| 판례 목록 조회 | prec | search_precedent | ✅ |
| 판례 본문 조회 | prec | get_precedent_detail | ✅ |

---

## 11. 헌재결정례 - 2개 API

**도구 파일**: `precedent_tools.py`

| API 제목 | target | 도구명 | 상태 |
|---------|--------|-------|------|
| 헌재결정례 목록 조회 | detc | search_constitutional_court | ✅ |
| 헌재결정례 본문 조회 | detc | get_constitutional_court_detail | ✅ |

---

## 12. 법령해석례 - 2개 API

**도구 파일**: `precedent_tools.py`

| API 제목 | target | 도구명 | 상태 |
|---------|--------|-------|------|
| 법령해석례 목록 조회 | expc | search_legal_interpretation | ✅ |
| 법령해석례 본문 조회 | expc | get_legal_interpretation_detail | ✅ |

---

## 13. 행정심판례 - 2개 API

**도구 파일**: `precedent_tools.py`

| API 제목 | target | 도구명 | 상태 |
|---------|--------|-------|------|
| 행정심판례 목록 조회 | decc | search_administrative_trial | ✅ |
| 행정심판례 본문 조회 | decc | get_administrative_trial_detail | ✅ |

---

## 14. 조약 - 2개 API

**도구 파일**: `specialized_tools.py`

| API 제목 | target | 도구명 | 상태 |
|---------|--------|-------|------|
| 조약 목록 조회 | trty | search_treaty | ✅ |
| 조약 본문 조회 | trty | get_treaty_detail | ✅ |

---

## 15. 학칙ㆍ공단ㆍ공공기관 - 2개 API

**도구 파일**: `specialized_tools.py`

| API 제목 | target | 도구명 | 상태 |
|---------|--------|-------|------|
| 학칙ㆍ공단ㆍ공공기관 목록 조회 | school/pi | search_university_regulation, search_public_corporation_regulation | ⚠️ |
| 학칙ㆍ공단ㆍ공공기관 본문 조회 | school/pi | get_university_regulation_detail | ⚠️ |

---

## 16. 법령용어 - 2개 API

**도구 파일**: `legal_term_tools.py`

| API 제목 | target | 도구명 | 상태 |
|---------|--------|-------|------|
| 법령 용어 목록 조회 | lstrm | search_legal_term | ✅ |
| 법령 용어 본문 조회 | lstrm | get_legal_term_detail | ✅ |

---

## 품질 현황 요약

| 상태 | 개수 | 비율 |
|------|------|------|
| ✅ JSON 정상 | 136 | 78.6% |
| ⚠️ 경고 (특수 파라미터/0건) | 24 | 13.9% |
| 📄 HTML 전용 | 13 | 7.5% |
| **합계** | **173** | **100%** |

---

## 개선 필요 항목

### 1. 캐시 적용 권장

| 구분 | 대상 도구 | 이유 | 우선순위 |
|------|----------|------|---------|
| 법령 | search_law | 호출 빈도 높음, 데이터 변경 적음 | 높음 |
| 법령 | get_law_detail | 본문 조회 캐싱으로 응답 속도 개선 | 높음 |
| 판례 | search_precedent | 검색 빈도 높음 | 중간 |
| 위원회 결정문 | 전체 위원회 검색 | 데이터 변경 적음 | 중간 |
| 중앙부처 1차 해석 | search_nts_interpretation | 135,765건, 대용량 | 높음 |

**캐시 구현 참고**: `optimized_law_tools.py`의 `search_law_with_cache` 패턴

### 2. 도구 추가 필요

| 구분 | target | 필요 도구 | 우선순위 |
|------|--------|----------|---------|
| 법령정보 지식베이스 | aiRltLs | search_ai_related_law | 중간 |
| 맞춤형 | couseAdmrul | search_custom_administrative_rule_articles | 낮음 |
| 법령 | drlaw | search_law_ordinance_status | 낮음 |

### 3. 도구 품질 개선 필요

| 구분 | 도구명 | 개선 내용 | 우선순위 |
|------|--------|----------|---------|
| 학칙ㆍ공단ㆍ공공기관 | search_university_regulation | target 값 명확화 (school vs pi) | 중간 |
| 법령정보 지식베이스 | search_legal_term_ai | 데이터 없음 원인 파악 | 낮음 |
| 중앙부처 1차 해석 | 0건 반환 부처 | 파라미터 조정 또는 안내 메시지 개선 | 낮음 |

### 4. 도구 분리/병합 검토

| 현재 상태 | 제안 | 이유 |
|----------|------|------|
| ministry_interpretation_tools.py (19개) + _extended.py (48개) | 유지 | 부처 수가 많아 분리 유지 |
| precedent_tools.py (판례+헌재+해석례+심판례) | 유지 | 유사 패턴, 통합 관리 효율적 |
| law_tools.py (39개) | 분리 검토 | 파일 크기 큼, 기능별 분리 가능 |

### 5. HTML 전용 API (13개) - JSON 미지원

| 구분 | API | 현재 처리 방식 |
|------|-----|--------------|
| 법령 | 법령 연혁, 변경이력, 조문 개정 이력 | HTML URL 안내 |
| 법령 | 법령 체계도, 한눈보기 | HTML URL 안내 |
| 법령정보 지식베이스 | 법령용어 연계 조회 5개 | HTML URL 안내 |

**대안**: 웹 스크래핑 도구 추가 검토 (복잡도 높음)

### 6. 응답 품질 개선

| 구분 | 문제 | 개선 방안 |
|------|------|----------|
| 전체 | 빈 결과 시 사용자 혼란 | 대안 검색어 제시, 관련 도구 안내 |
| 위원회 결정문 | 일부 위원회 0건 | 기간/검색어 조정 가이드 |
| 중앙부처 1차 해석 | 일부 부처 0건 | 해당 부처 데이터 없음 명시 |

---

## 버전 이력

- 2026-01-22 (오후): 법령 도구 품질 개선 - 정확 매치 정렬, HTML 태그 제거, 조문 번호 중복 수정
- 2026-01-22: api_layout 기준으로 전면 재구성 (16개 구분, 173개 API), 정식 명칭 적용
- 2026-01-21: 중앙부처해석 3개 부처 추가, 특별행정심판 2개 기관 추가
- 2026-01-20: 전체 중앙부처해석 API 활성화 (35개 부처)
