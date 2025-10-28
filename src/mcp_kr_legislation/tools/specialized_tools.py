"""
한국 법제처 OPEN API - 전문화된 도구들

조약, 별표서식, 학칙공단, 심판원 등 전문화된 영역의 
검색 및 조회 기능을 제공합니다.
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
# 전문화된 도구들
# ===========================================

@mcp.tool(name="search_treaty", description="""조약을 검색합니다. 한국이 체결한 국제조약과 협정을 조회합니다.

매개변수:
- query: 검색어 (필수) - 조약명 또는 키워드
- search: 검색범위 (1=조약명, 2=본문검색)
- display: 결과 개수 (최대 100)
- page: 페이지 번호
- treaty_type: 조약구분 (양자조약, 다자조약)
- effective_date_range: 발효일자 범위 (예: 20090101~20090130)
- agreement_date_range: 체결일자 범위 (예: 20090101~20090130)
- sort: 정렬 방식 (lasc=조약명오름차순, ldes=조약명내림차순, dasc=체결일자오름차순, ddes=체결일자내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)

사용 예시: search_treaty("무역협정"), search_treaty("FTA", treaty_type="양자조약")""")
def search_treaty(
    query: Optional[str] = None,
    search: int = 2,
    display: int = 20,
    page: int = 1,
    treaty_type: Optional[str] = None,
    effective_date_range: Optional[str] = None,
    agreement_date_range: Optional[str] = None,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """조약 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어 (조약명)
        search: 검색범위 (1=조약명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        treaty_type: 조약구분 (양자조약, 다자조약)
        effective_date_range: 발효일자 범위 (20090101~20090130)
        agreement_date_range: 체결일자 범위 (20090101~20090130)
        sort: 정렬 (lasc=조약명오름차순, ldes=조약명내림차순, dasc=체결일자오름차순, ddes=체결일자내림차순, efasc=발효일자오름차순, efdes=발효일자내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if treaty_type:
        params["trt"] = treaty_type
    if effective_date_range:
        params["efYd"] = effective_date_range
    if agreement_date_range:
        params["ancYd"] = agreement_date_range
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("trty", params)
        url = _generate_api_url("trty", params)
        result = _format_search_results(data, "trty", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"조약 검색 중 오류: {str(e)}")
@mcp.tool(name="search_university_regulation", description="""대학교 학칙을 검색합니다.

매개변수:
- query: 검색어 (필수) - 대학명, 학칙명, 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_university_regulation("서울대"), search_university_regulation("학점", display=50)""")
def search_university_regulation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """대학 학칙 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("schreg", params)
        url = _generate_api_url("schreg", params)
        result = _format_search_results(data, "schreg", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"대학 학칙 검색 중 오류: {str(e)}")

@mcp.tool(name="search_public_corporation_regulation", description="""지방공사공단 규정을 검색합니다.

매개변수:
- query: 검색어 (필수) - 공사공단명, 규정명, 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_public_corporation_regulation("시설공단"), search_public_corporation_regulation("인사규정")""")
def search_public_corporation_regulation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """지방공사공단 규정 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("locgongreg", params)
        url = _generate_api_url("locgongreg", params)
        result = _format_search_results(data, "locgongreg", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"지방공사공단 규정 검색 중 오류: {str(e)}")

@mcp.tool(name="search_public_institution_regulation", description="""공공기관 규정을 검색합니다.

매개변수:
- query: 검색어 (필수) - 기관명, 규정명, 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_public_institution_regulation("한국전력"), search_public_institution_regulation("복무규정")""")
def search_public_institution_regulation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """공공기관 규정 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("pubitreg", params)
        url = _generate_api_url("pubitreg", params)
        result = _format_search_results(data, "pubitreg", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"공공기관 규정 검색 중 오류: {str(e)}")

@mcp.tool(name="search_tax_tribunal", description="""조세심판원 특별행정심판례를 검색합니다.

매개변수:
- query: 검색어 (필수) - 세금 관련 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_tax_tribunal("양도소득세"), search_tax_tribunal("부가가치세")""")
def search_tax_tribunal(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """조세심판원 특별행정심판례 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("taxTibunal", params)
        url = _generate_api_url("taxTibunal", params)
        result = _format_search_results(data, "taxTibunal", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"조세심판원 검색 중 오류: {str(e)}")

@mcp.tool(name="search_maritime_safety_tribunal", description="""해양안전심판원 특별행정심판례를 검색합니다.

매개변수:
- query: 검색어 (필수) - 해양 안전 관련 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_maritime_safety_tribunal("충돌"), search_maritime_safety_tribunal("선박사고")""")
def search_maritime_safety_tribunal(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """해양안전심판원 특별행정심판례 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("marSafeTibunal", params)
        url = _generate_api_url("marSafeTibunal", params)
        result = _format_search_results(data, "marSafeTibunal", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"해양안전심판원 검색 중 오류: {str(e)}") 