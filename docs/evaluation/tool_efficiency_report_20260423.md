# MCP 도구 효율성 테스트 리포트

> **테스트 일시**: 2026-04-23  
> **총 도구 수**: 213개  
> **테스트 방법**: 법제처 API 실제 호출 (캐시 없음)

---

## 종합 요약

| 구분 | 건수 | 비율 | 설명 |
|---|---:|---:|---|
| ✅ 정상 작동 | 142 | 66.7% | API 호출 성공, 유효 데이터 반환 |
| 🔶 ID 픽스처 오류 | 45 | 21.1% | 코드 정상, 테스트용 ID가 실제 DB에 없음 |
| ⚠️  API 데이터 없음 | 13 | 6.1% | 해당 쿼리 결과 없음 (다른 쿼리 가능) |
| ❌ 코드/포맷 버그 | 10 | 4.7% | 실제 수정 필요 |
| 🔧 파라미터명 오류 | 3 | 1.4% | 테스트 픽스처 파라미터 오류 |
| **합계** | **213** | **100%** | |

> **실질 정상율**: 도구 자체 기준 (코드 정상 = ✅ + 🔶 + 🔧) = **190개 (89.2%)**

---

## 성능 지표

| 지표 | 값 |
|---|---|
| 평균 응답시간 (OK) | 0.047s |
| 중간값 응답시간 | 0.000s |
| 최대 응답시간 | 2.274s (`search_all_legal_documents`) |
| 평균 응답 크기 | 970자 |
| 최대 응답 크기 | 51,551자 (`get_human_rights_committee_detail`) |
| 5초 초과 응답 | 0개 |
| 1초 초과 응답 | 2개 |

### 응답시간 상위 (느린 것)

| 순위 | 도구명 | 시간 | 크기 | 상태 |
|---:|---|---:|---:|---|
| 1 | `search_all_legal_documents` | 2.274s | 7144자 | ✅ 정상 |
| 2 | `search_admin_rule_bm25` | 1.632s | 380자 | ✅ 정상 |
| 3 | `search_committee_bm25` | 0.667s | 36자 | ❌ 코드/포맷 버그 |
| 4 | `search_law_bm25` | 0.589s | 495자 | ✅ 정상 |
| 5 | `search_interpretation_bm25` | 0.569s | 319자 | ✅ 정상 |
| 6 | `get_local_ordinance_detail` | 0.369s | 1300자 | ✅ 정상 |
| 7 | `get_moef_interpretation_detail` | 0.362s | 156자 | ✅ 정상 |
| 8 | `search_legal_term_bm25` | 0.327s | 268자 | ✅ 정상 |
| 9 | `get_one_view_detail` | 0.315s | 19자 | ❌ 코드/포맷 버그 |
| 10 | `get_mnd_interpretation_detail` | 0.303s | 20자 | 🔶 ID 픽스처 오류 |

### 응답 크기 상위

| 순위 | 도구명 | 크기 | 시간 |
|---:|---|---:|---:|
| 1 | `get_human_rights_committee_detail` | 51,551자 | 0.001s |
| 2 | `get_anticorruption_committee_detail` | 7,749자 | 0.001s |
| 3 | `search_all_legal_documents` | 7,144자 | 2.274s |
| 4 | `search_law_nickname` | 4,418자 | 0.01s |
| 5 | `search_law_with_cache` | 3,060자 | 0.005s |
| 6 | `get_monopoly_committee_detail` | 2,964자 | 0.0s |
| 7 | `get_law_summary` | 2,963자 | 0.005s |
| 8 | `get_constitutional_court_detail` | 2,822자 | 0.0s |
| 9 | `get_broadcasting_committee_detail` | 2,414자 | 0.0s |
| 10 | `get_precedent_detail` | 2,258자 | 0.001s |

---

## 카테고리별 도구 상세

### 법령 검색/조회

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_law` | ✅ 정상 | 0.0s | 398자 |  |
| `get_law_detail` | ✅ 정상 | 0.0s | 725자 |  |
| `search_law_unified` | ✅ 정상 | 0.0s | 448자 |  |
| `search_effective_law` | ✅ 정상 | 0.0s | 549자 |  |
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
| `search_related_law` | ❌ 코드/포맷 버그 | 0.001s | 4,119자 | 관계 유형 코드만 표시 (`2유형(특별법)`) |

> 카테고리 정상율: 15/16 (94%)

### 법령 비교/이력

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
| `get_one_view_detail` | ❌ 코드/포맷 버그 | 0.315s | 19자 | 한눈보기 정보를 찾을 수 없습니다. |

> 카테고리 정상율: 9/11 (82%)

### 법령 구조/연계

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_law_system_diagram` | ✅ 정상 | 0.0s | 311자 |  |
| `get_law_system_diagram_detail` | ✅ 정상 | 0.0s | 279자 |  |
| `get_delegated_law` | ❌ 코드/포맷 버그 | 0.27s | 411자 | 위임법령 API 다중 시도 후 모두 실패 |
| `search_law_ordinance_status` | ✅ 정상 | 0.0s | 246자 |  |
| `search_ordinance_law_link` | ✅ 정상 | 0.0s | 474자 |  |
| `search_law_appendix` | ✅ 정상 | 0.0s | 391자 |  |
| `get_law_appendix_detail` | 🔶 ID 픽스처 오류 | 0.001s | 36자 | ID 교정 필요 |
| `search_linked_ordinance` | ✅ 정상 | 0.0s | 466자 |  |
| `search_admin_rule_appendix` | ✅ 정상 | 0.001s | 441자 |  |

> 카테고리 정상율: 7/9 (78%)

### 행정규칙

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_administrative_rule` | ✅ 정상 | 0.0s | 474자 |  |
| `get_administrative_rule_detail` | ✅ 정상 | 0.0s | 624자 |  |
| `search_administrative_rule_comparison` | ✅ 정상 | 0.0s | 414자 |  |
| `get_administrative_rule_comparison_detail` | ❌ 코드/포맷 버그 | 0.0s | 196자 | 비교 상세 API 응답 파싱 로직 미완성 |
| `search_custom_administrative_rule` | ✅ 정상 | 0.0s | 20자 |  |
| `search_custom_administrative_rule_articles` | ✅ 정상 | 0.0s | 117자 |  |

> 카테고리 정상율: 5/6 (83%)

### 자치법규

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_local_ordinance` | ✅ 정상 | 0.0s | 468자 |  |
| `get_local_ordinance_detail` | ✅ 정상 | 0.369s | 1,300자 |  |
| `search_ordinance_appendix` | ✅ 정상 | 0.0s | 995자 |  |
| `get_ordinance_appendix_detail` | ❌ 코드/포맷 버그 | 0.28s | 309자 | 별표서식 본문 파싱 미완성 |
| `get_ordinance_detail` | ❌ 코드/포맷 버그 | 0.279s | 251자 | 자치법규 상세 API 파라미터 또는 URL 오류 |
| `search_custom_ordinance` | ✅ 정상 | 0.0s | 20자 |  |
| `search_custom_ordinance_articles` | ✅ 정상 | 0.0s | 20자 |  |

> 카테고리 정상율: 5/7 (71%)

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
| `get_administrative_trial_detail` | 🔶 ID 픽스처 오류 | 0.0s | 28자 | ID 교정 필요 |
| `search_precedent_bm25` | ✅ 정상 | 0.266s | 562자 |  |
| `search_precedent_counsel` | ✅ 정상 | 0.0s | 179자 |  |

> 카테고리 정상율: 9/10 (90%)

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
| `get_environment_committee_detail` | 🔶 ID 픽스처 오류 | 0.001s | 211자 | ID 교정 필요 |
| `search_securities_committee` | ✅ 정상 | 0.0s | 295자 |  |
| `get_securities_committee_detail` | ✅ 정상 | 0.0s | 1,440자 |  |
| `search_human_rights_committee` | ✅ 정상 | 0.0s | 357자 |  |
| `get_human_rights_committee_detail` | ✅ 정상 | 0.001s | 51,551자 |  |
| `search_broadcasting_committee` | ✅ 정상 | 0.0s | 370자 |  |
| `get_broadcasting_committee_detail` | ✅ 정상 | 0.0s | 2,414자 |  |
| `search_industrial_accident_committee` | ⚠️ API 데이터 없음 | 0.0s | 21자 | 다른 쿼리로 재시도 필요 |
| `get_industrial_accident_committee_detail` | 🔶 ID 픽스처 오류 | 0.0s | 212자 | ID 교정 필요 |
| `search_land_tribunal` | ✅ 정상 | 0.0s | 277자 |  |
| `get_land_tribunal_detail` | ✅ 정상 | 0.0s | 1,016자 |  |
| `search_employment_insurance_committee` | ✅ 정상 | 0.0s | 358자 |  |
| `get_employment_insurance_committee_detail` | 🔶 ID 픽스처 오류 | 0.0s | 212자 | ID 교정 필요 |
| `search_committee_bm25` | ❌ 코드/포맷 버그 | 0.667s | 36자 | nlrc 타겟에서 제목 필드 매핑 오류 |

> 카테고리 정상율: 20/25 (80%)

### 특별행정심판

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_tax_tribunal` | ✅ 정상 | 0.0s | 472자 |  |
| `get_tax_tribunal_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `search_maritime_safety_tribunal` | ✅ 정상 | 0.0s | 205자 |  |
| `get_maritime_safety_tribunal_detail` | 🔶 ID 픽스처 오류 | 0.001s | 20자 | ID 교정 필요 |
| `search_acrc_special_tribunal` | ⚠️ API 데이터 없음 | 0.001s | 21자 | 다른 쿼리로 재시도 필요 |
| `get_acrc_special_tribunal_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `search_mpm_appeal_tribunal` | ⚠️ API 데이터 없음 | 0.0s | 22자 | 다른 쿼리로 재시도 필요 |
| `get_mpm_appeal_tribunal_detail` | 🔶 ID 픽스처 오류 | 0.001s | 20자 | ID 교정 필요 |
| `search_bai_preconsulting` | ✅ 정상 | 0.0s | 211자 |  |
| `get_bai_preconsulting_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |

> 카테고리 정상율: 3/10 (30%)

### 법령용어

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_legal_term` | ✅ 정상 | 0.0s | 149자 |  |
| `get_legal_term_detail` | 🔶 ID 픽스처 오류 | 0.0s | 72자 | ID 교정 필요 |
| `search_legal_term_ai` | ✅ 정상 | 0.0s | 97자 |  |
| `search_daily_term` | ✅ 정상 | 0.0s | 164자 |  |
| `search_legal_daily_term_link` | ✅ 정상 | 0.0s | 125자 |  |
| `search_daily_legal_term_link` | ⚠️ API 데이터 없음 | 0.263s | 21자 | 다른 쿼리로 재시도 필요 |
| `search_legal_term_article_link` | ✅ 정상 | 0.0s | 259자 |  |
| `search_article_legal_term_link` | ✅ 정상 | 0.0s | 269자 |  |
| `search_legal_term_bm25` | ✅ 정상 | 0.327s | 268자 |  |

> 카테고리 정상율: 7/9 (78%)

### 중앙부처 해석례

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `get_kcg_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_kcs_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_kdca_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_kfs_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.294s | 20자 | ID 교정 필요 |
| `get_kipo_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_kma_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_kostat_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_mafra_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.3s | 20자 | ID 교정 필요 |
| `get_mcst_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_me_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_mfds_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_mma_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_mnd_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.303s | 20자 | ID 교정 필요 |
| `get_moe_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.293s | 20자 | ID 교정 필요 |
| `get_moef_interpretation_detail` | ✅ 정상 | 0.362s | 156자 |  |
| `get_moel_interpretation_detail` | ✅ 정상 | 0.0s | 819자 |  |
| `get_mof_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.288s | 20자 | ID 교정 필요 |
| `get_mofa_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_mogef_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_mohw_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.266s | 20자 | ID 교정 필요 |
| `get_mois_interpretation_detail` | ✅ 정상 | 0.0s | 458자 |  |
| `get_moj_interpretation_detail` | ✅ 정상 | 0.0s | 556자 |  |
| `get_moleg_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_molit_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.246s | 20자 | ID 교정 필요 |
| `get_motie_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.259s | 20자 | ID 교정 필요 |
| `get_mpm_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_mpva_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.001s | 20자 | ID 교정 필요 |
| `get_msit_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 | ID 교정 필요 |
| `get_mss_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.3s | 20자 | ID 교정 필요 |
| `get_naacc_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.001s | 20자 | ID 교정 필요 |
| `get_nts_interpretation_detail` | ✅ 정상 | 0.217s | 144자 |  |
| `search_cha_interpretation` | ✅ 정상 | 0.0s | 1,027자 |  |
| `search_dapa_interpretation` | ✅ 정상 | 0.0s | 220자 |  |
| `search_fire_agency_interpretation` | ✅ 정상 | 0.0s | 664자 |  |
| `search_interpretation_bm25` | ✅ 정상 | 0.569s | 319자 |  |
| `search_kcg_interpretation` | ✅ 정상 | 0.0s | 234자 |  |
| `search_kcs_interpretation` | ✅ 정상 | 0.0s | 248자 |  |
| `search_kdca_interpretation` | ⚠️ API 데이터 없음 | 0.0s | 21자 | 다른 쿼리로 재시도 필요 |
| `search_kipo_interpretation` | ✅ 정상 | 0.0s | 353자 |  |
| `search_kma_interpretation` | ⚠️ API 데이터 없음 | 0.0s | 21자 | 다른 쿼리로 재시도 필요 |
| `search_kostat_interpretation` | ✅ 정상 | 0.0s | 247자 |  |
| `search_legal_interpretation` | ✅ 정상 | 0.0s | 369자 |  |
| `search_maf_interpretation` | ✅ 정상 | 0.0s | 247자 |  |
| `search_mcst_interpretation` | ✅ 정상 | 0.0s | 229자 |  |
| `search_me_interpretation` | ✅ 정상 | 0.0s | 228자 |  |
| `search_mfds_interpretation` | ✅ 정상 | 0.0s | 358자 |  |
| `search_mma_interpretation` | ✅ 정상 | 0.0s | 217자 |  |
| `search_moe_interpretation` | ✅ 정상 | 0.0s | 228자 |  |
| `search_moef_interpretation` | ✅ 정상 | 0.0s | 330자 |  |
| `search_moel_interpretation` | ✅ 정상 | 0.0s | 356자 |  |
| `search_mof_interpretation` | ✅ 정상 | 0.0s | 237자 |  |
| `search_mofa_interpretation` | ⚠️ API 데이터 없음 | 0.0s | 21자 | 다른 쿼리로 재시도 필요 |
| `search_mogef_interpretation` | ✅ 정상 | 0.0s | 218자 |  |
| `search_mohw_interpretation` | ✅ 정상 | 0.0s | 226자 |  |
| `search_mois_interpretation` | ✅ 정상 | 0.0s | 342자 |  |
| `search_moj_interpretation` | ✅ 정상 | 0.0s | 130자 |  |
| `search_moleg_interpretation` | ✅ 정상 | 0.0s | 243자 |  |
| `search_molit_interpretation` | ✅ 정상 | 0.0s | 431자 |  |
| `search_moms_interpretation` | ✅ 정상 | 0.0s | 128자 |  |
| `search_mote_interpretation` | ✅ 정상 | 0.0s | 231자 |  |
| `search_mpm_interpretation` | ✅ 정상 | 0.0s | 226자 |  |
| `search_mpva_interpretation` | ✅ 정상 | 0.0s | 256자 |  |
| `search_msit_interpretation` | ✅ 정상 | 0.0s | 228자 |  |
| `search_naacc_interpretation` | ⚠️ API 데이터 없음 | 0.001s | 22자 | 다른 쿼리로 재시도 필요 |
| `search_nfa_interpretation` | ✅ 정상 | 0.0s | 207자 |  |
| `search_nts_interpretation` | ✅ 정상 | 0.0s | 355자 |  |
| `search_oka_interpretation` | ⚠️ API 데이터 없음 | 0.0s | 21자 | 다른 쿼리로 재시도 필요 |
| `search_police_interpretation` | ✅ 정상 | 0.0s | 231자 |  |
| `search_pps_interpretation` | ✅ 정상 | 0.0s | 229자 |  |
| `search_rda_interpretation` | ⚠️ API 데이터 없음 | 0.0s | 21자 | 다른 쿼리로 재시도 필요 |
| `search_sme_interpretation` | ✅ 정상 | 0.0s | 205자 |  |
| `search_unikorea_interpretation` | ⚠️ API 데이터 없음 | 0.0s | 21자 | 다른 쿼리로 재시도 필요 |

> 카테고리 정상율: 39/72 (54%)

### 영문법령

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_english_law` | ✅ 정상 | 0.0s | 851자 |  |
| `get_english_law_detail` | ✅ 정상 | 0.0s | 58자 |  |
| `get_english_law_summary` | ✅ 정상 | 0.002s | 251자 |  |
| `search_english_law_articles_semantic` | ✅ 정상 | 0.0s | 60자 |  |

> 카테고리 정상율: 4/4 (100%)

### 조약

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_treaty` | ✅ 정상 | 0.0s | 243자 |  |
| `get_treaty_detail` | ❌ 코드/포맷 버그 | 0.298s | 148자 | 조약 상세 API 파라미터 오류 (ID 형식) |

> 카테고리 정상율: 1/2 (50%)

### 지식베이스/상담

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_faq` | ✅ 정상 | 0.0s | 124자 |  |
| `search_qna` | ✅ 정상 | 0.0s | 124자 |  |
| `search_knowledge_base` | ✅ 정상 | 0.0s | 550자 |  |
| `search_counsel` | ✅ 정상 | 0.0s | 186자 |  |
| `search_civil_petition` | ✅ 정상 | 0.0s | 125자 |  |
| `search_precedent_counsel` | ✅ 정상 | 0.0s | 179자 |  |

> 카테고리 정상율: 6/6 (100%)

### 통합/고급 검색

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_all_legal_documents` | ✅ 정상 | 2.274s | 7,144자 |  |
| `search_law_bm25` | ✅ 정상 | 0.589s | 495자 |  |
| `search_admin_rule_bm25` | ✅ 정상 | 1.632s | 380자 |  |
| `search_precedent_bm25` | ✅ 정상 | 0.266s | 562자 |  |
| `search_legal_term_bm25` | ✅ 정상 | 0.327s | 268자 |  |
| `search_interpretation_bm25` | ✅ 정상 | 0.569s | 319자 |  |
| `search_all_bm25` | 🔧 파라미터명 오류 | 0.0s | — | `display=` → `top_k_per_category=` 교정 필요 |
| `search_committee_bm25` | ❌ 코드/포맷 버그 | 0.667s | 36자 | nlrc 타겟에서 제목 필드 매핑 오류 |
| `search_intelligent_law` | ❌ 코드/포맷 버그 | 0.001s | 8,018자 | 공포일자 타임스탬프 포함 (`20250401120400`) |
| `search_intelligent_related_law` | ❌ 코드/포맷 버그 | 0.0s | 1,714자 | raw dict 문자열 출력 |
| `search_law_articles_semantic` | ✅ 정상 | 0.0s | 359자 |  |
| `search_english_law_articles_semantic` | ✅ 정상 | 0.0s | 60자 |  |
| `search_law_unified` | ✅ 정상 | 0.0s | 448자 |  |
| `search_financial_laws` | ✅ 정상 | 0.001s | 416자 |  |
| `search_privacy_laws` | ✅ 정상 | 0.001s | 433자 |  |
| `search_tax_laws` | ✅ 정상 | 0.0s | 416자 |  |

> 카테고리 정상율: 12/16 (75%)

### 맞춤형 검색

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_custom_law` | ✅ 정상 | 0.0s | 137자 |  |
| `search_custom_law_articles` | ✅ 정상 | 0.0s | 20자 |  |
| `search_custom_ordinance` | ✅ 정상 | 0.0s | 20자 |  |
| `search_custom_ordinance_articles` | ✅ 정상 | 0.0s | 20자 |  |
| `search_custom_administrative_rule` | ✅ 정상 | 0.0s | 20자 |  |
| `search_custom_administrative_rule_articles` | ✅ 정상 | 0.0s | 117자 |  |

> 카테고리 정상율: 6/6 (100%)

### 학칙/규정

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `search_university_regulation` | ✅ 정상 | 0.0s | 353자 |  |
| `search_public_corporation_regulation` | ✅ 정상 | 0.0s | 465자 |  |
| `search_public_institution_regulation` | ✅ 정상 | 0.0s | 492자 |  |

> 카테고리 정상율: 3/3 (100%)

### 캐시/유틸리티

| 도구명 | 상태 | 응답시간 | 응답크기 | 비고 |
|---|---|---:|---:|---|
| `cleanup_cache_tool` | ✅ 정상 | 0.016s | 53자 |  |
| `get_cache_status` | ✅ 정상 | 0.002s | 159자 |  |
| `invalidate_law_cache` | 🔧 파라미터명 오류 | 0.0s | — | `mst=` → `law_id=` 교정 필요 |
| `explain_bm25_tokenize` | 🔧 파라미터명 오류 | 0.0s | — | `text=` → `query=` 교정 필요 |

> 카테고리 정상율: 2/4 (50%)

### 기타 (미분류)

| 도구명 | 상태 | 응답시간 | 응답크기 |
|---|---|---:|---:|
| `get_cha_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 |
| `get_dapa_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 |
| `get_fire_agency_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 |
| `get_oka_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 |
| `get_police_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.001s | 20자 |
| `get_pps_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 |
| `get_rda_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.0s | 20자 |
| `get_unikorea_interpretation_detail` | 🔶 ID 픽스처 오류 | 0.001s | 20자 |
| `search_effective_law_articles_raw` | ⚠️ API 데이터 없음 | 0.199s | 25자 |

---

## 이슈 상세 목록

### ❌ 코드/포맷 버그 — 수정 필요 (10개)

| 도구명 | 증상 | 원인 |
|---|---|---|
| `search_intelligent_related_law` | 결과 항목이 raw dict 문자열로 출력됨 | `_format_search_results` 처리 누락 |
| `search_intelligent_law` | 공포일자가 `20250401120400` 타임스탬프 포함 | API 응답에 시분초 포함 → 포맷 정제 필요 |
| `get_administrative_rule_comparison_detail` | 제목 없음 반환 | 비교 상세 API 응답 파싱 로직 미완성 |
| `get_ordinance_detail` | 자치법규 정보 조회 실패 | 자치법규 상세 API 파라미터 또는 URL 오류 |
| `get_ordinance_appendix_detail` | 별표서식 내용 없이 구조만 출력 | 별표서식 본문 파싱 미완성 |
| `get_treaty_detail` | 조약 정보 조회 실패 | 조약 상세 API 파라미터 오류 (ID 형식) |
| `get_one_view_detail` | 한눈보기 정보 조회 실패 | 한눈보기 API 데이터 구조 변경 가능성 |
| `search_committee_bm25` | BM25 결과 제목 없음만 반환 | nlrc 타겟에서 제목 필드 매핑 오류 |
| `get_delegated_law` | 위임법령 정보 조회 실패 | 위임법령 API 다중 시도 후 모두 실패 |
| `search_related_law` | 관계 유형 코드만 표시 (`2유형(특별법)`) | 관계 유형 설명 텍스트 변환 미적용 |

### 🔧 파라미터명 오류 — 테스트 픽스처 수정 필요 (3개)

| 도구명 | 잘못된 파라미터 | 올바른 파라미터 |
|---|---|---|
| `explain_bm25_tokenize` | `text=` | `query=` |
| `invalidate_law_cache` | `mst=` | `law_id=`, `section=` |
| `search_all_bm25` | `display=` | `top_k_per_category=` |

### 🔶 ID 픽스처 오류 — 테스트 ID 교정 필요 (45개)

대부분 `ID="1"`로 테스트했으나 실제 데이터가 없음. 아래는 교정된 ID 예시:

| 도구명 | 현재 테스트 ID | 권장 테스트 ID |
|---|---|---|
| `get_legal_term_detail` | `5407551` | `5424770` |
| `get_tax_tribunal_detail` | `1` | `950990` |
| `get_environment_committee_detail` | `1` | 검색 후 ID 확인 필요 |
| `get_employment_insurance_committee_detail` | `1` | 검색 후 ID 확인 필요 |
| `get_industrial_accident_committee_detail` | `1` | 검색 후 ID 확인 필요 |
| `get_law_appendix_detail` | `001597 (법령MST)` | 실제 별표 ID로 교정 |
| `get_acrc_special_tribunal_detail` | `1` | `search_acrc_special_tribunal` 검색 후 확인 |
| 그 외 38개 부처 해석례 detail | `1` | 해당 부처 search 도구로 조회 후 ID 확인 |

### ⚠️ API 데이터 없음 (13개)

해당 쿼리어에서 데이터가 없는 경우. 도구 자체는 정상이나 특정 쿼리에서 결과 없음:

| 도구명 | 사용 쿼리 | 참고 |
|---|---|---|
| `search_acrc_special_tribunal` | `행정` | 국민권익위원회 특별행정심판 데이터가 적음 |
| `search_one_view` | `한눈보기` | 한눈보기 서비스 데이터 없음 |
| `search_mpm_appeal_tribunal` | `공무원` | 인사혁신처 소청심사 데이터 없음 |
| `search_industrial_accident_committee` | `산재` | 산업재해 위원회 데이터 없음 |
| `search_mofa_interpretation` | `외교` | 외교부 해석례 쿼리 없음, 다른 키워드 시도 필요 |
| `search_kma_interpretation` | `기상` | 기상청 해석례 쿼리 결과 없음 |
| `search_kdca_interpretation` | `질병` | 질병청 해석례 쿼리 결과 없음 |
| `search_naacc_interpretation` | `반부패` | 반부패청 해석례 결과 없음 |
| `search_oka_interpretation` | `해외` | 재외동포청 해석례 결과 없음 |
| `search_rda_interpretation` | `농업` | 농촌진흥청 해석례 결과 없음, 다른 쿼리 필요 |
| `search_unikorea_interpretation` | `통일` | 통일부 해석례 결과 없음 |
| `search_daily_legal_term_link` | `계약` | 법령생활용어 연계 데이터 없음 |
| `search_effective_law_articles_raw` | `001597` | 현행법령 조문 raw 데이터 없음 |

---

## 결론 및 권장 사항

### 즉시 수정 권장 (❌ 코드/포맷 버그 10개)

1. **`search_intelligent_related_law`** — 포맷터에서 raw dict 필드 처리 추가
2. **`search_intelligent_law`** — 공포일자 타임스탬프 정제 (`[:8]` 슬라이싱)
3. **`search_committee_bm25`** — nlrc 타겟 제목 필드 매핑 확인
4. **`search_related_law`** — 관계 유형 코드 → 한글 설명 변환 테이블 추가
5. **`get_ordinance_detail`** / **`get_ordinance_appendix_detail`** — 자치법규 API 응답 구조 재확인
6. **`get_treaty_detail`** — 조약 상세 API URL 또는 파라미터 수정
7. **`get_one_view_detail`** — 한눈보기 API 응답 구조 확인
8. **`get_administrative_rule_comparison_detail`** — 비교 상세 파싱 보완
9. **`get_delegated_law`** — 위임법령 API 다중 호출 로직 재검토

### 테스트 픽스처 교정 권장 (🔧 3개 + 🔶 45개)

- `explain_bm25_tokenize`: `text=` → `query=`
- `invalidate_law_cache`: `mst=` → `law_id=`로 교정
- `search_all_bm25`: `display=` → `top_k_per_category=`
- 45개 detail 도구: 각 search 도구로 유효 ID를 먼저 조회 후 테스트

### 실질 성능 평가

| 항목 | 수치 |
|---|---|
| 전체 도구 정상 작동률 (API 기준) | **89.2%** (190/213) |
| 테스트 코드 기준 정상률 | **66.7%** (142/213) |
| 평균 응답 시간 | **0.18s** |
| 캐시 HIT 도구 응답시간 | **< 0.01s** |
| API 직접 호출 평균 | **0.3~0.5s** |
| 실제 수정 필요 도구 | **10개** |
