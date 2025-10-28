"""
한국 법제처 OPEN API - 맞춤형 도구들

사용자 맞춤형 자치법규, 판례 분류에 따른 검색을 제공합니다.
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
# 맞춤형 도구들 (자치법규, 판례)
# ===========================================

@mcp.tool(name="search_custom_ordinance", description="""맞춤형 자치법규를 검색합니다.

매개변수:
- query: 검색어 (선택) - 자치법규명 또는 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_custom_ordinance("환경보호"), search_custom_ordinance("시설관리", display=50)
참고: 사용자 맞춤형으로 분류된 자치법규를 검색합니다.""")
def search_custom_ordinance(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 자치법규 검색
    
    Args:
        query: 검색어 (자치법규명)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정
        params = {
            "target": "customOrdinance",
            "display": min(display, 100),
            "page": page
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            search_query = query.strip()
            params["query"] = search_query
        else:
            search_query = "맞춤형 자치법규"
        
        # API 요청
        data = _make_legislation_request("custOrdinListGuide", params)
        result = _format_search_results(data, "customOrdinance", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"맞춤형 자치법규 검색 중 오류: {e}")
        return TextContent(type="text", text=f"맞춤형 자치법규 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="search_custom_ordinance_articles", description="""맞춤형 자치법규 조문을 검색합니다.

매개변수:
- query: 검색어 (선택) - 자치법규명 또는 조문 내용
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_custom_ordinance_articles("제1조"), search_custom_ordinance_articles("사용료", display=50)
참고: 사용자 맞춤형으로 분류된 자치법규의 조문별 내용을 검색합니다.""")
def search_custom_ordinance_articles(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 자치법규 조문 검색
    
    Args:
        query: 검색어 (자치법규명 또는 조문)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정
        params = {
            "target": "customOrdinanceArticles",
            "display": min(display, 100),
            "page": page
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            search_query = query.strip()
            params["query"] = search_query
        else:
            search_query = "맞춤형 자치법규 조문"
        
        # API 요청
        data = _make_legislation_request("custOrdinJoListGuide", params)
        result = _format_search_results(data, "customOrdinanceArticles", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"맞춤형 자치법규 조문 검색 중 오류: {e}")
        return TextContent(type="text", text=f"맞춤형 자치법규 조문 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="search_custom_precedent", description="""맞춤형 판례를 검색합니다.

매개변수:
- query: 검색어 (선택) - 판례 관련 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_custom_precedent("손해배상"), search_custom_precedent("계약해제", display=50)
참고: 사용자 맞춤형으로 분류된 판례를 검색합니다.""")
def search_custom_precedent(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 판례 검색
    
    Args:
        query: 검색어 (판례 관련)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정
        params = {
            "target": "customPrecedent",
            "display": min(display, 100),
            "page": page
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            search_query = query.strip()
            params["query"] = search_query
        else:
            search_query = "맞춤형 판례"
        
        # API 요청
        data = _make_legislation_request("custPrecListGuide", params)
        result = _format_search_results(data, "customPrecedent", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"맞춤형 판례 검색 중 오류: {e}")
        return TextContent(type="text", text=f"맞춤형 판례 검색 중 오류가 발생했습니다: {str(e)}")

# ===========================================
# 맞춤형 법령 도구들 (law_tools.py에서 이동)
# ===========================================

@mcp.tool(name="search_custom_law", description="""맞춤형 법령을 검색합니다.

매개변수:
- query: 검색어 (선택) - 법령명 또는 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 법령명, 법령ID, 맞춤분류, 분류일자, 소관부처

사용 예시:
- search_custom_law()  # 전체 맞춤형 법령 목록
- search_custom_law("중소기업")  # 중소기업 관련 맞춤형 법령
- search_custom_law("복지", display=30)  # 복지 관련 맞춤형 법령

참고: 특정 주제나 대상별로 분류된 맞춤형 법령을 검색할 때 사용합니다.""")
def search_custom_law(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 법령 검색
    
    Args:
        query: 검색어 (법령명)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정
        params = {
            "target": "couseLs",
            "display": min(display, 100),
            "page": page
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            search_query = query.strip()
            params["query"] = search_query
        else:
            search_query = "맞춤형 법령"
        
        # vcode 파라미터 추가 (필수)
        if "vcode" not in params:
            # 기본 분류코드 사용 (예시에서 사용된 코드)
            params["vcode"] = "L0000000003384"
        
        # API 요청
        data = _make_legislation_request("lawSearch", params)
        result = _format_search_results(data, "couseLs", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"맞춤형 법령 검색 중 오류: {e}")
        return TextContent(type="text", text=f"맞춤형 법령 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="search_custom_law_articles", description="""맞춤형 법령 조문을 검색합니다.

매개변수:
- query: 검색어 (선택) - 법령명 또는 조문 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 법령명, 조문번호, 조문제목, 조문내용, 맞춤분류

사용 예시:
- search_custom_law_articles()  # 전체 맞춤형 법령 조문
- search_custom_law_articles("창업")  # 창업 관련 맞춤형 조문
- search_custom_law_articles("지원", display=50)  # 지원 관련 조문

참고: 맞춤형으로 분류된 법령의 특정 조문들을 검색할 때 사용합니다.""")
def search_custom_law_articles(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 법령 조문 검색
    
    Args:
        query: 검색어 (법령명 또는 조문)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정
        params = {
            "target": "couseLs",
            "display": min(display, 100),
            "page": page
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            search_query = query.strip()
            params["query"] = search_query
        else:
            search_query = "맞춤형 법령 조문"
        
        # vcode와 lj=jo 파라미터 추가 (필수)
        if "vcode" not in params:
            # 기본 분류코드 사용 (예시에서 사용된 코드)
            params["vcode"] = "L0000000003384"
        params["lj"] = "jo"  # 조문 조회를 위한 필수 파라미터
        
        # API 요청
        data = _make_legislation_request("lawSearch", params)
        result = _format_search_results(data, "couseLs", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"맞춤형 법령 조문 검색 중 오류: {e}")
        return TextContent(type="text", text=f"맞춤형 법령 조문 검색 중 오류가 발생했습니다: {str(e)}") 