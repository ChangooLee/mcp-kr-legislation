"""
한국 법제처 OPEN API - 위원회 결정문 도구들

개인정보보호위원회, 금융위원회, 공정거래위원회, 국민권익위원회, 노동위원회 등
다양한 위원회의 결정문 검색 및 조회 기능을 제공합니다.
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
    _generate_api_url
)

def _format_committee_search_results(data: dict, target: str, search_query: str, max_results: int = 50) -> str:
    """위원회 검색 전용 결과 포맷팅 함수"""
    try:
        # 타겟별 루트 키 매핑 (실제 API 응답 구조 기준)
        target_root_map = {
            "ppc": "Ppc",
            "fsc": "Fsc", 
            "ftc": "Ftc",
            "acr": "Acr",
            "nlrc": "Nlrc",
            "ecc": "Ecc",
            "sfc": "Sfc",
            "nhrck": "Nhrck",
            "kcc": "Kcc",
            "iaciac": "Iaciac",
            "oclt": "Oclt",
            "eiac": "Eiac"
        }
        
        # 올바른 루트 키에서 데이터 추출
        root_key = target_root_map.get(target)
        if not root_key or root_key not in data:
            return f"'{search_query}'에 대한 검색 결과가 없습니다."
        
        search_data = data[root_key]
        
        # 위원회 데이터는 단수형 dict로 반환되는 경우가 많음
        committee_item = search_data.get(target, {})
        if isinstance(committee_item, dict) and committee_item:
            target_data = [committee_item]  # 배열로 통일
        elif isinstance(committee_item, list):
            target_data = committee_item  # 이미 배열인 경우
        else:
            return f"'{search_query}'에 대한 검색 결과가 없습니다."
        
        # 제한된 결과만 처리
        if isinstance(target_data, list):
            target_data = target_data[:max_results]
        
        # 타겟별 제목 키 설정
        if target == "ppc":
            # 개인정보보호위원회: 안건명이 비어있는 경우가 많으므로 대체 필드 사용
            title_keys = ['안건명', '의안명', '결정구분', '회의종류', '결정문제목']
        else:
            # 다른 위원회들
            title_keys = ['안건명', '의안명', '결정문제목', '위원회결정문명']
        
        # 상세 정보 필드
        detail_fields = {
            '결정문일련번호': ['결정문일련번호', '결정문ID', 'decision_id'],
            '의결일자': ['의결일자', '회의일자', '처리일자', '결정일자'],
            '의안번호': ['의안번호', '안건번호', '사건번호'],
            '회의종류': ['회의종류', '회의구분', '결정구분']
        }
        
        results = []
        
        for idx, item in enumerate(target_data, 1):
            if not isinstance(item, dict):
                continue
                
            # 제목 찾기
            title = "제목 없음"
            for key in title_keys:
                if key in item and item[key] and str(item[key]).strip():
                    title = str(item[key]).strip()
                    break
            
            result_lines = [f"**{idx}. {title}**"]
            
            # 상세 정보 추가
            for field_name, possible_keys in detail_fields.items():
                for key in possible_keys:
                    if key in item and item[key] and str(item[key]).strip():
                        result_lines.append(f"   {field_name}: {item[key]}")
                        break
            
            # ID 정보 추가 (상세조회용)
            for id_key in ['결정문일련번호', 'ID', 'id']:
                if id_key in item and item[id_key]:
                    result_lines.append(f"   상세조회: get_{target}_committee_detail(decision_id=\"{item[id_key]}\")")
                    break
                    
            results.append("\\n".join(result_lines))
        
        total_count = search_data.get('totalCnt', len(target_data))
        
        return f"**'{search_query}' 검색 결과** (총 {total_count}건)\\n\\n" + "\\n\\n".join(results)
        
    except Exception as e:
        logger.error(f"위원회 검색 결과 포맷팅 오류: {e}")
        return f"검색 결과 처리 중 오류가 발생했습니다: {str(e)}"

def _format_committee_detail(data: dict, target: str, decision_id: str, url: str) -> str:
    """위원회 결정문 상세조회 결과 포맷팅"""
    if not data:
        return f"결정문 상세 정보를 찾을 수 없습니다.\\n\\nAPI URL: {url}"
    
    # 위원회별 상세조회 응답 구조 매핑
    service_key_map = {
        "ppc": "PpcService",
        "fsc": "FscService", 
        "ftc": "FtcService",
        "acr": "AcrService",
        "nlrc": "NlrcService",
        "ecc": "EccService",
        "sfc": "SfcService",
        "nhrck": "NhrckService",
        "kcc": "KccService",
        "iaciac": "IaciacService",
        "oclt": "OcltService",
        "eiac": "EiacService"
    }
    
    service_key = service_key_map.get(target, "Law")
    
    if service_key in data:
        service_data = data[service_key]
        result = f"**위원회 결정문 상세정보** (ID: {decision_id})\\n"
        result += "=" * 50 + "\\n\\n"
        
        if isinstance(service_data, dict):
            # 구조화된 데이터인 경우
            for key, value in service_data.items():
                if isinstance(value, str) and value.strip():
                    result += f"**{key}:**\\n{value}\\n\\n"
                elif isinstance(value, dict):
                    result += f"**{key}:**\\n"
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str) and sub_value.strip():
                            result += f"  - {sub_key}: {sub_value}\\n"
                    result += "\\n"
        else:
            result += f"**결정문 내용:**\\n{str(service_data)}\\n\\n"
            
        result += f"\\n**API URL:** {url}"
        return result
        
    elif "Law" in data:
        # Law 키로 반환된 경우 (오류 메시지 등)
        law_content = data["Law"]
        if isinstance(law_content, str):
            if "없습니다" in law_content or "확인" in law_content:
                return f"결정문을 찾을 수 없습니다: {law_content}\\n\\n**해결방법:**\\n- 올바른 결정문 ID를 확인하세요\\n- 검색 결과에서 'id' 또는 '결정문일련번호' 필드값을 사용하세요\\n\\nAPI URL: {url}"
            else:
                return f"**위원회 결정문 상세정보** (ID: {decision_id})\\n{'=' * 50}\\n\\n{law_content}\\n\\nAPI URL: {url}"
    
    # 알 수 없는 구조
    available_keys = list(data.keys())
    return f"상세조회 응답 구조를 인식할 수 없습니다.\\n\\n**사용 가능한 키들:** {available_keys}\\n\\nAPI URL: {url}"

# ===========================================
# 위원회 결정문 도구들 (30개)
# ===========================================

@mcp.tool(name="search_privacy_committee", description="""개인정보보호위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=의안명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=의안명오름차순, ldes=의안명내림차순, dasc=개최일자오름차순, ddes=개최일자내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_privacy_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """개인정보보호위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=의안명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=의안명오름차순, ldes=의안명내림차순, dasc=개최일자오름차순, ddes=개최일자내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("ppc", params)
        url = _generate_api_url("ppc", params)
        result = _format_committee_search_results(data, "ppc", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"개인정보보호위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_financial_committee", description="""금융위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=안건명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=안건명오름차순, ldes=안건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_financial_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """금융위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=안건명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=안건명오름차순, ldes=안건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("fsc", params)
        url = _generate_api_url("fsc", params)
        result = _format_committee_search_results(data, "fsc", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"금융위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_monopoly_committee", description="""공정거래위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=의결내용명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=의결내용명오름차순, ldes=의결내용명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_monopoly_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """공정거래위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=의결내용명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=의결내용명오름차순, ldes=의결내용명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("ftc", params)
        url = _generate_api_url("ftc", params)
        result = _format_committee_search_results(data, "ftc", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"공정거래위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_anticorruption_committee", description="""국민권익위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=안건명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=안건명오름차순, ldes=안건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_anticorruption_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """국민권익위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=안건명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=안건명오름차순, ldes=안건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("acr", params)
        url = _generate_api_url("acr", params)
        result = _format_committee_search_results(data, "acr", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국민권익위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_labor_committee", description="""노동위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=사건명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, dasc=재정일자오름차순, ddes=재정일자내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_labor_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """노동위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=사건명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, dasc=재정일자오름차순, ddes=재정일자내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("nlrc", params)
        url = _generate_api_url("nlrc", params)
        result = _format_committee_search_results(data, "nlrc", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"노동위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_environment_committee", description="""중앙환경분쟁조정위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=사건명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, nasc=의결번호오름차순, ndes=의결번호내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_environment_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """중앙환경분쟁조정위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=사건명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, nasc=의결번호오름차순, ndes=의결번호내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("ecc", params)
        url = _generate_api_url("ecc", params)
        result = _format_committee_search_results(data, "ecc", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"중앙환경분쟁조정위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_securities_committee", description="""증권선물위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=사건명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순, nasc=사건번호오름차순, ndes=사건번호내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_securities_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """증권선물위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=사건명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순, nasc=사건번호오름차순, ndes=사건번호내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("sfc", params)
        url = _generate_api_url("sfc", params)
        result = _format_committee_search_results(data, "sfc", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"증권선물위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_human_rights_committee", description="""국가인권위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=사건명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순, nasc=사건번호오름차순, ndes=사건번호내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_human_rights_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """국가인권위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=사건명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순, nasc=사건번호오름차순, ndes=사건번호내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("nhrck", params)
        url = _generate_api_url("nhrck", params)
        result = _format_committee_search_results(data, "nhrck", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국가인권위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_broadcasting_committee", description="""방송통신위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=안건명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=안건명오름차순, ldes=안건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순, nasc=안건번호오름차순, ndes=안건번호내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_broadcasting_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """방송통신위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=안건명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=안건명오름차순, ldes=안건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순, nasc=안건번호오름차순, ndes=안건번호내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("kcc", params)
        url = _generate_api_url("kcc", params)
        result = _format_committee_search_results(data, "kcc", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"방송통신위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_industrial_accident_committee", description="""산업재해보상보험 재심사위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=사건, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=사건오름차순, ldes=사건내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순, nasc=사건번호오름차순, ndes=사건번호내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_industrial_accident_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """산업재해보상보험재심사위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=사건, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=사건오름차순, ldes=사건내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순, nasc=사건번호오름차순, ndes=사건번호내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("iaciac", params)
        url = _generate_api_url("iaciac", params)
        result = _format_committee_search_results(data, "iaciac", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"산업재해보상보험재심사위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_land_tribunal", description="""중앙토지수용위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=제목, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=제목오름차순, ldes=제목내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_land_tribunal(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """중앙토지수용위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=제목, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=제목오름차순, ldes=제목내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("oclt", params)
        url = _generate_api_url("oclt", params)
        result = _format_committee_search_results(data, "oclt", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"중앙토지수용위원회 결정문 검색 중 오류: {str(e)}")

@mcp.tool(name="search_employment_insurance_committee", description="""고용보험심사위원회 결정문을 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=사건명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순, nasc=사건번호오름차순, ndes=사건번호내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)""")
def search_employment_insurance_committee(
    query: Optional[str] = None, 
    search: int = 2, 
    display: int = 20, 
    page: int = 1,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None
) -> TextContent:
    """고용보험심사위원회 결정문 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=사건명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, dasc=의결일자오름차순, ddes=의결일자내림차순, nasc=사건번호오름차순, ndes=사건번호내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # search=2 (본문검색) 파라미터로 더 많은 결과 확보
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
        
    try:
        data = _make_legislation_request("eiac", params)
        url = _generate_api_url("eiac", params)
        result = _format_committee_search_results(data, "eiac", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"고용보험심사위원회 결정문 검색 중 오류: {str(e)}")

# ===========================================
# 위원회 결정문 상세 조회 도구들
# ===========================================

@mcp.tool(name="get_privacy_committee_detail", description="""개인정보보호위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문일련번호 - search_privacy_committee 도구의 결과에서 '결정문일련번호' 필드값 사용 (예: "6173")

⚠️ 주의: 'id' 필드(1,2,3...)가 아닌 '결정문일련번호' 필드값을 사용하세요.

사용 예시: get_privacy_committee_detail(decision_id="6173")""")
def get_privacy_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """개인정보보호위원회 결정문 본문 조회 (ppc)"""
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("ppc", params, is_detail=True)
        url = _generate_api_url("ppc", params, is_detail=True)
        result = _format_committee_detail(data, "ppc", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"개인정보보호위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(
    name="get_financial_committee_detail", 
    description="""금융위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문일련번호 - search_financial_committee 도구의 결과에서 '결정문일련번호' 필드값 사용

⚠️ 주의: 'id' 필드(1,2,3...)가 아닌 '결정문일련번호' 필드값을 사용하세요.

사용 예시: get_financial_committee_detail(decision_id="실제결정문일련번호")""",
    tags={"금융위원회", "결정문", "상세조회", "금융규제", "위원회"}
)
def get_financial_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """금융위원회 결정문 본문 조회 (fsc)"""
    if not decision_id:
        return TextContent(type="text", text="결정문 ID를 입력해주세요.")
    
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("fsc", params, is_detail=True)
        url = _generate_api_url("fsc", params, is_detail=True)
        
        # 응답 데이터 유효성 검사 강화
        if not data or isinstance(data, str) and "error" in data.lower():
            return TextContent(type="text", text=f"ID '{decision_id}'에 해당하는 금융위원회 결정문을 찾을 수 없습니다.\n\nsearch_financial_committee 도구로 올바른 ID를 먼저 확인해보세요.\n\nAPI URL: {url}")
        
        # JSON 파싱 오류 방지를 위한 안전한 처리
        if isinstance(data, dict) and not data:
            return TextContent(type="text", text=f"ID '{decision_id}'에 해당하는 결정문의 상세 내용이 없습니다.\n\nAPI URL: {url}")
        
        result = _format_committee_detail(data, "fsc", str(decision_id), url)
        return TextContent(type="text", text=result)
    except json.JSONDecodeError as e:
        return TextContent(type="text", text=f"응답 데이터 파싱 오류: {str(e)}\n\nAPI 응답 형식에 문제가 있을 수 있습니다. 다른 ID로 시도해보세요.")
    except Exception as e:
        return TextContent(type="text", text=f"금융위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_monopoly_committee_detail", description="""공정거래위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문일련번호 - search_monopoly_committee 도구의 결과에서 '결정문일련번호' 필드값 사용

⚠️ 주의: 'id' 필드(1,2,3...)가 아닌 '결정문일련번호' 필드값을 사용하세요.

사용 예시: get_monopoly_committee_detail(decision_id="실제결정문일련번호")""")
def get_monopoly_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """공정거래위원회 결정문 본문 조회 (ftc)"""
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("ftc", params, is_detail=True)
        url = _generate_api_url("ftc", params, is_detail=True)
        result = _format_committee_detail(data, "ftc", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"공정거래위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_anticorruption_committee_detail", description="""국민권익위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문ID - search_anticorruption_committee 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_anticorruption_committee_detail(decision_id="123456")""")
def get_anticorruption_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """국민권익위원회 결정문 본문 조회 (acr)"""
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("acr", params)
        url = _generate_api_url("acr", params)
        result = _format_committee_detail(data, "acr", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국민권익위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_labor_committee_detail", description="""노동위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문ID - search_labor_committee 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_labor_committee_detail(decision_id="123456")""")
def get_labor_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """노동위원회 결정문 본문 조회 (nlrc)"""
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("nlrc", params)
        url = _generate_api_url("nlrc", params)
        result = _format_committee_detail(data, "nlrc", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"노동위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_environment_committee_detail", description="""중앙환경분쟁조정위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문ID - search_environment_committee 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_environment_committee_detail(decision_id="123456")""")
def get_environment_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """중앙환경분쟁조정위원회 결정문 본문 조회 (ecc)"""
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("ecc", params)
        url = _generate_api_url("ecc", params)
        result = _format_committee_detail(data, "ecc", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"중앙환경분쟁조정위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_securities_committee_detail", description="""증권선물위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문ID - search_securities_committee 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_securities_committee_detail(decision_id="123456")""")
def get_securities_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """증권선물위원회 결정문 본문 조회 (sfc)"""
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("sfc", params)
        url = _generate_api_url("sfc", params)
        result = _format_committee_detail(data, "sfc", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"증권선물위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_human_rights_committee_detail", description="""국가인권위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문ID - search_human_rights_committee 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_human_rights_committee_detail(decision_id="123456")""")
def get_human_rights_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """국가인권위원회 결정문 본문 조회 (nhrck)"""
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("nhrck", params)
        url = _generate_api_url("nhrck", params)
        result = _format_committee_detail(data, "nhrck", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국가인권위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_broadcasting_committee_detail", description="""방송통신위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문ID - search_broadcasting_committee 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_broadcasting_committee_detail(decision_id="123456")""")
def get_broadcasting_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """방송통신위원회 결정문 본문 조회 (kcc)"""
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("kcc", params)
        url = _generate_api_url("kcc", params)
        result = _format_committee_detail(data, "kcc", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"방송통신위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_industrial_accident_committee_detail", description="""산업재해보상보험 재심사위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문ID - search_industrial_accident_committee 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_industrial_accident_committee_detail(decision_id="123456")""")
def get_industrial_accident_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """산업재해보상보험 재심사위원회 결정문 본문 조회 (eiac)"""
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("eiac", params)
        url = _generate_api_url("eiac", params)
        result = _format_committee_detail(data, "eiac", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"산업재해보상보험 재심사위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_land_tribunal_detail", description="""중앙토지수용위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문ID - search_land_tribunal 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_land_tribunal_detail(decision_id="123456")""")
def get_land_tribunal_detail(decision_id: Union[str, int]) -> TextContent:
    """중앙토지수용위원회 결정문 본문 조회 (lx)"""
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request("oclt", params)
        url = _generate_api_url("oclt", params)
        result = _format_committee_detail(data, "oclt", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"중앙토지수용위원회 결정문 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_employment_insurance_committee_detail", description="""고용보험심사위원회 결정문 상세내용을 조회합니다.

매개변수:
- decision_id: 결정문ID - search_employment_insurance_committee 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_employment_insurance_committee_detail(decision_id="123456")""")
def get_employment_insurance_committee_detail(decision_id: Union[str, int]) -> TextContent:
    """고용보험심사위원회 결정문 본문 조회"""
    params = {"target": "eiac", "ID": str(decision_id)}
    try:
        data = _make_legislation_request("eiac", params)
        url = _generate_api_url("eiac", params)
        result = _format_committee_detail(data, "eiac", str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"고용보험심사위원회 결정문 상세 조회 중 오류: {str(e)}") 