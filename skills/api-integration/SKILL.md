---
name: api-integration
description: 법제처 OPEN API를 MCP 프로젝트에 통합할 때 사용. lawSearch.do와 lawService.do 엔드포인트, target 파라미터로 기능 구분. 새로운 API 엔드포인트 통합 시 참조.
---

# API 통합 가이드

법제처 OPEN API를 MCP 프로젝트에 통합하는 방법입니다.

## API 레이아웃 (JSON)

추출된 API 정보는 JSON 파일로 관리됩니다:

**위치**: `src/mcp_kr_legislation/utils/api_layout/`

| 파일 | 카테고리 |
|------|----------|
| `law.json` | 법령 |
| `admin_rule.json` | 행정규칙 |
| `local_ordinance.json` | 자치법규 |
| `precedent.json` | 판례 |
| `committee.json` | 위원회결정문 |
| `ministry_interpretation_1.json` | 중앙부처 1차 해석 |
| `ministry_interpretation_2.json` | 중앙부처 2차 해석 |
| `special_tribunal.json` | 특별행정심판 |
| ... | 기타 카테고리 |

### JSON 구조
```json
{
  "category": "법령",
  "category_en": "law",
  "updated_at": "2026-01-21",
  "api_count": 26,
  "apis": [
    {
      "id": "1.1",
      "title": "현행법령(시행일) 목록 조회 API",
      "request_url": "http://www.law.go.kr/DRF/lawSearch.do?target=eflaw",
      "target": "eflaw",
      "api_type": "목록조회",
      "parameters": [...],
      "sample_urls": [...]
    }
  ]
}
```

## API 구조

### 핵심 URL 패턴

| 기능 | URL 패턴 | 설명 |
|------|----------|------|
| **목록 조회** | `lawSearch.do?target={value}` | 검색/목록 반환 |
| **본문 조회** | `lawService.do?target={value}` | 상세 내용 반환 |

### target 파라미터가 기능 결정

- 동일한 URL에서 `target` 값만으로 API 카테고리 구분
- 목록/본문 조회는 URL로, 카테고리는 target으로 결정

**전체 target 목록**: [targets.md](targets.md)

## LegislationClient 사용

```python
from mcp_kr_legislation.apis.client import LegislationClient
from mcp_kr_legislation.config import legislation_config

# 클라이언트 초기화
client = LegislationClient(config=legislation_config)

# 목록 조회
result = client.search(
    target="law",
    params={"query": "개인정보보호법", "display": 20}
)

# 본문 조회
detail = client.service(
    target="law",
    params={"ID": "법령ID"}
)
```

## Tool에서 API 호출

```python
from mcp_kr_legislation.utils.ctx_helper import with_context

@mcp.tool(name="search_law")
def search_law(query: str) -> TextContent:
    result = with_context(
        None,
        "search_law",
        lambda context: context.law_api.search(
            target="law",
            query=query
        )
    )
    return TextContent(type="text", text=str(result))
```

## 주요 파라미터

**공통**: `OC` (자동 추가), `target` (필수), `type` (JSON/XML/HTML)

**검색**: `query`, `display` (기본 20, 최대 100), `page`, `sort`

**상세 조회**: `ID` (필수)

## 유틸리티 스크립트

### 단일 API 테스트
```bash
python scripts/test_api.py law "개인정보보호법"
```

### 전체 API 회귀 테스트
```bash
# 모든 API 테스트
python scripts/test_regression.py

# 특정 카테고리만 테스트
python scripts/test_regression.py --category 법령
python scripts/test_regression.py --category 판례

# 상세 출력
python scripts/test_regression.py --verbose
```

### 도구 구현 완성도 체크
```bash
python scripts/test_tool_coverage.py
```
API 가이드의 API 목록과 실제 구현된 도구를 비교하여 미구현/불일치 항목을 확인합니다.

## 주의사항

1. **OC 값 자동 처리**: `LegislationClient`가 환경변수에서 자동 추가
2. **target 값 확인**: 잘못된 target은 빈 결과 반환
3. **타임아웃**: 기본 30초, `REQUEST_TIMEOUT` 환경변수로 변경 가능

## 도구 결과가 잘못된 경우 - 공식 가이드에서 직접 검증

도구가 예상과 다른 결과를 반환하거나 오류가 발생할 경우, 
**반드시 공식 가이드에서 샘플 URL을 직접 테스트**하여 API 동작을 확인해야 합니다.

> ⚠️ **중요**: 공식 가이드에 있는 모든 API는 정상 동작하는 것으로 간주합니다.
> "지원/미지원" 표현 대신 데이터 건수 확인 및 파라미터 조정으로 대응합니다.

### 검증 절차 (Step by Step)

#### Step 1: 공식 가이드 접속
- **URL**: https://open.law.go.kr/LSO/openApi/guideList.do
- 좌측 메뉴에서 API 카테고리 확인 가능

#### Step 2: 해당 API 찾기 및 선택
1. 좌측 메뉴에서 카테고리 확장 (예: "중앙부처해석", "특별행정심판")
2. 해당 부처/기관 클릭
3. "목록 조회" 또는 "본문 조회" 링크 클릭하여 상세 페이지로 이동

#### Step 3: 샘플 URL 직접 클릭하여 테스트
가이드 상세 페이지에는 보통 다음과 같은 샘플 URL이 있습니다:
- **JSON 검색**: `...lawSearch.do?OC=test&target=XXX&type=JSON...`
- **XML 검색**: `...lawSearch.do?OC=test&target=XXX&type=XML...`
- **HTML 검색**: `...lawSearch.do?OC=test&target=XXX&type=HTML...`

**직접 클릭**하여 브라우저에서 응답 확인:
- ✅ JSON 객체가 보이면 정상
- ✅ `totalCnt` 값 확인 (데이터 건수)
- ❌ 404 오류 → target 값 확인 필요
- ❌ 빈 응답 → 검색어/파라미터 확인

#### Step 4: target 값 추출 및 코드에 적용
샘플 URL에서 `target=XXX` 부분을 확인하여 코드에 적용:
```
# 샘플 URL 예시
http://www.law.go.kr/DRF/lawSearch.do?OC=test&target=moeCgmExpc&type=JSON&ID=411648
                                               ^^^^^^^^^^^
                                               이 값이 target

# 코드에 적용
data = _make_legislation_request("moeCgmExpc", params)
```

#### Step 5: 응답 구조 확인 및 파싱 로직 점검
응답 JSON의 루트 키와 데이터 리스트 키를 확인:
```json
{
  "CgmExpcSearch": {       // 루트 키
    "totalCnt": "123",
    "CgmExpc": [...]       // 데이터 리스트 키
  }
}
```

### 최근 검증된 target 값들 (2026-01-21)

| 카테고리 | target | 기관/부처 | 검증 방법 |
|---------|--------|----------|----------|
| 중앙부처해석 | `kostatCgmExpc` | 국가데이터처 | 공식 가이드 직접 확인 |
| 중앙부처해석 | `kipoCgmExpc` | 지식재산처 | 공식 가이드 직접 확인 |
| 중앙부처해석 | `naaccCgmExpc` | 행정중심복합도시건설청 | 공식 가이드 직접 확인 |
| 특별행정심판 | `acrSpecialDecc` | 국민권익위원회 | 공식 가이드 직접 확인 |
| 특별행정심판 | `adapSpecialDecc` | 인사혁신처 소청심사 | 공식 가이드 직접 확인 |

### 샘플 URL 예시 (공식 가이드에서 확인 가능)

```
# 중앙부처해석 (기획재정부)
http://www.law.go.kr/DRF/lawSearch.do?OC=test&target=moefCgmExpc&type=JSON&query=조세

# 중앙부처해석 (교육부) - ID 직접 조회
http://www.law.go.kr/DRF/lawService.do?OC=test&target=moeCgmExpc&ID=411648&type=JSON

# 특별행정심판 (조세심판원)
http://www.law.go.kr/DRF/lawSearch.do?OC=test&target=ttSpecialDecc&type=JSON

# 특별행정심판 (국민권익위원회)
http://www.law.go.kr/DRF/lawSearch.do?OC=test&target=acrSpecialDecc&type=JSON

# 법령 검색
http://www.law.go.kr/DRF/lawSearch.do?OC=test&target=law&type=JSON&query=개인정보보호법
```

### 체크포인트

- [ ] 공식 가이드의 target 값과 코드의 target 값이 일치하는가?
- [ ] 필수 파라미터(OC, target, type)가 올바르게 전달되는가?
- [ ] 브라우저에서 샘플 URL 호출 시 정상 응답이 오는가?
- [ ] JSON/XML 응답 구조가 코드의 파싱 로직과 일치하는가?
- [ ] `Referer: https://open.law.go.kr/` 헤더가 코드에 포함되어 있는가?

### Troubleshooting

| 증상 | 원인 | 해결 |
|-----|-----|-----|
| 404 Not Found | target 값 오류 | 공식 가이드에서 정확한 target 확인 |
| 빈 응답 (totalCnt: 0) | 검색어/파라미터 문제 | 다른 검색어 시도 또는 query 없이 호출 |
| JSON 파싱 오류 | HTML 응답 반환됨 | `type=JSON` 파라미터 확인 |
| 권한 오류 | Referer 헤더 누락 | client.py에 Referer 헤더 추가 |

## API 정보 추출 도구

### 크롤러 (Playwright 기반)
```bash
# 공식 가이드에서 API 정보 크롤링
python src/mcp_kr_legislation/utils/api_crawler.py
```
- Playwright로 JavaScript 동적 페이지 처리
- 구분별 JSON 파일 자동 생성

### Markdown → JSON 변환
```bash
# 기존 Markdown 파일을 JSON으로 변환
python src/mcp_kr_legislation/utils/api_md_to_json.py [input_file]
```

## 관련 파일

- [src/mcp_kr_legislation/apis/client.py](../../src/mcp_kr_legislation/apis/client.py) - LegislationClient 구현
- [src/mcp_kr_legislation/utils/api_layout/](../../src/mcp_kr_legislation/utils/api_layout/) - API JSON 파일
- [src/mcp_kr_legislation/utils/api_crawler.py](../../src/mcp_kr_legislation/utils/api_crawler.py) - API 크롤러
- [docs/api-master-guide.md](../../docs/api-master-guide.md) - 전체 API 가이드
