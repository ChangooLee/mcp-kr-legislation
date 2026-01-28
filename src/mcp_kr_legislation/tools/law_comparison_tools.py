"""
법령 비교/이력 도구 모듈

비교, 연계, 이력 조회 관련 도구들을 제공합니다.
- 법령 변경이력 검색
- 조문별 변경이력 검색
- 법령 버전 비교
- 관련법령 검색
- 자치법규 연계 검색
- 별표서식 검색/조회
"""

import logging
import requests
from typing import Optional, Union

from mcp.types import TextContent

from ..server import mcp
from ..config import legislation_config

# law_tools에서 공통 함수들 import
from .law_tools import (
    _make_legislation_request,
    _format_search_results,
    get_cache_key,
    load_from_cache,
    save_to_cache,
    normalize_article_key,
    find_article_in_data,
    clean_html_tags,
)

logger = logging.getLogger(__name__)

# ===========================================
# 법령 변경이력/비교 도구들
# ===========================================

@mcp.tool(name="search_law_change_history", description="""법령 변경이력을 검색합니다. (대용량 데이터로 시간이 오래 걸릴 수 있음)

매개변수:
- change_date: 변경일자 (필수) - YYYYMMDD 형식 (예: 20240101)
- org: 소관부처 코드 (선택)
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 법령명, 변경ID, 변경일자, 변경유형, 변경내용 요약

사용 예시:
- search_law_change_history("20240101")  # 2024년 1월 1일 변경이력
- search_law_change_history("20241201", display=50)  # 2024년 12월 1일 변경이력
- search_law_change_history("20240701", org="1270000")  # 특정 부처의 변경이력

후속 조회: 변경된 법령의 구체적 내용 확인
- get_law_detail(mst="법령ID")  # 변경된 법령의 전체 내용
- compare_law_versions("법령명")  # 개정 전후 비교
- search_law_history("법령명")  # 해당 법령의 전체 연혁

주의: 특정 날짜에 발생한 법령의 제정, 개정, 폐지 등 모든 변경사항을 추적하며, 대용량 데이터로 인해 응답 시간이 길 수 있습니다.""")
def search_law_change_history(change_date: str, org: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령 변경이력 검색
    
    Args:
        change_date: 변경일자 (YYYYMMDD, 필수)
        org: 소관부처 코드 (선택)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 변경일자 유효성 검사
        if not change_date or len(change_date) != 8 or not change_date.isdigit():
            return TextContent(type="text", text="변경일자는 YYYYMMDD 형식의 8자리 숫자여야 합니다. (예: 20240101)")
        
        # 기본 파라미터 설정 (필수 파라미터 포함)
        params = {
            "OC": legislation_config.oc,  # 필수: 기관코드
            "type": "JSON",               # 필수: 출력형태
            "target": "lsHstInf",         # 필수: 서비스 대상 (올바른 target)
            "regDt": change_date,         # 필수: 법령 변경일
            "display": min(display, 100),
            "page": page
        }
        
        # 선택적 파라미터 추가
        if org:
            params["org"] = org
        
        # API 요청 (타임아웃 대응)
        try:
            data = _make_legislation_request("lsHstInf", params, is_detail=False)
        except requests.exceptions.ReadTimeout:
            return TextContent(type="text", text=f"""**법령 변경이력 검색 결과**

**검색일자**: {change_date}

⚠️ **타임아웃 오류**: API 응답 시간이 초과되었습니다.

**해결 방법**:
1. **잠시 후 재시도**: 같은 명령을 다시 실행해보세요
2. **날짜 범위 축소**: 더 짧은 기간으로 검색해보세요  
3. **부처별 검색**: org 파라미터로 특정 부처만 검색해보세요

**대안 방법**:
- search_law("법령명")으로 특정 법령의 변경이력 확인
- get_law_detail()로 법령 기본정보 확인

**참고**: 변경이력 데이터가 많은 날짜는 응답 시간이 길어질 수 있습니다.""")
        except requests.exceptions.ConnectionError:
            return TextContent(type="text", text=f"""**법령 변경이력 검색 결과**

**검색일자**: {change_date}

⚠️ **연결 오류**: API 서버에 연결할 수 없습니다.

**해결 방법**:
1. **네트워크 확인**: 인터넷 연결 상태를 확인해주세요
2. **잠시 후 재시도**: API 서버가 일시적으로 불안정할 수 있습니다
3. **다른 도구 사용**: search_law()로 개별 법령 검색해보세요

**참고**: 법제처 API 서버가 점검 중일 수 있습니다.""")
        
        # 검색 조건 표시용
        search_query = f"법령 변경이력 ({change_date[:4]}-{change_date[4:6]}-{change_date[6:8]})"
        if org:
            search_query += f" [부처: {org}]"
        
        result = _format_search_results(data, "lsHstInf", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"법령 변경이력 검색 중 오류: {e}")
        return TextContent(type="text", text=f"법령 변경이력 검색 중 오류가 발생했습니다: {str(e)}")


@mcp.tool(name="search_article_change_history", description="""조문의 상세 변경이력과 정책적 배경을 조회합니다.

매개변수:
- mst: 법령일련번호 (필수) - search_law_unified로 먼저 확인
- article_no: 조문번호 (필수) - "제1조", "제15조" 형식 또는 "000100" 6자리 형식
- display: 결과 개수 (기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 변경일자, 변경유형, 변경내용, 정책적 배경

사용 예시:
- search_article_change_history(mst="248613", article_no="제15조")
- search_article_change_history(mst="248613", article_no="001500")

참고: 특정 조문의 시간에 따른 변경이력을 추적합니다.""")
def search_article_change_history(mst: str, article_no: str, display: int = 20, page: int = 1) -> TextContent:
    """조문별 변경이력 검색
    
    Args:
        mst: 법령일련번호(MST) (필수)
        article_no: 조번호 (다양한 형식 지원)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 필수 파라미터 유효성 검사
        if not mst or not mst.strip():
            return TextContent(type="text", text="법령일련번호(MST)가 필요합니다. search_law_unified 도구로 법령을 검색하여 MST를 확인하세요.")
        
        if not article_no:
            return TextContent(type="text", text="조번호가 필요합니다. (예: '제1조', '제15조', '제10조의2' 또는 '000100', '001500', '001002')")
        
        # 조문 번호 정규화
        normalized_article_no = _normalize_article_number(article_no.strip())
        if len(normalized_article_no) != 6 or not normalized_article_no.isdigit():
            return TextContent(type="text", text=f"조번호 형식이 올바르지 않습니다: '{article_no}' → '{normalized_article_no}'. 지원 형식: '제1조', '1조', '000100'")
        
        # MST인지 ID인지 확인 후 적절한 값 사용
        mst_str = mst.strip()
        actual_law_id = mst_str
        
        # MST 값인 경우 (보통 6자리 이상의 숫자) ID로 변환 시도
        if len(mst_str) >= 6 and mst_str.isdigit():
            try:
                # 해당 MST로 법령 검색하여 ID 확인
                search_params = {
                    "OC": legislation_config.oc,
                    "type": "JSON",
                    "target": "law",
                    "MST": mst_str,
                    "display": 1
                }
                search_data = _make_legislation_request("law", search_params, is_detail=True)
                
                if search_data and "법령" in search_data:
                    law_info = search_data["법령"]
                    basic_info = law_info.get("기본정보", {})
                    found_id = basic_info.get("법령ID", basic_info.get("ID", ""))
                    if found_id:
                        actual_law_id = str(found_id)
                        logger.info(f"MST {mst_str}를 ID {actual_law_id}로 변환")
            except Exception as e:
                logger.warning(f"MST를 ID로 변환 실패: {e}")
                # 변환 실패시 원래 값 사용
        
        # 기본 파라미터 설정 (필수 파라미터 포함)
        params = {
            "OC": legislation_config.oc,  # 필수: 기관코드
            "type": "JSON",               # 필수: 출력형태
            "target": "lsJoHstInf",       # 필수: 서비스 대상 (올바른 target)
            "ID": actual_law_id,          # 필수: 법령ID (MST에서 변환된 값)
            "JO": normalized_article_no,  # 필수: 조번호 (정규화됨)
            "display": min(display, 100),
            "page": page
        }
        
        # API 요청
        data = _make_legislation_request("lsJoHstInf", params, is_detail=True)
        
        # 조문번호 표시 형식화 (000200 -> 제2조)
        article_display = f"제{int(normalized_article_no[:4])}조"
        if normalized_article_no[4:6] != "00":
            article_display += f"의{int(normalized_article_no[4:6])}"
        
        search_term = f"조문 변경이력 (MST: {mst}, {article_display})"
        result = _format_search_results(data, "lsJoHstInf", search_term)
        
        # MST→ID 변환 정보 추가
        if actual_law_id != mst_str:
            result += f"""

**문제 해결**: MST를 ID로 변환했습니다 ({mst} → {actual_law_id})"""
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"조문별 변경이력 검색 중 오류: {e}")
        return TextContent(type="text", text=f"조문별 변경이력 검색 중 오류가 발생했습니다: {str(e)}")


@mcp.tool(
    name="compare_law_versions",
    description="""동일 법령의 현행 버전과 시행일 버전을 비교합니다.

매개변수:
- law_name: 법령명 (필수) - 비교할 법령의 이름

반환정보:
- 현행 버전 정보: 공포일자, 시행일자, 제개정구분
- 시행일 버전 정보: 공포일자, 시행일자, 제개정구분  
- 주요 변경사항: 조문별 차이점 요약 (신설/수정/삭제 조문)

사용 예시:
- compare_law_versions("개인정보보호법")
- compare_law_versions("소득세법")

참고: 최근 시행일 버전과 현행 버전을 자동으로 비교하며, 조문별 차이점을 표시합니다."""
)
def compare_law_versions(law_name: str) -> TextContent:
    """법령 버전 비교 (조문 차이점 포함)"""
    if not law_name:
        return TextContent(type="text", text="법령명을 입력해주세요.")
    
    try:
        # 1. 현행법령 검색
        current_data = _make_legislation_request("law", {"query": law_name, "display": 1})
        current_items = current_data.get("LawSearch", {}).get("law", [])
        
        if not current_items:
            return TextContent(type="text", text=f"'{law_name}'을(를) 찾을 수 없습니다.")
        
        current_law = current_items[0] if isinstance(current_items, list) else current_items
        current_mst = current_law.get("법령일련번호")
        
        if not current_mst:
            return TextContent(type="text", text=f"현행법령의 법령일련번호를 찾을 수 없습니다.")
        
        # 2. 시행일법령 검색
        eflaw_data = _make_legislation_request("eflaw", {"query": law_name, "display": 5})
        eflaw_items = eflaw_data.get("LawSearch", {}).get("law", [])
        
        if not isinstance(eflaw_items, list):
            eflaw_items = [eflaw_items] if eflaw_items else []
        
        if not eflaw_items:
            return TextContent(type="text", text=f"'{law_name}'의 시행일법령을 찾을 수 없습니다.")
        
        # 가장 최근 시행일법령 선택
        eflaw_law = eflaw_items[0]
        eflaw_mst = eflaw_law.get("법령일련번호")
        
        if not eflaw_mst:
            return TextContent(type="text", text=f"시행일법령의 법령일련번호를 찾을 수 없습니다.")
        
        # 3. 두 버전의 상세 조문 조회
        current_detail = _make_legislation_request("law", {"MST": current_mst}, is_detail=True)
        eflaw_detail = _make_legislation_request("eflaw", {"MST": eflaw_mst}, is_detail=True)
        
        # 4. 조문 추출
        current_articles = _extract_articles_from_detail(current_detail)
        eflaw_articles = _extract_articles_from_detail(eflaw_detail)
        
        # 5. 조문 비교
        comparison_result = _compare_articles(current_articles, eflaw_articles)
        
        # 6. 결과 포맷팅
        result = _format_version_comparison(
            law_name, 
            current_law, 
            eflaw_law, 
            current_articles, 
            eflaw_articles, 
            comparison_result
        )
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"버전 비교 중 오류: {e}")
        return TextContent(type="text", text=f"버전 비교 중 오류가 발생했습니다: {str(e)}")


# ===========================================
# 연계 검색 도구들
# ===========================================

@mcp.tool(name="search_ordinance_law_link", description="""자치법규와 연계된 법령 목록을 검색합니다 (법령 기준).

매개변수:
- query: 검색어 (선택) - 법령명 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 법령ID, 법령명, 법령구분, 시행일자, 공포일자

사용 예시:
- search_ordinance_law_link()  # 전체 목록
- search_ordinance_law_link("자동차")  # 자동차 관련 법령의 자치법규 연계

참고: 법령과 자치법규의 연계 현황을 파악할 때 사용합니다.""")
def search_ordinance_law_link(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령 기준 자치법규 연계 목록 검색
    
    Args:
        query: 검색어 (법령명)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정
        params = {
            "display": min(display, 100),
            "page": page
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            search_query = query.strip()
            params["query"] = search_query
        else:
            search_query = "법령-자치법규 연계"
        
        # API 요청 - target: lnkLs (법령 기준 자치법규 연계)
        data = _make_legislation_request("lnkLs", params)
        result = _format_search_results(data, "lnkLs", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"자치법규-법령 연계정보 검색 중 오류: {e}")
        return TextContent(type="text", text=f"자치법규-법령 연계정보 검색 중 오류가 발생했습니다: {str(e)}")


@mcp.tool(name="search_related_law", description="""관련법령을 검색합니다.

[중요] query 입력 가이드:
- 올바른 예: "민법", "상법", "개인정보"
- 잘못된 예: "민법과 관련된 법령을 찾아줘" (문장 금지)
- 법령명 또는 키워드만 입력하세요.

매개변수:
- query: 법령명만 입력 (필수, 문장 금지)
- display: 결과 개수 (기본 20)

반환정보: 기준법령명, 관련법령명, 관계유형

사용 예시:
- search_related_law("민법")
- search_related_law("상법")""")
def search_related_law(query: str, display: int = 20, page: int = 1) -> TextContent:
    """관련법령 검색 (캐시 지원)
    
    Args:
        query: 검색어 (법령명) - 필수
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 검색어 필수 체크
        if not query or not query.strip():
            return TextContent(type="text", text="""**관련법령 검색**

⚠️ **검색어가 필요합니다**

관련법령을 검색하려면 법령명 또는 키워드를 입력해주세요.

**사용 예시**:
- search_related_law("개인정보보호법")
- search_related_law("소득세법")
- search_related_law("민법")

**참고**: 전체 관련법령 목록(5,300건 이상)은 응답 시간이 매우 길어 검색어 지정을 권장합니다.""")
        
        search_query = query.strip()
        
        # 캐시 확인
        try:
            cache_key = get_cache_key(f"lsRlt_{search_query}_{display}_{page}", "related_law")
            cached_data = load_from_cache(cache_key)
            if cached_data:
                logger.info(f"관련법령 캐시 히트: {search_query}")
                result = _format_search_results(cached_data, "lsRlt", search_query)
                return TextContent(type="text", text=result + "\n\n(캐시된 결과)")
        except Exception:
            logger.warning("캐시 모듈 로드 실패, API 직접 호출")
            cached_data = None
            cache_key = None
        
        # 기본 파라미터 설정
        params = {
            "query": search_query,
            "display": min(display, 100),
            "page": page
        }
        
        # API 요청 (타임아웃 60초)
        data = _make_legislation_request("lsRlt", params, timeout=60)
        
        # 캐시 저장 (결과가 있는 경우)
        if data and cache_key:
            try:
                save_to_cache(cache_key, data)
                logger.info(f"관련법령 캐시 저장: {search_query}")
            except Exception as cache_err:
                logger.warning(f"캐시 저장 실패: {cache_err}")
        
        result = _format_search_results(data, "lsRlt", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"관련법령 검색 중 오류: {e}")
        return TextContent(type="text", text=f"관련법령 검색 중 오류가 발생했습니다: {str(e)}")


# ===========================================
# 별표서식 도구들
# ===========================================

@mcp.tool(name="search_law_appendix", description="""법령 별표서식을 검색합니다.

매개변수:
- query: 검색어 (선택) - 별표명 또는 서식명
- search: 검색범위 (기본값: 1)
  - 1: 명칭으로만 검색
  - 2: 내용 포함 검색
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)
- appendix_type: 별표종류 (선택)
  - 1: 별표
  - 2: 서식
  - 3: 양식
  - 4: 기타
- ministry_code: 소관부처 코드 (선택)
- local_gov_code: 지자체 코드 (선택)
- sort: 정렬 방식 (선택)
  - name_asc: 명칭 오름차순
  - name_desc: 명칭 내림차순
  - date_asc: 일자 오름차순
  - date_desc: 일자 내림차순

반환정보: 별표서식명, 별표서식ID, 관련법령명, 법령ID, 별표종류, 소관부처

사용 예시:
- search_law_appendix("신청서")
- search_law_appendix("수수료", appendix_type=1)  # 별표만 검색
- search_law_appendix("시행규칙", search=2, sort="date_desc")  # 최신순 정렬

참고: 법령에 첨부된 별표, 서식, 양식 등을 검색할 수 있습니다.""")
def search_law_appendix(
    query: Optional[str] = None,
    search: int = 1,
    display: int = 20,
    page: int = 1,
    appendix_type: Optional[str] = None,
    ministry_code: Optional[str] = None,
    local_gov_code: Optional[str] = None,
    sort: Optional[str] = None
) -> TextContent:
    """법령 별표서식 검색
    
    Args:
        query: 검색어 (별표/서식명)
        search: 검색범위 (1=명칭, 2=내용)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        appendix_type: 별표종류 (1=별표, 2=서식, 3=양식, 4=기타)
        ministry_code: 소관부처 코드
        local_gov_code: 지자체 코드
        sort: 정렬 (name_asc=명칭오름차순, name_desc=명칭내림차순, date_asc=일자오름차순, date_desc=일자내림차순)
    """
    try:
        # 기본 파라미터 설정
        params = {
            "search": search,
            "display": min(display, 100),
            "page": page
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            search_query = query.strip()
            params["query"] = search_query
        else:
            search_query = "법령 별표서식"
        
        # 선택적 파라미터 추가
        optional_params = {
            "appendixType": appendix_type,
            "ministryCode": ministry_code,
            "localGovCode": local_gov_code,
            "sort": sort
        }
        
        for key, value in optional_params.items():
            if value is not None:
                params[key] = value
        
        # API 요청 - target: licbyl (법령 별표서식)
        data = _make_legislation_request("licbyl", params)
        result = _format_search_results(data, "licbyl", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"법령 별표서식 검색 중 오류: {e}")
        return TextContent(type="text", text=f"법령 별표서식 검색 중 오류가 발생했습니다: {str(e)}")


@mcp.tool(name="get_law_appendix_detail", description="""법령 별표서식 상세정보를 조회합니다.

매개변수:
- appendix_id: 별표일련번호 - search_law_appendix 결과의 '별표일련번호' 필드값 사용

사용 예시: get_law_appendix_detail(appendix_id="16483259")

참고: 별표서식 상세는 HTML만 지원됩니다. PDF/이미지 파일 링크를 제공합니다.""")
def get_law_appendix_detail(appendix_id: Union[str, int]) -> TextContent:
    """법령 별표서식 상세내용 조회
    
    Args:
        appendix_id: 별표일련번호
    """
    if not appendix_id:
        return TextContent(type="text", text="별표일련번호를 입력해주세요. (예: 16483259)")
    
    try:
        # 목록에서 해당 별표 정보 찾기
        params = {"display": 100}
        data = _make_legislation_request("licbyl", params, is_detail=False)
        
        if "licBylSearch" in data and "licbyl" in data["licBylSearch"]:
            items = data["licBylSearch"]["licbyl"]
            if isinstance(items, dict):
                items = [items]
            
            for item in items:
                if str(item.get("별표일련번호", "")) == str(appendix_id):
                    result = f"""**별표서식 상세**

**별표명**: {item.get('별표명', '')}
**별표종류**: {item.get('별표종류', '')}
**별표번호**: {item.get('별표번호', '')}

**관련법령**: {item.get('관련법령명', '')}
**관련법령ID**: {item.get('관련법령ID', '')}
**공포일자**: {item.get('공포일자', '')}

**파일 링크**:
- 서식파일: http://www.law.go.kr{item.get('별표서식파일링크', '')}
- PDF파일: http://www.law.go.kr{item.get('별표서식PDF파일링크', '')}

**상세페이지**: http://www.law.go.kr{item.get('별표법령상세링크', '')}

참고: 별표서식 상세는 HTML만 지원됩니다. 위 링크를 통해 확인하세요."""
                    return TextContent(type="text", text=result)
            
            return TextContent(type="text", text=f"별표일련번호 {appendix_id}에 해당하는 별표서식을 찾을 수 없습니다.")
        
        return TextContent(type="text", text="별표서식 정보를 조회할 수 없습니다.")
        
    except Exception as e:
        logger.error(f"법령 별표서식 상세조회 중 오류: {e}")
        return TextContent(type="text", text=f"법령 별표서식 상세조회 중 오류가 발생했습니다: {str(e)}")


# ===========================================
# 헬퍼 함수들
# ===========================================

def _normalize_article_number(article_no: str) -> str:
    """조문 번호를 6자리 형식으로 정규화"""
    import re
    
    try:
        # 이미 6자리 숫자 형식인 경우
        if re.match(r'^\d{6}$', article_no):
            return article_no
        
        # "제N조" 형식 처리
        match = re.match(r'^제(\d+)조(?:의(\d+))?$', article_no)
        if match:
            main_num = int(match.group(1))
            sub_num = int(match.group(2)) if match.group(2) else 0
            return f"{main_num:04d}{sub_num:02d}"
        
        # "N조" 형식 처리
        match = re.match(r'^(\d+)조(?:의(\d+))?$', article_no)
        if match:
            main_num = int(match.group(1))
            sub_num = int(match.group(2)) if match.group(2) else 0
            return f"{main_num:04d}{sub_num:02d}"
        
        # 숫자만 있는 경우
        match = re.match(r'^(\d+)$', article_no)
        if match:
            main_num = int(match.group(1))
            return f"{main_num:04d}00"
        
        # 변환 실패 시 원본 반환
        return article_no
        
    except Exception as e:
        logger.warning(f"조문 번호 정규화 실패: {article_no} -> {e}")
        return article_no


def _extract_articles_from_detail(detail_data: dict) -> list:
    """법령 상세 데이터에서 조문 추출
    
    Args:
        detail_data: 법령 상세 API 응답 데이터
        
    Returns:
        조문 리스트 (각 조문은 dict 형태)
    """
    articles = []
    
    try:
        # 법령 구조 확인
        law_info = detail_data.get("법령", {})
        if not law_info:
            # eflaw는 다른 구조일 수 있음
            law_info = detail_data
        
        # 조문 섹션 확인
        articles_section = law_info.get("조문", {})
        if not articles_section:
            return articles
        
        # 조문단위 추출
        article_units = []
        if isinstance(articles_section, dict) and "조문단위" in articles_section:
            article_units = articles_section.get("조문단위", [])
        elif isinstance(articles_section, list):
            article_units = articles_section
        
        if not isinstance(article_units, list):
            article_units = [article_units] if article_units else []
        
        # 실제 조문만 필터링
        for article in article_units:
            if isinstance(article, dict) and article.get("조문여부") == "조문":
                article_no = article.get("조문번호", "")
                article_content = article.get("조문내용", "")
                article_title = article.get("조문제목", "")
                
                if article_no:
                    articles.append({
                        "조문번호": article_no,
                        "조문제목": article_title,
                        "조문내용": clean_html_tags(article_content) if article_content else "",
                        "전체내용": article  # 원본 데이터 보관
                    })
        
        return articles
        
    except Exception as e:
        logger.error(f"조문 추출 중 오류: {e}")
        return articles


def _compare_articles(current_articles: list, previous_articles: list) -> dict:
    """두 버전의 조문 비교
    
    Args:
        current_articles: 현행법령 조문 리스트
        previous_articles: 시행일법령 조문 리스트
        
    Returns:
        비교 결과 딕셔너리
    """
    result = {
        "신설": [],  # 새로 추가된 조문
        "수정": [],  # 내용이 변경된 조문
        "삭제": [],  # 삭제된 조문
        "동일": []   # 변경되지 않은 조문
    }
    
    # 조문번호를 키로 하는 딕셔너리 생성
    current_dict = {art["조문번호"]: art for art in current_articles}
    previous_dict = {art["조문번호"]: art for art in previous_articles}
    
    # 모든 조문번호 수집
    all_article_nos = set(current_dict.keys()) | set(previous_dict.keys())
    
    for article_no in sorted(all_article_nos, key=lambda x: int(x) if x.isdigit() else 9999):
        current_art = current_dict.get(article_no)
        previous_art = previous_dict.get(article_no)
        
        if current_art and not previous_art:
            # 신설 조문
            result["신설"].append({
                "조문번호": article_no,
                "조문제목": current_art.get("조문제목", ""),
                "조문내용": current_art.get("조문내용", "")[:200]  # 미리보기
            })
        elif not current_art and previous_art:
            # 삭제된 조문
            result["삭제"].append({
                "조문번호": article_no,
                "조문제목": previous_art.get("조문제목", ""),
                "조문내용": previous_art.get("조문내용", "")[:200]  # 미리보기
            })
        elif current_art and previous_art:
            # 내용 비교
            current_content = current_art.get("조문내용", "").strip()
            previous_content = previous_art.get("조문내용", "").strip()
            
            if current_content != previous_content:
                # 수정된 조문
                result["수정"].append({
                    "조문번호": article_no,
                    "조문제목": current_art.get("조문제목", ""),
                    "현행내용": current_content[:200],
                    "이전내용": previous_content[:200]
                })
            else:
                # 동일한 조문
                result["동일"].append(article_no)
    
    return result


def _format_version_comparison(
    law_name: str,
    current_law: dict,
    eflaw_law: dict,
    current_articles: list,
    eflaw_articles: list,
    comparison_result: dict
) -> str:
    """버전 비교 결과 포맷팅"""
    result = f"**{law_name}** 버전 비교\n"
    result += "=" * 50 + "\n\n"
    
    # 기본 정보
    result += "**현행법령:**\n"
    result += f"• 법령일련번호: {current_law.get('법령일련번호')}\n"
    result += f"• 공포일자: {current_law.get('공포일자')}\n"
    result += f"• 시행일자: {current_law.get('시행일자')}\n"
    result += f"• 제개정구분: {current_law.get('제개정구분명')}\n"
    result += f"• 조문 수: {len(current_articles)}개\n\n"
    
    result += "**시행일법령:**\n"
    result += f"• 법령일련번호: {eflaw_law.get('법령일련번호')}\n"
    result += f"• 공포일자: {eflaw_law.get('공포일자')}\n"
    result += f"• 시행일자: {eflaw_law.get('시행일자')}\n"
    result += f"• 제개정구분: {eflaw_law.get('제개정구분명')}\n"
    result += f"• 조문 수: {len(eflaw_articles)}개\n\n"
    
    # 변경사항 요약
    result += "**변경사항 요약:**\n"
    result += f"• 신설 조문: {len(comparison_result['신설'])}개\n"
    result += f"• 수정 조문: {len(comparison_result['수정'])}개\n"
    result += f"• 삭제 조문: {len(comparison_result['삭제'])}개\n"
    result += f"• 동일 조문: {len(comparison_result['동일'])}개\n\n"
    
    # 신설 조문
    if comparison_result["신설"]:
        result += "**신설 조문:**\n"
        for art in comparison_result["신설"][:10]:  # 최대 10개
            result += f"\n• 제{art['조문번호']}조"
            if art.get("조문제목"):
                result += f" ({art['조문제목']})"
            result += "\n"
            if art.get("조문내용"):
                result += f"  {art['조문내용']}...\n"
        if len(comparison_result["신설"]) > 10:
            result += f"\n... 외 {len(comparison_result['신설']) - 10}개 신설 조문\n"
        result += "\n"
    
    # 수정 조문
    if comparison_result["수정"]:
        result += "**수정 조문:**\n"
        for art in comparison_result["수정"][:5]:  # 최대 5개
            result += f"\n• 제{art['조문번호']}조"
            if art.get("조문제목"):
                result += f" ({art['조문제목']})"
            result += "\n"
            result += f"  [이전] {art.get('이전내용', '')}...\n"
            result += f"  [현행] {art.get('현행내용', '')}...\n"
        if len(comparison_result["수정"]) > 5:
            result += f"\n... 외 {len(comparison_result['수정']) - 5}개 수정 조문\n"
        result += "\n"
    
    # 삭제 조문
    if comparison_result["삭제"]:
        result += "**삭제 조문:**\n"
        for art in comparison_result["삭제"][:10]:  # 최대 10개
            result += f"\n• 제{art['조문번호']}조"
            if art.get("조문제목"):
                result += f" ({art['조문제목']})"
            result += "\n"
            if art.get("조문내용"):
                result += f"  {art['조문내용']}...\n"
        if len(comparison_result["삭제"]) > 10:
            result += f"\n... 외 {len(comparison_result['삭제']) - 10}개 삭제 조문\n"
        result += "\n"
    
    # 상세 조회 안내
    result += "\n**상세 조회**:\n"
    result += f"• 현행법령: get_law_detail(mst=\"{current_law.get('법령일련번호')}\")\n"
    result += f"• 시행일법령: get_effective_law_detail(mst=\"{eflaw_law.get('법령일련번호')}\")\n"
    
    return result


logger.info("법령 비교/이력 도구가 로드되었습니다! (7개 도구)")
