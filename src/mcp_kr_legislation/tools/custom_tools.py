"""
한국 법제처 OPEN API - 맞춤형 도구들

맞춤형 법령, 자치법규, 행정규칙, 판례 검색을 제공합니다.

올바른 target 값:
- couseLs: 맞춤법령 목록
- couseOrdin: 맞춤자치법규 목록
- couseAdmrul: 맞춤행정규칙 목록
- cousePrec: 맞춤판례 목록
"""

import logging
from typing import Optional
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
# 맞춤형 법령 도구들
# ===========================================

@mcp.tool(name="search_custom_law", description="""맞춤형 법령을 검색합니다.

매개변수:
- vcode: 분류코드 (필수) - 예: L0000000003384
- query: 검색어 (선택) - 법령명 또는 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

사용 예시:
- search_custom_law(vcode="L0000000003384")  # 특정 분류의 맞춤형 법령
- search_custom_law(vcode="L0000000003384", query="중소기업")

참고: vcode(분류코드)는 공식 가이드에서 확인 가능합니다.""")
def search_custom_law(vcode: Optional[str] = None, query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 법령 검색"""
    if not vcode:
        return TextContent(type="text", text="vcode(분류코드)를 입력해주세요.\n\n예시: search_custom_law(vcode=\"L0000000003384\")\n\n분류코드는 https://open.law.go.kr/LSO/openApi/guideResult.do 에서 확인 가능합니다.")
    
    params = {"vcode": vcode, "display": min(display, 100), "page": page}
    
    if query and query.strip():
        search_query = query.strip()
        params["query"] = search_query
    else:
        search_query = f"맞춤형 법령 (분류: {vcode})"
    
    try:
        data = _make_legislation_request("couseLs", params)
        result = _format_search_results(data, "couseLs", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"맞춤형 법령 검색 중 오류: {str(e)}")


@mcp.tool(name="search_custom_law_articles", description="""맞춤형 법령 조문을 검색합니다.

매개변수:
- vcode: 분류코드 (필수)
- query: 검색어 (선택) - 법령명 또는 조문 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시:
- search_custom_law_articles(vcode="L0000000003384", query="창업")

참고: 조문 조회를 위해 lj=jo 파라미터가 자동으로 추가됩니다.""")
def search_custom_law_articles(vcode: Optional[str] = None, query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 법령 조문 검색"""
    if not vcode:
        return TextContent(type="text", text="vcode(분류코드)를 입력해주세요.")
    
    params = {"vcode": vcode, "display": min(display, 100), "page": page, "lj": "jo"}
    
    if query and query.strip():
        search_query = query.strip()
        params["query"] = search_query
    else:
        search_query = f"맞춤형 법령 조문 (분류: {vcode})"
    
    try:
        data = _make_legislation_request("couseLs", params)
        result = _format_search_results(data, "couseLs", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"맞춤형 법령 조문 검색 중 오류: {str(e)}")


# ===========================================
# 맞춤형 자치법규 도구들
# ===========================================

@mcp.tool(name="search_custom_ordinance", description="""맞춤형 자치법규를 검색합니다.

매개변수:
- vcode: 분류코드 (필수)
- query: 검색어 (선택) - 자치법규명 또는 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_custom_ordinance(vcode="O0000000000001", query="환경보호")""")
def search_custom_ordinance(vcode: Optional[str] = None, query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 자치법규 검색"""
    if not vcode:
        return TextContent(type="text", text="vcode(분류코드)를 입력해주세요.")
    
    params = {"vcode": vcode, "display": min(display, 100), "page": page}
    
    if query and query.strip():
        search_query = query.strip()
        params["query"] = search_query
    else:
        search_query = f"맞춤형 자치법규 (분류: {vcode})"
    
    try:
        data = _make_legislation_request("couseOrdin", params)
        result = _format_search_results(data, "couseOrdin", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"맞춤형 자치법규 검색 중 오류: {str(e)}")


@mcp.tool(name="search_custom_ordinance_articles", description="""맞춤형 자치법규 조문을 검색합니다.

매개변수:
- vcode: 분류코드 (필수)
- query: 검색어 (선택) - 자치법규명 또는 조문 내용
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_custom_ordinance_articles(vcode="O0000000000001", query="제1조")""")
def search_custom_ordinance_articles(vcode: Optional[str] = None, query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 자치법규 조문 검색"""
    if not vcode:
        return TextContent(type="text", text="vcode(분류코드)를 입력해주세요.")
    
    params = {"vcode": vcode, "display": min(display, 100), "page": page, "lj": "jo"}
    
    if query and query.strip():
        search_query = query.strip()
        params["query"] = search_query
    else:
        search_query = f"맞춤형 자치법규 조문 (분류: {vcode})"
    
    try:
        data = _make_legislation_request("couseOrdin", params)
        result = _format_search_results(data, "couseOrdin", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"맞춤형 자치법규 조문 검색 중 오류: {str(e)}")


# ===========================================
# 맞춤형 행정규칙 도구들
# ===========================================

@mcp.tool(name="search_custom_administrative_rule", description="""맞춤형 행정규칙을 검색합니다.

매개변수:
- vcode: 분류코드 (필수)
- query: 검색어 (선택) - 행정규칙명 또는 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_custom_administrative_rule(vcode="A0000000000001", query="훈령")""")
def search_custom_administrative_rule(vcode: Optional[str] = None, query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 행정규칙 검색"""
    if not vcode:
        return TextContent(type="text", text="vcode(분류코드)를 입력해주세요.")
    
    params = {"vcode": vcode, "display": min(display, 100), "page": page}
    
    if query and query.strip():
        search_query = query.strip()
        params["query"] = search_query
    else:
        search_query = f"맞춤형 행정규칙 (분류: {vcode})"
    
    try:
        data = _make_legislation_request("couseAdmrul", params)
        result = _format_search_results(data, "couseAdmrul", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"맞춤형 행정규칙 검색 중 오류: {str(e)}")


# ===========================================
# 맞춤형 판례 도구들
# ===========================================

@mcp.tool(name="search_custom_precedent", description="""맞춤형 판례를 검색합니다.

매개변수:
- vcode: 분류코드 (필수)
- query: 검색어 (선택) - 판례 관련 키워드
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_custom_precedent(vcode="P0000000000001", query="손해배상")""")
def search_custom_precedent(vcode: Optional[str] = None, query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """맞춤형 판례 검색"""
    if not vcode:
        return TextContent(type="text", text="vcode(분류코드)를 입력해주세요.")
    
    params = {"vcode": vcode, "display": min(display, 100), "page": page}
    
    if query and query.strip():
        search_query = query.strip()
        params["query"] = search_query
    else:
        search_query = f"맞춤형 판례 (분류: {vcode})"
    
    try:
        data = _make_legislation_request("cousePrec", params)
        result = _format_search_results(data, "cousePrec", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"맞춤형 판례 검색 중 오류: {str(e)}")


logger.info("맞춤형 도구가 로드되었습니다! (6개 도구)")
