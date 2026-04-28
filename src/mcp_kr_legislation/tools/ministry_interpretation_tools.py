"""
한국 법제처 OPEN API - 중앙부처해석 도구들 (통합)

39개 부처의 법령해석 검색/상세조회를 2개 도구로 통합:
- search_ministry_interpretation: 검색
- get_ministry_interpretation_detail: 상세조회
"""

import logging
from typing import Optional, Union, Annotated
from mcp.types import TextContent

from ..server import mcp

logger = logging.getLogger(__name__)

from .law_tools import (
    _make_legislation_request,
    _format_search_results,
)

# 부처 코드 → (API 타겟, 한글명) 매핑
MINISTRY_TARGETS: dict[str, tuple[str, str]] = {
    # 원본 파일 (13개)
    "moef":   ("moefCgmExpc",   "기획재정부"),
    "molit":  ("molitCgmExpc",  "국토교통부"),
    "moel":   ("moelCgmExpc",   "고용노동부"),
    "mof":    ("mofCgmExpc",    "해양수산부"),
    "mohw":   ("mohwCgmExpc",   "보건복지부"),
    "moe":    ("moeCgmExpc",    "교육부"),
    "motie":  ("motieCgmExpc",  "산업통상자원부"),
    "mafra":  ("mafraCgmExpc",  "농림축산식품부"),
    "mnd":    ("mndCgmExpc",    "국방부"),
    "mss":    ("mssCgmExpc",    "중소벤처기업부"),
    "kfs":    ("kfsCgmExpc",    "산림청"),
    "nts":    ("ntsCgmExpc",    "국세청"),
    "kcs":    ("kcsCgmExpc",    "관세청"),
    # 확장 파일 (26개)
    "mois":        ("moisCgmExpc",  "행정안전부"),
    "me":          ("meCgmExpc",    "환경부"),
    "mcst":        ("mcstCgmExpc",  "문화체육관광부"),
    "moj":         ("mojCgmExpc",   "법무부"),
    "mogef":       ("mogefCgmExpc", "성평등가족부"),
    "mofa":        ("mofaCgmExpc",  "외교부"),
    "unikorea":    ("mouCgmExpc",   "통일부"),
    "moleg":       ("molegCgmExpc", "법제처"),
    "mfds":        ("mfdsCgmExpc",  "식품의약품안전처"),
    "mpm":         ("mpmCgmExpc",   "인사혁신처"),
    "kma":         ("kmaCgmExpc",   "기상청"),
    "cha":         ("khsCgmExpc",   "국가유산청"),
    "rda":         ("rdaCgmExpc",   "농촌진흥청"),
    "police":      ("npaCgmExpc",   "경찰청"),
    "dapa":        ("dapaCgmExpc",  "방위사업청"),
    "mma":         ("mmaCgmExpc",   "병무청"),
    "fire_agency": ("nfaCgmExpc",   "소방청"),
    "pps":         ("ppsCgmExpc",   "조달청"),
    "kdca":        ("kdcaCgmExpc",  "질병관리청"),
    "kcg":         ("kcgCgmExpc",   "해양경찰청"),
    "mpva":        ("mpvaCgmExpc",  "국가보훈부"),
    "kostat":      ("kostatCgmExpc","통계청"),
    "kipo":        ("kipoCgmExpc",  "특허청"),
    "naacc":       ("naaccCgmExpc", "행정중심복합도시건설청"),
    "msit":        ("msitCgmExpc",  "과학기술정보통신부"),
    "oka":         ("okaCgmExpc",   "재외동포청"),
}

# 한글명 → 코드 역방향 매핑 (입력 편의)
_MINISTRY_NAME_TO_CODE: dict[str, str] = {v[1]: k for k, v in MINISTRY_TARGETS.items()}

_MINISTRY_LIST = "\n".join(
    f"  {code}: {name}" for code, (_, name) in MINISTRY_TARGETS.items()
)


def _resolve_ministry(ministry: str) -> tuple[str, str] | None:
    """부처 코드 또는 한글명으로 (API타겟, 한글명) 반환. 없으면 None."""
    key = ministry.strip().lower()
    if key in MINISTRY_TARGETS:
        return MINISTRY_TARGETS[key]
    # 한글명 매칭
    code = _MINISTRY_NAME_TO_CODE.get(ministry.strip())
    if code:
        return MINISTRY_TARGETS[code]
    return None


def _get_cgmexpc_detail(target: str, interpretation_id: Union[str, int], ministry_name: str) -> TextContent:
    """부처 법령해석 상세조회 공통 함수"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request(target, params, is_detail=True, use_cache=True)
        result = _format_search_results(data, target, str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"{ministry_name} 법령해석 상세조회 중 오류: {str(e)}")


@mcp.tool(name="search_ministry_interpretation", description=f"""중앙부처 법령해석을 검색합니다. 39개 부처를 단일 도구로 지원합니다.

매개변수:
- ministry: 부처 코드 (필수). 아래 목록 참조.
- query: 검색어
- display: 결과 개수 (기본 20, 최대 100)
- page: 페이지 번호

부처 코드 목록:
{_MINISTRY_LIST}

사용 예시:
  search_ministry_interpretation(ministry="moef", query="예산집행")
  search_ministry_interpretation(ministry="moel", query="근로시간", display=50)
  search_ministry_interpretation(ministry="nts", query="소득세")

상세조회: 결과의 법령해석일련번호(ID)로 get_ministry_interpretation_detail 호출""")
def search_ministry_interpretation(
    ministry: Annotated[str, "부처 코드 (예: moef, moel, nts)"],
    query: Annotated[Optional[str], "검색어"] = None,
    display: Annotated[int, "결과 개수 (최대 100)"] = 20,
    page: Annotated[int, "페이지 번호"] = 1,
) -> TextContent:
    resolved = _resolve_ministry(ministry)
    if not resolved:
        valid = ", ".join(MINISTRY_TARGETS.keys())
        return TextContent(type="text", text=f"알 수 없는 부처 코드: '{ministry}'\n유효한 코드: {valid}")

    target, ministry_name = resolved
    search_query = (query or "").strip()
    if not search_query:
        return TextContent(type="text", text="검색어를 입력해주세요.")

    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request(target, params, use_cache=True)
        result = _format_search_results(data, target, search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"{ministry_name} 법령해석 검색 중 오류: {str(e)}")


@mcp.tool(name="get_ministry_interpretation_detail", description=f"""중앙부처 법령해석 상세내용을 조회합니다.

매개변수:
- ministry: 부처 코드 (search_ministry_interpretation의 ministry 파라미터와 동일)
- interpretation_id: 법령해석일련번호 (search_ministry_interpretation 결과의 ID 필드값)

부처 코드 목록:
{_MINISTRY_LIST}

사용 예시:
  get_ministry_interpretation_detail(ministry="moef", interpretation_id="123456")
  get_ministry_interpretation_detail(ministry="nts", interpretation_id="78901")""")
def get_ministry_interpretation_detail(
    ministry: Annotated[str, "부처 코드 (예: moef, moel, nts)"],
    interpretation_id: Annotated[Union[str, int], "법령해석일련번호 (search_ministry_interpretation 결과의 ID)"],
) -> TextContent:
    resolved = _resolve_ministry(ministry)
    if not resolved:
        valid = ", ".join(MINISTRY_TARGETS.keys())
        return TextContent(type="text", text=f"알 수 없는 부처 코드: '{ministry}'\n유효한 코드: {valid}")

    target, ministry_name = resolved
    return _get_cgmexpc_detail(target, interpretation_id, ministry_name)
