---
name: context-handling
description: Tool에서 API 호출 시 컨텍스트 처리. streamable-http와 stdio transport 모두 지원. with_context() 패턴으로 전역 컨텍스트 fallback 자동 처리.
---

# 컨텍스트 처리 가이드

Tool에서 API 호출 시 컨텍스트를 안전하게 처리하는 방법입니다.

## 핵심 패턴

### with_context() 사용

```python
from mcp_kr_legislation.utils.ctx_helper import with_context

@mcp.tool(name="search_law")
def search_law(query: str) -> TextContent:
    result = with_context(
        None,  # ctx 파라미터 제거됨
        "search_law",  # 로깅용 도구명
        lambda context: context.law_api.search(
            target="law",
            query=query
        )
    )
    return TextContent(type="text", text=str(result))
```

## 동작 방식

1. **MCP 컨텍스트 우선**: `ctx.request_context.lifespan_context` 사용 시도
2. **전역 컨텍스트 fallback**: 실패 시 자동으로 전역 컨텍스트 사용
3. **에러 처리**: 모든 예외를 안전하게 처리

## 컨텍스트 접근

```python
# ✅ context.law_api 사용
result = with_context(
    None,
    "tool_name",
    lambda context: context.law_api.search(...)
)

# ✅ context.legislation_api 사용
result = with_context(
    None,
    "tool_name",
    lambda context: context.legislation_api.search(...)
)

# ✅ context.client 직접 사용
result = with_context(
    None,
    "tool_name",
    lambda context: context.client.search(...)
)
```

## Transport별 동작

- **stdio Transport**: MCP context 정상 주입, 전역 컨텍스트는 fallback
- **streamable-http Transport**: MCP context 없을 수 있음, 자동 fallback

## 유틸리티 스크립트

컨텍스트 상태 확인:
```bash
python scripts/check_context.py
```

## 주의사항

1. **ctx 파라미터 절대 사용 금지**: Tool 시그니처에 포함하지 않음
2. **전역 컨텍스트 의존성**: 서버 시작 시 생성, 설정 오류 시 실패 가능
3. **로깅**: `with_context()`는 자동으로 로깅 (MCP vs 전역 구분)

## 관련 파일

- [src/mcp_kr_legislation/utils/ctx_helper.py](../../src/mcp_kr_legislation/utils/ctx_helper.py) - with_context 구현
- [src/mcp_kr_legislation/server.py](../../src/mcp_kr_legislation/server.py) - 전역 컨텍스트 생성
