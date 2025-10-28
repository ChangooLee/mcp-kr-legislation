"""
한국 법제처 OPEN API - AI 도구들

AI 기반 종합 법률 검색 등 인공지능 기반 검색 기능을 제공합니다.
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
# AI 도구들 (1개)
# ===========================================

@mcp.tool(name="search_legal_ai", description="""AI 기반 종합 법률 검색을 수행합니다.

매개변수:
- query: 검색어 (필수)
- target: 검색 대상 (기본값: all)
  - all: 전체
  - law: 법령
  - prec: 판례
  - expc: 해석례
  - committee: 위원회결정문
- display: 결과 개수 (1-50, 기본값: 10)
- page: 페이지 번호 (기본값: 1)
- sort: 정렬 방식
  - rel: 관련도순
  - date: 최신순
  - alpha: 가나다순

반환정보: 
- 법령: 법령명, 법령ID, 공포일자, 시행일자
- 판례: 사건명, 판례ID, 선고일자, 법원명
- 해석례: 제목, 해석례ID, 작성일자, 소관부처
- 위원회결정문: 안건명, 결정문ID, 의결일자, 위원회명

사용 예시:
- search_legal_ai("개인정보보호")  # 전체 검색
- search_legal_ai("근로기준", target="law")  # 법령만 검색
- search_legal_ai("손해배상", target="prec", sort="date")  # 판례 최신순 검색

참고: AI가 여러 법률 문서를 종합적으로 검색하여 관련도가 높은 결과를 제공합니다.""")
def search_legal_ai(
    query: Optional[str] = None,
    target: str = "all",
    display: int = 10,
    page: int = 1,
    sort: Optional[str] = None
) -> TextContent:
    """AI 기반 종합 법률 검색
    
    Args:
        query: 검색어 (필수)
        target: 검색 대상 (all=전체, law=법령, prec=판례, expc=해석례, committee=위원회결정문)
        display: 결과 개수 (1-50)
        page: 페이지 번호 
        sort: 정렬 방식 (rel=관련도순, date=최신순, alpha=가나다순)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    
    # AI 검색 파라미터 구성
    params = {
        "query": search_query,
        "target": target,
        "display": min(max(display, 1), 50),
        "page": max(page, 1)
    }
    
    if sort:
        params["sort"] = sort
        
    try:
        # AI 검색 구현: target에 따라 적절한 API 호출
        if target == "all":
            # 전체 검색인 경우 주요 카테고리별로 검색 수행
            result = f"AI 기반 종합 법률 검색 결과: '{search_query}'\n"
            result += "=" * 50 + "\n\n"
            
            # 1. 법령 검색
            try:
                law_params = {**params, "target": "law"}
                law_data = _make_legislation_request("law", law_params)
                law_url = _generate_api_url("law", law_params)
                if law_data and isinstance(law_data, dict) and law_data.get('LawSearch'):
                    law_total = law_data['LawSearch'].get('totalCnt', 0)
                    try:
                        law_total = int(law_total)
                    except:
                        law_total = 0
                    if law_total > 0:
                        result += f"**법령 검색 결과**: {law_total}건\n"
                        law_result = _format_search_results(law_data, "law", search_query, 5)
                        result += law_result + "\n\n"
            except Exception as e:
                result += f"**법령 검색 오류**: {str(e)}\n\n"
            
            # 2. 판례 검색
            try:
                prec_params = {**params, "target": "prec", "search": 2}
                prec_data = _make_legislation_request("prec", prec_params)
                prec_url = _generate_api_url("prec", prec_params)
                if prec_data and isinstance(prec_data, dict) and prec_data.get('PrecSearch'):
                    prec_total = prec_data['PrecSearch'].get('totalCnt', 0)
                    try:
                        prec_total = int(prec_total)
                    except:
                        prec_total = 0
                    if prec_total > 0:
                        result += f"**판례 검색 결과**: {prec_total}건\n"
                        prec_result = _format_search_results(prec_data, "prec", search_query, 5)
                        result += prec_result + "\n\n"
            except Exception as e:
                result += f"**판례 검색 오류**: {str(e)}\n\n"
            
            # 3. 해석례 검색
            try:
                expc_params = {**params, "target": "expc"}
                expc_data = _make_legislation_request("expc", expc_params)
                expc_url = _generate_api_url("expc", expc_params)
                if expc_data and isinstance(expc_data, dict) and expc_data.get('Expc'):
                    expc_total = expc_data['Expc'].get('totalCnt', 0)
                    try:
                        expc_total = int(expc_total)
                    except:
                        expc_total = 0
                    if expc_total > 0:
                        result += f"**해석례 검색 결과**: {expc_total}건\n"
                        expc_result = _format_search_results(expc_data, "expc", search_query, 5)
                        result += expc_result + "\n\n"
            except Exception as e:
                result += f"**해석례 검색 오류**: {str(e)}\n\n"
        else:
            # 특정 타겟 검색인 경우
            data = _make_legislation_request(target, params)
            url = _generate_api_url(target, params)
            
            if data and isinstance(data, dict):
                result = _format_search_results(data, target, search_query, 10)
                result += f"\n\nAPI URL: {url}"
            else:
                result = f"'{search_query}'에 대한 {target} 검색 결과가 없습니다.\nAPI URL: {url}"
        
        return TextContent(type="text", text=result)
    
    except Exception as e:
        error_msg = f"AI 검색 중 오류가 발생했습니다: {str(e)}"
        return TextContent(type="text", text=error_msg)

logger.info("AI 도구가 로드되었습니다!")

 