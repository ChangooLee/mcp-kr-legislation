"""
한국 법제처 OPEN API - 행정규칙 및 자치법규 도구들

행정규칙, 자치법규(조례, 규칙) 관련 검색 및 조회 기능을 제공합니다.
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
# 행정규칙 도구들 (5개)
# ===========================================

@mcp.tool(name="search_administrative_rule", description="행정규칙을 검색합니다. 각 부처의 행정규칙과 예규를 제공합니다.")
def search_administrative_rule(query: Optional[str] = None, search: int = 2, display: int = 20, page: int = 1) -> TextContent:
    """행정규칙 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "admrul", "query": search_query, "search": search, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("admrul", params)
        url = _generate_api_url("admrul", params)
        result = _format_search_results(data, "admrul", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"행정규칙 검색 중 오류: {str(e)}")

@mcp.tool(name="get_administrative_rule_detail", description="행정규칙 상세내용을 조회합니다. 특정 행정규칙의 본문을 제공합니다.")
def get_administrative_rule_detail(rule_id: Union[str, int]) -> TextContent:
    """행정규칙 본문 조회"""
    params = {"target": "admrul", "ID": str(rule_id)}
    try:
        data = _make_legislation_request("admrul", params, is_detail=True)
        url = _generate_api_url("admrul", params)
        result = _format_search_results(data, "admrul", f"행정규칙ID:{rule_id}", 50)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"행정규칙 상세 조회 중 오류: {str(e)}")

@mcp.tool(name="search_administrative_rule_comparison", description="행정규칙 신구법 비교를 검색합니다. 행정규칙의 개정 전후 비교 정보를 제공합니다.")
def search_administrative_rule_comparison(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """행정규칙 신구법 비교 목록 조회 (업데이트됨)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "admrulOldAndNew", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("admrulOldAndNew", params)
        url = _generate_api_url("admrulOldAndNew", params)
        result = _format_search_results(data, "admrulOldAndNew", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"행정규칙 신구법 비교 검색 중 오류: {str(e)}")

@mcp.tool(name="get_administrative_rule_comparison_detail", description="행정규칙 신구법 비교 상세내용을 조회합니다. 특정 행정규칙의 신구법 비교 본문을 제공합니다.")
def get_administrative_rule_comparison_detail(comparison_id: Union[str, int]) -> TextContent:
    """행정규칙 신구법 비교 본문 조회"""
    params = {"target": "admrulOldAndNew", "ID": str(comparison_id)}
    try:
        data = _make_legislation_request("admrulOldAndNew", params, is_detail=True)
        url = _generate_api_url("admrulOldAndNew", params)
        result = _format_search_results(data, "admrulOldAndNew", f"비교ID:{comparison_id}", 50)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"행정규칙 신구법 비교 상세 조회 중 오류: {str(e)}")

# ===========================================
# 자치법규 도구들 (4개)
# ===========================================

@mcp.tool(name="search_local_ordinance", description="자치법규(조례, 규칙)를 검색합니다. 지방자치단체의 조례와 규칙을 제공합니다.")
def search_local_ordinance(query: Optional[str] = None, search: int = 2, display: int = 20, page: int = 1) -> TextContent:
    """자치법규 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "ordin", "query": search_query, "search": search, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("ordin", params)
        url = _generate_api_url("ordin", params)
        result = _format_search_results(data, "ordin", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"자치법규 검색 중 오류: {str(e)}")

@mcp.tool(name="search_ordinance_appendix", description="자치법규 별표서식을 검색합니다. 조례와 규칙의 별표 및 서식을 제공합니다.")
def search_ordinance_appendix(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """자치법규 별표서식 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "ordinanceApp", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("ordinanceApp", params)
        url = _generate_api_url("ordinanceApp", params)
        result = _format_search_results(data, "ordinanceApp", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"자치법규 별표서식 검색 중 오류: {str(e)}")

@mcp.tool(name="search_linked_ordinance", description="연계 자치법규를 검색합니다. 법령과 연계된 조례를 조회할 수 있습니다.")
def search_linked_ordinance(
    query: Optional[str] = None,
    law_id: Optional[str] = None,
    ordinance_id: Optional[str] = None,
    display: int = 20,
    page: int = 1
) -> TextContent:
    """연계 자치법규 검색"""
    params = {"target": "lnkLsOrd", "display": min(display, 100), "page": page}
    
    if query and query.strip():
        params["query"] = query.strip()
    if law_id:
        params["knd"] = law_id  # 법령ID는 knd 파라미터 사용
    if ordinance_id:
        params["OID"] = ordinance_id
    
    try:
        data = _make_legislation_request("lnkLsOrd", params)
        search_term = query or f"법령ID:{law_id}" if law_id else f"자치법규ID:{ordinance_id}" if ordinance_id else "연계 자치법규"
        result = _format_search_results(data, "lnkLsOrd", search_term, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"연계 자치법규 검색 중 오류: {str(e)}")

@mcp.tool(name="get_local_ordinance_detail", description="자치법규 상세내용을 조회합니다. 특정 자치법규의 본문을 제공합니다.")
def get_local_ordinance_detail(ordinance_id: Union[str, int]) -> TextContent:
    """자치법규 본문 조회"""
    try:
        # 올바른 API 엔드포인트 사용 (lawService.do)
        oc = os.getenv("LEGISLATION_API_KEY", "lchangoo")
        url = f"http://www.law.go.kr/DRF/lawService.do?OC={oc}&target=ordin&ID={ordinance_id}&type=JSON"
        
        # API 요청 - 직접 requests 사용 (Referer 헤더 필수)
        headers = {"Referer": "https://open.law.go.kr/"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # 결과 포맷팅 - 상세 조례 내용 제공
        result = f"**자치법규 상세 정보** (ID: {ordinance_id})\n"
        result += "=" * 60 + "\n\n"
        
        if 'LawService' in data and data['LawService']:
            law_service = data['LawService']
            
            if '자치법규기본정보' in law_service:
                basic_info = law_service['자치법규기본정보']
                
                # 기본 정보 출력
                result += "**📋 기본 정보**\n"
                if '자치법규명' in basic_info and basic_info['자치법규명']:
                    result += f"**자치법규명**: {basic_info['자치법규명']}\n"
                if '지자체기관명' in basic_info and basic_info['지자체기관명']:
                    result += f"**지자체**: {basic_info['지자체기관명']}\n"
                if '공포일자' in basic_info and basic_info['공포일자']:
                    result += f"**공포일자**: {basic_info['공포일자']}\n"
                if '시행일자' in basic_info and basic_info['시행일자']:
                    result += f"**시행일자**: {basic_info['시행일자']}\n"
                if '공포번호' in basic_info and basic_info['공포번호']:
                    result += f"**공포번호**: {basic_info['공포번호']}\n"
                if '담당부서명' in basic_info and basic_info['담당부서명']:
                    result += f"**담당부서**: {basic_info['담당부서명']}\n"
                
                result += "\n" + "=" * 60 + "\n\n"
                
                # 조문 내용 출력 (상세)
                if '조문' in law_service and law_service['조문']:
                    조문_data = law_service['조문']
                    if '조' in 조문_data and 조문_data['조']:
                        result += "**📜 조문 내용**\n\n"
                        for 조 in 조문_data['조']:
                            if '조제목' in 조 and '조내용' in 조:
                                result += f"**{조['조제목']}**\n"
                                result += f"{조['조내용']}\n\n"
                    else:
                        result += "**📜 조문 내용**\n\n"
                        result += "조문 내용을 찾을 수 없습니다.\n\n"
                else:
                    result += "**📜 조문 내용**\n\n"
                    result += "조문 내용을 찾을 수 없습니다.\n\n"
                
                # 부칙 정보 출력
                if '부칙' in law_service and law_service['부칙']:
                    부칙_data = law_service['부칙']
                    if '부칙내용' in 부칙_data and 부칙_data['부칙내용']:
                        result += "**📋 부칙**\n"
                        result += f"{부칙_data['부칙내용']}\n\n"
            else:
                result += "자치법규 기본정보를 찾을 수 없습니다.\n\n"
        else:
            result += "자치법규 정보를 찾을 수 없습니다.\n\n"
        
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"자치법규 상세 조회 중 오류: {str(e)}") 