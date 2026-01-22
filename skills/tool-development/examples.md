# Tool 개발 상세 예제

## 예제 1: 간단한 조회 Tool

```python
@mcp.tool(
    name="search_law",
    description="현행 법령 검색",
)
def search_law(
    query: Annotated[str, "법령명 또는 검색어"],
    display: Annotated[int, "결과 개수 (기본값: 20, 최대: 100)"] = 20,
) -> TextContent:
    """
    현행 법령 검색
    """
    result = with_context(
        None,
        "search_law",
        lambda context: context.law_api.search(
            target="law",
            query=query,
            display=display
        )
    )
    return TextContent(type="text", text=str(result))
```

## 예제 2: 복잡한 파라미터 Tool

```python
@mcp.tool(
    name="search_precedent",
    description="대법원 판례 검색",
)
def search_precedent(
    query: Annotated[str, "검색어"],
    date_from: Annotated[Optional[str], "시작일자 (YYYYMMDD)"] = None,
    date_to: Annotated[Optional[str], "종료일자 (YYYYMMDD)"] = None,
    display: Annotated[int, "결과 개수 (기본값: 20)"] = 20,
    page: Annotated[int, "페이지 번호 (기본값: 1)"] = 1,
) -> TextContent:
    params = {"query": query, "display": display, "page": page}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    
    result = with_context(
        None,
        "search_precedent",
        lambda context: context.law_api.search("prec", params)
    )
    return TextContent(type="text", text=str(result))
```

## 예제 3: 상세 조회 Tool

```python
@mcp.tool(
    name="get_law_detail",
    description="법령 상세 정보 조회",
)
def get_law_detail(
    law_id: Annotated[str, "법령 ID (법령목록 조회에서 얻은 ID)"],
) -> TextContent:
    result = with_context(
        None,
        "get_law_detail",
        lambda context: context.law_api.service(
            target="law",
            params={"ID": law_id}
        )
    )
    return TextContent(type="text", text=str(result))
```

## 예제 4: 비동기 Tool

```python
@mcp.tool(
    name="async_tool_name",
    description="비동기 도구 설명",
)
async def async_tool_function(
    param: Annotated[str, "파라미터 설명"],
) -> TextContent:
    from mcp_kr_legislation.utils.ctx_helper import with_context_async
    
    result = await with_context_async(
        None,
        "async_tool_name",
        lambda context: context.law_api.async_search(param)
    )
    return TextContent(type="text", text=str(result))
```

## 주의사항

1. **파라미터 설명 명확히 작성**
   - Annotated의 두 번째 인자에 상세 설명
   - 예시 값 포함 (예: "YYYYMMDD", "법령 ID")

2. **에러 처리**
   - API 호출 실패 시 적절한 에러 메시지 반환
   - `TextContent`로 일관된 형식 유지

3. **API target 값 확인**
   - 법제처 API는 `target` 파라미터로 기능 구분
   - 올바른 target 값 사용 확인
   - 참고: [docs/api-master-guide.md](../../docs/api-master-guide.md)
