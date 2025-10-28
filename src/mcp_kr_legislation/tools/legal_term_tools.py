"""
한국 법제처 OPEN API - 법령용어 도구들

법령용어 검색, AI 기반 검색, 연계정보 조회 등 법령용어 관련 기능을 제공합니다.
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
# 법령용어 도구들 (6개)
# ===========================================

@mcp.tool(name="search_legal_term", description="법령용어를 검색합니다. 법률 용어의 정의와 설명을 조회할 수 있습니다.")
def search_legal_term(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령용어 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "legalTerm", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("legalTerm", params)
        result = _format_search_results(data, "legalTerm", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법령용어 검색 중 오류: {str(e)}")

@mcp.tool(name="search_legal_term_ai", description="법령용어 AI 지식베이스를 검색합니다. AI 기반으로 법령용어의 정의와 해석을 제공합니다.")
def search_legal_term_ai(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령용어 AI 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "legalTermAi", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("legalTermAi", params)
        result = _format_search_results(data, "legalTermAi", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법령용어 AI 검색 중 오류: {str(e)}")

@mcp.tool(name="search_daily_legal_term_link", description="일상용어-법령용어 연계 정보를 검색합니다. 일상용어에서 법령용어로의 연관관계를 조회할 수 있습니다.")
def search_daily_legal_term_link(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """일상용어-법령용어 연계 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "dailyLegalTermLink", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("dailyLegalTermLink", params)
        result = _format_search_results(data, "dailyLegalTermLink", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"일상용어-법령용어 연계 검색 중 오류: {str(e)}")

@mcp.tool(name="search_legal_term_article_link", description="법령용어-조문 연계 정보를 검색합니다. 법령용어가 사용된 조문들의 연관관계를 조회할 수 있습니다.")
def search_legal_term_article_link(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령용어-조문 연계 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "legalTermArticleLink", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("legalTermArticleLink", params)
        result = _format_search_results(data, "legalTermArticleLink", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법령용어-조문 연계 검색 중 오류: {str(e)}")

@mcp.tool(name="search_article_legal_term_link", description="조문-법령용어 연계 정보를 검색합니다. 조문에서 사용된 법령용어들의 연관관계를 조회할 수 있습니다.")
def search_article_legal_term_link(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """조문-법령용어 연계 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="❌ 검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "articleLegalTermLink", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("articleLegalTermLink", params)
        result = _format_search_results(data, "articleLegalTermLink", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"조문-법령용어 연계 검색 중 오류: {str(e)}")

@mcp.tool(name="get_legal_term_detail", description="법령용어 상세내용을 조회합니다. 특정 법령용어의 정의와 설명을 제공합니다. 목록 검색은 search_legal_term 도구를 사용하세요.")
def get_legal_term_detail(term_id: Union[str, int]) -> TextContent:
    """법령용어 상세 조회"""
    params = {"ID": str(term_id)}
    try:
        data = _make_legislation_request("legalTerm", params, is_detail=True)
        url = _generate_api_url("legalTerm", params, is_detail=True)
        result = _format_search_results(data, "legalTerm", str(term_id), 50)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법령용어 상세조회 중 오류: {str(e)}") 