"""
한국 법제처 OPEN API - 연계정보 도구들

법령용어-일상용어 연계 등 용어 관련 연계정보 조회 기능을 제공합니다.
"""

import logging
import json
import os
import requests
from urllib.parse import urlencode
from typing import Optional, Union, Annotated
from mcp.types import TextContent

from ..server import mcp
from ..config import legislation_config

logger = logging.getLogger(__name__)

# 유틸리티 함수들 import (law_tools로 변경)
from .law_tools import (
    _make_legislation_request,
    _generate_api_url,
    _format_search_results
)

# ===========================================
# 연계정보 도구들 (용어 관련)
# ===========================================

@mcp.tool(name="search_daily_term", description="""일상용어를 검색합니다.

매개변수:
- query: 일상용어 검색어 (선택)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_daily_term("계약"), search_daily_term("근로시간", display=50)""")
def search_daily_term(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """일상용어 검색
    
    Args:
        query: 검색어 (일상용어)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정
        params = {
            "target": "dailyTerm",
            "display": min(display, 100),
            "page": page
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            search_query = query.strip()
            params["query"] = search_query
        else:
            search_query = "일상용어"
        
        # API 요청
        data = _make_legislation_request("dlytrmGuide", params)
        result = _format_search_results(data, "dailyTerm", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"일상용어 검색 중 오류: {e}")
        return TextContent(type="text", text=f"일상용어 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="search_legal_daily_term_link", description="""법령용어-일상용어 연계 정보를 검색합니다.

매개변수:
- query: 법령용어 또는 일상용어 검색어 (선택)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_legal_daily_term_link("채권"), search_legal_daily_term_link("계약", display=50)
참고: 법령용어와 일상용어 간의 대응 관계를 확인할 수 있습니다.""")
def search_legal_daily_term_link(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령용어-일상용어 연계 정보 검색
    
    Args:
        query: 검색어 (법령용어 또는 일상용어)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정
        params = {
            "target": "legalDailyTermLink",
            "display": min(display, 100),
            "page": page
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            search_query = query.strip()
            params["query"] = search_query
        else:
            search_query = "법령용어-일상용어 연계"
        
        # API 요청
        data = _make_legislation_request("dlytrmRltGuide", params)
        result = _format_search_results(data, "legalDailyTermLink", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"법령용어-일상용어 연계 검색 중 오류: {e}")
        return TextContent(type="text", text=f"법령용어-일상용어 연계 검색 중 오류가 발생했습니다: {str(e)}") 