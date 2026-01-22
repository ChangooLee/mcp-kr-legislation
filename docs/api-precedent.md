# 판례 API 가이드

> 판례 관련 API 상세 가이드
> 전체 내용은 [전체 API 가이드](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md)의 "판례관련" 섹션 참고

## 개요

판례 관련 API는 대법원 판례, 헌법재판소 결정례, 법령해석례, 행정심판례를 제공합니다.

## 주요 API

### 1. 대법원 판례

**목록 조회**: `lawSearch.do?target=prec`
- **도구**: `search_precedent`
- **파라미터**: `query`, `display`, `page`, `date_from`, `date_to` 등

**본문 조회**: `lawService.do?target=prec`
- **도구**: `get_precedent_detail`
- **파라미터**: `ID` (판례일련번호, 필수)

### 2. 헌법재판소 결정례

**목록 조회**: `lawSearch.do?target=detc`
- **도구**: `search_constitutional_court`

**본문 조회**: `lawService.do?target=detc`
- **도구**: `get_constitutional_court_detail`

### 3. 법령해석례

**목록 조회**: `lawSearch.do?target=expc`
- **도구**: `search_legal_interpretation`

**본문 조회**: `lawService.do?target=expc`
- **도구**: `get_legal_interpretation_detail`

### 4. 행정심판례

**목록 조회**: `lawSearch.do?target=decc`
- **도구**: `search_administrative_trial`

**본문 조회**: `lawService.do?target=decc`
- **도구**: `get_administrative_trial_detail`

## 공통 파라미터

### 목록 조회 공통 파라미터
- `OC`: 사용자 이메일 ID (자동 추가)
- `target`: 서비스 대상 (prec, detc, expc, decc)
- `type`: 출력 형태 (JSON, XML, HTML, 기본값: JSON)
- `query`: 검색어
- `display`: 결과 개수 (기본값: 20, 최대: 100)
- `page`: 페이지 번호 (기본값: 1)
- `date_from`: 시작일자 (YYYYMMDD)
- `date_to`: 종료일자 (YYYYMMDD)

### 본문 조회 공통 파라미터
- `OC`: 사용자 이메일 ID (자동 추가)
- `target`: 서비스 대상 (prec, detc, expc, decc)
- `type`: 출력 형태 (JSON, XML, HTML, 기본값: JSON)
- `ID`: 판례/결정례 일련번호 (필수)

## 응답 필드

### 목록 조회 응답
- `totalCnt`: 검색건수
- `page`: 결과페이지번호
- `prec`/`detc`/`expc`/`decc`: 판례 목록 배열
  - `판례일련번호`: 판례일련번호 (ID)
  - `사건명`: 사건명
  - `선고일자`: 선고일자
  - `법원명`: 법원명
  - `사건번호`: 사건번호
  - `판결요지`: 판결요지 (요약)

### 본문 조회 응답
- `판례일련번호`: 판례일련번호
- `사건명`: 사건명
- `선고일자`: 선고일자
- `법원명`: 법원명
- `사건번호`: 사건번호
- `판결요지`: 판결요지
- `판시사항`: 판시사항
- `참조조문`: 참조조문
- `참조판례`: 참조판례
- `판결내용`: 판결내용 (전체)

## 사용 예시

### 판례 검색
```python
# 목록 조회
result = client.search("prec", {
    "query": "계약 해지",
    "date_from": "20200101",
    "date_to": "20241231",
    "display": 20
})

# 본문 조회
prec_id = result["prec"][0]["판례일련번호"]
detail = client.service("prec", {"ID": prec_id})
```

### 헌법재판소 결정례 검색
```python
# 목록 조회
result = client.search("detc", {
    "query": "개인정보",
    "display": 20
})

# 본문 조회
detc_id = result["detc"][0]["판례일련번호"]
detail = client.service("detc", {"ID": detc_id})
```

## 관련 문서

- [API 마스터 가이드](api-master-guide.md)
- [전체 API 가이드 - 판례관련 섹션](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md#판례관련)
