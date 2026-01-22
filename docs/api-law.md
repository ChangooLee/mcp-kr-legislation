# 법령 API 가이드

> 법령 관련 API 상세 가이드
> 전체 내용은 [전체 API 가이드](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md)의 "법령" 섹션 참고

## 개요

법령 관련 API는 현행법령, 시행일법령, 영문법령, 법령연혁, 조문, 체계도, 연계정보 등을 제공합니다.

## 주요 API

### 1. 현행법령

**목록 조회**: `lawSearch.do?target=law`
- **도구**: `search_law`
- **파라미터**: `query`, `display`, `page`, `sort`, `search` 등

**본문 조회**: `lawService.do?target=law`
- **도구**: `get_law_detail`
- **파라미터**: `ID` 또는 `MST` (필수)

### 2. 시행일법령

**목록 조회**: `lawSearch.do?target=eflaw`
- **도구**: `search_effective_law`
- **특수 파라미터**: `nw` (1: 연혁, 2: 시행예정, 3: 현행)

**본문 조회**: `lawService.do?target=eflaw`
- **도구**: `get_effective_law_detail`
- **파라미터**: `ID` 또는 `MST`, `efYd` (시행일자, 필수)

### 3. 영문법령

**목록 조회**: `lawSearch.do?target=elaw`
- **도구**: `search_english_law`

**본문 조회**: `lawService.do?target=elaw`
- **도구**: `get_english_law_detail`

### 4. 법령 조문

**현행법령 조문**: `lawService.do?target=lawjosub`
- **도구**: `get_current_law_articles`, `search_law_articles`
- **파라미터**: `ID` 또는 `MST`, `JO` (조번호, 선택)

**시행일법령 조문**: `lawService.do?target=eflawjosub`
- **도구**: `get_effective_law_articles`

### 5. 법령 연혁

**목록 조회**: `lawSearch.do?target=lsHistory`
- **도구**: `search_law_history`
- **참고**: HTML 응답만 지원

### 6. 법령 변경이력

**변경이력 목록**: `lawSearch.do?target=lsHstInf`
- **도구**: `search_law_change_history`

**일자별 조문 개정 이력**: `lawSearch.do?target=lsJoHstInf`
- **도구**: `search_daily_article_revision`

**조문별 변경 이력**: `lawSearch.do?target=lsJoHstInf`
- **도구**: `search_article_change_history`

### 7. 법령 연계

**자치법규 연계**: `lawSearch.do?target=lnkLs`
- **도구**: `search_law_ordinance_link`
- **파라미터**: `knd` (법령ID, 필수)

**위임법령 조회**: `lawService.do?target=lsDelegated`
- **도구**: `get_delegated_law`

### 8. 부가서비스

**체계도**: `lawSearch.do?target=lsStmd` / `lawService.do?target=lsStmd`
- **도구**: `search_law_system_diagram`, `get_law_system_diagram_detail`

**신구법 비교**: `lawSearch.do?target=oldAndNew` / `lawService.do?target=oldAndNew`
- **도구**: `search_old_and_new_law`, `get_old_and_new_law_detail`

**3단 비교**: `lawSearch.do?target=thdCmp` / `lawService.do?target=thdCmp`
- **도구**: `search_three_way_comparison`, `get_three_way_comparison_detail`

**법률명 약칭**: `lawSearch.do?target=lsAbrv`
- **도구**: `search_law_nickname`

**삭제 데이터**: `lawSearch.do?target=datDel`
- **도구**: `search_deleted_law_data`

**한눈보기**: `lawSearch.do?target=oneview` / `lawService.do?target=oneview`
- **도구**: `search_one_view`, `get_one_view_detail`

**별표·서식**: `lawSearch.do?target=licbyl` / `lawService.do?target=licbyl`
- **도구**: `search_law_appendix`, `get_law_appendix_detail`

## 공통 파라미터

### 목록 조회 공통 파라미터
- `OC`: 사용자 이메일 ID (자동 추가)
- `target`: 서비스 대상 (필수)
- `type`: 출력 형태 (JSON, XML, HTML, 기본값: JSON)
- `query`: 검색어
- `display`: 결과 개수 (기본값: 20, 최대: 100)
- `page`: 페이지 번호 (기본값: 1)
- `sort`: 정렬옵션 (lasc, ldes, dasc, ddes, nasc, ndes, efasc, efdes)
- `search`: 검색범위 (1=법령명, 2=본문검색)

### 본문 조회 공통 파라미터
- `OC`: 사용자 이메일 ID (자동 추가)
- `target`: 서비스 대상 (필수)
- `type`: 출력 형태 (JSON, XML, HTML, 기본값: JSON)
- `ID`: 법령 ID (ID 또는 MST 중 하나 필수)
- `MST`: 법령 마스터 번호 (ID 대신 사용 가능)
- `JO`: 조번호 (선택, 생략 시 모든 조 표시)
- `LANG`: 원문/한글 여부 (KO: 한글, ORI: 원문)

## 응답 필드

### 목록 조회 응답
- `totalCnt`: 검색건수
- `page`: 결과페이지번호
- `law`: 법령 목록 배열
  - `법령ID`: 법령ID
  - `법령명한글`: 법령명
  - `법령약칭명`: 법령약칭
  - `공포일자`: 공포일자
  - `시행일자`: 시행일자
  - `소관부처명`: 소관부처
  - `법령일련번호`: 법령일련번호 (MST)

### 본문 조회 응답
- `법령ID`: 법령ID
- `법령명_한글`: 법령명
- `공포일자`: 공포일자
- `시행일자`: 시행일자
- `소관부처`: 소관부처명
- `조문`: 조문 배열
  - `조문번호`: 조문번호
  - `조문제목`: 조문제목
  - `조문내용`: 조문내용
  - `항`: 항 배열
    - `항번호`: 항번호
    - `항내용`: 항내용
    - `호`: 호 배열
      - `호번호`: 호번호
      - `호내용`: 호내용

## 사용 예시

### 법령 검색
```python
# 목록 조회
result = client.search("law", {
    "query": "개인정보보호법",
    "display": 20
})

# 본문 조회
law_id = result["law"][0]["법령ID"]
detail = client.service("law", {"ID": law_id})
```

### 시행일법령 검색
```python
# 목록 조회 (현행만)
result = client.search("eflaw", {
    "query": "개인정보보호법",
    "nw": 3  # 현행만
})

# 본문 조회
detail = client.service("eflaw", {
    "MST": mst,
    "efYd": "20250101"  # 시행일자 필수
})
```

### 조문 조회
```python
# 특정 조문만 조회
articles = client.service("lawjosub", {
    "ID": law_id,
    "JO": 3  # 3조만
})
```

## 관련 문서

- [API 마스터 가이드](api-master-guide.md)
- [전체 API 가이드 - 법령 섹션](../src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md#법령)
