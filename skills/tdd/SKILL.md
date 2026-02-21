---
name: test-driven-development
description: 새 도구 개발 또는 버그 수정 시 실패하는 테스트를 먼저 작성하고, 구현 후 통과를 확인. superpowers의 test-driven-development 기반.
---

# 테스트 주도 개발 (Test-Driven Development)

> 원본: [superpowers/test-driven-development](https://github.com/obra/superpowers)
> MCP 한국 법령 프로젝트에 맞게 커스터마이징

## 핵심 원칙

```
실패하는 테스트 없이 프로덕션 코드를 작성하지 않는다.
```

## RED-GREEN-REFACTOR 사이클

### RED: 실패하는 테스트 작성

**새 도구 개발 시**:

```python
# tests/test_api_regression.py에 추가
def test_new_tool_returns_results(self, legislation_client):
    result = legislation_client.search(
        target="NEW_TARGET",
        params={"query": "테스트", "type": "JSON", "display": 5}
    )
    assert result is not None
    assert not result.get("error")
```

**버그 수정 시**:

```python
# 버그를 재현하는 테스트
def test_tool_handles_empty_query(self, legislation_client):
    """빈 검색어에 대한 에러 처리 확인"""
    result = legislation_client.search(
        target="law",
        params={"query": "", "type": "JSON"}
    )
    # 빈 검색어에도 적절한 응답 반환
    assert result is not None
```

### 실패 확인 (필수)

```bash
.venv/bin/python -m pytest tests/test_api_regression.py::TestAPIRegression::test_new_tool -v
```

반드시 확인:
- 테스트가 **실패**하는지 (FAIL, not ERROR)
- 실패 이유가 **기능 미구현**인지 (오타 아닌지)

### GREEN: 최소 구현

도구를 구현하여 테스트를 통과시킴:

```python
@mcp.tool(name="new_tool", description="...")
def new_tool(query: Annotated[str, "..."]) -> TextContent:
    result = with_context(
        None, "new_tool",
        lambda context: context.law_api.search(
            target="NEW_TARGET", query=query
        )
    )
    return TextContent(type="text", text=str(result))
```

### 통과 확인 (필수)

```bash
# 새 테스트 통과 확인
.venv/bin/python -m pytest tests/test_api_regression.py::TestAPIRegression::test_new_tool -v

# 전체 테스트 회귀 확인
.venv/bin/python -m pytest tests/ -v --tb=short
```

### REFACTOR: 정리

테스트가 통과한 후에만:
- 중복 코드 제거
- 이름 개선
- 포맷팅 정리

정리 후에도 테스트가 통과하는지 재확인.

## 자동화 세션에서의 적용

1. progress.json에서 `type: "development"` 작업 선택
2. 해당 도구에 대한 테스트를 먼저 `tests/test_api_regression.py`에 추가
3. 테스트 실패 확인
4. 도구 구현
5. 테스트 통과 확인
6. progress.json 업데이트

## 예외 사항

- 기존 도구의 description 개선 등 동작 변경 없는 수정은 TDD 불필요
- HTML 전용 API (JSON 미지원)는 테스트 대상 제외
- 0건 반환 부처 등 데이터 자체가 없는 경우 테스트 기대값 조정
