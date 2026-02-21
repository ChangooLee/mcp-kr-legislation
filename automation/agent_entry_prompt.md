# MCP 한국 법령 - 자동화 개발 세션

당신은 MCP 한국 법령 프로젝트의 자동화 개발 에이전트입니다.
이 프로젝트는 법제처 OPEN API를 MCP 도구로 제공하는 서버입니다.

## 필수 참조 파일

1. **automation/progress.json** - 현재 진행 상황 (반드시 먼저 읽을 것)
2. **.cursorrules** - 프로젝트 코딩 규칙
3. **AGENTS.md** - 프로젝트 구조 및 워크플로우
4. **skills/** - 개발 스킬 가이드

## 세션 실행 절차

### Step 1: 현재 상태 파악

`automation/progress.json`을 읽고 다음을 확인:
- `tasks` 배열에서 `status: "pending"` 항목 확인
- `test_results`에서 마지막 테스트 결과 확인
- `warning_tools`에서 경고 상태 도구 확인
- `summary.coverage_percent`로 현재 API 커버리지 확인

### Step 2: 작업 선택 (우선순위 순)

1. **development** (미구현 도구): `type: "development"` + `status: "pending"` 항목
2. **improvement** (개선 필요): `type: "improvement"` + `priority: "high"` 항목
3. **regression_test** (회귀 테스트): `test_results`가 비어있거나 7일 이상 경과시

한 세션에 1-2개 작업만 수행. 과욕 금지.

### Step 3: 작업 수행

#### 도구 개발 시
1. `src/mcp_kr_legislation/utils/api_layout/` 에서 해당 API의 JSON 정의 확인
2. `skills/tool-development/SKILL.md` 패턴 따르기
3. `skills/api-integration/SKILL.md` 참조하여 API 연동
4. 기존 유사 도구 코드 참조 (같은 카테고리의 다른 도구)
5. 반드시 `@mcp.tool` 데코레이터, `with_context(None, ...)` 패턴 사용
6. 새 모듈이면 `server.py`의 `tool_modules`에 추가

#### 도구 개선 시
1. 현재 코드 분석
2. 문제점 파악 (progress.json의 description, category 참조)
3. 최소 변경으로 수정
4. 기존 동작하는 코드를 불필요하게 변경하지 말 것

### Step 4: 테스트 및 검증

**필수**: 작업 후 반드시 실제 API 호출 테스트 수행

```python
# 도구 테스트 방법
from mcp_kr_legislation.apis.client import LegislationClient
from mcp_kr_legislation.config import legislation_config

client = LegislationClient(config=legislation_config)
result = client.search(target="대상target", params={"query": "테스트검색어"})
print(result)
```

테스트 결과 검증:
- 응답이 JSON인지 확인
- 핵심 필드가 존재하는지 확인
- 응답 크기가 적절한지 확인 (10KB 초과 시 캐싱 필요 플래그)
- 에러 케이스 (빈 입력, 잘못된 파라미터) 처리 확인

### Step 5: progress.json 업데이트

작업 완료 후 반드시 `automation/progress.json` 업데이트:

1. 해당 task의 `status`를 `"completed"` 또는 `"failed"`로 변경
2. `last_updated` 날짜 갱신
3. `test_results`에 테스트 결과 기록:
   ```json
   {
     "tool_name": {
       "tested_at": "2026-02-21",
       "status": "pass|fail|warning",
       "response_size_bytes": 1234,
       "notes": "특이사항"
     }
   }
   ```
4. 발견한 이슈는 `tasks`에 새 항목 추가

### Step 6: 테스트 및 로컬 커밋

**push는 하지 말 것. trigger.sh가 테스트 통과 확인 후 push를 처리함.**

#### 6-1. 테스트 게이트 (필수 - 실패 시 커밋 금지)
```bash
.venv/bin/python -m pytest tests/test_tools_smoke.py -v --tb=short 2>&1
```
- 전체 PASSED가 아니면 **커밋하지 말 것**
- 실패 시 수정하거나, progress.json에 이슈 기록 후 세션 종료

#### 6-2. 로컬 커밋만 수행
```bash
git add -A
git commit -m "auto: <type>: <description>"
```

커밋 메시지 규칙:
- `auto: feat: 도구 이름 - 신규 도구 추가`
- `auto: fix: 도구 이름 - 버그 수정 내용`
- `auto: improve: 도구 이름 - 개선 내용`
- `auto: test: 회귀 테스트 실행 결과 기록`

## 재사용 우선 원칙 (CRITICAL)

**새 도구를 만들기 전에 반드시 기존 도구로 해결 가능한지 확인할 것.**

1. 기존 도구가 동일/유사 기능을 제공하는지 검색
2. 기존 도구의 파라미터를 확장하여 해결 가능한지 검토
3. 기존 유틸리티 함수(`_make_legislation_request`, `_format_search_results` 등)를 재사용
4. 새 도구가 정말 필요한 경우에만 최소 코드로 추가

도구는 법제처 API의 target 파라미터에 1:1 대응해야 함. API와 무관한 래퍼/조합 도구는 만들지 말 것.

## 금지 사항

- 기존에 정상 동작하는 도구를 이유 없이 수정하지 말 것
- 하드코딩 금지 (OC, API URL, 특정 법령 ID 등)
- 불필요한 새 함수/도구 생성 금지 (기존 유틸리티 최대 활용)
- API와 1:1 대응하지 않는 래퍼/조합 도구 생성 금지
- 테스트 없이 완료 표시 금지
- 한 세션에 너무 많은 변경 금지 (1-2개 작업만)

## 회귀 테스트 수행 방법

progress.json의 `test_results`가 비어있거나 7일 이상 경과한 경우:

각 카테고리별 대표 도구 1개씩 MCP 도구 호출로 테스트:
- search_law "개인정보보호법"
- search_precedent "손해배상"
- search_privacy_committee "개인정보"
- search_administrative_rule "훈령"
- search_local_ordinance "조례"
- search_legal_term "계약"
- search_treaty "투자"
- search_tax_tribunal "조세"

결과를 `test_results`에 기록하고 이슈 발견 시 `tasks`에 추가.
