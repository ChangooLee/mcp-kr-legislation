"""
한국 법제처 OPEN API - 부가서비스 도구들

지식베이스, FAQ, 질의응답, 상담, 민원 등 부가서비스 검색 기능을 제공합니다.

주의: 이 API들은 JSON을 지원하지 않고 HTML만 반환합니다.
따라서 직접 웹 URL을 안내하는 방식으로 제공됩니다.
"""

import logging
from typing import Optional
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
# 부가서비스 도구들 (6개) - HTML 전용 API
# ===========================================

@mcp.tool(name="search_knowledge_base", description="""지식베이스를 검색합니다. 법령 관련 지식과 정보를 종합적으로 제공합니다.

주의: FAQ, QNA 등 지식베이스 API는 HTML만 지원합니다. 직접 웹 URL이 제공됩니다.

매개변수:
- query: 검색어 (필수)

사용 예시: search_knowledge_base("법령 해석")

대안: 법령해석례 검색은 search_legal_interpretation 도구를 사용하세요.""")
def search_knowledge_base(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """지식베이스 검색 (HTML 전용)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    base_url = "http://www.law.go.kr/DRF/lawSearch.do"
    oc = legislation_config.oc
    
    # HTML URL 생성
    urls = []
    targets = [
        ("FAQ", "faq"),
        ("QNA", "qna"),
        ("상담사례", "counsel"),
        ("민원사례", "civil"),
    ]
    
    for name, target in targets:
        urls.append(f"- {name}: {base_url}?OC={oc}&target={target}&type=HTML&query={search_query}")
    
    result = f"""지식베이스 검색: '{search_query}'

⚠️ 이 API들은 HTML만 지원합니다. 아래 URL에서 직접 확인해주세요:

{chr(10).join(urls)}

💡 대안 도구:
- 법령해석례 검색: search_legal_interpretation("{search_query}")
- 판례 검색: search_precedent("{search_query}")
- 헌재결정례 검색: search_constitutional_court("{search_query}")"""
    
    return TextContent(type="text", text=result)


@mcp.tool(name="search_faq", description="""자주 묻는 질문(FAQ)을 검색합니다.

주의: 이 API는 HTML만 지원합니다. 직접 웹 URL이 제공됩니다.

매개변수:
- query: 검색어 (필수)

사용 예시: search_faq("법률 용어")""")
def search_faq(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """FAQ 검색 (HTML 전용)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    oc = legislation_config.oc
    url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={oc}&target=faq&type=HTML&query={search_query}"
    
    return TextContent(type="text", text=f"""FAQ 검색: '{search_query}'

⚠️ 이 API는 HTML만 지원합니다.

직접 확인: {url}""")


@mcp.tool(name="search_qna", description="""질의응답(QNA)을 검색합니다.

주의: 이 API는 HTML만 지원합니다. 직접 웹 URL이 제공됩니다.

매개변수:
- query: 검색어 (필수)

사용 예시: search_qna("판례 조회 방법")""")
def search_qna(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """질의응답 검색 (HTML 전용)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    oc = legislation_config.oc
    url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={oc}&target=qna&type=HTML&query={search_query}"
    
    return TextContent(type="text", text=f"""QNA 검색: '{search_query}'

⚠️ 이 API는 HTML만 지원합니다.

직접 확인: {url}""")


@mcp.tool(name="search_counsel", description="""상담 사례를 검색합니다.

주의: 이 API는 HTML만 지원합니다. 직접 웹 URL이 제공됩니다.

매개변수:
- query: 검색어 (필수)

사용 예시: search_counsel("임대차 분쟁")

대안: 법령해석례 검색은 search_legal_interpretation 도구를 사용하세요.""")
def search_counsel(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """상담 검색 (HTML 전용)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    oc = legislation_config.oc
    url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={oc}&target=counsel&type=HTML&query={search_query}"
    
    return TextContent(type="text", text=f"""상담 검색: '{search_query}'

⚠️ 이 API는 HTML만 지원합니다.

직접 확인: {url}

💡 대안: 법령해석례 검색은 search_legal_interpretation("{search_query}")를 사용하세요.""")


@mcp.tool(name="search_precedent_counsel", description="""판례 상담을 검색합니다.

주의: 이 API는 HTML만 지원합니다. 직접 웹 URL이 제공됩니다.

매개변수:
- query: 검색어 (필수)

사용 예시: search_precedent_counsel("계약 해제")

대안: 판례 검색은 search_precedent 도구를 사용하세요.""")
def search_precedent_counsel(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """판례 상담 검색 (HTML 전용)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    oc = legislation_config.oc
    url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={oc}&target=precCounsel&type=HTML&query={search_query}"
    
    return TextContent(type="text", text=f"""판례 상담 검색: '{search_query}'

⚠️ 이 API는 HTML만 지원합니다.

직접 확인: {url}

💡 대안: 판례 검색은 search_precedent("{search_query}")를 사용하세요.""")


@mcp.tool(name="search_civil_petition", description="""민원 사례를 검색합니다.

주의: 이 API는 HTML만 지원합니다. 직접 웹 URL이 제공됩니다.

매개변수:
- query: 검색어 (필수)

사용 예시: search_civil_petition("건축허가")""")
def search_civil_petition(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """민원 검색 (HTML 전용)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    oc = legislation_config.oc
    url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={oc}&target=civil&type=HTML&query={search_query}"
    
    return TextContent(type="text", text=f"""민원 검색: '{search_query}'

⚠️ 이 API는 HTML만 지원합니다.

직접 확인: {url}""")


logger.info("부가서비스 도구가 로드되었습니다! (6개 도구 - HTML 전용)")
