"""
한국 법제처 OPEN API - 법령용어 도구들

법령용어 검색, AI 기반 검색, 연계정보 조회 등 법령용어 관련 기능을 제공합니다.

올바른 target 값:
- lstrm: 법령용어 검색
- lstrmAI: 법령용어 AI 검색
- dlytrmRlt: 일상용어-법령용어 연계 (HTML만 지원)
- lstrmRlt: 법령용어-조문 연계 (HTML만 지원)
- joRltLstrm: 조문-법령용어 연계 (HTML만 지원)
"""

import logging
from typing import Optional, Union
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

@mcp.tool(name="search_legal_term", description="""법령용어를 검색합니다. 법률 용어의 정의와 설명을 조회할 수 있습니다.

매개변수:
- query: 검색어 (필수) - 법령용어명
- display: 결과 개수 (기본 20, 최대 100)
- page: 페이지 번호

사용 예시: search_legal_term("계약"), search_legal_term("소유권", display=50)""")
def search_legal_term(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령용어 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("lstrm", params)
        result = _format_search_results(data, "lstrm", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법령용어 검색 중 오류: {str(e)}")

@mcp.tool(name="search_legal_term_ai", description="""법령용어 AI 지식베이스를 검색합니다. AI 기반으로 법령용어의 정의와 해석을 제공합니다.

매개변수:
- query: 검색어 (필수) - 법령용어명
- display: 결과 개수 (기본 20, 최대 100)
- page: 페이지 번호

사용 예시: search_legal_term_ai("계약"), search_legal_term_ai("채권", display=50)""")
def search_legal_term_ai(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령용어 AI 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("lstrmAI", params)
        result = _format_search_results(data, "lstrmAI", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법령용어 AI 검색 중 오류: {str(e)}")

@mcp.tool(name="search_daily_legal_term_link", description="""일상용어-법령용어 연계 정보를 검색합니다.

참고: 이 API는 HTML만 지원합니다. JSON 응답을 원하시면 search_legal_term 도구를 사용하세요.

매개변수:
- query: 검색어 (필수) - 일상용어명

사용 예시: search_daily_legal_term_link("약속")""")
def search_daily_legal_term_link(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """일상용어-법령용어 연계 검색 (HTML만 지원)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("dlytrmRlt", params)
        # HTML 응답 처리
        if isinstance(data, dict) and data.get("status") == "html":
            return TextContent(type="text", text=f"일상용어-법령용어 연계 API는 HTML만 지원합니다.\n\n직접 확인: http://www.law.go.kr/DRF/lawSearch.do?OC=lchangoo&target=dlytrmRlt&type=HTML&query={search_query}\n\nJSON 법령용어 검색은 search_legal_term 도구를 이용해주세요.")
        result = _format_search_results(data, "dlytrmRlt", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"일상용어-법령용어 연계 검색 중 오류: {str(e)}")

@mcp.tool(name="search_legal_term_article_link", description="""법령용어-조문 연계 정보를 검색합니다.

참고: 이 API는 HTML만 지원합니다. JSON 응답을 원하시면 search_legal_term 도구를 사용하세요.

매개변수:
- term_id: 법령용어 ID (필수) - search_legal_term 결과에서 얻을 수 있음

사용 예시: search_legal_term_article_link("12345")""")
def search_legal_term_article_link(term_id: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령용어-조문 연계 검색 (HTML만 지원)"""
    if not term_id or not str(term_id).strip():
        return TextContent(type="text", text="법령용어 ID를 입력해주세요. search_legal_term 도구로 먼저 법령용어를 검색하세요.")
    
    term_id_str = str(term_id).strip()
    params = {"ID": term_id_str, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("lstrmRlt", params)
        # HTML 응답 처리
        if isinstance(data, dict) and data.get("status") == "html":
            return TextContent(type="text", text=f"법령용어-조문 연계 API는 HTML만 지원합니다.\n\n직접 확인: http://www.law.go.kr/DRF/lawSearch.do?OC=lchangoo&target=lstrmRlt&type=HTML&ID={term_id_str}")
        result = _format_search_results(data, "lstrmRlt", term_id_str)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법령용어-조문 연계 검색 중 오류: {str(e)}")

@mcp.tool(name="search_article_legal_term_link", description="""조문-법령용어 연계 정보를 검색합니다.

참고: 이 API는 HTML만 지원합니다.

매개변수:
- article_id: 조문 ID (필수)

사용 예시: search_article_legal_term_link("12345")""")
def search_article_legal_term_link(article_id: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """조문-법령용어 연계 검색 (HTML만 지원)"""
    if not article_id or not str(article_id).strip():
        return TextContent(type="text", text="조문 ID를 입력해주세요.")
    
    article_id_str = str(article_id).strip()
    params = {"ID": article_id_str, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("joRltLstrm", params)
        # HTML 응답 처리
        if isinstance(data, dict) and data.get("status") == "html":
            return TextContent(type="text", text=f"조문-법령용어 연계 API는 HTML만 지원합니다.\n\n직접 확인: http://www.law.go.kr/DRF/lawSearch.do?OC=lchangoo&target=joRltLstrm&type=HTML&ID={article_id_str}")
        result = _format_search_results(data, "joRltLstrm", article_id_str)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"조문-법령용어 연계 검색 중 오류: {str(e)}")

@mcp.tool(name="get_legal_term_detail", description="""법령용어 상세내용을 조회합니다. 특정 법령용어의 정의와 설명을 제공합니다.

매개변수:
- term_id: 법령용어 ID (필수) - search_legal_term 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_legal_term_detail(term_id="12345")""")
def get_legal_term_detail(term_id: Union[str, int]) -> TextContent:
    """법령용어 상세 조회"""
    params = {"ID": str(term_id)}
    try:
        data = _make_legislation_request("lstrm", params, is_detail=True)
        url = _generate_api_url("lstrm", params, is_detail=True)
        result = _format_search_results(data, "lstrm", str(term_id), 50)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법령용어 상세조회 중 오류: {str(e)}")


# ===========================================
# 추가 법령용어 도구들
# ===========================================

@mcp.tool(name="search_daily_term", description="""일상용어를 검색합니다. 법령용어와 연계된 일상용어를 조회할 수 있습니다.

참고: 이 API는 HTML만 지원합니다.

매개변수:
- query: 검색어 (필수)

사용 예시: search_daily_term("약속")""")
def search_daily_term(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """일상용어 검색 (HTML만 지원)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    # dlytrmRlt API는 HTML만 지원
    return TextContent(type="text", text=f"일상용어 검색 API는 HTML만 지원합니다.\n\n직접 확인: http://www.law.go.kr/DRF/lawSearch.do?OC=lchangoo&target=dlytrmRlt&type=HTML&query={search_query}\n\nJSON 법령용어 검색은 search_legal_term 도구를 이용해주세요.")

@mcp.tool(name="search_legal_daily_term_link", description="""법령용어에서 일상용어로의 연계 정보를 검색합니다.

참고: 이 API는 HTML만 지원합니다.

매개변수:
- term_id: 법령용어 ID (필수)

사용 예시: search_legal_daily_term_link("12345")""")
def search_legal_daily_term_link(term_id: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령용어-일상용어 연계 검색 (HTML만 지원)"""
    if not term_id or not str(term_id).strip():
        return TextContent(type="text", text="법령용어 ID를 입력해주세요. search_legal_term 도구로 먼저 법령용어를 검색하세요.")
    
    term_id_str = str(term_id).strip()
    return TextContent(type="text", text=f"법령용어-일상용어 연계 API는 HTML만 지원합니다.\n\n직접 확인: http://www.law.go.kr/DRF/lawSearch.do?OC=lchangoo&target=lstrmRlt&type=HTML&ID={term_id_str}")


logger.info("법령용어 도구가 로드되었습니다! (8개 도구)")
