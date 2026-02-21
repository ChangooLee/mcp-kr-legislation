"""
지능형 법령검색 시스템 API 도구

- aiRltLs: 연관법령 API (질의어에 대한 연관 법령 조문 목록)
- aiSearch: 지능형 검색 API (별도 도구에서 제공 시 동일 패턴으로 추가 가능)
"""

import logging
from typing import Annotated

from mcp.types import TextContent

from mcp_kr_legislation.server import mcp
from mcp_kr_legislation.tools.law_tools import (
    _make_legislation_request,
    _format_search_results,
)

logger = logging.getLogger(__name__)


@mcp.tool(
    name="search_ai_related_law",
    description="지능형 법령검색 시스템 연관법령 API. 질의어에 대해 연관된 법령 조문 목록을 반환합니다. "
    "query로 검색어를 넣고, search는 검색범위(0: 법령조문, 1: 행정규칙조문)를 지정합니다.",
)
def search_ai_related_law(
    query: Annotated[str, "연관 법령을 찾을 검색어 (예: 뺑소니, 개인정보)"],
    search: Annotated[int, "검색범위 (0: 법령조문, 1: 행정규칙조문). 기본 0"] = 0,
) -> TextContent:
    """지능형 법령검색 연관법령 조회 (target=aiRltLs)."""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    search_val = 0 if search not in (0, 1) else search
    params = {"query": query.strip(), "search": search_val}
    try:
        data = _make_legislation_request("aiRltLs", params)
        if data.get("error"):
            return TextContent(type="text", text=f"오류: {data['error']}")
        result = _format_search_results(data, "aiRltLs", query.strip())
        return TextContent(type="text", text=result)
    except Exception as e:
        logger.exception("search_ai_related_law failed")
        return TextContent(type="text", text=f"연관법령 검색 중 오류: {str(e)}")
