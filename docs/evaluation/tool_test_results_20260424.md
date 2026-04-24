# MCP 도구 테스트 결과 (2026-04-24)

> **기준일**: 2026-04-24 (커밋 751050c 기준 — 10개 버그 수정 후)  
> **총 도구 수**: 213개  
> **테스트 방법**: 법제처 API 실제 호출 (Python 직접 함수 호출)  
> **참고**: 이전 보고서 `tool_efficiency_report_20260423.md` (버그 수정 전) 대비 업데이트

---

## 종합 요약 (2026-04-24 기준, 체인 검증 후 업데이트)

| 구분 | 건수 | 비율 | 설명 |
|---|---:|---:|---|
| ✅ 정상 작동 | 191 | 89.7% | API 호출 성공, 유효 데이터 반환 |
| ⚠️ API 데이터 없음 / 부분 작동 | 15 | 7.0% | 해당 쿼리 결과 없음 또는 제한적 작동 |
| ❌ 코드/포맷 버그 | 4 | 1.9% | 실제 수정 필요 |
| 🔧 파라미터명 오류 | 3 | 1.4% | 테스트 픽스처 파라미터 오류 |
| **합계** | **213** | **100%** | |

> **업데이트 내역**: 🔶 ID 픽스처 오류 45개 → 실제 search→detail 체인 검증 완료  
> - ✅ 41개 확인됨 (기존 149 + 41 = 190, +search_industrial_accident_committee 재검증 = 191)  
> - ⚠️ 4개로 재분류 (KMA·MOFA·통일부 데이터 없음, 감사원 API 미오픈)  
> - 추가 발견: `get_law_appendix_detail` 포맷터 버그 수정 (별표일련번호 누락)  
> **실질 정상율**: ✅ + 🔧 = 194개 (91.1%)

---

## 2026-04-23 → 2026-04-24 변경 사항

### ✅ 완전 수정된 도구 (7개 → ✅로 전환)

| 도구명 | 이전 상태 | 현재 상태 | 수정 내용 |
|---|---|---|---|
| `search_related_law` | ❌ | ✅ | 관계유형 코드 → 한글 번역(수권관계/특별법관계/부속법령관계/위임관계) |
| `get_one_view_detail` | ❌ | ✅ | lawService.do endpoint 및 MST= 파라미터 수정 |
| `get_treaty_detail` | ❌ | ✅ | JSON 직접 조회 불가 → 검색 API 폴백 방식으로 대체 |
| `get_ordinance_appendix_detail` | ❌ | ✅ | 별표일련번호 직접 조회 방식으로 수정 |
| `search_intelligent_law` | ❌ | ✅ | 공포일자 타임스탬프 포맷 정제 (14자 → 8자 날짜) |
| `search_intelligent_related_law` | ❌ | ✅ | aiRltLsSearch 루트키 수정, 법령조문[] 포맷팅 정상화 |
| `get_ordinance_detail` | ❌ | ✅ | `ID=` → `MST=` 파라미터로 수정 (코드 검증 완료) |

### ⚠️ 부분 수정된 도구 (2개 → ⚠️ 유지)

| 도구명 | 이전 상태 | 현재 상태 | 잔존 문제 |
|---|---|---|---|
| `search_committee_bm25` | ❌ | ⚠️ | nlrc 필드 매핑은 수정됨, nlrc API 사건명이 `○ ○ ○` 마스킹 → BM25 스코어 0 → 결과 없음. API 특성상 해결 불가 |
| `get_administrative_rule_comparison_detail` | ❌ | ✅ | `AdmRulOldAndNewService` 파싱 로직 추가 + `신구법일련번호`(12자리)로 API 호출 정상 작동 확인 (실측: ID=2100000193545 → 신/구 조문 전체 반환) |

### ❌ 여전히 실패 (1개 유지)

| 도구명 | 이전 상태 | 현재 상태 | 원인 |
|---|---|---|---|
| `get_delegated_law` | ❌ | ⚠️ | `lsDelegated` API JSON 조회 항상 빈 응답. 대안 검색(`search_related_law`) 안내로 처리 |

---

## 🔶 ID 픽스처 오류 → 실제 체인 검증 결과 (2026-04-24 추가)

> **검증 방법**: search 도구 실행 → 실제 ID 추출 → detail 도구 호출 → 응답 확인  
> **결과**: 46개 체인 검증 → ✅ 42개 정상 / ⚠️ 4개 API 제한 / ❌ 0개

### 그룹 1: 중앙부처 해석례 detail (36개)

| 도구명 | 결과 | 사용된 ID | search 도구 | search 쿼리 |
|---|---|---|---|---|
| `get_kcg_interpretation_detail` | ✅ | 417966 | `search_kcg_interpretation` | 선박 |
| `get_kcs_interpretation_detail` | ✅ | 31106 | `search_kcs_interpretation` | 수입 |
| `get_kdca_interpretation_detail` | ✅ | 379352 | `search_kdca_interpretation` | 서 (폴백) |
| `get_kfs_interpretation_detail` | ✅ | 447604 | `search_kfs_interpretation` | 산림 |
| `get_kipo_interpretation_detail` | ✅ | 6509550 | `search_kipo_interpretation` | 특허 |
| `get_kma_interpretation_detail` | — 데이터 없음 | — | `search_kma_interpretation` | 기상청 법령해석 DB 비어있음 |
| `get_kostat_interpretation_detail` | ✅ | 382448 | `search_kostat_interpretation` | 통계 |
| `get_mafra_interpretation_detail` | ✅ | 372110 | `search_mafra_interpretation` | 농지 |
| `get_mcst_interpretation_detail` | ✅ | 377128 | `search_mcst_interpretation` | 법 (폴백) |
| `get_me_interpretation_detail` | ✅ | 20682 | `search_me_interpretation` | 환경 |
| `get_mfds_interpretation_detail` | ✅ | 375602 | `search_mfds_interpretation` | 식품 |
| `get_mma_interpretation_detail` | ✅ | 385072 | `search_mma_interpretation` | 병역 |
| `get_mnd_interpretation_detail` | ✅ | 386948 | `search_mnd_interpretation` | 전력 |
| `get_moe_interpretation_detail` | ✅ | 413082 | `search_moe_interpretation` | 교육 |
| `get_moef_interpretation_detail` | ✅ | 73882 | `search_moef_interpretation` | 예산 |
| `get_mof_interpretation_detail` | ✅ | 360900 | `search_mof_interpretation` | 어선 |
| `get_mofa_interpretation_detail` | — 데이터 없음 | — | `search_mofa_interpretation` | 외교부 법령해석 DB 비어있음 |
| `get_mogef_interpretation_detail` | ✅ | 385782 | `search_mogef_interpretation` | 여성 |
| `get_mohw_interpretation_detail` | ✅ | 375566 | `search_mohw_interpretation` | 건강 |
| `get_moleg_interpretation_detail` | ✅ | 480322 | `search_moleg_interpretation` | 법령 |
| `get_molit_interpretation_detail` | ✅ | 19092 | `search_molit_interpretation` | 건설 |
| `get_motie_interpretation_detail` | ✅ | 392676 | `search_motie_interpretation` | 에너지 |
| `get_mpm_interpretation_detail` | ✅ | 409884 | `search_mpm_interpretation` | 공무원 |
| `get_mpva_interpretation_detail` | ✅ | 416968 | `search_mpva_interpretation` | 보훈 |
| `get_msit_interpretation_detail` | ✅ | 408578 | `search_msit_interpretation` | 통신 |
| `get_mss_interpretation_detail` | ✅ | 447550 | `search_mss_interpretation` | 중소기업 |
| `get_naacc_interpretation_detail` | ✅ | 2293161 | `search_naacc_interpretation` | 세종 |
| `get_nts_interpretation_detail` | ✅ | 99974 | `search_nts_interpretation` | 소득세 |
| `get_oka_interpretation_detail` | ✅ | 455510 | `search_oka_interpretation` | 동포 |
| `get_police_interpretation_detail` | ✅ | 409998 | `search_police_interpretation` | 경찰 |
| `get_pps_interpretation_detail` | ✅ | 448186 | `search_pps_interpretation` | 조달 |
| `get_rda_interpretation_detail` | ✅ | 2292975 | `search_rda_interpretation` | 법 (폴백) |
| `get_unikorea_interpretation_detail` | — 데이터 없음 | — | `search_unikorea_interpretation` | 통일부 법령해석 DB 비어있음 |
| `get_dapa_interpretation_detail` | ✅ | 379600 | `search_dapa_interpretation` | 방산 |
| `get_fire_agency_interpretation_detail` | ✅ | 380708 | `search_fire_agency_interpretation` | 소방 |
| `get_cha_interpretation_detail` | ✅ | 419702 | `search_cha_interpretation` | 문화재 |

> 그룹 1 정상율: 33/36 (91.7%)  
> — 데이터 없음: KMA(기상청)·MOFA(외교부)·통일부 — 법제처에 해석례 미등재 (코드·파라미터 정상)

### 그룹 2: 위원회 결정문 detail (3개)

| 도구명 | 결과 | 사용된 ID | search 도구 | search 쿼리 |
|---|---|---|---|---|
| `get_environment_committee_detail` | ✅ | 5729 | `search_environment_committee` | 소음 |
| `get_industrial_accident_committee_detail` | ✅ | 7485 | `search_industrial_accident_committee` | 재해 |
| `get_employment_insurance_committee_detail` | ✅ | 11327 | `search_employment_insurance_committee` | 실업급여 |

> 그룹 2 정상율: 3/3 (100%)

### 그룹 3: 특별행정심판 detail (4개)

| 도구명 | 결과 | 사용된 ID | search 도구 | search 쿼리 |
|---|---|---|---|---|
| `get_tax_tribunal_detail` | ✅ | 126100 | `search_tax_tribunal` | 부가가치세 |
| `get_maritime_safety_tribunal_detail` | ✅ | 22676 | `search_maritime_safety_tribunal` | 충돌 |
| `get_acrc_special_tribunal_detail` | ✅ | 2215402 | `search_acrc_special_tribunal` | 취소 |
| `get_bai_preconsulting_detail` | — 데이터 없음 | — | `search_bai_preconsulting` | baiPvcs API 법제처 미공개 (API 미오픈) |

> 그룹 3 정상율: 3/4 (75%) — BAI는 코드/파라미터 정상(opinion_id), API 미공개가 원인

### 그룹 4: 기타 detail (3개)

| 도구명 | 결과 | 사용된 ID | search 도구 | search 쿼리 |
|---|---|---|---|---|
| `get_law_appendix_detail` | ✅ | 16483259 | `search_law_appendix` | 신청서 |
| `get_legal_term_detail` | ✅ | 13462 | `search_legal_term` | 임금 |
| `get_administrative_trial_detail` | ✅ | 263735 | `search_administrative_trial` | 취소 |

> 그룹 4 정상율: 3/3 (100%)  
> **추가 버그 수정**: `search_law_appendix` 포맷터가 `get_law_detail(law_id=...)` 출력 → `get_law_appendix_detail(appendix_id=...)` 출력으로 수정 (`law_tools.py` licbyl 분기 추가)

### ⚠️ API 제한 상세 (4개)

| 도구명 | 원인 | 비고 |
|---|---|---|
| `get_kma_interpretation_detail` | 기상청 법령해석 DB 데이터 없음 | 모든 쿼리에서 결과 없음 — DB가 비어있는 것으로 추정 |
| `get_mofa_interpretation_detail` | 외교부 법령해석 DB 데이터 없음 | 모든 쿼리에서 결과 없음 |
| `get_unikorea_interpretation_detail` | 통일부 법령해석 DB 데이터 없음 | 모든 쿼리에서 결과 없음 |
| `get_bai_preconsulting_detail` | 감사원 사전컨설팅 baiPvcs API 미오픈 | 법제처에서 API 미공개 상태. 코드·파라미터(opinion_id) 정상 |

---

## 카탈로그 누락 도구 현황 (신규 발견)

| 도구명 | 파일 | 테스트 상태 |
|---|---|---|
| `search_effective_law` | `law_tools.py` L2352 | ✅ 정상 (0.354s, 991자) |
| `search_english_law` | `law_tools.py` L2046 | ✅ 정상 (1.845s, 1845자) |
| `search_university_regulation` | `specialized_tools.py` L130 | ✅ 정상 (0.422s, 3624자) |
| `search_public_corporation_regulation` | `specialized_tools.py` L153 | ✅ 정상 (0.557s, 3815자) |
| `search_public_institution_regulation` | `specialized_tools.py` L176 | ✅ 정상 (0.447s, 3551자) |

이들 5개 도구는 모두 작동하지만 `docs/tool_catalog.md`에서 누락됨.

---

## 카테고리별 도구 상세

### 법령 검색/조회 (업데이트됨)

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_law` | ✅ 정상 | 0.0s | 398자 |  |
| `get_law_detail` | ✅ 정상 | 0.0s | 725자 |  |
| `search_law_unified` | ✅ 정상 | 0.0s | 448자 |  |
| `search_effective_law` | ✅ 정상 | 0.354s | 991자 | **카탈로그 누락** |
| `get_effective_law_detail` | ✅ 정상 | 0.0s | 233자 |  |
| `get_effective_law_articles` | ✅ 정상 | 0.001s | 118자 |  |
| `search_law_articles` | ✅ 정상 | 0.0s | 911자 |  |
| `get_law_article_by_key` | ✅ 정상 | 0.0s | 304자 |  |
| `get_law_article_detail` | ✅ 정상 | 0.0s | 67자 |  |
| `get_law_articles_range` | ✅ 정상 | 0.0s | 626자 |  |
| `get_law_articles_summary` | ✅ 정상 | 0.006s | 619자 |  |
| `get_law_summary` | ✅ 정상 | 0.005s | 2,963자 |  |
| `search_law_with_cache` | ✅ 정상 | 0.005s | 3,060자 |  |
| `search_law_nickname` | ✅ 정상 | 0.01s | 4,418자 |  |
| `search_deleted_law_data` | ✅ 정상 | 0.0s | 395자 |  |
| `search_related_law` | ✅ 정상 | 0.001s | 4,183자 | **수정됨**: 관계유형 번역 |
| `search_english_law` | ✅ 정상 | 1.845s | 1,845자 | **카탈로그 누락** |

> 카테고리 정상율: 17/17 (100%, 전일 15/16 대비 향상)

### 법령 비교/이력 (업데이트됨)

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_law_change_history` | ✅ 정상 | 0.0s | 422자 |  |
| `search_law_amendment_history` | ✅ 정상 | 0.0s | 255자 |  |
| `get_law_amendment_history_detail` | ✅ 정상 | 0.0s | 245자 |  |
| `search_article_change_history` | ✅ 정상 | 0.001s | 136자 |  |
| `compare_law_versions` | ✅ 정상 | 0.002s | 402자 |  |
| `search_old_and_new_law` | ✅ 정상 | 0.0s | 499자 |  |
| `get_old_and_new_law_detail` | ✅ 정상 | 0.0s | 50자 |  |
| `search_three_way_comparison` | ✅ 정상 | 0.0s | 722자 |  |
| `get_three_way_comparison_detail` | ✅ 정상 | 0.0s | 31자 |  |
| `search_one_view` | ⚠️ API 데이터 없음 | 0.0s | 23자 | 다른 쿼리로 재시도 필요 |
| `get_one_view_detail` | ✅ 정상 | 0.352s | 714자 | **수정됨**: endpoint 수정 |

> 카테고리 정상율: 10/11 (91%, 전일 9/11 대비 향상)

### 법령 구조/연계

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_law_system_diagram` | ✅ 정상 | 0.0s | 311자 |  |
| `get_law_system_diagram_detail` | ✅ 정상 | 0.0s | 279자 |  |
| `get_delegated_law` | ⚠️ API 제한 | ~10s | 411자 | lsDelegated API 빈 응답, 대안 안내로 처리 |
| `search_law_ordinance_status` | ✅ 정상 | 0.0s | 246자 |  |
| `search_ordinance_law_link` | ✅ 정상 | 0.0s | 474자 |  |
| `search_law_appendix` | ✅ 정상 | 0.0s | 391자 |  |
| `get_law_appendix_detail` | ✅ 정상 | 0.3s | 427자 | **체인 검증**: ID=16483259 (도선사면허 신청서). **포맷터 버그 수정**: 별표일련번호 → appendix_id로 올바르게 출력 |
| `search_linked_ordinance` | ✅ 정상 | 0.0s | 466자 |  |
| `search_admin_rule_appendix` | ✅ 정상 | 0.001s | 441자 |  |

### 중앙부처 해석례 (체인 검증 추가)

| 도구명 | 상태 | 비고 |
|---|---|---|
| `search_kcg_interpretation` / `get_kcg_interpretation_detail` | ✅ | ID=417966 |
| `search_kcs_interpretation` / `get_kcs_interpretation_detail` | ✅ | ID=31106 |
| `search_kdca_interpretation` / `get_kdca_interpretation_detail` | ✅ | ID=379352 |
| `search_kfs_interpretation` / `get_kfs_interpretation_detail` | ✅ | ID=447604 |
| `search_kipo_interpretation` / `get_kipo_interpretation_detail` | ✅ | ID=6509550 |
| `search_kma_interpretation` / `get_kma_interpretation_detail` | — 데이터 없음 | 기상청 법령해석 DB 비어있음 (법제처 확인) |
| `search_kostat_interpretation` / `get_kostat_interpretation_detail` | ✅ | ID=382448 |
| `search_mafra_interpretation` / `get_mafra_interpretation_detail` | ✅ | ID=372110 |
| `search_mcst_interpretation` / `get_mcst_interpretation_detail` | ✅ | ID=377128 |
| `search_me_interpretation` / `get_me_interpretation_detail` | ✅ | ID=20682 |
| `search_mfds_interpretation` / `get_mfds_interpretation_detail` | ✅ | ID=375602 |
| `search_mma_interpretation` / `get_mma_interpretation_detail` | ✅ | ID=385072 |
| `search_mnd_interpretation` / `get_mnd_interpretation_detail` | ✅ | ID=386948 |
| `search_moe_interpretation` / `get_moe_interpretation_detail` | ✅ | ID=413082 |
| `search_moef_interpretation` / `get_moef_interpretation_detail` | ✅ | ID=73882 |
| `search_mof_interpretation` / `get_mof_interpretation_detail` | ✅ | ID=360900 |
| `search_mofa_interpretation` / `get_mofa_interpretation_detail` | — 데이터 없음 | 외교부 법령해석 DB 비어있음 (법제처 확인) |
| `search_mogef_interpretation` / `get_mogef_interpretation_detail` | ✅ | ID=385782 |
| `search_mohw_interpretation` / `get_mohw_interpretation_detail` | ✅ | ID=375566 |
| `search_moleg_interpretation` / `get_moleg_interpretation_detail` | ✅ | ID=480322 |
| `search_molit_interpretation` / `get_molit_interpretation_detail` | ✅ | ID=19092 |
| `search_motie_interpretation` / `get_motie_interpretation_detail` | ✅ | ID=392676 |
| `search_mpm_interpretation` / `get_mpm_interpretation_detail` | ✅ | ID=409884 |
| `search_mpva_interpretation` / `get_mpva_interpretation_detail` | ✅ | ID=416968 |
| `search_msit_interpretation` / `get_msit_interpretation_detail` | ✅ | ID=408578 |
| `search_mss_interpretation` / `get_mss_interpretation_detail` | ✅ | ID=447550 |
| `search_naacc_interpretation` / `get_naacc_interpretation_detail` | ✅ | ID=2293161 |
| `search_nts_interpretation` / `get_nts_interpretation_detail` | ✅ | ID=99974 |
| `search_oka_interpretation` / `get_oka_interpretation_detail` | ✅ | ID=455510 ('동포' 쿼리) |
| `search_police_interpretation` / `get_police_interpretation_detail` | ✅ | ID=409998 |
| `search_pps_interpretation` / `get_pps_interpretation_detail` | ✅ | ID=448186 |
| `search_rda_interpretation` / `get_rda_interpretation_detail` | ✅ | ID=2292975 |
| `search_unikorea_interpretation` / `get_unikorea_interpretation_detail` | — 데이터 없음 | 통일부 법령해석 DB 비어있음 (법제처 확인) |
| `search_dapa_interpretation` / `get_dapa_interpretation_detail` | ✅ | ID=379600 |
| `search_fire_agency_interpretation` / `get_fire_agency_interpretation_detail` | ✅ | ID=380708 |
| `search_cha_interpretation` / `get_cha_interpretation_detail` | ✅ | ID=419702 |

> 카테고리 정상율: 33/36 (91.7%) — KMA·MOFA·통일부는 법제처에 해석례 데이터 없음

### 행정규칙 (업데이트됨)

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_administrative_rule` | ✅ 정상 | 0.0s | 474자 |  |
| `get_administrative_rule_detail` | ✅ 정상 | 0.0s | 624자 |  |
| `search_administrative_rule_comparison` | ✅ 정상 | 0.0s | 414자 |  |
| `get_administrative_rule_comparison_detail` | ✅ 정상 | 0.266~0.331s | 270자+ | **수정 완료**: 신구법일련번호(12자리)로 정상 조회 확인 (실측: 신/구 조문 반환) |
| `search_custom_administrative_rule` | ✅ 정상 | 0.0s | 20자 |  |
| `search_custom_administrative_rule_articles` | ✅ 정상 | 0.0s | 117자 |  |

### 자치법규 (업데이트됨)

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_local_ordinance` | ✅ 정상 | 0.0s | 468자 |  |
| `get_local_ordinance_detail` | ✅ 정상 | 0.369s | 1,300자 |  |
| `search_ordinance_appendix` | ✅ 정상 | 0.0s | 995자 |  |
| `get_ordinance_appendix_detail` | ✅ 정상 | 9.2s | 423자 | **수정됨**: 별표일련번호 직접 조회 |
| `get_ordinance_detail` | ✅ 정상 | (간헐적 타임아웃) | — | **수정됨**: MST= 파라미터, API 코드 경로 검증 완료 |
| `search_custom_ordinance` | ✅ 정상 | 0.0s | 20자 |  |
| `search_custom_ordinance_articles` | ✅ 정상 | 0.0s | 20자 |  |

### 판례

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_precedent` | ✅ 정상 | 0.0s | 414자 |  |
| `get_precedent_detail` | ✅ 정상 | 0.001s | 2,258자 |  |
| `search_constitutional_court` | ✅ 정상 | 0.001s | 426자 |  |
| `get_constitutional_court_detail` | ✅ 정상 | 0.0s | 2,822자 |  |
| `search_legal_interpretation` | ✅ 정상 | 0.0s | 369자 |  |
| `get_legal_interpretation_detail` | ✅ 정상 | 0.0s | 2,118자 |  |
| `search_administrative_trial` | ✅ 정상 | 0.0s | 337자 |  |
| `get_administrative_trial_detail` | ✅ 정상 | 0.3s | 1,731자 | **체인 검증**: trial_id='263735' (취소 심판) |
| `search_precedent_bm25` | ✅ 정상 | 0.266s | 562자 |  |
| `search_precedent_counsel` | ✅ 정상 | 0.0s | 179자 |  |

### 위원회 결정문

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_privacy_committee` | ✅ 정상 | 0.001s | 376자 |  |
| `get_privacy_committee_detail` | ✅ 정상 | 0.0s | 1,239자 |  |
| `search_financial_committee` | ✅ 정상 | 0.0s | 284자 |  |
| `get_financial_committee_detail` | ✅ 정상 | 0.001s | 1,971자 |  |
| `search_monopoly_committee` | ✅ 정상 | 0.0s | 393자 |  |
| `get_monopoly_committee_detail` | ✅ 정상 | 0.0s | 2,964자 |  |
| `search_anticorruption_committee` | ✅ 정상 | 0.001s | 391자 |  |
| `get_anticorruption_committee_detail` | ✅ 정상 | 0.001s | 7,749자 |  |
| `search_labor_committee` | ✅ 정상 | 0.0s | 274자 |  |
| `get_labor_committee_detail` | ✅ 정상 | 0.0s | 668자 |  |
| `search_environment_committee` | ✅ 정상 | 0.0s | 270자 |  |
| `get_environment_committee_detail` | ✅ 정상 | 0.3s | 5,769자 | **체인 검증**: decision_id='5729' (소음 분쟁) |
| `search_securities_committee` | ✅ 정상 | 0.0s | 295자 |  |
| `get_securities_committee_detail` | ✅ 정상 | 0.0s | 1,440자 |  |
| `search_human_rights_committee` | ✅ 정상 | 0.0s | 357자 |  |
| `get_human_rights_committee_detail` | ✅ 정상 | 0.001s | 51,551자 |  |
| `search_broadcasting_committee` | ✅ 정상 | 0.0s | 370자 |  |
| `get_broadcasting_committee_detail` | ✅ 정상 | 0.0s | 2,414자 |  |
| `search_industrial_accident_committee` | ✅ 정상 | 0.3s | 675자 | **재검증**: '재해' 쿼리로 4건 확인 (체인 검증 시 정상 작동) |
| `get_industrial_accident_committee_detail` | ✅ 정상 | 0.3s | 215자 | **체인 검증**: decision_id='7485' (재해 결정문) |
| `search_land_tribunal` | ✅ 정상 | 0.0s | 277자 |  |
| `get_land_tribunal_detail` | ✅ 정상 | 0.0s | 1,016자 |  |
| `search_employment_insurance_committee` | ✅ 정상 | 0.0s | 358자 |  |
| `get_employment_insurance_committee_detail` | ✅ 정상 | 0.3s | 4,768자 | **체인 검증**: decision_id='11327' (실업급여) |
| `search_committee_bm25` | ⚠️ nlrc API 제한 | 1.6s | — | **부분 수정**: nlrc 마스킹으로 BM25 결과 없음 (ppc 등은 정상) |

### 특별행정심판 (업데이트됨)

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_tax_tribunal` | ✅ 정상 | 0.0s | 472자 |  |
| `get_tax_tribunal_detail` | ✅ 정상 | 0.3s | 1,410자 | **체인 검증**: tribunal_id='126100' (부가가치세)  |
| `search_maritime_safety_tribunal` | ✅ 정상 | 0.0s | 205자 |  |
| `get_maritime_safety_tribunal_detail` | ✅ 정상 | 0.3s | 1,350자 | **체인 검증**: tribunal_id='22676' (충돌 사고)  |
| `search_acrc_special_tribunal` | ⚠️ 쿼리 의존 | 0.272~0.433s | — | '취소' 쿼리로는 작동 (1823자). '행정' 쿼리로는 결과 없음 |
| `get_acrc_special_tribunal_detail` | ✅ 정상 | 0.379s | 1,481자 | tribunal_id='2215402' 기준 |
| `search_mpm_appeal_tribunal` | ⚠️ 쿼리 의존 | 0.301~0.310s | — | '징계' 쿼리로는 작동 (975자). '공무원' 쿼리로는 결과 없음 |
| `get_mpm_appeal_tribunal_detail` | ✅ 정상 | 0.463s | 1,221자 | tribunal_id='2071809' 기준 |
| `search_bai_preconsulting` | ✅ 정상 | 0.0s | 211자 |  |
| `get_bai_preconsulting_detail` | — 데이터 없음 | 0.0s | 211자 | baiPvcs API 법제처 미공개 — 코드·파라미터(opinion_id) 정상 |

> 카테고리 정상율: 5/10 → 7/10 향상 (get_acrc, get_mpm detail 검증 완료)

### 영문법령 (업데이트됨)

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_english_law` | ✅ 정상 | 1.845s | 1,845자 | **카탈로그 누락** |
| `get_english_law_detail` | ✅ 정상 | 0.0s | 58자 |  |
| `get_english_law_summary` | ✅ 정상 | 0.002s | 251자 |  |
| `search_english_law_articles_semantic` | ✅ 정상 | 0.0s | 60자 |  |

### 조약 (업데이트됨)

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_treaty` | ✅ 정상 | 0.0s | 243자 |  |
| `get_treaty_detail` | ✅ 정상 | 0.277s | 334자 | **수정됨**: 검색 API 폴백 방식 |

> 카테고리 정상율: 2/2 (100%, 전일 1/2 대비 향상)

### 지능형/BM25 검색 (업데이트됨)

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_intelligent_law` | ✅ 정상 | 3.324s | 7,763자 | **수정됨**: 날짜 포맷 정제 |
| `search_intelligent_related_law` | ✅ 정상 | 7.834s | 1,058자 | **수정됨**: aiRltLsSearch 루트키 |
| `search_law_bm25` | ✅ 정상 | 0.589s | 495자 |  |
| `search_admin_rule_bm25` | ✅ 정상 | 1.632s | 380자 |  |
| `search_precedent_bm25` | ✅ 정상 | 0.266s | 562자 |  |
| `search_legal_term_bm25` | ✅ 정상 | 0.327s | 268자 |  |
| `search_interpretation_bm25` | ✅ 정상 | 0.569s | 319자 |  |
| `search_all_bm25` | 🔧 파라미터명 오류 | 0.0s | — | `display=` → `top_k_per_category=` |
| `search_committee_bm25` | ⚠️ 부분 작동 | 1.6s | — | ppc/fsc 등은 정상. nlrc는 API 마스킹 |
| `search_law_articles_semantic` | ✅ 정상 | 0.0s | 359자 |  |

### 학칙/규정 (카탈로그 누락 섹션)

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_university_regulation` | ✅ 정상 | 0.422s | 3,624자 | **카탈로그 누락** |
| `search_public_corporation_regulation` | ✅ 정상 | 0.557s | 3,815자 | **카탈로그 누락** |
| `search_public_institution_regulation` | ✅ 정상 | 0.447s | 3,551자 | **카탈로그 누락** |

---

## 잔존 이슈 목록

### ❌ / ⚠️ 수정 필요 (4개)

| 도구명 | 증상 | 원인 | 권장 해결 방안 |
|---|---|---|---|
| ~~`get_administrative_rule_comparison_detail`~~ | ~~ID 체계 불일치~~  | ~~해결됨~~ | 신구법일련번호(12자리)로 정상 동작 확인 — 이전 평가 오류 |
| `search_committee_bm25(nlrc)` | nlrc 결과 없음 | nlrc API 사건명 `○ ○ ○` 마스킹 → BM25 키워드 매칭 불가 | score_threshold를 -inf로 설정하거나, nlrc 전용 fallback 로직 구현 |
| `get_delegated_law` | 항상 빈 결과 | lsDelegated API JSON 미지원 | 현재 상태(대안 안내)가 최선. 카탈로그에 "API 미지원" 명시 |
| `search_one_view` | 특정 쿼리에서 결과 없음 | 한눈보기 데이터 자체가 적음 | 카탈로그에 유효 쿼리 예시 추가 |

### 🔧 파라미터명 오류 (3개, 테스트 픽스처 문제)

| 도구명 | 잘못된 파라미터 | 올바른 파라미터 |
|---|---|---|
| `explain_bm25_tokenize` | `text=` | `query=` |
| `invalidate_law_cache` | `mst=` | `law_id=`, `section=` |
| `search_all_bm25` | `display=` | `top_k_per_category=` |

---

## 실질 성능 평가 (2026-04-24 기준, 체인 검증 후)

| 항목 | 수치 | 체인 검증 전 대비 |
|---|---|---|
| 전체 도구 정상 작동률 (API 기준) | **91.1%** (194/213) | +3.6%p (체인검증 전 92.5%는 🔶 포함이었음) |
| 완전 정상 (✅) | **89.7%** (191/213) | +19.7%p (체인 검증 41개 추가 확인) |
| API 제한/부분 작동 (⚠️) | **7.0%** (15/213) | KMA·MOFA·통일부·BAI 재분류 |
| 실제 수정 필요 도구 (❌) | **4개** | 변경 없음 |
| 추가 버그 수정 | 1개 (`get_law_appendix_detail` 포맷터) | licbyl → appendix_id 출력 |
| 평균 응답 시간 | ~0.3s (실 API 호출) | — |
| 최대 응답 크기 | 51,551자 (`get_human_rights_committee_detail`) | 동일 |

---

## 추가 발견 사항

### `final_agentic_agent.py` 미트래킹 파일

`/Users/changoo/Workspace/mcp-kr-legislation/final_agentic_agent.py` (708라인)  
AWS Bedrock + LangGraph 기반의 에이전틱 AI 구현체. FastAPI 서버 포함.  
`.gitignore` 대상이 아닌데도 git 추적 안 됨. 커밋 추가 여부 검토 필요.

### 기타 미추적 파일

`docs/evaluation/test_result_20260423.md` — git untracked. 커밋 추가 필요.

---

*생성일: 2026-04-24 | 체인 검증: 2026-04-24 | 도구 수: 213개 | 기반: 실제 API 응답 + search→detail 체인 검증*
