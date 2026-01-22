# MCP 도구 품질 체크리스트

> 마지막 업데이트: 2026-01-21 12:30
> 총 도구: 186개 | 테스트 완료: 186개 (100%)
> 공식 가이드 검증: https://open.law.go.kr/LSO/openApi/guideList.do#

## 테스트 상태 범례

- ✅ 성공: 정상 동작, 데이터 반환
- ⚠️ 경고: 특수 파라미터 필요 또는 0건 반환
- 📄 HTML: JSON 미지원, HTML URL 안내
- ❌ 실패: API 에러 또는 404

---

## 1. 법령 검색 (14개)

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| search_law | law | ✅ | 핵심 도구, 정상 |
| search_english_law | elaw | ✅ | HTML 태그 포함 |
| search_effective_law | eflaw | ✅ | 시행일법령 |
| search_law_nickname | lawNm | ⚠️ | 법령별칭 - 특수 파라미터 |
| search_deleted_law_data | datDel | ⚠️ | 삭제데이터 - 특수 파라미터 |
| search_law_articles | joRltLstrm | ⚠️ | 조문-용어 - 조문번호 필요 |
| search_old_and_new_law | lstrmRltJo | ⚠️ | 용어-조문 - 용어ID 필요 |
| search_related_law | lsRlt | ⚠️ | 연관법령 - MST 필요 |
| search_law_change_history | lsHstInf | 📄 | HTML만 지원 |
| search_one_view | onViewLs | 📄 | HTML만 지원 |
| search_law_system_diagram | lsInfoP | 📄 | HTML만 지원 |
| search_law_ordinance_link | lsLnkOrd | 📄 | HTML만 지원 |
| search_ordinance_law_link | ordLnkLs | 📄 | HTML만 지원 |
| search_law_unified | lsNmUnfi | ⚠️ | 통합법령 - 특수 파라미터 |

---

## 2. 법령 상세조회 (17개)

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| get_law_detail | law | ✅ | 핵심 도구 |
| get_english_law_detail | elaw | ✅ | 영문법령 |
| get_law_summary | law | ✅ | 요약 |
| get_english_law_summary | elaw | ✅ | 영문 요약 |
| get_law_article_by_key | law | ✅ | 조문별 |
| get_law_articles_range | law | ✅ | 조문 범위 |
| get_law_articles_summary | law | ✅ | 조문 요약 |
| get_law_article_detail | law | ✅ | 조문 상세 |
| get_delegated_law | law | ✅ | 위임법령 |
| get_effective_law_articles | law | ✅ | 시행조문 |
| get_current_law_articles | law | ✅ | 현행조문 |
| get_effective_law_detail | law | ✅ | 시행상세 |
| get_law_appendix_detail | law | ✅ | 별표 |
| get_law_system_diagram_detail | lsInfoP | 📄 | HTML |
| get_law_system_diagram_full | lsInfoP | 📄 | HTML |
| compare_law_versions | law | ✅ | 버전비교 |
| compare_article_before_after | law | ✅ | 조문비교 |

---

## 3. 판례 (8개)

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| search_precedent | prec | ✅ | 핵심 도구 |
| search_constitutional_court | detc | ✅ | 헌재결정례 |
| search_legal_interpretation | expc | ✅ | 법령해석례 |
| search_administrative_trial | decc | ✅ | 행정심판례 |
| get_precedent_detail | prec | ✅ | JSON+HTML 지원 |
| get_constitutional_court_detail | detc | ✅ | JSON |
| get_legal_interpretation_detail | expc | ✅ | JSON |
| get_administrative_trial_detail | decc | ✅ | JSON |

---

## 4. 위원회결정문 (24개)

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| search_privacy_committee | ppc | ✅ | 개인정보위 |
| search_financial_committee | fsc | ✅ | 금융위 |
| search_monopoly_committee | ftc | ✅ | 공정위 |
| search_anticorruption_committee | acr | ✅ | 국민권익위 (635건, 검색어 선택) |
| search_labor_committee | nlrc | ✅ | 노동위 |
| search_environment_committee | ecc | ✅ | 환경분쟁위 |
| search_securities_committee | sfc | ✅ | 증권위 |
| search_human_rights_committee | nhrck | ✅ | 인권위 |
| search_broadcasting_committee | kcc | ✅ | 방송위 |
| search_industrial_accident_committee | iaciac | ✅ | 산재위 |
| search_land_tribunal | oclt | ✅ | 토지위 |
| search_employment_insurance_committee | eiac | ✅ | 고용보험위 |
| get_privacy_committee_detail | ppc | ✅ | |
| get_financial_committee_detail | fsc | ✅ | |
| get_monopoly_committee_detail | ftc | ✅ | |
| get_anticorruption_committee_detail | acr | ✅ | |
| get_labor_committee_detail | nlrc | ✅ | |
| get_environment_committee_detail | ecc | ✅ | |
| get_securities_committee_detail | sfc | ✅ | |
| get_human_rights_committee_detail | nhrck | ✅ | |
| get_broadcasting_committee_detail | kcc | ✅ | |
| get_industrial_accident_committee_detail | iaciac | ✅ | |
| get_land_tribunal_detail | oclt | ✅ | |
| get_employment_insurance_committee_detail | eiac | ✅ | |

---

## 5. 행정규칙 (4개)

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| search_administrative_rule | admrul | ✅ | 핵심 도구 |
| get_administrative_rule_detail | admrul | ✅ | |
| search_administrative_rule_comparison | admrulCmp | ⚠️ | 비교 - 특수 파라미터 |
| get_administrative_rule_comparison_detail | admrulCmp | ⚠️ | |

---

## 6. 자치법규 (4개)

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| search_local_ordinance | ordin | ✅ | 핵심 도구 |
| get_local_ordinance_detail | ordin | ✅ | |
| search_ordinance_appendix | ordin | ⚠️ | 별표 - 특수 파라미터 |
| search_linked_ordinance | lnkOrdin | ⚠️ | 연계 - 특수 파라미터 |

---

## 7. 조약/학칙/공공기관 (6개)

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| search_treaty | trty | ✅ | 조약 |
| get_treaty_detail | trty | ✅ | |
| search_university_regulation | schl | ⚠️ | 학칙 |
| search_public_corporation_regulation | pubcorp | ⚠️ | 공공기관 |
| search_public_institution_regulation | pubinst | ⚠️ | 공공기관 |
| get_ordinance_appendix_detail | ordin | ⚠️ | 자치법규 별표 |

---

## 8. 법령용어 (8개)

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| search_legal_term | lstrm | ✅ | JSON 정상 (452건) |
| search_legal_term_ai | lstrmAI | ⚠️ | AI 용어 (데이터 없음) |
| search_daily_legal_term_link | dlytrmRlt | 📄 | HTML URL 안내 |
| search_daily_term | dlytrmRlt | 📄 | HTML URL 안내 |
| search_legal_daily_term_link | lstrmRlt | 📄 | HTML URL 안내 |
| search_legal_term_article_link | lstrmRlt | 📄 | HTML URL 안내 (ID 필요) |
| search_article_legal_term_link | joRltLstrm | 📄 | HTML URL 안내 (ID 필요) |
| get_legal_term_detail | lstrm | ✅ | JSON 정상 (ID 필요) |

---

## 9. 지식베이스 (6개) - HTML 전용, URL 안내 방식

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| search_knowledge_base | - | 📄 | HTML URL 통합 안내 |
| search_faq | faq | 📄 | HTML URL 안내 |
| search_qna | qna | 📄 | HTML URL 안내 |
| search_counsel | counsel | 📄 | HTML URL 안내 + 대안 제시 |
| search_precedent_counsel | precCounsel | 📄 | HTML URL 안내 + 대안 제시 |
| search_civil_petition | civil | 📄 | HTML URL 안내 |

---

## 10. 맞춤형 (6개) - vcode(분류코드) 필수

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| search_custom_law | couseLs | ✅ | vcode 필수, 가이드 안내 |
| search_custom_law_articles | couseLs | ✅ | vcode 필수 |
| search_custom_ordinance | couseOrdin | ✅ | vcode 필수 |
| search_custom_ordinance_articles | couseOrdin | ✅ | vcode 필수 |
| search_custom_administrative_rule | couseAdmrul | ✅ | vcode 필수 |
| search_custom_precedent | cousePrec | ✅ | vcode 필수 |

---

## 11. 중앙부처해석 (57개) ✅ 전체 활성화 완료

### 기존 도구 (ministry_interpretation_tools.py - 19개)

| 도구명 | target | 상태 | 데이터 건수 |
|--------|--------|------|-----------|
| search_moef_interpretation | moefCgmExpc | ✅ | 2,297 |
| search_molit_interpretation | molitCgmExpc | ✅ | 5,660 |
| search_moel_interpretation | moelCgmExpc | ✅ | 9,573 |
| search_mof_interpretation | mofCgmExpc | ✅ | 547 |
| search_mohw_interpretation | mohwCgmExpc | ✅ | 142+ |
| search_moe_interpretation | moeCgmExpc | ✅ | 40+ |
| search_mote_interpretation | motieCgmExpc | ✅ | 32 |
| search_maf_interpretation | mafraCgmExpc | ✅ | 32 |
| search_moms_interpretation | mndCgmExpc | ✅ | 40 |
| search_sme_interpretation | mssCgmExpc | ✅ | 4 |
| search_nfa_interpretation | kfsCgmExpc | ✅ | 623 |
| search_nts_interpretation | ntsCgmExpc | ✅ | 135,765 |
| search_kcs_interpretation | kcsCgmExpc | ✅ | 1,279 |
| search_korea_interpretation | koreaCgmExpc | ⚠️ | 검색어 조정 |
| search_mssp_interpretation | msspCgmExpc | ⚠️ | 검색어 조정 |
| search_korail_interpretation | korailCgmExpc | ⚠️ | 검색어 조정 |
| get_moef_interpretation_detail | moefCgmExpc | ✅ | |
| get_nts_interpretation_detail | ntsCgmExpc | ✅ | |
| get_kcs_interpretation_detail | kcsCgmExpc | ✅ | |

### 확장 도구 (ministry_interpretation_tools_extended.py - 44개)

| 도구명 | target | 상태 | 데이터 건수 |
|--------|--------|------|-----------|
| search_mois_interpretation | moisCgmExpc | ✅ | 4,039 |
| search_me_interpretation | meCgmExpc | ✅ | 2,291 |
| search_mcst_interpretation | mcstCgmExpc | ✅ | 44 |
| search_moj_interpretation | mojCgmExpc | ✅ | 1+ |
| search_mogef_interpretation | mogefCgmExpc | ✅ | 4+ |
| search_mofa_interpretation | mofaCgmExpc | ✅ | 17 |
| search_unikorea_interpretation | mouCgmExpc | ✅ | 6 |
| search_moleg_interpretation | molegCgmExpc | ✅ | 17 |
| search_mfds_interpretation | mfdsCgmExpc | ✅ | 1,216 |
| search_mpm_interpretation | mpmCgmExpc | ✅ | 10 |
| search_kma_interpretation | kmaCgmExpc | ✅ | 21 |
| search_cha_interpretation | khaCgmExpc | ⚠️ | 0건 |
| search_rda_interpretation | rdaCgmExpc | ✅ | 6 |
| search_police_interpretation | knpaCgmExpc | ⚠️ | 0건 |
| search_dapa_interpretation | dapaCgmExpc | ✅ | 46 |
| search_mma_interpretation | mmaCgmExpc | ✅ | 1+ |
| search_fire_agency_interpretation | nfaCgmExpc | ✅ | 328 |
| search_pps_interpretation | ppsCgmExpc | ✅ | 23 |
| search_kdca_interpretation | kdcaCgmExpc | ⚠️ | 0건 |
| search_kcg_interpretation | kcgCgmExpc | ⚠️ | 0건 |
| search_mpva_interpretation | mpvaCgmExpc | ✅ | 116 |
| **search_kostat_interpretation** | **kostatCgmExpc** | **✅** | **4** |
| **search_kipo_interpretation** | **kipoCgmExpc** | **✅** | **186** |
| **search_naacc_interpretation** | **naaccCgmExpc** | **✅** | **37** |
| get_mois_interpretation_detail | moisCgmExpc | ✅ | |
| get_me_interpretation_detail | meCgmExpc | ✅ | |
| get_mcst_interpretation_detail | mcstCgmExpc | ✅ | |
| get_moj_interpretation_detail | mojCgmExpc | ✅ | |
| get_mogef_interpretation_detail | mogefCgmExpc | ✅ | |
| get_mofa_interpretation_detail | mofaCgmExpc | ✅ | |
| get_unikorea_interpretation_detail | mouCgmExpc | ✅ | |
| get_moleg_interpretation_detail | molegCgmExpc | ✅ | |
| get_mfds_interpretation_detail | mfdsCgmExpc | ✅ | |
| get_mpm_interpretation_detail | mpmCgmExpc | ✅ | |
| get_kma_interpretation_detail | kmaCgmExpc | ✅ | |
| get_cha_interpretation_detail | khaCgmExpc | ⚠️ | |
| get_rda_interpretation_detail | rdaCgmExpc | ✅ | |
| get_police_interpretation_detail | knpaCgmExpc | ⚠️ | |
| get_dapa_interpretation_detail | dapaCgmExpc | ✅ | |
| get_mma_interpretation_detail | mmaCgmExpc | ✅ | |
| get_fire_agency_interpretation_detail | nfaCgmExpc | ✅ | |
| get_pps_interpretation_detail | ppsCgmExpc | ✅ | |
| get_kdca_interpretation_detail | kdcaCgmExpc | ⚠️ | |
| get_kcg_interpretation_detail | kcgCgmExpc | ⚠️ | |
| get_mpva_interpretation_detail | mpvaCgmExpc | ✅ | |
| **get_kostat_interpretation_detail** | **kostatCgmExpc** | **✅** | |
| **get_kipo_interpretation_detail** | **kipoCgmExpc** | **✅** | |
| **get_naacc_interpretation_detail** | **naaccCgmExpc** | **✅** | |

---

## 12. 특별행정심판 (8개)

| 도구명 | target | 상태 | 데이터 건수 |
|--------|--------|------|-----------|
| search_tax_tribunal | ttSpecialDecc | ✅ | 조세심판원 |
| search_maritime_safety_tribunal | kmstSpecialDecc | ✅ | 해양안전심판원 |
| get_tax_tribunal_detail | ttSpecialDecc | ✅ | |
| get_maritime_safety_tribunal_detail | kmstSpecialDecc | ✅ | |
| **search_acrc_special_tribunal** | **acrSpecialDecc** | **✅** | **85건** |
| **search_mpm_appeal_tribunal** | **adapSpecialDecc** | **✅** | **210건** |
| **get_acrc_special_tribunal_detail** | **acrSpecialDecc** | **✅** | |
| **get_mpm_appeal_tribunal_detail** | **adapSpecialDecc** | **✅** | |

---

## 13. AI/통합 도구 (10개)

| 도구명 | target | 상태 | 비고 |
|--------|--------|------|------|
| search_legal_ai | - | ✅ | AI 통합검색 |
| search_all_legal_documents | - | ✅ | 전체검색 |
| get_practical_law_guide | - | ✅ | 실무가이드 |
| search_law_articles_semantic | - | ✅ | 시맨틱 검색 |
| search_english_law_articles_semantic | - | ✅ | 영문 시맨틱 |
| search_financial_laws | - | ✅ | 금융법 특화 |
| search_tax_laws | - | ✅ | 세법 특화 |
| search_privacy_laws | - | ✅ | 개인정보법 특화 |
| search_law_with_cache | law | ✅ | 캐싱 |

---

## 결과 요약

| 카테고리 | 총 도구 | 성공 | 경고 | HTML전용 |
|---------|--------|------|------|---------|
| 법령 검색 | 14 | 3 | 6 | 5 |
| 법령 상세조회 | 17 | 15 | 0 | 2 |
| 판례 | 8 | 8 | 0 | 0 |
| 위원회결정문 | 24 | 24 | 0 | 0 |
| 행정규칙 | 4 | 2 | 2 | 0 |
| 자치법규 | 4 | 2 | 2 | 0 |
| 조약/학칙 | 6 | 2 | 4 | 0 |
| 법령용어 | 8 | 2 | 1 | 5 |
| 지식베이스 | 6 | 0 | 0 | 6 |
| 맞춤형 | 6 | 6 | 0 | 0 |
| 중앙부처해석 | 63 | 55 | 8 | 0 |
| 특별행정심판 | 8 | 8 | 0 | 0 |
| AI/통합 | 10 | 9 | 1 | 0 |
| **합계** | **186** | **136** | **24** | **18** |

**JSON 성공률**: 136/186 = 73.1%
**실질 작동률**: 178/186 = 95.7% (HTML URL 안내 포함)

> 참고: HTML 전용 API는 직접 웹 URL을 안내하여 사용자가 브라우저에서 확인 가능

---

## 개선 참고사항

### HTML 전용 API (18개)
- **법령 관련 (5개)**: 법령연혁, 법령한눈에보기, 법령체계도 등
- **법령용어 연계 (5개)**: 일상용어-법령용어 연계 등
- **지식베이스 (6개)**: FAQ, QNA, 상담, 민원 등
- **법령 상세 (2개)**: 법령체계도 상세 등

→ HTML URL을 직접 안내하여 브라우저에서 확인 가능

### 경고 상태 (24개)
- **특수 파라미터 필요**: vcode, ID, MST 등 필수 파라미터 필요
- **데이터 없음**: 일부 중앙부처해석은 0건 (국가유산청, 경찰청, 질병관리청, 해양경찰청)

### 최근 개선 (2026-01-21)
- `search_anticorruption_committee`: 검색어 선택 가능 (전체 목록 635건)
- 지식베이스 도구 6개: HTML URL 안내 및 대안 도구 제시
- 맞춤형 도구 6개: vcode 필수 파라미터 안내 개선

---

## 버전 이력

- 2026-01-21: 공식 가이드에서 누락된 3개 부처 추가 (국가데이터처, 지식재산처, 행정중심복합도시건설청)
- 2026-01-21: 특별행정심판 2개 기관 추가 (국민권익위원회, 인사혁신처 소청심사위원회)
- 2026-01-21: SKILL.md에 공식 가이드 직접 검증 절차 추가
- 2026-01-20: 전체 중앙부처해석 API 활성화 (35개 부처)
- 2026-01-20: 중복 도구 정리 (산림청, 국방부, 농림축산식품부)
- 2026-01-20: Referer 헤더 추가로 API 호출 문제 해결
- 2026-01-20: 올바른 target 값 검증 및 수정 완료
