"""
한국 법제처 OPEN API - 중앙부처해석 확장 도구들

기존 ministry_interpretation_tools.py에 없는 추가 부처들의 
법령해석 검색 및 상세조회 기능을 제공합니다.

2026-01-20: 공식 가이드 기반 전체 API 재검증 및 올바른 target 값으로 업데이트
https://open.law.go.kr/LSO/openApi/guideList.do#

추가된 부처 (모두 활성화됨, 19개):
- 행정안전부, 환경부, 문화체육관광부, 법무부, 성평등가족부
- 외교부, 통일부, 법제처, 식품의약품안전처, 인사혁신처
- 기상청, 국가유산청, 농촌진흥청, 경찰청, 방위사업청
- 병무청, 소방청, 조달청, 질병관리청, 해양경찰청, 국가보훈부

※ 산림청(search_nfa), 국방부(search_moms), 농림축산식품부(search_maf)는 
  ministry_interpretation_tools.py에 이미 존재하므로 중복 방지를 위해 제외
"""

import logging
from typing import Optional, Union
from mcp.types import TextContent

from ..server import mcp
from ..config import legislation_config

logger = logging.getLogger(__name__)

from .law_tools import (
    _make_legislation_request,
    _generate_api_url,
    _format_search_results
)

# ===========================================
# 중앙부처해석 확장 도구들 (올바른 target 값 적용)
# ===========================================

# --- 행정안전부 (moisCgmExpc) - 4,039건 ---
@mcp.tool(name="search_mois_interpretation", description="""행정안전부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mois_interpretation("지방자치"), search_mois_interpretation("재난", display=50)""")
def search_mois_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """행정안전부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("moisCgmExpc", params)
        result = _format_search_results(data, "moisCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"행정안전부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_mois_interpretation_detail", description="""행정안전부 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_mois_interpretation_detail(interpretation_id="123456")""")
def get_mois_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """행정안전부 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("moisCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "moisCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"행정안전부 법령해석 상세조회 중 오류: {str(e)}")

# --- 환경부 (meCgmExpc) - 2,291건 ---
@mcp.tool(name="search_me_interpretation", description="""환경부(기후에너지환경부) 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_me_interpretation("환경영향평가"), search_me_interpretation("폐기물", display=50)""")
def search_me_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """환경부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("meCgmExpc", params)
        result = _format_search_results(data, "meCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"환경부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_me_interpretation_detail", description="""환경부 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_me_interpretation_detail(interpretation_id="123456")""")
def get_me_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """환경부 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("meCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "meCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"환경부 법령해석 상세조회 중 오류: {str(e)}")

# --- 문화체육관광부 (mcstCgmExpc) - 44건 ---
@mcp.tool(name="search_mcst_interpretation", description="""문화체육관광부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mcst_interpretation("저작권"), search_mcst_interpretation("관광", display=50)""")
def search_mcst_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """문화체육관광부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mcstCgmExpc", params)
        result = _format_search_results(data, "mcstCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"문화체육관광부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_mcst_interpretation_detail", description="""문화체육관광부 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_mcst_interpretation_detail(interpretation_id="123456")""")
def get_mcst_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """문화체육관광부 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("mcstCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "mcstCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"문화체육관광부 법령해석 상세조회 중 오류: {str(e)}")

# --- 법무부 (mojCgmExpc) ---
@mcp.tool(name="search_moj_interpretation", description="""법무부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_moj_interpretation("출입국"), search_moj_interpretation("형사", display=50)""")
def search_moj_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법무부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mojCgmExpc", params)
        result = _format_search_results(data, "mojCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법무부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_moj_interpretation_detail", description="""법무부 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_moj_interpretation_detail(interpretation_id="123456")""")
def get_moj_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """법무부 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("mojCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "mojCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법무부 법령해석 상세조회 중 오류: {str(e)}")

# --- 성평등가족부 (mogefCgmExpc) - 구 여성가족부 ---
@mcp.tool(name="search_mogef_interpretation", description="""성평등가족부(구 여성가족부) 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mogef_interpretation("양육"), search_mogef_interpretation("가정폭력", display=50)""")
def search_mogef_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """성평등가족부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mogefCgmExpc", params)
        result = _format_search_results(data, "mogefCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"성평등가족부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_mogef_interpretation_detail", description="""성평등가족부 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_mogef_interpretation_detail(interpretation_id="123456")""")
def get_mogef_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """성평등가족부 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("mogefCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "mogefCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"성평등가족부 법령해석 상세조회 중 오류: {str(e)}")

# --- 외교부 (mofaCgmExpc) - 17건 ---
@mcp.tool(name="search_mofa_interpretation", description="""외교부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mofa_interpretation("비자"), search_mofa_interpretation("외교", display=50)""")
def search_mofa_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """외교부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mofaCgmExpc", params)
        result = _format_search_results(data, "mofaCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"외교부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_mofa_interpretation_detail", description="""외교부 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_mofa_interpretation_detail(interpretation_id="123456")""")
def get_mofa_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """외교부 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("mofaCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "mofaCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"외교부 법령해석 상세조회 중 오류: {str(e)}")

# --- 통일부 (mouCgmExpc) - 6건 ---
@mcp.tool(name="search_unikorea_interpretation", description="""통일부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_unikorea_interpretation("북한"), search_unikorea_interpretation("통일", display=50)""")
def search_unikorea_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """통일부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mouCgmExpc", params)
        result = _format_search_results(data, "mouCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"통일부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_unikorea_interpretation_detail", description="""통일부 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_unikorea_interpretation_detail(interpretation_id="123456")""")
def get_unikorea_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """통일부 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("mouCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "mouCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"통일부 법령해석 상세조회 중 오류: {str(e)}")

# --- 법제처 (molegCgmExpc) - 17건 ---
@mcp.tool(name="search_moleg_interpretation", description="""법제처 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_moleg_interpretation("법령"), search_moleg_interpretation("해석", display=50)""")
def search_moleg_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법제처 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("molegCgmExpc", params)
        result = _format_search_results(data, "molegCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법제처 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_moleg_interpretation_detail", description="""법제처 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_moleg_interpretation_detail(interpretation_id="123456")""")
def get_moleg_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """법제처 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("molegCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "molegCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법제처 법령해석 상세조회 중 오류: {str(e)}")

# --- 식품의약품안전처 (mfdsCgmExpc) - 1,216건 ---
@mcp.tool(name="search_mfds_interpretation", description="""식품의약품안전처 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mfds_interpretation("식품"), search_mfds_interpretation("의약품", display=50)""")
def search_mfds_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """식품의약품안전처 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mfdsCgmExpc", params)
        result = _format_search_results(data, "mfdsCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"식품의약품안전처 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_mfds_interpretation_detail", description="""식품의약품안전처 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_mfds_interpretation_detail(interpretation_id="123456")""")
def get_mfds_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """식품의약품안전처 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("mfdsCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "mfdsCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"식품의약품안전처 법령해석 상세조회 중 오류: {str(e)}")

# --- 인사혁신처 (mpmCgmExpc) - 10건 ---
@mcp.tool(name="search_mpm_interpretation", description="""인사혁신처 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mpm_interpretation("인사"), search_mpm_interpretation("공무원", display=50)""")
def search_mpm_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """인사혁신처 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mpmCgmExpc", params)
        result = _format_search_results(data, "mpmCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"인사혁신처 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_mpm_interpretation_detail", description="""인사혁신처 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_mpm_interpretation_detail(interpretation_id="123456")""")
def get_mpm_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """인사혁신처 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("mpmCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "mpmCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"인사혁신처 법령해석 상세조회 중 오류: {str(e)}")

# --- 기상청 (kmaCgmExpc) - 21건 ---
@mcp.tool(name="search_kma_interpretation", description="""기상청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_kma_interpretation("기상"), search_kma_interpretation("예보", display=50)""")
def search_kma_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """기상청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("kmaCgmExpc", params)
        result = _format_search_results(data, "kmaCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"기상청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_kma_interpretation_detail", description="""기상청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_kma_interpretation_detail(interpretation_id="123456")""")
def get_kma_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """기상청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("kmaCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "kmaCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"기상청 법령해석 상세조회 중 오류: {str(e)}")

# --- 국가유산청 (khaCgmExpc) ---
@mcp.tool(name="search_cha_interpretation", description="""국가유산청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_cha_interpretation("유산"), search_cha_interpretation("문화재", display=50)""")
def search_cha_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """국가유산청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("khaCgmExpc", params)
        result = _format_search_results(data, "khaCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국가유산청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_cha_interpretation_detail", description="""국가유산청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_cha_interpretation_detail(interpretation_id="123456")""")
def get_cha_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """국가유산청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("khaCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "khaCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국가유산청 법령해석 상세조회 중 오류: {str(e)}")

# --- 농촌진흥청 (rdaCgmExpc) - 6건 ---
@mcp.tool(name="search_rda_interpretation", description="""농촌진흥청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_rda_interpretation("농업"), search_rda_interpretation("진흥", display=50)""")
def search_rda_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """농촌진흥청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("rdaCgmExpc", params)
        result = _format_search_results(data, "rdaCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"농촌진흥청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_rda_interpretation_detail", description="""농촌진흥청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_rda_interpretation_detail(interpretation_id="123456")""")
def get_rda_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """농촌진흥청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("rdaCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "rdaCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"농촌진흥청 법령해석 상세조회 중 오류: {str(e)}")

# --- 경찰청 (knpaCgmExpc) ---
@mcp.tool(name="search_police_interpretation", description="""경찰청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_police_interpretation("경찰"), search_police_interpretation("치안", display=50)""")
def search_police_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """경찰청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("knpaCgmExpc", params)
        result = _format_search_results(data, "knpaCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"경찰청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_police_interpretation_detail", description="""경찰청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_police_interpretation_detail(interpretation_id="123456")""")
def get_police_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """경찰청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("knpaCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "knpaCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"경찰청 법령해석 상세조회 중 오류: {str(e)}")

# --- 방위사업청 (dapaCgmExpc) - 46건 ---
@mcp.tool(name="search_dapa_interpretation", description="""방위사업청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_dapa_interpretation("방위"), search_dapa_interpretation("무기", display=50)""")
def search_dapa_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """방위사업청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("dapaCgmExpc", params)
        result = _format_search_results(data, "dapaCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"방위사업청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_dapa_interpretation_detail", description="""방위사업청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_dapa_interpretation_detail(interpretation_id="123456")""")
def get_dapa_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """방위사업청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("dapaCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "dapaCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"방위사업청 법령해석 상세조회 중 오류: {str(e)}")

# --- 병무청 (mmaCgmExpc) ---
@mcp.tool(name="search_mma_interpretation", description="""병무청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mma_interpretation("병역"), search_mma_interpretation("입영", display=50)""")
def search_mma_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """병무청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mmaCgmExpc", params)
        result = _format_search_results(data, "mmaCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"병무청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_mma_interpretation_detail", description="""병무청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_mma_interpretation_detail(interpretation_id="123456")""")
def get_mma_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """병무청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("mmaCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "mmaCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"병무청 법령해석 상세조회 중 오류: {str(e)}")

# --- 소방청 (nfaCgmExpc) - 328건 ---
@mcp.tool(name="search_fire_agency_interpretation", description="""소방청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_fire_agency_interpretation("소방"), search_fire_agency_interpretation("화재", display=50)""")
def search_fire_agency_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """소방청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("nfaCgmExpc", params)
        result = _format_search_results(data, "nfaCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"소방청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_fire_agency_interpretation_detail", description="""소방청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_fire_agency_interpretation_detail(interpretation_id="123456")""")
def get_fire_agency_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """소방청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("nfaCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "nfaCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"소방청 법령해석 상세조회 중 오류: {str(e)}")

# --- 조달청 (ppsCgmExpc) - 23건 ---
@mcp.tool(name="search_pps_interpretation", description="""조달청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_pps_interpretation("조달"), search_pps_interpretation("계약", display=50)""")
def search_pps_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """조달청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("ppsCgmExpc", params)
        result = _format_search_results(data, "ppsCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"조달청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_pps_interpretation_detail", description="""조달청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_pps_interpretation_detail(interpretation_id="123456")""")
def get_pps_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """조달청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("ppsCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "ppsCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"조달청 법령해석 상세조회 중 오류: {str(e)}")

# --- 질병관리청 (kdcaCgmExpc) ---
@mcp.tool(name="search_kdca_interpretation", description="""질병관리청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_kdca_interpretation("질병"), search_kdca_interpretation("감염", display=50)""")
def search_kdca_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """질병관리청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("kdcaCgmExpc", params)
        result = _format_search_results(data, "kdcaCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"질병관리청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_kdca_interpretation_detail", description="""질병관리청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_kdca_interpretation_detail(interpretation_id="123456")""")
def get_kdca_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """질병관리청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("kdcaCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "kdcaCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"질병관리청 법령해석 상세조회 중 오류: {str(e)}")

# --- 해양경찰청 (kcgCgmExpc) ---
@mcp.tool(name="search_kcg_interpretation", description="""해양경찰청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_kcg_interpretation("해양"), search_kcg_interpretation("경찰", display=50)""")
def search_kcg_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """해양경찰청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("kcgCgmExpc", params)
        result = _format_search_results(data, "kcgCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"해양경찰청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_kcg_interpretation_detail", description="""해양경찰청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_kcg_interpretation_detail(interpretation_id="123456")""")
def get_kcg_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """해양경찰청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("kcgCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "kcgCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"해양경찰청 법령해석 상세조회 중 오류: {str(e)}")

# --- 국가보훈부 (mpvaCgmExpc) - 116건 ---
@mcp.tool(name="search_mpva_interpretation", description="""국가보훈부 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_mpva_interpretation("보훈"), search_mpva_interpretation("유공자", display=50)""")
def search_mpva_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """국가보훈부 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("mpvaCgmExpc", params)
        result = _format_search_results(data, "mpvaCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국가보훈부 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_mpva_interpretation_detail", description="""국가보훈부 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_mpva_interpretation_detail(interpretation_id="123456")""")
def get_mpva_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """국가보훈부 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("mpvaCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "mpvaCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국가보훈부 법령해석 상세조회 중 오류: {str(e)}")

# --- 국가데이터처 (kostatCgmExpc) ---
@mcp.tool(name="search_kostat_interpretation", description="""국가데이터처 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_kostat_interpretation("통계"), search_kostat_interpretation("데이터", display=50)""")
def search_kostat_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """국가데이터처 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("kostatCgmExpc", params)
        result = _format_search_results(data, "kostatCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국가데이터처 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_kostat_interpretation_detail", description="""국가데이터처 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_kostat_interpretation_detail(interpretation_id="123456")""")
def get_kostat_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """국가데이터처 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("kostatCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "kostatCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"국가데이터처 법령해석 상세조회 중 오류: {str(e)}")

# --- 지식재산처 (kipoCgmExpc) ---
@mcp.tool(name="search_kipo_interpretation", description="""지식재산처 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_kipo_interpretation("특허"), search_kipo_interpretation("상표", display=50)""")
def search_kipo_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """지식재산처 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("kipoCgmExpc", params)
        result = _format_search_results(data, "kipoCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"지식재산처 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_kipo_interpretation_detail", description="""지식재산처 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_kipo_interpretation_detail(interpretation_id="123456")""")
def get_kipo_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """지식재산처 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("kipoCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "kipoCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"지식재산처 법령해석 상세조회 중 오류: {str(e)}")

# --- 행정중심복합도시건설청 (naaccCgmExpc) ---
@mcp.tool(name="search_naacc_interpretation", description="""행정중심복합도시건설청 법령해석을 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_naacc_interpretation("도시"), search_naacc_interpretation("건설", display=50)""")
def search_naacc_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """행정중심복합도시건설청 법령해석 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("naaccCgmExpc", params)
        result = _format_search_results(data, "naaccCgmExpc", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"행정중심복합도시건설청 법령해석 검색 중 오류: {str(e)}")

@mcp.tool(name="get_naacc_interpretation_detail", description="""행정중심복합도시건설청 법령해석 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID

사용 예시: get_naacc_interpretation_detail(interpretation_id="123456")""")
def get_naacc_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """행정중심복합도시건설청 법령해석 상세 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("naaccCgmExpc", params, is_detail=True)
        result = _format_search_results(data, "naaccCgmExpc", str(interpretation_id))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"행정중심복합도시건설청 법령해석 상세조회 중 오류: {str(e)}")

# ===========================================
# 로깅
# ===========================================
logger.info("44개 추가 중앙부처해석 도구가 로드되었습니다! (22개 부처 x 검색/상세 도구)")
