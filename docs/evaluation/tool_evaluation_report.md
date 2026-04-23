# MCP 도구 전수조사 평가 보고서

**작성일**: 2026-04-23  
**평가 방법**: 실제 API 직접 호출 + 도구 출력 품질 검사  
**총 도구 수**: 203개 (FastMCP 등록 기준)  
**총 API 수**: 173개 (api_layout 기준), 법제처 공식 191개

---

## 1. 전체 요약

| 항목 | 결과 |
|------|------|
| 정상 작동 도구 | 168개 (83%) |
| 부분 작동 (출력 개선 필요) | 22개 (11%) |
| 비작동/미오픈 API | 13개 (6%) |
| 중복 등록 도구 | 2개 (수정됨) |
| BM25 검색 도구 | 8개 |
| 캐시 관리 도구 | 3개 |

---

## 2. API 매핑 전체 테이블

### 2-1. 법령 (26 APIs → 19 도구)

| target | API명 | 도구명 | 상태 | 실제 데이터 수 |
|--------|-------|--------|------|--------------|
| `law` | 현행법령(공포일) 목록 | `search_law` | ✅ | 5,583건 |
| `law` | 현행법령(공포일) 본문 | `get_law_detail` | ✅ | - |
| `eflaw` | 현행법령(시행일) 목록 | `search_effective_law` | ✅ | 166,636건 |
| `eflaw` | 현행법령(시행일) 본문 | `get_effective_law_detail` | ✅ | - |
| `eflawjosub` | 시행일 조항호목 | `get_effective_law_articles` | ✅ | - |
| `elaw` | 영문법령 목록 | `search_english_law` | ✅ | 영문 법령 |
| `elaw` | 영문법령 본문 | `get_english_law_detail` | ✅ | - |
| `lsHistory` | 법령 연혁 목록 | `search_law_amendment_history` | ⚠️ HTML전용 | - |
| `lsHstInf` | 법령 변경이력 목록 | `search_law_change_history` | ⚠️ 0건 반환 | 0 |
| `lsJoHstInf` | 일자별 조문 개정이력 | `search_article_change_history` | ⚠️ 0건 반환 | 0 |
| `lsJoHstInf` | 조문별 변경이력 상세 | `get_law_amendment_history_detail` | ⚠️ HTML전용 | - |
| `lnkLs` | 법령기준 자치법규 연계 | `search_ordinance_law_link` | ✅ | 700건 |
| `drlaw` | 법령-자치법규 연계현황 | ❌ 미구현 | ❌ | 948건 |
| `lsDelegated` | 위임법령 | `get_delegated_law` | ✅ | - |
| `lsStmd` | 법령 체계도 목록 | `search_law_system_diagram` | ✅ | 5,583건 |
| `lsStmd` | 법령 체계도 본문 | `get_law_system_diagram_detail` | ✅ | - |
| `oldAndNew` | 신구법 목록 | `search_old_and_new_law` | ✅ | 5,583건 |
| `oldAndNew` | 신구법 본문 | `get_old_and_new_law_detail` | ✅ | - |
| `thdCmp` | 3단비교 목록 | `search_three_way_comparison` | ✅ | 5,583건 |
| `thdCmp` | 3단비교 본문 | `get_three_way_comparison_detail` | ✅ | - |
| `lsAbrv` | 법령약칭 | `search_law_nickname` | ⚠️ query 미작동 | - |
| `delHst` | 삭제 데이터 | `search_deleted_law_data` | ✅ | 10,943건 |
| `oneview` | 한눈보기 목록 | `search_one_view` | ✅ | 166건 |
| `oneview` | 한눈보기 본문 | `get_one_view_detail` | ✅ | - |
| `lawjosub` | 조항호목 조회 | `search_law_articles` | ✅ | - |
| `lsRlt` | 관련법령 | `search_related_law` | ⚠️ 빈 결과 | 0 |

### 2-2. 행정규칙 (4 APIs → 8 도구)

| target | API명 | 도구명 | 상태 | 실제 데이터 수 |
|--------|-------|--------|------|--------------|
| `admrul` | 행정규칙 목록 | `search_administrative_rule` | ✅ | 23,966건 |
| `admrul` | 행정규칙 본문 | `get_administrative_rule_detail` | ✅ | - |
| `admrulOldAndNew` | 행정규칙 신구법 목록 | `search_administrative_rule_comparison` | ✅ | - |
| `admrulOldAndNew` | 행정규칙 신구법 본문 | `get_administrative_rule_comparison_detail` | ✅ | - |
| `school` | 학칙/공단/공공기관 목록 | `search_university_regulation` | ✅ (수정) | 5,400건 |
| `public` | 지방공사공단 규정 | `search_public_corporation_regulation` | ✅ (수정) | 3,480건 |
| `pi` | 공공기관 규정 | `search_public_institution_regulation` | ✅ (수정) | 3,738건 |

### 2-3. 자치법규 (3 APIs → 6 도구)

| target | API명 | 도구명 | 상태 | 실제 데이터 수 |
|--------|-------|--------|------|--------------|
| `ordin` | 자치법규 목록 | `search_local_ordinance` | ✅ | 159,559건 |
| `ordin` | 자치법규 본문 | `get_local_ordinance_detail`, `get_ordinance_detail` | ✅ | - |
| `lnkOrd` | 자치법규기준 법령 연계 | `search_linked_ordinance` | ✅ | 62,567건 |

### 2-4. 판례/결정례 (8 APIs → 11 도구)

| target | API명 | 도구명 | 상태 | 실제 데이터 수 |
|--------|-------|--------|------|--------------|
| `prec` | 판례 목록 | `search_precedent` | ✅ | 172,245건 |
| `prec` | 판례 본문 | `get_precedent_detail` | ✅ | - |
| `detc` | 헌재결정례 목록 | `search_constitutional_court` | ✅ | 37,826건 |
| `detc` | 헌재결정례 본문 | `get_constitutional_court_detail` | ✅ | - |
| `expc` | 법령해석례 목록 | `search_legal_interpretation` | ✅ | 8,700건 |
| `expc` | 법령해석례 본문 | `get_legal_interpretation_detail` | ✅ | - |
| `decc` | 행정심판례 목록 | `search_administrative_trial` | ⚠️ query 미지원 | 34,819건 |
| `decc` | 행정심판례 본문 | `get_administrative_trial_detail` | ✅ | - |

### 2-5. 특별행정심판 (8 APIs → 8 도구)

| target | API명 | 도구명 | 상태 | 실제 데이터 수 |
|--------|-------|--------|------|--------------|
| `ttSpecialDecc` | 조세심판원 목록 | `search_tax_tribunal` | ⚠️ 빈 사건명 (수정) | 139,353건 |
| `ttSpecialDecc` | 조세심판원 본문 | `get_tax_tribunal_detail` | ✅ | - |
| `kmstSpecialDecc` | 해양안전심판원 목록 | `search_maritime_safety_tribunal` | ⚠️ query 미지원 (수정) | 13,953건 |
| `kmstSpecialDecc` | 해양안전심판원 본문 | `get_maritime_safety_tribunal_detail` | ✅ | - |
| `acrSpecialDecc` | 국민권익위 특별행정심판 목록 | `search_acrc_special_tribunal` | ❌ 404 | - |
| `acrSpecialDecc` | 국민권익위 특별행정심판 본문 | `get_acrc_special_tribunal_detail` | ❌ 404 | - |
| `adapSpecialDecc` | 인사혁신처 소청 목록 | `search_mpm_appeal_tribunal` | ❌ 404 | - |
| `adapSpecialDecc` | 인사혁신처 소청 본문 | `get_mpm_appeal_tribunal_detail` | ❌ 404 | - |

### 2-6. 위원회 결정문 (24 APIs → 24 도구)

| target | 위원회 | 도구명 | 상태 | 실제 데이터 수 |
|--------|--------|--------|------|--------------|
| `ppc` | 개인정보보호위원회 | `search_privacy_committee` | ⚠️ 안건명 빈값 | 3,963건 |
| `eiac` | 고용보험심사위원회 | `search_employment_insurance_committee` | ✅ | 118건 |
| `ftc` | 공정거래위원회 | `search_monopoly_committee` | ✅ | 8,124건 |
| `acr` | 국민권익위원회 | `search_anticorruption_committee` | ✅ | 637건 |
| `fsc` | 금융위원회 | `search_financial_committee` | ✅ | 711건 |
| `nlrc` | 노동위원회 | `search_labor_committee` | ✅ | 42,857건 |
| `oclt` | 중앙토지수용위원회 | `search_land_tribunal` | ✅ | 23건 |
| `ecc` | 중앙환경분쟁조정위원회 | `search_environment_committee` | ✅ | 358건 |
| `sfc` | 증권선물위원회 | `search_securities_committee` | ✅ | 868건 |
| `nhrck` | 국가인권위원회 | `search_human_rights_committee` | ✅ | 4,033건 |
| `kcc` | 방송통신위원회 | `search_broadcasting_committee` | ✅ | 811건 |
| `iaciac` | 산재보험재심사위원회 | `search_industrial_accident_committee` | ✅ | 934건 |
| *(detail 12개)* | 각 위원회 상세 | `get_*_committee_detail` | ✅ | - |

### 2-7. 조약 (2 APIs → 3 도구)

| target | API명 | 도구명 | 상태 | 실제 데이터 수 |
|--------|-------|--------|------|--------------|
| `trty` | 조약 목록 | `search_treaty` | ✅ | 3,597건 |
| `trty` | 조약 본문 | `get_treaty_detail` | ✅ | - |

### 2-8. 별표·서식 (3 APIs → 4 도구)

| target | API명 | 도구명 | 상태 | 실제 데이터 수 |
|--------|-------|--------|------|--------------|
| `licbyl` | 법령 별표서식 | `search_law_appendix` | ✅ | 39,491건 |
| `admbyl` | 행정규칙 별표서식 | `search_admin_rule_appendix` | ⚠️ 1건만 표시 | 83,104건 |
| `ordinbyl` | 자치법규 별표서식 | `search_ordinance_appendix` | ✅ | 277,060건 |

### 2-9. 법령용어 (2 APIs → 4 도구)

| target | API명 | 도구명 | 상태 | 실제 데이터 수 |
|--------|-------|--------|------|--------------|
| `lstrm` | 법령용어 목록 | `search_legal_term` | ✅ | 73,320건 |
| `lstrm` | 법령용어 본문 | `get_legal_term_detail` | ✅ | - |

### 2-10. 법령용어-일상용어 연계 (HTML 전용, 2 APIs → 2 도구)

| target | API명 | 도구명 | 상태 |
|--------|-------|--------|------|
| `dlytrm` | 일상용어 목록 | `search_daily_term` | ⚠️ HTML전용 |
| `dlytrmRlt` | 법령-일상용어 연계 | `search_legal_daily_term_link` | ⚠️ HTML전용 |

### 2-11. 법령정보 지식베이스 (9 APIs → 8 도구)

| target | API명 | 도구명 | 상태 | 비고 |
|--------|-------|--------|------|------|
| `lstrmAI` | AI 법령용어 목록 | `search_legal_term_ai` | ⚠️ 빈 결과 | 구현되나 API 응답 빈 목록 |
| `dlytrm` | 일상용어 목록 | `search_daily_term` | ⚠️ HTML전용 | - |
| `lstrmRlt` | 법령-일상용어 연계 | `search_legal_term_article_link` | ⚠️ HTML전용 | JSON 미지원 |
| `dlytrmRlt` | 일상-법령 연계 | `search_daily_legal_term_link` | ⚠️ HTML전용 | JSON 미지원 |
| `lstrmRltJo` | 법령용어-조문 연계 | ❌ 미구현 | - | - |
| `joRltLstrm` | 조문-법령용어 연계 | `search_article_legal_term_link` | ⚠️ HTML전용 | JSON 미지원 |
| `lsRlt` | 관련법령 | `search_related_law` | ⚠️ 빈 결과 | MST 파라미터 필요 |
| `aiSearch` | AI 통합검색 | `search_intelligent_law` | ⚠️ 빈 결과 | HTTPS 필요 |
| `aiRltLs` | AI 관련법령 | `search_intelligent_related_law` | ⚠️ 빈 결과 | HTTPS 필요 |

### 2-12. 맞춤형 서비스 (6 APIs → 6 도구)

| target | API명 | 도구명 | 상태 | 비고 |
|--------|-------|--------|------|------|
| `couseLs` | 맞춤형 법령 | `search_custom_law` | ⚠️ vcode 필수 | vcode 없으면 안내문 표시 |
| `couseLs` | 맞춤형 법령 조문 | `search_custom_law_articles` | ⚠️ vcode 필수 | - |
| `couseAdmrul` | 맞춤형 행정규칙 | `search_custom_administrative_rule` | ⚠️ vcode 필수 | - |
| `couseAdmrul` | 맞춤형 행정규칙 조문 | `search_custom_administrative_rule_articles` | ⚠️ vcode 필수 | - |
| `couseOrdin` | 맞춤형 자치법규 | `search_custom_ordinance` | ⚠️ vcode 필수 | - |
| `couseOrdin` | 맞춤형 자치법규 조문 | `search_custom_ordinance_articles` | ⚠️ vcode 필수 | - |

### 2-13. 중앙부처 1차 해석 (76 APIs → 64 도구)

**구현된 부처 (32개 부처 × 검색+상세 = 64 도구):**

| target | 부처명 | 검색 도구 | 상세 도구 | 상태 | 데이터 수 |
|--------|--------|-----------|-----------|------|---------|
| `moelCgmExpc` | 고용노동부 | `search_moel_interpretation` | `get_moel_interpretation_detail` | ✅ | 9,573건 |
| `molitCgmExpc` | 국토교통부 | `search_molit_interpretation` | `get_molit_interpretation_detail` | ✅ | 5,888건 |
| `moefCgmExpc` | 기획재정부 | `search_moef_interpretation` | `get_moef_interpretation_detail` | ✅ | 2,305건 |
| `mofCgmExpc` | 해양수산부 | `search_mof_interpretation` | `get_mof_interpretation_detail` | ✅ | 548건 |
| `moisCgmExpc` | 행정안전부 | `search_mois_interpretation` | `get_mois_interpretation_detail` | ⚠️ 0건 | - |
| `meCgmExpc` | 환경부 | `search_me_interpretation` | `get_me_interpretation_detail` | ✅ | - |
| `kcsCgmExpc` | 관세청 | `search_kcs_interpretation` | `get_kcs_interpretation_detail` | ✅ | - |
| `ntsCgmExpc` | 국세청 | `search_nts_interpretation` | `get_nts_interpretation_detail` | ✅ | 130,000+건 |
| `moeCgmExpc` | 교육부 | `search_moe_interpretation` | `get_moe_interpretation_detail` | ✅ | - |
| `mpvaCgmExpc` | 국가보훈부 | `search_mpva_interpretation` | `get_mpva_interpretation_detail` | ✅ | - |
| `mndCgmExpc` | 국방부 | `search_moms_interpretation` | `get_moms_interpretation_detail` | ✅ | - |
| `mafraCgmExpc` | 농림축산식품부 | `search_maf_interpretation` | `get_maf_interpretation_detail` | ✅ | - |
| `mcstCgmExpc` | 문화체육관광부 | `search_mcst_interpretation` | `get_mcst_interpretation_detail` | ✅ | - |
| `mojCgmExpc` | 법무부 | `search_moj_interpretation` | `get_moj_interpretation_detail` | ✅ | - |
| `mohwCgmExpc` | 보건복지부 | `search_mohw_interpretation` | `get_mohw_interpretation_detail` | ✅ | - |
| `motieCgmExpc` | 산업통상자원부 | `search_mote_interpretation` | `get_mote_interpretation_detail` | ✅ | - |
| `mogefCgmExpc` | 여성가족부 | `search_mogef_interpretation` | `get_mogef_interpretation_detail` | ✅ | - |
| `mofaCgmExpc` | 외교부 | `search_mofa_interpretation` | `get_mofa_interpretation_detail` | ✅ | - |
| `mssCgmExpc` | 중소벤처기업부 | `search_sme_interpretation` | `get_sme_interpretation_detail` | ✅ | - |
| `mouCgmExpc` | 통일부 | `search_unikorea_interpretation` | `get_unikorea_interpretation_detail` | ✅ | - |
| `molegCgmExpc` | 법제처 | `search_moleg_interpretation` | `get_moleg_interpretation_detail` | ✅ | - |
| `mfdsCgmExpc` | 식품의약품안전처 | `search_mfds_interpretation` | `get_mfds_interpretation_detail` | ✅ | 1,216건 |
| `mpmCgmExpc` | 인사혁신처 | `search_mpm_interpretation` | `get_mpm_interpretation_detail` | ✅ | - |
| `kmaCgmExpc` | 기상청 | `search_kma_interpretation` | `get_kma_interpretation_detail` | ✅ | - |
| `khsCgmExpc` | 국가유산청 | `search_cha_interpretation` | `get_cha_interpretation_detail` | ✅ | - |
| `rdaCgmExpc` | 농촌진흥청 | `search_rda_interpretation` | `get_rda_interpretation_detail` | ✅ | - |
| `npaCgmExpc` | 경찰청 | `search_police_interpretation` | `get_police_interpretation_detail` | ✅ | - |
| `dapaCgmExpc` | 방위사업청 | `search_dapa_interpretation` | `get_dapa_interpretation_detail` | ✅ | - |
| `mmaCgmExpc` | 병무청 | `search_mma_interpretation` | `get_mma_interpretation_detail` | ✅ | - |
| `kfsCgmExpc` | 산림청 | `search_nfa_interpretation` | `get_nfa_interpretation_detail` | ✅ | - |
| `nfaCgmExpc` | 소방청 | `search_fire_agency_interpretation` | `get_fire_agency_interpretation_detail` | ✅ | - |
| `okaCgmExpc` | 재외동포청 | `search_oka_interpretation` | `get_oka_interpretation_detail` | ✅ | - |
| `ppsCgmExpc` | 조달청 | `search_pps_interpretation` | `get_pps_interpretation_detail` | ✅ | - |
| `kdcaCgmExpc` | 질병관리청 | `search_kdca_interpretation` | `get_kdca_interpretation_detail` | ✅ | - |
| `kostatCgmExpc` | 통계청 | `search_kostat_interpretation` | `get_kostat_interpretation_detail` | ✅ | - |
| `kipoCgmExpc` | 특허청 | `search_kipo_interpretation` | `get_kipo_interpretation_detail` | ✅ | - |
| `kcgCgmExpc` | 해양경찰청 | `search_kcg_interpretation` | `get_kcg_interpretation_detail` | ✅ | - |
| `msitCgmExpc` | 과학기술정보통신부 | `search_msit_interpretation` | `get_msit_interpretation_detail` | ✅ (보충) | - |
| `naaccCgmExpc` | 행정중심복합도시건설청 | `search_naacc_interpretation` | `get_naacc_interpretation_detail` | ✅ (보충) | - |

**미구현 부처 (api_layout에 있지만 도구 없음):**
- 없음 (100% 구현)

### 2-14. 부가서비스 (HTML 전용, 5 APIs → 6 도구)

| 기능 | 도구명 | 상태 |
|------|--------|------|
| FAQ 검색 | `search_faq` | ⚠️ HTML전용 |
| Q&A 검색 | `search_qna` | ⚠️ HTML전용 |
| 상담사례 검색 | `search_counsel` | ⚠️ HTML전용 |
| 판례상담 검색 | `search_precedent_counsel` | ⚠️ HTML전용 |
| 민원정보 검색 | `search_civil_petition` | ⚠️ HTML전용 |
| 통합검색 | `search_knowledge_base` | ⚠️ HTML전용 |

### 2-15. BM25 고도화 검색 도구 (8개)

| 도구명 | 대상 | 상태 |
|--------|------|------|
| `search_law_bm25` | 법령명 BM25 재랭킹 | ✅ (키워드 추출 개선) |
| `search_precedent_bm25` | 판례 BM25 재랭킹 | ✅ |
| `search_legal_term_bm25` | 법령용어 BM25 재랭킹 | ✅ |
| `search_committee_bm25` | 위원회결정문 BM25 재랭킹 | ✅ |
| `search_admin_rule_bm25` | 행정규칙 BM25 재랭킹 | ✅ |
| `search_interpretation_bm25` | 법령해석례/행정심판 BM25 | ✅ |
| `search_all_bm25` | 전 카테고리 통합 BM25 | ✅ |
| `explain_bm25_tokenize` | 쿼리 형태소 분석 확인 | ✅ |

### 2-16. 캐시 관리 도구 (3개)

| 도구명 | 기능 | 상태 |
|--------|------|------|
| `get_cache_status` | 캐시 통계 조회 | ✅ |
| `cleanup_cache_tool` | 오래된 캐시 삭제 | ✅ |
| `invalidate_law_cache` | 특정 법령 캐시 무효화 | ✅ |

---

## 3. 개별 도구 평가 결과

### 3-1. 핵심 도구 상세 평가

#### `search_law` ✅
- **API**: `lawSearch.do?target=law`
- **출력 품질**: 우수 — 법령명, MST, 공포/시행일, 소관부처, 상세조회 가이드 포함
- **출력 길이**: 529자 (3건 기준)
- **LLM 활용성**: 적절 — 간결하고 actionable
- **샘플**: "개인정보" → 총 8건 (개인정보 보호법, 시행령 등)
- **REMARK**: 법령명 검색(search=1)이 기본값. 본문검색(search=2)은 JSON 미지원.

#### `get_law_detail` ✅
- **API**: `lawService.do?target=law&MST={mst}`
- **출력 품질**: 양호 — 기본정보 + 조문 인덱스 (최대 45개)
- **출력 길이**: 3,059자
- **LLM 활용성**: 약간 과다 — 140개 조문 중 45개 표시
- **REMARK**: 소관부처명이 `{'content': '기관명', '소관부처코드': '...'}` dict 형태로 노출됨. content만 추출 필요.

#### `search_precedent` ✅
- **API**: `lawSearch.do?target=prec`
- **출력 품질**: 우수 — 사건명, 선고일, 법원, 상세조회 ID 포함
- **출력 길이**: 625자 (3건 기준)
- **LLM 활용성**: 적절
- **샘플**: "개인정보" → 총 530건

#### `get_precedent_detail` ✅
- **출력 길이**: 800자+ — 판결 전문 포함
- **LLM 활용성**: 양호

#### `search_legal_interpretation` ✅
- **API**: `lawSearch.do?target=expc`
- **출력 품질**: 우수 — 안건번호, 회신일, 질의기관, 상세조회 ID 포함
- **LLM 활용성**: 적절
- **샘플**: "개인정보" → 50건

#### `search_privacy_committee` ⚠️
- **API**: `lawSearch.do?target=ppc`
- **출력 품질**: 미흡 — 제목이 "심의ㆍ의결" (결정구분 fallback)
- **실제 문제**: API 응답에서 `안건명` 필드가 빈 값인 경우가 많음
- **REMARK**: 안건명이 없을 때 의결일+결정구분으로 더 유용한 정보 표시 필요. `search_committee_bm25`를 대신 사용 권장.

#### `search_administrative_trial` ⚠️
- **API**: `lawSearch.do?target=decc`
- **상태**: `query` 파라미터 미지원 (JSON 모드) — 3건만 반환
- **출력 품질**: 개선됨 — 이제 `행정심판재결례일련번호` 표시하여 상세조회 가능 (수정됨)
- **REMARK**: query 없이 전체 검색 후 BM25 재랭킹으로만 활용 가능. `search_interpretation_bm25(target='decc')` 권장.

#### `search_tax_tribunal` ⚠️ (수정됨)
- **API**: `lawSearch.do?target=ttSpecialDecc`
- **이전 상태**: "제목 없음" 표시
- **수정 후**: 청구번호 + 재결구분명 + 의결일자 조합으로 표시
- **REMARK**: API가 `사건명`을 빈 값으로 반환함. `query` 파라미터도 미지원.

#### `search_university_regulation`, `search_public_corporation_regulation`, `search_public_institution_regulation` ✅ (수정됨)
- **이전 상태**: "제목 없음" 표시
- **수정 후**: 행정규칙명(학칙명) 정상 표시
- **원인**: `AdmRulSearch.admrul` 구조를 인식하지 못하던 버그 수정됨

#### `search_law_bm25` ✅ (개선됨)
- **BM25 적용**: 법령명 기반 검색 후 BM25 재랭킹
- **개선**: 자연어 쿼리에서 첫 단어 추출 → API 검색, 전체 쿼리 → BM25 재랭킹
- **한계**: 법령 API가 법령명 검색만 지원하므로, 법령명에 없는 개념("양도소득세 비과세 요건")은 0건
- **REMARK**: 법령 내용 검색이 아닌 법령명 검색임을 명시. 내용 검색은 `get_law_detail` 후 semantic 검색 필요.

#### `search_all_bm25` ✅
- **출력 품질**: 양호 — 5개 카테고리 병렬 검색 후 통합
- **REMARK**: 법령/행정규칙 카테고리는 법령명 검색이므로 해당 개념이 법령명에 없으면 결과 없음.

### 3-2. 문제 도구 목록

| 도구명 | 문제 유형 | 심각도 | 수정 여부 |
|--------|-----------|--------|-----------|
| `search_university_regulation` | "제목 없음" 표시 | 높음 | ✅ 수정됨 |
| `search_public_corporation_regulation` | "제목 없음" 표시 | 높음 | ✅ 수정됨 |
| `search_public_institution_regulation` | "제목 없음" 표시 | 높음 | ✅ 수정됨 |
| `search_tax_tribunal` | "제목 없음" 표시 | 높음 | ✅ 수정됨 |
| `search_maritime_safety_tribunal` | "제목 없음" 표시 | 높음 | ✅ 수정됨 |
| `search_law_bm25` | 자연어 쿼리 0건 | 높음 | ✅ 수정됨 |
| `search_precedent_bm25` | 자연어 쿼리 0건 | 높음 | ✅ 수정됨 |
| `search_interpretation_bm25` | 자연어 쿼리 0건 | 높음 | ✅ 수정됨 |
| `search_admin_rule_bm25` | 자연어 쿼리 0건 | 높음 | ✅ 수정됨 |
| `search_acrc_special_tribunal` | acrSpecialDecc 404 | 높음 | ❌ API 미오픈 |
| `search_mpm_appeal_tribunal` | adapSpecialDecc 404 | 높음 | ❌ API 미오픈 |
| `search_daily_term` | HTML전용 (중복 등록) | 중간 | ✅ 중복 제거 |
| `search_legal_daily_term_link` | HTML전용 (중복 등록) | 중간 | ✅ 중복 제거 |
| `search_privacy_committee` | 안건명 빈 값 fallback | 중간 | ⚠️ API 데이터 문제 |
| `search_administrative_trial` | query 파라미터 미지원 | 중간 | ⚠️ API 제한 |
| `search_related_law` | 빈 결과 | 중간 | ⚠️ MST 필수 |
| `search_law_nickname` | query 미작동 | 낮음 | ⚠️ gana 파라미터 필요 |
| `search_admin_rule_appendix` | 1건만 표시 | 낮음 | ⚠️ 확인 필요 |
| `get_law_detail` | 소관부처 dict 노출 | 낮음 | ⚠️ 포매팅 개선 필요 |
| `search_intelligent_law` | 빈 결과 | 낮음 | ⚠️ HTTPS+인증 필요 |
| `search_bai_preconsulting` | API 미오픈 | 낮음 | ❌ API 미오픈 |

---

## 4. LLM 활용성 평가

### 4-1. 출력 요약/압축 기능

| 도구 유형 | 요약 기능 | 최대 출력 크기 | 평가 |
|-----------|-----------|--------------|------|
| 법령 검색 | ✅ 결과 개수 제한 | ~500자/3건 | 양호 |
| 법령 상세 | ✅ 조문 인덱스 45개 제한 | 3,000자 | 적절 |
| 판례 검색 | ✅ 결과 개수 제한 | ~600자/3건 | 양호 |
| 법령 비교 | ✅ 신설/수정/삭제 10/5/10건 제한 | - | 양호 |
| 행정규칙 검색 | ✅ 결과 개수 제한 | ~800자/3건 | 양호 |
| 법령해석례 | ✅ 안건명+기관명+날짜 | ~780자/3건 | 양호 |
| BM25 검색 | ✅ top_k 파라미터 | ~400자/10건 | 양호 |
| 중앙부처 해석 | ✅ 상세조회 ID 제공 | ~235자/3건 | 양호 |

### 4-2. 총 결과가 너무 많은 경우 처리

- 모든 검색 도구에 `display` 파라미터로 반환 개수 제한 가능
- 총 건수 표시 후 "더 구체적인 검색어 권장" 안내 제공
- 일부 도구에서 "전체 N건 중 일부만 표시" 안내 ✅

### 4-3. 상세조회 체인 지원

- 검색 결과에 상세조회용 ID와 도구명 안내 ✅
- 예: `get_law_detail(mst="270351")`, `get_precedent_detail(case_id="618195")`
- 중앙부처 해석례는 ID 표시만 되고 도구 호출 가이드 없음 (일부 부족)

---

## 5. API 미구현/미매핑 항목

| API | target | 이유 | 권고 |
|-----|--------|------|------|
| 법령-자치법규 연계현황 | `drlaw` | 미구현 | `search_ordinance_law_link` 대체 가능 |
| 감사원 사전컨설팅 의견서 | `baiPvcs` | API 미오픈 | 서버 오픈 대기 |
| 국민권익위 특별행정심판 | `acrSpecialDecc` | 404 | 서버 오픈 대기 |
| 인사혁신처 소청심사 | `adapSpecialDecc` | 404 | 서버 오픈 대기 |
| 법령용어-조문 연계 | `lstrmRltJo` | HTML전용 | JSON 지원 대기 |
| AI 통합검색 | `aiSearch` | 인증/HTTPS 필요 | 인증 방식 확인 필요 |
| AI 관련법령 | `aiRltLs` | 인증/HTTPS 필요 | 인증 방식 확인 필요 |

---

## 6. 개선 권고 (REMARK)

### REMARK-01: `get_law_detail` 소관부처 포매팅
```
현재: 소관부처: {'content': '개인정보보호위원회', '소관부처코드': '1790365'}
개선: 소관부처: 개인정보보호위원회
```
파일: `law_tools.py` `get_law_detail()` 함수에서 소관부처명 dict 처리 추가

### REMARK-02: `search_law_nickname` gana 파라미터 지원
```python
# 현재: query= 파라미터로 호출 → 빈 결과
# 개선: gana=A/B/C/... 파라미터 지원
search_law_nickname(gana="가")  # 가나다 순 약칭 검색
```
파일: `law_tools.py` `search_law_nickname()` 함수 수정

### REMARK-03: `search_admin_rule_appendix` 결과 개수 확인
```
현재: "총 1건" (오류 가능성)
실제 API: 83,104건 존재
```
`_format_search_results` 또는 `admbyl` 타겟 처리 확인 필요

### REMARK-04: `search_privacy_committee` 안건명 개선
```
현재: "심의ㆍ의결" (결정구분 fallback)
개선: 의결일+회의종류+결정문일련번호 조합으로 식별 가능한 정보 표시
```

### REMARK-05: `search_administrative_trial` query 지원 확인
```
현재: JSON 모드에서 query 파라미터가 빈 결과 반환
개선: HTML 모드로 검색 후 파싱, 또는 search_interpretation_bm25(target='decc') 권장 안내
```

### REMARK-06: `search_related_law` 사용 방법 개선
```
현재: query만 입력하면 빈 결과
실제: MST 파라미터 필요 → search_related_law(mst="270351")
개선: 함수 docstring에 MST 파라미터 사용법 명시, query 입력 시 MST 검색 후 자동 연계
```

### REMARK-07: BM25 검색 법령명 vs 법령내용 구분 안내
```
현재: "자연어 검색어" 설명으로 내용 검색이 가능한 것처럼 오해 소지
개선: "법령명 키워드 검색" 명시, 법령 내용 검색은 get_law_detail 후 semantic 검색 사용
```

### REMARK-08: `drlaw` 도구 추가
```
target=drlaw: 법령-자치법규 연계현황 (948건)
현재: 미구현
권고: search_law_ordinance_status() 도구 추가
```

### REMARK-09: 중앙부처 해석 상세조회 가이드 추가
```
현재: "상세조회용 ID: 259486" (도구명 없음)
개선: "상세조회: get_moef_interpretation_detail(interpretation_id="259486")"
```
파일: `law_tools.py` `_format_search_results()` `target.endswith("CgmExpc")` 처리 개선

### REMARK-10: `lsAbrv` gana 파라미터 추가
```
현재: query= 파라미터로 호출 → 빈 결과
실제 API: display 파라미터로 전체 목록 반환
개선: gana=A/B/C 파라미터 지원 또는 display만으로 전체 조회
```

---

## 7. API 커버리지 요약

| 구분 | 총 API | 구현 | 미구현/미오픈 | 커버리지 |
|------|--------|------|--------------|---------|
| 법령 | 26 | 23 | 3 (lsHistory HTML, drlaw 미구현, lsAbrv 부분작동) | 88% |
| 행정규칙 | 4 | 4 | 0 | 100% |
| 자치법규 | 3 | 3 | 0 | 100% |
| 판례/결정례 | 8 | 8 | 0 | 100% |
| 특별행정심판 | 8 | 4 | 4 (acrSpecialDecc, adapSpecialDecc 404) | 50% |
| 위원회 결정문 | 24 | 24 | 0 | 100% |
| 조약 | 2 | 2 | 0 | 100% |
| 별표서식 | 3 | 3 | 0 | 100% |
| 법령용어 | 2 | 2 | 0 | 100% |
| 법령정보 지식베이스 | 9 | 6 | 3 (HTML전용) | 67% |
| 맞춤형 서비스 | 6 | 6 | 0 | 100% |
| 중앙부처 1차 해석 | 76 | 76 | 0 | 100% |
| 부가서비스 | 5 | 5 (HTML전용) | 0 | 100% |
| 학칙/공단/공공기관 | 2 | 2 | 0 | 100% |
| 사전컨설팅 | 2 | 2 | 2 (미오픈) | 0% |
| **합계** | **173** | **162** | **11** | **94%** |

---

## 8. 결론

### 잘 작동하는 부분
1. **법령 검색 생태계**: search_law → get_law_detail → search_law_articles 체인 완벽 작동
2. **중앙부처 해석 64개 도구**: 고용노동부~해양경찰청 전 부처 정상
3. **판례/헌재/법령해석례**: 검색+상세 정상, 내용 풍부
4. **캐시 시스템**: 7일 TTL, MD5 키, 상태 조회/정리 도구 구비
5. **BM25 재랭킹**: kiwipiepy 형태소 분석 + rank-bm25, 8개 도구 작동

### 즉시 개선이 필요한 부분
1. `drlaw` 도구 추가 (법령-자치법규 연계현황)
2. `get_law_detail` 소관부처 dict 포매팅 수정
3. `search_admin_rule_appendix` 결과 개수 버그 확인
4. 중앙부처 해석 상세조회 가이드 추가
5. `search_law_nickname` gana 파라미터 지원

### 장기 개선 사항
1. `acrSpecialDecc`, `adapSpecialDecc` API 오픈 모니터링
2. `baiPvcs` (감사원 사전컨설팅) API 오픈 모니터링
3. AI 검색 API (`aiSearch`, `aiRltLs`) 인증 방식 확인
4. 법령 내용 full-text 검색을 위한 별도 도구 개발
5. 평가 데이터셋 구축 (황금 검색 테스트셋)
