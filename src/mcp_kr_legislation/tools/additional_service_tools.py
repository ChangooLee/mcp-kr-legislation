"""
한국 법제처 OPEN API - 부가서비스 도구들

지식베이스, FAQ, 질의응답, 상담, 민원 등 부가서비스 검색 기능을 제공합니다.
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

# 유틸리티 함수들 import
from .law_tools import (
    _make_legislation_request,
    _generate_api_url,
    _format_search_results
)

# ===========================================
# 부가서비스 도구들 (6개)
# ===========================================

@mcp.tool(name="search_knowledge_base", description="지식베이스를 검색합니다. 법령 관련 지식과 정보를 종합적으로 제공합니다.")
def search_knowledge_base(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """지식베이스 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "knowledge", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("knowledge", params)
        result = _format_search_results(data, "knowledge", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"지식베이스 검색 중 오류: {str(e)}")

@mcp.tool(name="search_faq", description="자주 묻는 질문을 검색합니다. 법령 관련 FAQ 정보를 제공합니다.")
def search_faq(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """FAQ 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "faq", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("faq", params)
        result = _format_search_results(data, "faq", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"FAQ 검색 중 오류: {str(e)}")

@mcp.tool(name="search_qna", description="질의응답을 검색합니다. 법령 관련 질의응답 정보를 제공합니다.")
def search_qna(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """질의응답 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "qna", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("qna", params)
        result = _format_search_results(data, "qna", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"질의응답 검색 중 오류: {str(e)}")

@mcp.tool(name="search_counsel", description="상담 내용을 검색합니다. 법령 상담 사례와 답변을 제공합니다.")
def search_counsel(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """상담 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "counsel", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("counsel", params)
        result = _format_search_results(data, "counsel", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"상담 검색 중 오류: {str(e)}")

@mcp.tool(name="search_precedent_counsel", description="판례 상담을 검색합니다. 판례 관련 상담 사례와 답변을 제공합니다.")
def search_precedent_counsel(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """판례 상담 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "precCounsel", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("precCounsel", params)
        result = _format_search_results(data, "precCounsel", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"판례 상담 검색 중 오류: {str(e)}")

@mcp.tool(name="search_civil_petition", description="민원을 검색합니다. 법령 관련 민원 사례와 처리 현황을 제공합니다.")
def search_civil_petition(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """민원 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "minwon", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("minwon", params)
        result = _format_search_results(data, "minwon", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"민원 검색 중 오류: {str(e)}") 