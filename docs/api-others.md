# 기타 API 가이드

> 조약, 학칙공단, 법령용어, 맞춤형, 지식베이스, 중앙부처해석, 특별행정심판 등 기타 API 상세 가이드
> 업데이트: 2026. 1. 20. - 중앙부처해석 30개 부처, 특별행정심판 4개 기관 추가
> 전체 내용은 [전체 API 가이드](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md)의 해당 섹션 참고

## 개요

기타 API는 조약, 학칙·공단·공공기관, 법령용어, 맞춤형, 지식베이스, 중앙부처해석, 특별행정심판 등을 제공합니다.

## 조약 API

### 목록/본문 조회

**목록 조회**: `lawSearch.do?target=trty`
- **도구**: `search_treaty`

**본문 조회**: `lawService.do?target=trty`
- **도구**: `get_treaty_detail`
- **파라미터**: `ID` (조약ID, 필수)

## 학칙·공단·공공기관 API

### 목록/본문 조회

**목록 조회**: `lawSearch.do?target=pi`
- **도구**: 
  - `search_university_regulation` (학칙)
  - `search_public_corporation_regulation` (공단)
  - `search_public_institution_regulation` (공공기관)

**본문 조회**: `lawService.do?target=pi`
- **도구**: 
  - `get_university_regulation_detail`
  - `get_public_corporation_regulation_detail`
  - `get_public_institution_regulation_detail`
- **파라미터**: `ID` (학칙/공단/공공기관 ID, 필수)

## 법령용어 API

### 목록/본문 조회

**목록 조회**: `lawSearch.do?target=lstrm`
- **도구**: `search_legal_term`

**본문 조회**: `lawService.do?target=lstrm`
- **도구**: `get_legal_term_detail`
- **파라미터**: `query` (법령용어, 필수)

## 맞춤형 API

### 법령 맞춤형

**목록 조회**: `lawSearch.do?target=couseLs`
- **도구**: `search_custom_law`

**조문 목록 조회**: `lawSearch.do?target=couseLs`
- **도구**: `search_custom_law_articles`

### 행정규칙 맞춤형

**목록 조회**: `lawSearch.do?target=couseAdmrul`
- **도구**: `search_custom_administrative_rule`

**조문 목록 조회**: `lawSearch.do?target=couseAdmrul`
- **도구**: `search_custom_administrative_rule_articles`

### 자치법규 맞춤형

**목록 조회**: `lawSearch.do?target=couseOrdin`
- **도구**: `search_custom_ordinance`

**조문 목록 조회**: `lawSearch.do?target=couseOrdin`
- **도구**: `search_custom_ordinance_articles`

## 지식베이스 API

### 용어 조회

**법령용어**: `lawSearch.do?target=lstrmAI`
- **도구**: `search_legal_term_ai`

**일상용어**: `lawSearch.do?target=dlytrm`
- **도구**: `search_daily_term`

### 용어 간 관계

**법령용어-일상용어 연계**: `lawSearch.do?target=lstrmRlt`
- **도구**: `search_legal_daily_term_link`

**일상용어-법령용어 연계**: `lawSearch.do?target=dlytrmRlt`
- **도구**: `search_daily_legal_term_link`

### 조문 간 관계

**법령용어-조문 연계**: `lawSearch.do?target=lstrmRltJo`
- **도구**: `search_legal_term_article_link`

**조문-법령용어 연계**: `lawSearch.do?target=joRltLstrm`
- **도구**: `search_article_legal_term_link`

### 법령 간 관계

**관련법령 조회**: `lawSearch.do?target=lsRlt`
- **도구**: `search_related_law`

## 중앙부처해석 API

> 법제처 OPEN API는 총 30개 부처의 법령해석을 제공합니다.
> 현재 8개 부처가 구현되어 있으며, 22개 부처 추가 구현이 필요합니다.

### 구현된 부처 (8개)

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

### 추가 필요 부처 (22개)

법제처 OPEN API 공식 가이드에서 확인된 추가 부처:

| 부처 | 설명 | 구현 상태 |
|------|------|----------|
| 농림축산식품부 | 농업, 축산, 식품 관련 법령해석 | 미구현 |
| 문화체육관광부 | 문화, 체육, 관광 관련 법령해석 | 미구현 |
| 법무부 | 법무 관련 법령해석 | 미구현 |
| 보건복지부 | 보건, 복지 관련 법령해석 | 미구현 |
| 산업통상자원부 | 산업, 통상, 에너지 관련 법령해석 | 미구현 |
| 성평등가족부(여성가족부) | 여성, 가족 관련 법령해석 | 미구현 |
| 외교부 | 외교 관련 법령해석 | 미구현 |
| 중소벤처기업부 | 중소기업, 벤처 관련 법령해석 | 미구현 |
| 통일부 | 통일 관련 법령해석 | 미구현 |
| 법제처 | 법제 관련 법령해석 | 미구현 |
| 식품의약품안전처 | 식약 관련 법령해석 | 미구현 |
| 인사혁신처 | 인사, 공무원 관련 법령해석 | 미구현 |
| 기상청 | 기상 관련 법령해석 | 미구현 |
| 국가유산청 | 문화재 관련 법령해석 | 미구현 |
| 농촌진흥청 | 농촌 진흥 관련 법령해석 | 미구현 |
| 경찰청 | 경찰 관련 법령해석 | 미구현 |
| 방위사업청 | 방위사업 관련 법령해석 | 미구현 |
| 병무청 | 병무 관련 법령해석 | 미구현 |
| 산림청 | 산림 관련 법령해석 | 미구현 |
| 소방청 | 소방 관련 법령해석 | 미구현 |
| 재외동포청 | 재외동포 관련 법령해석 | 미구현 |
| 조달청 | 조달 관련 법령해석 | 미구현 |
| 질병관리청 | 질병관리 관련 법령해석 | 미구현 |
| 국가데이터처 | 데이터 관련 법령해석 | 미구현 |
| 지식재산처 | 지식재산 관련 법령해석 | 미구현 |
| 해양경찰청 | 해양경찰 관련 법령해석 | 미구현 |
| 행정중심복합도시건설청 | 세종시 건설 관련 법령해석 | 미구현 |

### 공통 파라미터

**목록 조회**:
- `OC`: 사용자 이메일 ID (자동 추가)
- `target`: 부처별 target 값
- `type`: 출력 형태 (JSON, XML, HTML)
- `query`: 검색어
- `display`: 결과 개수 (기본값: 20, 최대: 100)
- `page`: 페이지 번호 (기본값: 1)

**본문 조회**:
- `OC`: 사용자 이메일 ID (자동 추가)
- `target`: 부처별 target 값
- `type`: 출력 형태 (JSON, XML, HTML)
- `ID`: 해석 일련번호 (필수)

## 특별행정심판 API

> 법제처 OPEN API는 총 4개 기관의 특별행정심판례를 제공합니다.
> 현재 2개 기관이 구현되어 있으며, 2개 기관 추가 구현이 필요합니다.

### 구현된 기관 (2개)

#### 조세심판원

**목록 조회**: `lawSearch.do?target=ttSpecialDecc`
- **도구**: `search_tax_tribunal`

**본문 조회**: `lawService.do?target=ttSpecialDecc`
- **도구**: `get_tax_tribunal_detail`

#### 해양안전심판원

**목록 조회**: `lawSearch.do?target=kmstSpecialDecc`
- **도구**: `search_maritime_safety_tribunal`

**본문 조회**: `lawService.do?target=kmstSpecialDecc`
- **도구**: `get_maritime_safety_tribunal_detail`

### 추가 필요 기관 (2개)

| 기관 | target (예상) | 설명 | 구현 상태 |
|------|-------------|------|----------|
| 국민권익위원회 | `acrSpecialDecc` | 행정심판 재결례 | 미구현 |
| 인사혁신처 소청심사위원회 | `mpoSpecialDecc` | 소청심사 재결례 | 미구현 |

> 참고: target 값은 법제처 OPEN API 공식 가이드에서 확인 필요

## 사용 예시

### 조약 검색
```python
# 목록 조회
result = client.search("trty", {
    "query": "자유무역협정",
    "display": 20
})

# 본문 조회
trty_id = result["trty"][0]["조약ID"]
detail = client.service("trty", {"ID": trty_id})
```

### 법령용어 검색
```python
# 목록 조회
result = client.search("lstrm", {
    "query": "계약",
    "display": 20
})

# 본문 조회
detail = client.service("lstrm", {"query": "계약"})
```

### 중앙부처해석 검색
```python
# 고용노동부 법령해석
result = client.search("moelCgmExpc", {
    "query": "근로기준법",
    "display": 20
})

# 본문 조회
interpretation_id = result["moelCgmExpc"][0]["해석일련번호"]
detail = client.service("moelCgmExpc", {"ID": interpretation_id})
```

### 특별행정심판 검색
```python
# 조세심판원 심판례
result = client.search("ttSpecialDecc", {
    "query": "부가가치세",
    "display": 20
})

# 본문 조회
decision_id = result["ttSpecialDecc"][0]["결정번호"]
detail = client.service("ttSpecialDecc", {"ID": decision_id})
```

## 구현 계획

### Phase 1: 중앙부처해석 확장
- 신규 파일: `ministry_interpretation_tools_extended.py`
- 추가 부처: 22개
- 추가 도구: 44개 (목록/본문 각각)

### Phase 2: 특별행정심판 확장
- 신규 파일: `special_tribunal_tools.py`
- 추가 기관: 2개 (국민권익위원회, 인사혁신처 소청심사위원회)
- 추가 도구: 4개 (목록/본문 각각)

## 관련 문서

- [API 마스터 가이드](api-master-guide.md)
- [전체 API 가이드](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md)
