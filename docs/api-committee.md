# 위원회결정문 API 가이드

> 위원회결정문 API 상세 가이드
> 전체 내용은 [전체 API 가이드](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md)의 "위원회결정문" 섹션 참고

## 개요

위원회결정문 API는 12개 위원회의 결정문을 제공합니다. 각 위원회별로 독립적인 target 값을 사용합니다.

## 지원 위원회

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

## 공통 파라미터

### 목록 조회 공통 파라미터
- `OC`: 사용자 이메일 ID (자동 추가)
- `target`: 서비스 대상 (위원회별 target 값)
- `type`: 출력 형태 (JSON, XML, HTML, 기본값: JSON)
- `query`: 검색어
- `display`: 결과 개수 (기본값: 20, 최대: 100)
- `page`: 페이지 번호 (기본값: 1)
- `date_from`: 시작일자 (YYYYMMDD)
- `date_to`: 종료일자 (YYYYMMDD)

### 본문 조회 공통 파라미터
- `OC`: 사용자 이메일 ID (자동 추가)
- `target`: 서비스 대상 (위원회별 target 값)
- `type`: 출력 형태 (JSON, XML, HTML, 기본값: JSON)
- `ID`: 결정문 일련번호 (필수)

## 응답 필드

### 목록 조회 응답
- `totalCnt`: 검색건수
- `page`: 결과페이지번호
- `[target]`: 결정문 목록 배열 (target 값에 따라 필드명 변경)
  - `결정문일련번호`: 결정문일련번호 (ID)
  - `사건명`: 사건명
  - `결정일자`: 결정일자
  - `위원회명`: 위원회명
  - `결정요지`: 결정요지 (요약)

### 본문 조회 응답
- `결정문일련번호`: 결정문일련번호
- `사건명`: 사건명
- `결정일자`: 결정일자
- `위원회명`: 위원회명
- `결정요지`: 결정요지
- `결정내용`: 결정내용 (전체)
- `참조법령`: 참조법령
- `참조판례`: 참조판례

## 사용 예시

### 개인정보보호위원회 결정문 검색
```python
# 목록 조회
result = client.search("ppc", {
    "query": "개인정보 유출",
    "date_from": "20200101",
    "date_to": "20241231",
    "display": 20
})

# 본문 조회
decision_id = result["ppc"][0]["결정문일련번호"]
detail = client.service("ppc", {"ID": decision_id})
```

### 공정거래위원회 결정문 검색
```python
# 목록 조회
result = client.search("ftc", {
    "query": "불공정거래",
    "display": 20
})

# 본문 조회
decision_id = result["ftc"][0]["결정문일련번호"]
detail = client.service("ftc", {"ID": decision_id})
```

## 관련 문서

- [API 마스터 가이드](api-master-guide.md)
- [전체 API 가이드 - 위원회결정문 섹션](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md#위원회결정문)
