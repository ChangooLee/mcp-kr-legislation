---
name: tool-development
description: 법제처 API를 MCP tool로 추가할 때 사용. @mcp.tool 데코레이터, Annotated 타입힌트, with_context 패턴 필수. 새로운 tool 파일 생성 또는 기존 파일 수정 시 참조.
---

# Tool 개발 가이드

법제처 API 기능을 MCP tool로 노출하는 방법입니다.

## 핵심 패턴

### 1. 기본 구조

```python
from typing import Annotated
from mcp_kr_legislation.server import mcp
from mcp.types import TextContent
from mcp_kr_legislation.utils.ctx_helper import with_context

@mcp.tool(
    name="tool_name",
    description="도구 설명 (LLM이 이해할 수 있도록 명확하게)",
)
def tool_function(
    param1: Annotated[str, "파라미터 설명"],
) -> TextContent:
    result = with_context(
        None,  # ctx 파라미터 제거됨
        "tool_name",
        lambda context: context.law_api.search(param1)
    )
    return TextContent(type="text", text=str(result))
```

### 2. 필수 규칙

- **ctx 파라미터 절대 사용 금지**: `with_context(None, ...)` 사용
- **Annotated 필수**: 모든 파라미터에 `Annotated[Type, "description"]` 사용
- **with_context() 래핑**: 모든 API 호출은 `with_context()`로 래핑

### 3. Tool 파일 선택

카테고리별 tool 파일:
- `law_tools.py` - 법령 관련
- `precedent_tools.py` - 판례 관련
- `committee_tools.py` - 위원회결정문 관련
- 기타 카테고리별 파일

### 4. 모듈 등록

새 tool 파일 생성 시 `server.py`의 `tool_modules` 리스트에 추가:

```python
tool_modules = [
    "law_tools",
    "new_tool_module",  # 추가
]
```

## 상세 예제

복잡한 구현 예제는 [examples.md](examples.md) 참조.

## 유틸리티 스크립트

Tool 시그니처 검증:
```bash
python scripts/validate_tool.py src/mcp_kr_legislation/tools/law_tools.py
```

Tool 실행 테스트:
```bash
python scripts/test_tool.py search_law "개인정보보호법"
```

## 관련 파일

- [src/mcp_kr_legislation/tools/](../src/mcp_kr_legislation/tools/) - Tool 구현 예제
- [src/mcp_kr_legislation/utils/ctx_helper.py](../src/mcp_kr_legislation/utils/ctx_helper.py) - with_context 함수
- [docs/api-master-guide.md](../../docs/api-master-guide.md) - API target 값 참고
