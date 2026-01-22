# 자치법규/행정규칙 API 가이드

> 자치법규 및 행정규칙 API 상세 가이드
> 전체 내용은 [전체 API 가이드](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md)의 "행정규칙", "자치법규" 섹션 참고

## 개요

자치법규 및 행정규칙 API는 지방자치단체의 자치법규와 중앙행정기관의 행정규칙을 제공합니다.

## 행정규칙 API

### 1. 행정규칙 목록/본문

**목록 조회**: `lawSearch.do?target=admrul`
- **도구**: `search_administrative_rule`
- **파라미터**: `query`, `display`, `page` 등

**본문 조회**: `lawService.do?target=admrul`
- **도구**: `get_administrative_rule_detail`
- **파라미터**: `ID` (행정규칙ID, 필수)

### 2. 행정규칙 신구법 비교

**목록 조회**: `lawSearch.do?target=admrulOldAndNew`
- **도구**: `search_administrative_rule_comparison`

**본문 조회**: `lawService.do?target=admrulOldAndNew`
- **도구**: `get_administrative_rule_comparison_detail`

### 3. 행정규칙 별표·서식

**목록 조회**: `lawSearch.do?target=admbyl`
- **도구**: `search_administrative_rule_appendix`

**본문 조회**: `lawService.do?target=admbyl`
- **도구**: `get_administrative_rule_appendix_detail`

## 자치법규 API

### 1. 자치법규 목록/본문

**목록 조회**: `lawSearch.do?target=ordinfd`
- **도구**: `search_local_ordinance`
- **파라미터**: `query`, `display`, `page` 등

**본문 조회**: `lawService.do?target=ordin`
- **도구**: `get_local_ordinance_detail`, `get_ordinance_detail`
- **파라미터**: `ID` (자치법규ID, 필수)

### 2. 자치법규 연계

**법령 연계 목록**: `lawSearch.do?target=lnkOrd`
- **도구**: `search_linked_ordinance`
- **파라미터**: `knd` (법령ID, 필수)

### 3. 자치법규 별표·서식

**목록 조회**: `lawSearch.do?target=ordinbyl`
- **도구**: `search_ordinance_appendix`

**본문 조회**: `lawService.do?target=ordinbyl`
- **도구**: `get_ordinance_appendix_detail`

## 공통 파라미터

### 목록 조회 공통 파라미터
- `OC`: 사용자 이메일 ID (자동 추가)
- `target`: 서비스 대상 (admrul, ordinfd 등)
- `type`: 출력 형태 (JSON, XML, HTML, 기본값: JSON)
- `query`: 검색어
- `display`: 결과 개수 (기본값: 20, 최대: 100)
- `page`: 페이지 번호 (기본값: 1)

### 본문 조회 공통 파라미터
- `OC`: 사용자 이메일 ID (자동 추가)
- `target`: 서비스 대상 (admrul, ordin 등)
- `type`: 출력 형태 (JSON, XML, HTML, 기본값: JSON)
- `ID`: 행정규칙/자치법규 ID (필수)

## 응답 필드

### 행정규칙 목록 조회 응답
- `totalCnt`: 검색건수
- `page`: 결과페이지번호
- `admrul`: 행정규칙 목록 배열
  - `행정규칙ID`: 행정규칙ID
  - `행정규칙명`: 행정규칙명
  - `공포일자`: 공포일자
  - `시행일자`: 시행일자
  - `소관부처명`: 소관부처명

### 자치법규 목록 조회 응답
- `totalCnt`: 검색건수
- `page`: 결과페이지번호
- `ordin`: 자치법규 목록 배열
  - `자치법규ID`: 자치법규ID
  - `자치법규명`: 자치법규명
  - `공포일자`: 공포일자
  - `시행일자`: 시행일자
  - `지방자치단체명`: 지방자치단체명

## 사용 예시

### 행정규칙 검색
```python
# 목록 조회
result = client.search("admrul", {
    "query": "개인정보",
    "display": 20
})

# 본문 조회
admrul_id = result["admrul"][0]["행정규칙ID"]
detail = client.service("admrul", {"ID": admrul_id})
```

### 자치법규 검색
```python
# 목록 조회
result = client.search("ordinfd", {
    "query": "조례",
    "display": 20
})

# 본문 조회
ordin_id = result["ordin"][0]["자치법규ID"]
detail = client.service("ordin", {"ID": ordin_id})
```

### 자치법규 연계 조회
```python
# 법령 기준 자치법규 연계
result = client.search("lnkOrd", {
    "knd": "830"  # 법령ID 필수
})
```

## 관련 문서

- [API 마스터 가이드](api-master-guide.md)
- [전체 API 가이드 - 행정규칙 섹션](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md#행정규칙)
- [전체 API 가이드 - 자치법규 섹션](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md#자치법규)
