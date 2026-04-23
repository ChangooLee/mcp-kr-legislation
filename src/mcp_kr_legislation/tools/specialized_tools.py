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
    _format_search_results,
)

def _format_special_decc_detail(svc: dict, tribunal_id: str, 기관명: str) -> str:
    """SpecialDeccService 응답 포맷팅 (조세심판원, 해양안전심판원 공통)"""
    import re
    lines = [f"**{기관명} 특별행정심판례 상세** (ID: {tribunal_id})", "=" * 50, ""]
    사건명 = svc.get('사건명', '') or svc.get('사건번호', '')
    재결청 = svc.get('재결청', '')
    의결일자 = svc.get('의결일자', '')
    청구취지 = svc.get('청구취지', '').strip()
    재결요지 = svc.get('재결요지', '').strip()
    이유 = svc.get('이유', '').strip()
    주문 = svc.get('주문', '').strip()
    세목 = svc.get('세목', '')

    if 사건명:
        lines += [f"**사건명**: {사건명}", ""]
    if 재결청:
        lines.append(f"**재결청**: {재결청}")
    if 의결일자:
        lines.append(f"**의결일자**: {의결일자}")
    if 세목:
        lines.append(f"**세목**: {세목}")
    lines.append("")
    if 청구취지:
        lines += [f"## 청구취지", 청구취지[:500] + ("..." if len(청구취지) > 500 else ""), ""]
    if 주문:
        lines += [f"## 주문", 주문, ""]
    if 재결요지:
        clean_요지 = re.sub(r'\s{2,}', ' ', 재결요지)
        lines += [f"## 재결요지", clean_요지[:1000] + ("..." if len(clean_요지) > 1000 else ""), ""]
    if 이유:
        clean_이유 = re.sub(r'\s{2,}', ' ', 이유)
        lines += [f"## 이유 (요약)", clean_이유[:1000] + ("..." if len(clean_이유) > 1000 else ""), ""]
    return "\n".join(lines)


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
        data = _make_legislation_request("trty", params, use_cache=True)
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
        data = _make_legislation_request("school", params, use_cache=True)
        url = _generate_api_url("school", params)
        result = _format_search_results(data, "school", search_query, min(display, 100))
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
        data = _make_legislation_request("public", params, use_cache=True)
        url = _generate_api_url("public", params)
        result = _format_search_results(data, "public", search_query, min(display, 100))
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
        data = _make_legislation_request("pi", params, use_cache=True)
        url = _generate_api_url("pi", params)
        result = _format_search_results(data, "pi", search_query, min(display, 100))
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
        data = _make_legislation_request("ttSpecialDecc", params, use_cache=True)
        result = _format_search_results(data, "ttSpecialDecc", search_query, min(display, 100))
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
        data = _make_legislation_request("kmstSpecialDecc", params, use_cache=True)
        url = _generate_api_url("kmstSpecialDecc", params)
        result = _format_search_results(data, "kmstSpecialDecc", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"해양안전심판원 검색 중 오류: {str(e)}")

@mcp.tool(name="get_tax_tribunal_detail", description="""조세심판원 특별행정심판례 상세내용을 조회합니다.

매개변수:
- tribunal_id: 심판례ID

사용 예시: get_tax_tribunal_detail(tribunal_id="1018160")""")
def get_tax_tribunal_detail(tribunal_id: Union[str, int]) -> TextContent:
    """조세심판원 특별행정심판례 상세 조회"""
    params = {"ID": str(tribunal_id)}
    try:
        data = _make_legislation_request("ttSpecialDecc", params, is_detail=True, use_cache=True)
        if isinstance(data, dict) and 'SpecialDeccService' in data:
            return TextContent(type="text", text=_format_special_decc_detail(data['SpecialDeccService'], str(tribunal_id), "조세심판원"))
        result = _format_search_results(data, "ttSpecialDecc", str(tribunal_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"조세심판원 상세조회 중 오류: {str(e)}")

@mcp.tool(name="get_maritime_safety_tribunal_detail", description="""해양안전심판원 특별행정심판례 상세내용을 조회합니다.

매개변수:
- tribunal_id: 심판례ID

사용 예시: get_maritime_safety_tribunal_detail(tribunal_id="2")""")
def get_maritime_safety_tribunal_detail(tribunal_id: Union[str, int]) -> TextContent:
    """해양안전심판원 특별행정심판례 상세 조회"""
    params = {"ID": str(tribunal_id)}
    try:
        data = _make_legislation_request("kmstSpecialDecc", params, is_detail=True, use_cache=True)
        if isinstance(data, dict) and 'SpecialDeccService' in data:
            return TextContent(type="text", text=_format_special_decc_detail(data['SpecialDeccService'], str(tribunal_id), "해양안전심판원"))
        result = _format_search_results(data, "kmstSpecialDecc", str(tribunal_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"해양안전심판원 상세조회 중 오류: {str(e)}")

# ===========================================
# 추가 특별행정심판 도구들 (2026-01-21 추가)
# ===========================================

@mcp.tool(name="search_acrc_special_tribunal", description="""국민권익위원회 특별행정심판재결례를 검색합니다.

매개변수:
- query: 검색어 (선택) - 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_acrc_special_tribunal("자동차"), search_acrc_special_tribunal("면허", display=50)""")
def search_acrc_special_tribunal(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """국민권익위원회 특별행정심판재결례 검색"""
    params = {"display": min(display, 100), "page": page}
    if query and query.strip():
        params["query"] = query.strip()
        search_query = query.strip()
    else:
        search_query = "전체"
    
    try:
        data = _make_legislation_request("acrSpecialDecc", params, use_cache=True)
        result = _format_search_results(data, "acrSpecialDecc", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국민권익위원회 특별행정심판 검색 중 오류: {str(e)}")

@mcp.tool(name="get_acrc_special_tribunal_detail", description="""국민권익위원회 특별행정심판재결례 상세내용을 조회합니다.

매개변수:
- tribunal_id: 재결례ID

사용 예시: get_acrc_special_tribunal_detail(tribunal_id="123456")""")
def get_acrc_special_tribunal_detail(tribunal_id: Union[str, int]) -> TextContent:
    """국민권익위원회 특별행정심판재결례 상세 조회"""
    params = {"ID": str(tribunal_id)}
    try:
        data = _make_legislation_request("acrSpecialDecc", params, is_detail=True, use_cache=True)
        if isinstance(data, dict) and 'SpecialDeccService' in data:
            return TextContent(type="text", text=_format_special_decc_detail(data['SpecialDeccService'], str(tribunal_id), "국민권익위원회"))
        result = _format_search_results(data, "acrSpecialDecc", str(tribunal_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국민권익위원회 특별행정심판 상세조회 중 오류: {str(e)}")

@mcp.tool(name="search_mpm_appeal_tribunal", description="""인사혁신처 소청심사위원회 특별행정심판재결례를 검색합니다.

매개변수:
- query: 검색어 (선택) - 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mpm_appeal_tribunal("징계"), search_mpm_appeal_tribunal("해임", display=50)""")
def search_mpm_appeal_tribunal(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """인사혁신처 소청심사위원회 특별행정심판재결례 검색"""
    params = {"display": min(display, 100), "page": page}
    if query and query.strip():
        params["query"] = query.strip()
        search_query = query.strip()
    else:
        search_query = "전체"
    
    try:
        data = _make_legislation_request("adapSpecialDecc", params, use_cache=True)
        result = _format_search_results(data, "adapSpecialDecc", search_query, min(display, 100))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"인사혁신처 소청심사위원회 검색 중 오류: {str(e)}")

@mcp.tool(name="get_mpm_appeal_tribunal_detail", description="""인사혁신처 소청심사위원회 특별행정심판재결례 상세내용을 조회합니다.

매개변수:
- tribunal_id: 재결례ID

사용 예시: get_mpm_appeal_tribunal_detail(tribunal_id="123456")""")
def get_mpm_appeal_tribunal_detail(tribunal_id: Union[str, int]) -> TextContent:
    """인사혁신처 소청심사위원회 특별행정심판재결례 상세 조회"""
    params = {"ID": str(tribunal_id)}
    try:
        data = _make_legislation_request("adapSpecialDecc", params, is_detail=True, use_cache=True)
        if isinstance(data, dict) and 'SpecialDeccService' in data:
            return TextContent(type="text", text=_format_special_decc_detail(data['SpecialDeccService'], str(tribunal_id), "인사혁신처 소청심사위원회"))
        result = _format_search_results(data, "adapSpecialDecc", str(tribunal_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"인사혁신처 소청심사위원회 상세조회 중 오류: {str(e)}")

# ===========================================
# 사전컨설팅의견서 도구들 (감사원)
# ===========================================

@mcp.tool(name="search_bai_preconsulting", description="""감사원 사전컨설팅 의견서를 검색합니다.

매개변수:
- query: 검색어 (선택) - 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_bai_preconsulting("감사"), search_bai_preconsulting("공공기관", display=50)

참고: 이 API는 2026년 기준 미오픈 상태일 수 있습니다.""")
def search_bai_preconsulting(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """감사원 사전컨설팅 의견서 검색"""
    return TextContent(
        type="text",
        text=(
            "**감사원 사전컨설팅 의견서 API는 현재 미오픈 상태입니다.**\n\n"
            "이 API(baiPvcs)는 법제처 OPEN API에 아직 공개되지 않아 데이터를 조회할 수 없습니다.\n\n"
            "**대안:**\n"
            "- 감사원 공식 홈페이지(https://www.bai.go.kr)에서 직접 검색하세요.\n"
            "- 감사원 사전컨설팅 의견서는 감사원 홈페이지 > 정책자료 > 사전컨설팅 메뉴에서 확인할 수 있습니다."
        )
    )

@mcp.tool(name="get_bai_preconsulting_detail", description="""감사원 사전컨설팅 의견서 상세내용을 조회합니다.

매개변수:
- opinion_id: 의견서ID

사용 예시: get_bai_preconsulting_detail(opinion_id="123456")

참고: 이 API는 2026년 기준 미오픈 상태일 수 있습니다.""")
def get_bai_preconsulting_detail(opinion_id: Union[str, int]) -> TextContent:
    """감사원 사전컨설팅 의견서 상세 조회"""
    params = {"ID": str(opinion_id)}
    try:
        data = _make_legislation_request("baiPvcs", params, is_detail=True, use_cache=True)
        result = _format_search_results(data, "baiPvcs", str(opinion_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"감사원 사전컨설팅 의견서 상세조회 중 오류: {str(e)}")