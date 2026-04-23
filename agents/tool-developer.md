# Tool Developer Agent

## Purpose
법제처 OPEN API를 MCP 도구로 변환합니다.

## Primary Responsibilities
- api_layout/*.json 기반으로 새 MCP 도구 구현
- 기존 도구의 버그 수정
- 도구 파라미터 설계 및 설명 작성

## Required Inputs
- `api_layout/{category}.json` — API 스펙
- `skills/tool-development/SKILL.md` — 개발 가이드
- `skills/api-integration/targets.md` — target 값 목록

## Tool Development Pattern
```python
# 1. api_layout에서 target 확인
# 2. 샘플 URL 직접 호출하여 응답 구조 파악
# 3. 도구 구현

@mcp.tool(
    name="search_{category}",
    description="...[파라미터 설명 + 사용 예시]...",
    tags={"{category}", "검색"},
)
def search_{category}(
    query: Annotated[str, "검색어"],
    display: Annotated[int, "결과 수 (기본 20)"] = 20,
) -> TextContent:
    params = {"query": query, "display": display}
    data = _make_legislation_request("{target}", params, use_cache=True)
    # 결과 파싱 및 포맷팅
```

## 도구 구현 후 필수 검증
```bash
# 1. 모듈 import 테스트
uv run python3 -c "from mcp_kr_legislation.tools.{module} import *"

# 2. 실제 API 호출
uv run python3 -c "
from mcp_kr_legislation.tools.{module} import {tool_name}
result = {tool_name}('개인정보')
print(result.text[:200])
"
```

## Handoff
완료 후 → api-verifier에게 검증 요청
