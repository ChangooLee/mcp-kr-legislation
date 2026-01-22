# 법제처 OPEN API 마스터 가이드

> 생성일: 2025. 7. 22.
> 업데이트: 2026. 1. 21. - 원본 구분 기준 18개 JSON 파일로 분리, 모바일 제외

이 문서는 법제처 OPEN API의 전체 구조와 패턴을 설명하는 마스터 가이드입니다. 

**참고**: 모바일 API는 별도 모바일 앱 전용으로, 본 프로젝트에서는 제외됩니다.

카테고리별 상세 가이드는 다음 문서를 참고하세요:

- [법령 API](api-law.md)
- [판례 API](api-precedent.md)
- [위원회결정문 API](api-committee.md)
- [자치법규/행정규칙 API](api-ordinance.md)
- [기타 API](api-others.md) - 중앙부처해석, 특별행정심판 포함

## API 구조 패턴

### 핵심 URL 패턴

| 기능 | URL 패턴 | 설명 | 예시 |
|------|-----------|------|------|
| **목록 조회** | `lawSearch.do?target={value}` | 검색/목록 반환 | `lawSearch.do?target=law` |
| **본문 조회** | `lawService.do?target={value}` | 상세 내용 반환 | `lawService.do?target=law` |

### target 파라미터가 기능 결정

- 동일한 URL에서 `target` 값만으로 API 카테고리 구분
- 총 **95개 이상**의 고유한 target 값 존재
- 목록/본문 조회는 URL로, 카테고리는 target으로 결정

## 원본 구분별 JSON 파일 (18개, 모바일 제외)

| 원본 구분 | JSON 파일 | 비고 |
|----------|-----------|------|
| **법령** | `law.json` | 목록/본문/조항호목/연혁/연계/부가서비스 |
| **행정규칙** | `admin_rule.json` | 목록/본문/신구법비교 |
| **자치법규** | `local_ordinance.json` | 목록/본문/연계 |
| **판례** | `precedent.json` | 판례 목록/본문 |
| **헌재결정례** | `constitutional_court.json` | 헌법재판소 결정례 |
| **법령해석례** | `legal_interpretation.json` | 법령해석례 |
| **행정심판례** | `administrative_appeal.json` | 행정심판례 |
| **위원회 결정문** | `committee.json` | 12개 위원회 결정문 |
| **조약** | `treaty.json` | 조약 목록/본문 |
| **별표·서식** | `appendix.json` | 별표/서식 |
| **학칙·공단·공공기관** | `school_corp.json` | 학칙/공단/공공기관 |
| **법령용어** | `legal_term.json` | 법령용어 목록/본문 |
| **맞춤형** | `custom.json` | 맞춤형 서비스 |
| **법령정보 지식베이스** | `knowledge_base.json` | 지식베이스 |
| **법령 간 관계** | `law_relation.json` | 법령 관계 |
| **지능형 법령검색 시스템** | `intelligent_search.json` | AI 기반 검색 |
| **중앙부처 1차 해석** | `ministry_interpretation.json` | 중앙부처 법령해석 |
| **특별행정심판** | `special_tribunal.json` | 특별행정심판 |

**JSON 파일 위치**: `src/mcp_kr_legislation/utils/api_layout/`

> **제외됨**: 모바일 API (별도 모바일 앱 전용)

### API Layout JSON 재생성

```bash
source .crawler_venv/bin/activate  # 또는 uv pip install playwright beautifulsoup4 lxml
playwright install chromium
python src/mcp_kr_legislation/utils/api_crawler.py
```

## API 카테고리별 구분표

### 법령 API

| 중분류 | 목록 조회 API | target | 본문 조회 API | target | 목록 조회 도구 | 본문/상세 조회 도구 |
|--------|---------------|--------|---------------|--------|------------|---------------|
| **본문** | 현행법령 목록 조회 | `law` | 현행법령 본문 조회 | `law` | `search_law` | `get_law_detail` |
| | 시행일 법령 목록 조회 | `eflaw` | 시행일 법령 본문 조회 | `eflaw` | `search_effective_law` | `get_effective_law_detail` |
| **통합검색** | 범용 법령 통합 검색 | `다중` | - | - | `search_law_unified` | - |
| **조항호목** | - | - | 현행법령 본문 조항호목 조회 | `lawjosub` | - | `get_current_law_articles`, `search_law_articles` |
| | - | - | 시행일 법령 본문 조항호목 조회 | `eflawjosub` | - | `get_effective_law_articles` |
| **영문법령** | 영문 법령 목록 조회 | `elaw` | 영문 법령 본문 조회 | `elaw` | `search_english_law` | `get_english_law_detail` |
| **이력** | 법령 변경이력 목록 조회 | `lsHstInf` | - | - | `search_law_change_history` | - |
| | 일자별 조문 개정 이력 목록 조회 | `lsJoHstInf` | - | - | `search_daily_article_revision` | - |
| | 조문별 변경 이력 목록 조회 | `lsJoHstInf` | - | - | `search_article_change_history` | - |
| **연계** | 법령 기준 자치법규 연계 관련 목록 조회 | `lnkLs` | - | - | `search_law_ordinance_link` | - |
| | - | - | 위임법령 조회 | `lsDelegated` | - | `get_delegated_law` |
| **부가서비스** | 법령 체계도 목록 조회 | `lsStmd` | 법령 체계도 본문 조회 | `lsStmd` | `search_law_system_diagram` | `get_law_system_diagram_detail` |
| | 신구법 목록 조회 | `oldAndNew` | 신구법 본문 조회 | `oldAndNew` | `search_old_and_new_law` | `get_old_and_new_law_detail` |
| | 3단 비교 목록 조회 | `thdCmp` | 3단 비교 본문 조회 | `thdCmp` | `search_three_way_comparison` | `get_three_way_comparison_detail` |
| | 법률명 약칭 조회 | `lsAbrv` | - | - | `search_law_nickname` | - |
| | 삭제 데이터 목록 조회 | `datDel` | - | - | `search_deleted_law_data` | - |
| | 한눈보기 목록 조회 | `oneview` | 한눈보기 본문 조회 | `oneview` | `search_one_view` | `get_one_view_detail` |
| | 별표·서식 목록 조회 | `licbyl` | - | - | `search_law_appendix` | `get_law_appendix_detail` |

### 행정규칙/자치법규 API

| 대분류 | 중분류 | 목록 조회 API | target | 본문 조회 API | target | 목록 조회 도구 | 본문/상세 조회 도구 |
|--------|--------|---------------|--------|---------------|--------|------------|---------------|
| **행정규칙** | **본문** | 행정규칙 목록 조회 | `admrul` | 행정규칙 본문 조회 | `admrul` | `search_administrative_rule` | `get_administrative_rule_detail` |
| | **부가서비스** | 행정규칙 신구법 비교 목록 조회 | `admrulOldAndNew` | 행정규칙 신구법 비교 본문 조회 | `admrulOldAndNew` | `search_administrative_rule_comparison` | `get_administrative_rule_comparison_detail` |
| | | 별표·서식 목록 조회 | `admbyl` | - | - | `search_administrative_rule_appendix` | `get_administrative_rule_appendix_detail` |
| **자치법규** | **본문** | 자치법규 목록 조회 | `ordinfd` | 자치법규 본문 조회 | `ordin` | `search_local_ordinance` | `get_local_ordinance_detail`, `get_ordinance_detail` |
| | **연계** | 자치법규 기준 법령 연계 관련 목록 조회 | `lnkOrd` | - | - | `search_linked_ordinance` | - |
| | | 별표·서식 목록 조회 | `ordinbyl` | - | - | `search_ordinance_appendix` | `get_ordinance_appendix_detail` |

### 판례관련 API

| 중분류 | 목록 조회 API | target | 본문 조회 API | target | 목록 조회 도구 | 본문/상세 조회 도구 |
|--------|---------------|--------|---------------|--------|------------|---------------|
| **판례** | 판례 목록 조회 | `prec` | 판례 본문 조회 | `prec` | `search_precedent` | `get_precedent_detail` |
| **헌재결정례** | 헌재결정례 목록 조회 | `detc` | 헌재결정례 본문 조회 | `detc` | `search_constitutional_court` | `get_constitutional_court_detail` |
| **법령해석례** | 법령해석례 목록 조회 | `expc` | 법령해석례 본문 조회 | `expc` | `search_legal_interpretation` | `get_legal_interpretation_detail` |
| **행정심판례** | 행정심판례 목록 조회 | `decc` | 행정심판례 본문 조회 | `decc` | `search_administrative_trial` | `get_administrative_trial_detail` |

### 위원회결정문 API (12개 위원회)

| 위원회 | target | 목록 조회 도구 | 본문 조회 도구 |
|--------|--------|------------|---------------|
| 개인정보보호위원회 | `ppc` | `search_privacy_committee` | `get_privacy_committee_detail` |
| 고용보험심사위원회 | `eiac` | `search_employment_insurance_committee` | `get_employment_insurance_committee_detail` |
| 공정거래위원회 | `ftc` | `search_monopoly_committee` | `get_monopoly_committee_detail` |
| 국민권익위원회 | `acr` | `search_anticorruption_committee` | `get_anticorruption_committee_detail` |
| 금융위원회 | `fsc` | `search_financial_committee` | `get_financial_committee_detail` |
| 노동위원회 | `nlrc` | `search_labor_committee` | `get_labor_committee_detail` |
| 방송통신위원회 | `kcc` | `search_broadcasting_committee` | `get_broadcasting_committee_detail` |
| 산업재해보상보험재심사위원회 | `iaciac` | `search_industrial_accident_committee` | `get_industrial_accident_committee_detail` |
| 중앙토지수용위원회 | `oclt` | `search_land_tribunal` | `get_land_tribunal_detail` |
| 중앙환경분쟁조정위원회 | `ecc` | `search_environment_committee` | `get_environment_committee_detail` |
| 증권선물위원회 | `sfc` | `search_securities_committee` | `get_securities_committee_detail` |
| 국가인권위원회 | `nhrck` | `search_human_rights_committee` | `get_human_rights_committee_detail` |

### 중앙부처해석 API (30개 부처)

#### 구현된 부처 (8개)

| 부처 | target | 목록 조회 도구 | 본문 조회 도구 |
|------|--------|------------|---------------|
| 고용노동부 | `moelCgmExpc` | `search_moel_interpretation` | `get_moel_interpretation_detail` |
| 국토교통부 | `molitCgmExpc` | `search_molit_interpretation` | `get_molit_interpretation_detail` |
| 기획재정부 | `moefCgmExpc` | `search_moef_interpretation` | `get_moef_interpretation_detail` |
| 해양수산부 | `mofCgmExpc` | `search_mof_interpretation` | `get_mof_interpretation_detail` |
| 행정안전부 | `moisCgmExpc` | `search_mois_interpretation` | `get_mois_interpretation_detail` |
| 환경부 | `meCgmExpc` | `search_me_interpretation` | `get_me_interpretation_detail` |
| 관세청 | `kcsCgmExpc` | `search_kcs_interpretation` | `get_kcs_interpretation_detail` |
| 국세청 | `ntsCgmExpc` | `search_nts_interpretation` | `get_nts_interpretation_detail` |

#### 추가 필요 부처 (22개)

| 부처 | target (예상) | 구현 상태 |
|------|-------------|----------|
| 농림축산식품부 | `mafCgmExpc` | 미구현 |
| 문화체육관광부 | `moctCgmExpc` | 미구현 |
| 법무부 | `mojCgmExpc` | 미구현 |
| 보건복지부 | `mohwCgmExpc` | 미구현 |
| 산업통상자원부 | `motieCgmExpc` | 미구현 |
| 여성가족부(성평등가족부) | `mogefCgmExpc` | 미구현 |
| 외교부 | `mofaCgmExpc` | 미구현 |
| 중소벤처기업부 | `mssCgmExpc` | 미구현 |
| 통일부 | `unikoreaaCgmExpc` | 미구현 |
| 법제처 | `molegCgmExpc` | 미구현 |
| 식품의약품안전처 | `mfdsCgmExpc` | 미구현 |
| 인사혁신처 | `mpoCgmExpc` | 미구현 |
| 기상청 | `kmaCgmExpc` | 미구현 |
| 국가유산청 | `chaCgmExpc` | 미구현 |
| 농촌진흥청 | `rdaCgmExpc` | 미구현 |
| 경찰청 | `policeCgmExpc` | 미구현 |
| 방위사업청 | `dpaCgmExpc` | 미구현 |
| 병무청 | `mmaCgmExpc` | 미구현 |
| 산림청 | `forestCgmExpc` | 미구현 |
| 소방청 | `nfaCgmExpc` | 미구현 |
| 재외동포청 | `okaCgmExpc` | 미구현 |
| 조달청 | `ppsCgmExpc` | 미구현 |
| 질병관리청 | `kdcaCgmExpc` | 미구현 |
| 국가데이터처 | `ndaCgmExpc` | 미구현 |
| 지식재산처 | `kipoCgmExpc` | 미구현 |
| 해양경찰청 | `kcgCgmExpc` | 미구현 |
| 행정중심복합도시건설청 | `naacc CgmExpc` | 미구현 |

> 참고: target 값은 법제처 OPEN API 공식 가이드에서 확인 필요

### 특별행정심판 API (4개 기관)

| 기관 | target | 목록 조회 도구 | 본문 조회 도구 | 구현 상태 |
|------|--------|------------|---------------|----------|
| 조세심판원 | `ttSpecialDecc` | `search_tax_tribunal` | `get_tax_tribunal_detail` | 구현됨 |
| 해양안전심판원 | `kmstSpecialDecc` | `search_maritime_safety_tribunal` | `get_maritime_safety_tribunal_detail` | 구현됨 |
| 국민권익위원회 | `acrSpecialDecc` | - | - | 미구현 |
| 인사혁신처 소청심사위원회 | `mpoSpecialDecc` | - | - | 미구현 |

### 기타 API

| 대분류 | 중분류 | target | 목록 조회 도구 | 본문 조회 도구 |
|--------|--------|--------|------------|---------------|
| **조약** | 본문 | `trty` | `search_treaty` | `get_treaty_detail` |
| **학칙·공단·공공기관** | 학칙 | `pi` | `search_university_regulation` | `get_university_regulation_detail` |
| | 공단 | `pi` | `search_public_corporation_regulation` | `get_public_corporation_regulation_detail` |
| | 공공기관 | `pi` | `search_public_institution_regulation` | `get_public_institution_regulation_detail` |
| **법령용어** | 본문 | `lstrm` | `search_legal_term` | `get_legal_term_detail` |
| **맞춤형** | 법령 | `couseLs` | `search_custom_law` | - |
| | 행정규칙 | `couseAdmrul` | `search_custom_administrative_rule` | - |
| | 자치법규 | `couseOrdin` | `search_custom_ordinance` | - |
| **지식베이스** | 법령용어 | `lstrmAI` | `search_legal_term_ai` | - |
| | 일상용어 | `dlytrm` | `search_daily_term` | - |
| | 법령용어-일상용어 연계 | `lstrmRlt` | `search_legal_daily_term_link` | - |
| | 일상용어-법령용어 연계 | `dlytrmRlt` | `search_daily_legal_term_link` | - |
| | 법령용어-조문 연계 | `lstrmRltJo` | `search_legal_term_article_link` | - |
| | 조문-법령용어 연계 | `joRltLstrm` | `search_article_legal_term_link` | - |
| | 관련법령 | `lsRlt` | `search_related_law` | - |

## 추가 도구 분류

| 분류 | 도구명 | 목적 | 파일 위치 |
|------|--------|------|----------|
| **최적화 도구** | `get_law_summary` | 법령 요약 조회 (캐싱 최적화) | optimized_law_tools.py |
| | `get_law_articles_summary` | 법령 조문 요약 (성능 최적화) | optimized_law_tools.py |
| | `get_law_article_detail` | 단일 조문 상세 조회 | optimized_law_tools.py |
| | `search_law_with_cache` | 캐시 기반 법령 검색 | optimized_law_tools.py |
| **AI/스마트 도구** | `search_legal_ai` | AI 기반 법령 검색 | ai_tools.py |
| | `search_law_articles_semantic` | 의미론적 조문 검색 | law_tools.py |
| | `search_english_law_articles_semantic` | 영문법령 의미론적 검색 | law_tools.py |
| **부가 서비스** | `search_knowledge_base` | 법령 지식베이스 검색 | additional_service_tools.py |
| | `search_faq` | 자주묻는질문 검색 | additional_service_tools.py |
| | `search_qna` | 질의응답 검색 | additional_service_tools.py |
| | `search_counsel` | 법령상담 검색 | additional_service_tools.py |
| | `search_precedent_counsel` | 판례상담 검색 | additional_service_tools.py |
| | `search_civil_petition` | 민원사례 검색 | additional_service_tools.py |
| **분석/비교 도구** | `compare_law_versions` | 법령 버전 비교 분석 | law_tools.py |
| | `compare_article_before_after` | 조문 개정 전후 비교 | law_tools.py |
| **실무 가이드** | `get_practical_law_guide` | 실무 가이드 제공 | law_tools.py |
| | `search_financial_laws` | 금융법령 통합 검색 | law_tools.py |
| | `search_tax_laws` | 세법 통합 검색 | law_tools.py |
| | `search_privacy_laws` | 개인정보보호법령 통합 검색 | law_tools.py |
| **통합 검색** | `search_all_legal_documents` | 전체 법령문서 통합 검색 | legislation_tools.py |

**현재 총 132개 도구** = 105개 (API 매핑) + 27개 (추가 기능)

## 연결된 도구 워크플로우

### 기본 2단계 워크플로우

```
1. 목록 조회 (search_*) → 2. 상세 조회 (get_*_detail)
```

### 주요 워크플로우 예시

**법령 검색 플로우**
```
search_law(query="민법") 
→ 결과에서 ID 선택 
→ get_law_detail(law_id) 또는 get_current_law_articles(law_id)
```

**판례 검색 플로우**
```
search_precedent(query="계약") 
→ 결과에서 사건번호 선택 
→ get_precedent_detail(case_id)
```

**위원회결정문 검색 플로우**
```
search_privacy_committee(query="개인정보") 
→ 결과에서 결정문번호 선택 
→ get_privacy_committee_detail(decision_id)
```

**영문법령 검색 플로우**
```
search_english_law(query="Civil Act") 
→ 결과에서 법령ID 선택 
→ get_english_law_detail(law_id)
```

## 도구 사용 가이드라인

### 목록 조회 도구 (`search_*`) 사용법
- **목적**: 여러 건의 결과를 빠르게 검색
- **반환**: 목록 형태의 요약 정보 (제목, ID, 요약 등)
- **다음 단계**: 관심 있는 항목의 ID를 사용해 상세 조회

### 상세 조회 도구 (`get_*_detail`) 사용법
- **목적**: 특정 문서의 전체 내용 조회
- **입력**: 목록 조회에서 얻은 ID
- **반환**: 해당 문서의 전체 내용

### 성능 최적화 팁
1. **단계적 접근**: 목록 조회 → 필요한 것만 상세 조회
2. **적절한 페이징**: `display`와 `page` 파라미터 활용
3. **구체적 검색어**: 너무 일반적인 용어보다는 구체적인 키워드 사용

## 공통 파라미터

### 필수 파라미터
- `OC`: 사용자 이메일 ID (자동 추가됨, 환경변수 `LEGISLATION_API_KEY`에서 읽음)
- `target`: 서비스 대상 (필수, 카테고리 구분)
- `type`: 출력 형태 (JSON, XML, HTML, 기본값: JSON)

### 검색 파라미터
- `query`: 검색어
- `display`: 결과 개수 (기본값: 20, 최대: 100)
- `page`: 페이지 번호 (기본값: 1)
- `search`: 검색범위 (1=법령명, 2=본문검색)

### 상세 조회 파라미터
- `ID`: 문서 ID (필수, 목록 조회에서 얻음)
- `MST`: 법령 마스터 번호 (ID 대신 사용 가능)

## 구현 계획

### Phase 1: 중앙부처해석 확장 (우선순위 높음)
신규 파일: `ministry_interpretation_tools_extended.py`
- 22개 부처 추가 (목록/본문 각각)
- 약 44개 도구 추가 예정

### Phase 2: 특별행정심판 확장
신규 파일: `special_tribunal_tools.py`
- 2개 기관 추가 (국민권익위원회, 인사혁신처 소청심사위원회)
- 4개 도구 추가 예정

## 관련 문서

- [법령 API 상세 가이드](api-law.md)
- [판례 API 상세 가이드](api-precedent.md)
- [위원회결정문 API 상세 가이드](api-committee.md)
- [자치법규/행정규칙 API 상세 가이드](api-ordinance.md)
- [기타 API 상세 가이드](api-others.md)
- [전체 API 가이드](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md) (참고용)
