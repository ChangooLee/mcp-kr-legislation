"""
한국 법제처 OPEN API - 중앙부처해석 도구들

각 중앙부처(기획재정부, 국토교통부, 고용노동부 등)의 법령해석 사례 
검색 및 상세조회 기능을 제공합니다.
"""

import logging
import json
import os
import requests  # type: ignore
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
# 중앙부처해석 도구들 (30개+)
# ===========================================

@mcp.tool(name="search_moef_interpretation", description="""기획재정부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_moef_interpretation("예산"), search_moef_interpretation("재정", display=50)""")
def search_moef_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """기획재정부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "moef", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("moef", params)
        result = _format_search_results(data, "moef", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"기획재정부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_molit_interpretation", description="""국토교통부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_molit_interpretation("건축"), search_molit_interpretation("도로", display=50)""")
def search_molit_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """국토교통부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "molit", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("molit", params)
        result = _format_search_results(data, "molit", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국토교통부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_moel_interpretation", description="""고용노동부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_moel_interpretation("근로시간"), search_moel_interpretation("임금", display=50)""")
def search_moel_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """고용노동부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "moel", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("moel", params)
        result = _format_search_results(data, "moel", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"고용노동부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_mof_interpretation", description="""해양수산부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mof_interpretation("어업"), search_mof_interpretation("항만", display=50)""")
def search_mof_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """해양수산부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "mof", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mof", params)
        result = _format_search_results(data, "mof", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"해양수산부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_mohw_interpretation", description="""보건복지부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mohw_interpretation("의료법"), search_mohw_interpretation("복지", display=50)""")
def search_mohw_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """보건복지부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "mohw", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mohw", params)
        result = _format_search_results(data, "mohw", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"보건복지부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_moe_interpretation", description="""교육부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_moe_interpretation("학교"), search_moe_interpretation("교육", display=50)""")
def search_moe_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """교육부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "moe", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("moe", params)
        result = _format_search_results(data, "moe", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"교육부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_korea_interpretation", description="""한국 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_korea_interpretation("행정"), search_korea_interpretation("정책", display=50)""")
def search_korea_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """한국 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "korea", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("korea", params)
        result = _format_search_results(data, "korea", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"한국 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_mssp_interpretation", description="""보훈처 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mssp_interpretation("보훈"), search_mssp_interpretation("유공자", display=50)""")
def search_mssp_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """보훈처 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "mssp", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mssp", params)
        result = _format_search_results(data, "mssp", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"보훈처 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_mote_interpretation", description="""산업통상자원부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mote_interpretation("무역"), search_mote_interpretation("산업", display=50)""")
def search_mote_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """산업통상자원부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "mote", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mote", params)
        result = _format_search_results(data, "mote", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"산업통상자원부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_maf_interpretation", description="""농림축산식품부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_maf_interpretation("농업"), search_maf_interpretation("축산", display=50)""")
def search_maf_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """농림축산식품부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "maf", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("maf", params)
        result = _format_search_results(data, "maf", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"농림축산식품부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_moms_interpretation", description="""국방부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_moms_interpretation("병역"), search_moms_interpretation("군인", display=50)""")
def search_moms_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """국방부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "moms", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("moms", params)
        result = _format_search_results(data, "moms", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국방부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_sme_interpretation", description="""중소벤처기업부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_sme_interpretation("중소기업"), search_sme_interpretation("벤처", display=50)""")
def search_sme_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """중소벤처기업부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "sme", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("sme", params)
        result = _format_search_results(data, "sme", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"중소벤처기업부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_nfa_interpretation", description="""산림청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_nfa_interpretation("산림"), search_nfa_interpretation("임업", display=50)""")
def search_nfa_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """산림청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "nfa", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("nfa", params)
        result = _format_search_results(data, "nfa", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"산림청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_korail_interpretation", description="""한국철도공사 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_korail_interpretation("철도"), search_korail_interpretation("운송", display=50)""")
def search_korail_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """한국철도공사 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "korail", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("korail", params)
        result = _format_search_results(data, "korail", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"한국철도공사 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_nts_interpretation", description="""국세청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_nts_interpretation("소득세"), search_nts_interpretation("부가가치세", display=50)""")
def search_nts_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """국세청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "nts", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("nts", params)
        result = _format_search_results(data, "nts", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국세청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="search_kcs_interpretation", description="""관세청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_kcs_interpretation("관세"), search_kcs_interpretation("수입", display=50)""")
def search_kcs_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """관세청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "kcs", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("kcs", params)
        result = _format_search_results(data, "kcs", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"관세청 법령해석 검색 중 오류: {str(e)}")

# ===========================================
# 중앙부처해석 상세 조회 도구들
# ===========================================

@mcp.tool(name="get_moef_interpretation_detail", description="""기획재정부 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID - search_moef_interpretation 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_moef_interpretation_detail(interpretation_id="123456")""")
def get_moef_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """기획재정부 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("moef", params, is_detail=True)
        url = _generate_api_url("moef", params, is_detail=True)
        result = _format_search_results(data, "moef", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"기획재정부 법령해석 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_nts_interpretation_detail", description="""국세청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID - search_nts_interpretation 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_nts_interpretation_detail(interpretation_id="123456")""")
def get_nts_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """국세청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("nts", params, is_detail=True)
        url = _generate_api_url("nts", params, is_detail=True)
        result = _format_search_results(data, "nts", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국세청 법령해석 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_kcs_interpretation_detail", description="""관세청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID - search_kcs_interpretation 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_kcs_interpretation_detail(interpretation_id="123456")""")
def get_kcs_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """관세청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("kcs", params, is_detail=True)
        url = _generate_api_url("kcs", params, is_detail=True)
        result = _format_search_results(data, "kcs", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"관세청 법령해석 상세조회 중 오류: {str(e)}")

# 추가로 더 많은 부처별 상세 조회 도구들이 있을 수 있습니다... 