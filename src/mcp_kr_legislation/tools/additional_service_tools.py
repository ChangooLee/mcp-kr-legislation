"""
한국 법제처 OPEN API - 부가서비스 도구들

지식베이스, FAQ, 질의응답, 상담, 민원 등 부가서비스 검색 기능을 제공합니다.

주의: 이 API들은 JSON을 지원하지 않고 HTML만 반환합니다.
따라서 직접 웹 URL을 안내하는 방식으로 제공됩니다.
"""

import logging
from typing import Optional, Annotated
from mcp.types import TextContent

from ..server import mcp
from ..config import legislation_config

logger = logging.getLogger(__name__)

# ===========================================
# 부가서비스 도구들 (2개) - HTML 전용 API
# ===========================================

_KB_SOURCE_MAP = {
    "faq":              ("faq",        "FAQ(자주 묻는 질문)"),
    "qna":              ("qna",        "QNA(질의응답)"),
    "counsel":          ("counsel",    "상담사례"),
    "precedent_counsel":("precCounsel","판례상담"),
}


@mcp.tool(name="search_legal_kb", description="""법제처 지식베이스를 검색합니다. FAQ, QNA, 상담사례, 판례상담을 단일 도구로 지원합니다.

⚠️ 이 API는 HTML만 지원합니다. 웹 URL을 제공합니다.

매개변수:
- query: 검색어 (필수)
- source: 검색 출처 (기본 "all")
  - "all": 모든 출처 (FAQ + QNA + 상담사례 + 판례상담)
  - "faq": 자주 묻는 질문
  - "qna": 질의응답
  - "counsel": 상담사례
  - "precedent_counsel": 판례상담

사용 예시:
  search_legal_kb("임대차 분쟁")
  search_legal_kb("계약 해제", source="precedent_counsel")
  search_legal_kb("법률 용어", source="faq")

💡 대안: 구조화된 데이터가 필요하면
  - 법령해석례: search_legal_interpretation
  - 판례: search_precedent""")
def search_legal_kb(
    query: Annotated[str, "검색어"],
    source: Annotated[str, "출처 (all/faq/qna/counsel/precedent_counsel)"] = "all",
) -> TextContent:
    """법제처 지식베이스 검색 (HTML 전용)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")

    search_query = query.strip()
    oc = legislation_config.oc
    base = "http://www.law.go.kr/DRF/lawSearch.do"

    src = source.strip().lower()

    if src == "all":
        targets = list(_KB_SOURCE_MAP.items())
    elif src in _KB_SOURCE_MAP:
        targets = [(src, _KB_SOURCE_MAP[src])]
    else:
        valid = ", ".join(_KB_SOURCE_MAP.keys()) + ", all"
        return TextContent(type="text", text=f"알 수 없는 source: '{source}'\n유효한 값: {valid}")

    lines = [f"법제처 지식베이스 검색: '{search_query}'", "",
             "⚠️ 이 API는 HTML만 지원합니다. 아래 URL에서 직접 확인해주세요:", ""]
    for code, (api_target, label) in targets:
        url = f"{base}?OC={oc}&target={api_target}&type=HTML&query={search_query}"
        lines.append(f"- {label}: {url}")

    lines += ["", "💡 구조화된 데이터가 필요하면:",
              f'  - 법령해석례: search_legal_interpretation("{search_query}")',
              f'  - 판례: search_precedent("{search_query}")']

    return TextContent(type="text", text="\n".join(lines))


@mcp.tool(name="search_civil_petition", description="""민원 사례를 검색합니다.

⚠️ 이 API는 HTML만 지원합니다. 직접 웹 URL이 제공됩니다.

매개변수:
- query: 검색어 (필수)

사용 예시: search_civil_petition("건축허가")""")
def search_civil_petition(query: Annotated[Optional[str], "검색어"] = None) -> TextContent:
    """민원 검색 (HTML 전용)"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")

    search_query = query.strip()
    oc = legislation_config.oc
    url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={oc}&target=civil&type=HTML&query={search_query}"

    return TextContent(type="text", text=f"민원 검색: '{search_query}'\n\n⚠️ 이 API는 HTML만 지원합니다.\n\n직접 확인: {url}")


logger.info("부가서비스 도구가 로드되었습니다! (2개 도구 - HTML 전용)")
