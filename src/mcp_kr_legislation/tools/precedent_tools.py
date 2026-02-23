"""
한국 법제처 OPEN API - 판례 관련 도구들

대법원 판례, 헌법재판소 결정례, 법령해석례, 행정심판례 등 
판례 관련 검색 및 조회 기능을 제공합니다.
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
)
from ..utils.law_tools_utils import extract_total_count, format_result_guidance

def _format_precedent_search_results(data: dict, target: str, search_query: str, max_results: int = 50) -> str:
    """판례/해석례/행정심판례 전용 검색 결과 포맷팅 함수"""
    try:
        # 타겟별 루트 키 매핑 (실제 API 응답 구조 기준)
        target_root_map = {
            "prec": "PrecSearch",
            "expc": "Expc", 
            "decc": "Decc"
        }
        
        # 올바른 루트 키에서 데이터 추출
        root_key = target_root_map.get(target)
        if not root_key or root_key not in data:
            return f"'{search_query}'에 대한 검색 결과가 없습니다."
        
        search_data = data[root_key]
        target_data = search_data.get(target, [])
        
        if isinstance(target_data, str):
            if target_data.strip() == "" or "검색 결과가 없습니다" in target_data:
                target_data = []
        elif isinstance(target_data, dict) and target_data:
            # 단일 딕셔너리인 경우 리스트로 변환
            target_data = [target_data]
        
        if not target_data:
            return f"'{search_query}'에 대한 검색 결과가 없습니다."
        
        # 제한된 결과만 처리
        if isinstance(target_data, list):
            target_data = target_data[:max_results]
        
        # 타겟별 제목 키 설정
        if target == "prec":
            title_keys = ['사건명', '재판사건명', '사건제목']
            detail_fields = {
                '사건번호': ['사건번호', 'CaseNo', 'caseNo'],
                '선고일자': ['선고일자', 'judgment_date', 'judgeDate'], 
                '법원명': ['법원명', 'court', 'courtName']
            }
        elif target == "expc":
            title_keys = ['안건명', '해석례명', '해석제목', '질의제목']
            detail_fields = {
                '안건번호': ['안건번호', '해석례번호', 'expc_no', 'ExpcNo'],
                '회신일자': ['회신일자', '작성일자', 'create_date', 'createDate'],
                '질의기관': ['질의기관명', '소관부처', 'dept', 'department']
            }
        elif target == "decc":
            title_keys = ['재결례명', '사건명', '재결제목']
            detail_fields = {
                '사건번호': ['사건번호', 'case_no', 'caseNo'],
                '재결일자': ['재결일자', 'decision_date', 'decisionDate'],
                '심판부': ['심판부', 'panel', 'tribunal']
            }
        else:
            title_keys = ['title', 'name', '제목']
            detail_fields = {}
        
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
            
            # ID 정보 추가 (상세조회용) - 타겟별 올바른 ID 키 사용
            # 주의: 안건번호/사건번호와 일련번호는 다름! 상세조회는 일련번호를 사용해야 함
            if target == "prec":
                # 판례는 판례일련번호를 사용해야 함 (검색의 id는 순번일 뿐)
                for id_key in ['판례일련번호', '판례정보일련번호', 'mstSeq']:
                    if id_key in item and item[id_key]:
                        result_lines.append(f"   ★ 상세조회용 ID: {item[id_key]}")
                        result_lines.append(f"   상세조회: get_precedent_detail(case_id=\"{item[id_key]}\")")
                        break
            elif target == "expc":
                # 해석례는 법령해석례일련번호 사용 (안건번호 아님!)
                for id_key in ['법령해석례일련번호', '해석례일련번호', 'mstSeq']:
                    if id_key in item and item[id_key]:
                        result_lines.append(f"   ★ 상세조회용 ID: {item[id_key]} (※안건번호와 다름)")
                        result_lines.append(f"   상세조회: get_legal_interpretation_detail(interpretation_id=\"{item[id_key]}\")")
                        break
            elif target == "decc":
                # 행정심판례는 행정심판례일련번호 사용
                for id_key in ['행정심판례일련번호', '심판례일련번호', 'mstSeq']:
                    if id_key in item and item[id_key]:
                        result_lines.append(f"   ★ 상세조회용 ID: {item[id_key]}")
                        result_lines.append(f"   상세조회: get_administrative_trial_detail(trial_id=\"{item[id_key]}\")")
                        break
            else:
                # 기타 타겟은 기존 방식 사용
                for id_key in ['ID', 'id', 'mstSeq', '일련번호']:
                    if id_key in item and item[id_key]:
                        result_lines.append(f"   상세조회: get_{target}_detail(id=\"{item[id_key]}\")")
                        break
                    
            results.append("\\n".join(result_lines))
        
        total_count = search_data.get('totalCnt', len(target_data))
        
        return f"**'{search_query}' 검색 결과** (총 {total_count}건)\\n\\n" + "\\n\\n".join(results)
        
    except Exception as e:
        logger.error(f"판례 검색 결과 포맷팅 오류: {e}")
        return f"검색 결과 처리 중 오류가 발생했습니다: {str(e)}"

def _format_constitutional_search_results(data: dict, target: str, search_query: str, max_results: int = 50) -> str:
    """헌법재판소 검색 전용 결과 포맷팅 함수"""
    try:
        # 헌법재판소는 DetcSearch > Detc 구조 사용
        if 'DetcSearch' not in data or 'Detc' not in data['DetcSearch']:
            return f"'{search_query}'에 대한 검색 결과가 없습니다."
        
        detc_item = data['DetcSearch']['Detc']
        
        # Detc는 배열 형태로 반환됨
        if isinstance(detc_item, list):
            target_data = detc_item
        elif isinstance(detc_item, dict) and detc_item:
            target_data = [detc_item]
        else:
            return f"'{search_query}'에 대한 검색 결과가 없습니다."
        
        # 제한된 결과만 처리
        target_data = target_data[:max_results]
        
        # 헌법재판소 제목 및 상세 정보 필드
        title_keys = ['사건명', '결정명', '헌법재판소결정명']
        detail_fields = {
            '사건번호': ['사건번호', 'caseNo', 'CaseNo'],
            '종국일자': ['종국일자', 'finalDate', 'judgment_date'],
            '재판관': ['재판관', 'judge', 'justices']
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
            for id_key in ['헌재결정례일련번호', 'ID', 'id']:
                if id_key in item and item[id_key]:
                    result_lines.append(f"   상세조회: get_constitutional_court_detail(decision_id=\"{item[id_key]}\")")
                    break
                    
            results.append("\\n".join(result_lines))
        
        search_data = data['DetcSearch']
        total_count = search_data.get('totalCnt', len(target_data))
        
        return f"**'{search_query}' 검색 결과** (총 {total_count}건)\\n\\n" + "\\n\\n".join(results)
        
    except Exception as e:
        logger.error(f"헌법재판소 검색 결과 포맷팅 오류: {e}")
        return f"검색 결과 처리 중 오류가 발생했습니다: {str(e)}"

# ===========================================
# 판례 관련 도구들 (8개)
# ===========================================

@mcp.tool(name="search_precedent", description="""대법원 판례를 검색합니다.

매개변수:
- query: 검색어 (필수)
- search: 검색범위 (1=판례명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- court_type: 법원종류 (400201=대법원, 400202=하위법원)
- court_name: 법원명 (대법원, 서울고등법원, 광주지법, 인천지방법원 등)
- referenced_law: 참조법령명 (형법, 민법 등)
- sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, dasc=선고일자오름차순, ddes=선고일자내림차순)
- alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
- date: 판례 선고일자 (YYYYMMDD)
- date_range: 선고일자 범위 (20090101~20090130)
- case_number: 판례 사건번호
- data_source: 데이터출처명 (국세법령정보시스템, 근로복지공단산재판례, 대법원)""")
def search_precedent(
    query: Optional[str] = None,
    search: int = 2,  # 본문검색이 제목검색보다 더 풍부한 결과 제공
    display: int = 20,
    page: int = 1,
    court_type: Optional[str] = None,
    court_name: Optional[str] = None,
    referenced_law: Optional[str] = None,
    sort: Optional[str] = None,
    alphabetical: Optional[str] = None,
    date: Optional[str] = None,
    date_range: Optional[str] = None,
    case_number: Optional[str] = None,
    data_source: Optional[str] = None
) -> TextContent:
    """판례 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어
        search: 검색범위 (1=판례명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        court_type: 법원종류 (400201=대법원, 400202=하위법원)
        court_name: 법원명 (대법원, 서울고등법원, 광주지법, 인천지방법원 등)
        referenced_law: 참조법령명 (형법, 민법 등)
        sort: 정렬 (lasc=사건명오름차순, ldes=사건명내림차순, dasc=선고일자오름차순, ddes=선고일자내림차순)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
        date: 판례 선고일자 (YYYYMMDD)
        date_range: 선고일자 범위 (20090101~20090130)
        case_number: 판례 사건번호
        data_source: 데이터출처명 (국세법령정보시스템, 근로복지공단산재판례, 대법원)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "search": search, "display": min(display, 100), "page": page}
    
    # 고급 검색 파라미터 추가
    if court_type:
        params["org"] = court_type
    if court_name:
        params["nw"] = court_name  # 실제 API 테스트에서 nw(84건) > curt(36건) 확인
    if referenced_law:
        params["JO"] = referenced_law
    if sort:
        params["sort"] = sort
    if alphabetical:
        params["gana"] = alphabetical
    if date:
        params["date"] = date
    if date_range:
        params["prncYd"] = date_range
    if case_number:
        params["nb"] = case_number
    if data_source:
        params["datSrcNm"] = data_source

    try:
        data = _make_legislation_request("prec", params, use_cache=True)
        result = _format_precedent_search_results(data, "prec", search_query, display)
        result += format_result_guidance(extract_total_count(data), search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"판례 검색 중 오류: {str(e)}")

@mcp.tool(name="search_constitutional_court", description="헌법재판소 결정례를 검색합니다. 매개변수: query(필수), display, page")
def search_constitutional_court(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """헌법재판소 결정례 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "detc", "query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("detc", params, use_cache=True)
        result = _format_constitutional_search_results(data, "detc", search_query, display)
        result += format_result_guidance(extract_total_count(data), search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"헌법재판소 결정례 검색 중 오류: {str(e)}")

@mcp.tool(name="search_legal_interpretation", description="법제처 법령해석례를 검색합니다. 매개변수: query(필수), display, page")
def search_legal_interpretation(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령해석례 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"query": search_query, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("expc", params, use_cache=True)
        url = _generate_api_url("expc", params)
        result = _format_precedent_search_results(data, "expc", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법령해석례 검색 중 오류: {str(e)}")

@mcp.tool(name="search_administrative_trial", description="행정심판례를 검색합니다. 매개변수: query(필수), search(1=사건명, 2=본문검색), display, page")
def search_administrative_trial(query: Optional[str] = None, search: int = 1, display: int = 20, page: int = 1) -> TextContent:
    """행정심판례 검색"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    search_query = query.strip()
    params = {"target": "decc", "query": search_query, "search": search, "display": min(display, 100), "page": page}
    try:
        data = _make_legislation_request("decc", params, use_cache=True)
        url = _generate_api_url("decc", params)
        result = _format_precedent_search_results(data, "decc", search_query, display)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"행정심판례 검색 중 오류: {str(e)}")

@mcp.tool(name="get_administrative_trial_detail", description="""행정심판례 상세내용을 조회합니다.

매개변수:
- trial_id: 행정심판례ID - search_administrative_trial 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_administrative_trial_detail(trial_id="123456")""")
def get_administrative_trial_detail(trial_id: Union[str, int]) -> TextContent:
    """행정심판례 본문 조회"""
    params = {"target": "decc", "ID": str(trial_id)}
    try:
        data = _make_legislation_request("decc", params, is_detail=True, use_cache=True)
        url = _generate_api_url("decc", params)
        result = _format_precedent_search_results(data, "decc", f"행정심판례ID:{trial_id}", 1)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"행정심판례 상세 조회 중 오류: {str(e)}")

@mcp.tool(name="get_precedent_detail", description="""판례 상세내용을 조회합니다. 국세청 판례의 경우 HTML만 지원됩니다.

매개변수:
- case_id: 판례ID - search_precedent 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_precedent_detail(case_id="123456")
참고: 국세청 판례는 HTML 형태로만 제공됩니다.""")
def get_precedent_detail(case_id: Union[str, int]) -> TextContent:
    """판례 본문 조회 - 개선된 JSON/HTML 지원"""
    params = {"ID": str(case_id)}
    
    try:
        # 기본 JSON 시도 (is_detail=True로 lawService.do 사용)
        data = _make_legislation_request("prec", params, is_detail=True, use_cache=True)
        url = _generate_api_url("prec", params, is_detail=True)
        
        # JSON 응답 확인
        if isinstance(data, dict) and data:
            result = _format_precedent_search_results(data, "prec", f"판례ID:{case_id}", 1)
            return TextContent(type="text", text=result)
        else:
            # HTML 폴백 (국세청 판례 등)
            oc = os.getenv("LEGISLATION_API_KEY", "lchangoo")
            html_params = {"OC": oc, "target": "prec", "ID": str(case_id)}
            
            url = f"{legislation_config.service_base_url}?{urlencode(html_params)}"
            headers = {"Referer": "https://open.law.go.kr/"}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # HTML 응답 포맷팅
            return _format_html_precedent_response(response.text, str(case_id), url)
            
    except json.JSONDecodeError as je:
        # JSON 파싱 실패시 HTML 폴백
        try:
            oc = os.getenv("LEGISLATION_API_KEY", "lchangoo") 
            html_params = {"OC": oc, "target": "prec", "ID": str(case_id)}
            
            url = f"{legislation_config.service_base_url}?{urlencode(html_params)}"
            headers = {"Referer": "https://open.law.go.kr/"}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            return _format_html_precedent_response(response.text, str(case_id), url)
            
        except Exception as he:
            return TextContent(type="text", text=f"JSON 파싱 오류 (HTML 폴백 실패): {str(je)}\n\nsearch_precedent 도구로 올바른 판례 ID를 먼저 확인해보세요.\n\nAPI URL: {url}")
            
    except Exception as e:
        return TextContent(type="text", text=f"판례 상세 조회 중 오류: {str(e)}")

@mcp.tool(name="get_constitutional_court_detail", description="""헌법재판소 결정례 상세내용을 조회합니다.

매개변수:
- decision_id: 결정례ID - search_constitutional_court 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_constitutional_court_detail(decision_id="123456")""")
def get_constitutional_court_detail(decision_id: Union[str, int]) -> TextContent:
    """헌법재판소 결정례 본문 조회"""
    params = {"target": "detc", "ID": str(decision_id)}
    try:
        # 상세조회이므로 is_detail=True로 lawService.do 사용
        data = _make_legislation_request("detc", params, is_detail=True, use_cache=True)
        url = _generate_api_url("detc", params, is_detail=True)
        result = _format_constitutional_court_detail(data, str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"헌법재판소 결정례 상세 조회 중 오류: {str(e)}")

@mcp.tool(name="get_legal_interpretation_detail", description="""법령해석례 상세내용을 조회합니다.

매개변수:
- interpretation_id: 해석례ID - search_legal_interpretation 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_legal_interpretation_detail(interpretation_id="327301")
참고: interpretation_id는 검색 결과의 '법령해석례일련번호' 필드값을 사용하세요. (안건번호 아님)""")
def get_legal_interpretation_detail(interpretation_id: Union[str, int]) -> TextContent:
    """법령해석례 본문 조회"""
    params = {"ID": str(interpretation_id)}
    try:
        data = _make_legislation_request("expc", params, is_detail=True, use_cache=True)
        url = _generate_api_url("expc", params)
        result = _format_precedent_search_results(data, "expc", f"법령해석례ID:{interpretation_id}", 1)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"법령해석례 상세 조회 중 오류: {str(e)}")

def _format_constitutional_court_detail(data: dict, decision_id: str, url: str) -> str:
    """헌법재판소 결정례 상세조회 결과 포맷팅"""
    if not data:
        return f"헌법재판소 결정례 상세 정보를 찾을 수 없습니다.\n\nAPI URL: {url}"
    
    # DetcService 구조 확인
    if 'DetcService' in data:
        detc_info = data['DetcService']
        
        result = f"**헌법재판소 결정례 상세정보** (ID: {decision_id})\n"
        result += "=" * 50 + "\n\n"
        
        # 기본 정보
        basic_fields = {
            '사건명': '사건명',
            '사건번호': '사건번호', 
            '종국일자': '종국일자',
            '사건종류명': '사건종류명',
            '재판부구분': '재판부구분코드',
            '헌재결정례일련번호': '헌재결정례일련번호'
        }
        
        for display_name, field_key in basic_fields.items():
            if field_key in detc_info and detc_info[field_key]:
                value = detc_info[field_key]
                # 날짜 포맷팅
                if '일자' in display_name and len(str(value)) == 8:
                    value = f"{value[:4]}.{value[4:6]}.{value[6:8]}"
                result += f"**{display_name}**: {value}\n"
        
        result += "\n" + "=" * 50 + "\n\n"
        
        # 상세 내용
        detail_fields = {
            '심판대상조문': '심판대상조문',
            '참조조문': '참조조문', 
            '참조판례': '참조판례',
            '판시사항': '판시사항',
            '결정요지': '결정요지'
        }
        
        for display_name, field_key in detail_fields.items():
            if field_key in detc_info and detc_info[field_key]:
                content = detc_info[field_key].strip()
                if content:
                    result += f"## {display_name}\n{content}\n\n"
        
        # 전문 (일부만 표시)
        if '전문' in detc_info and detc_info['전문']:
            full_text = detc_info['전문'].strip()
            if full_text:
                # 전문이 너무 길면 요약
                if len(full_text) > 2000:
                    result += f"## 전문 (요약)\n{full_text[:2000]}...\n\n"
                    result += f"💡 **전체 전문 보기**: 헌재결정례일련번호 {detc_info.get('헌재결정례일련번호', decision_id)}로 별도 조회\n\n"
                else:
                    result += f"## 전문\n{full_text}\n\n"
        
        return result
    else:
        return f"예상과 다른 응답 구조입니다: {list(data.keys())}\n\nAPI URL: {url}"

def _format_html_precedent_response(html_content: str, case_id: str, url: str) -> TextContent:
    """HTML 판례 응답 포맷팅"""
    try:
        # HTML 태그 제거 (간단한 처리)
        import re
        text_content = re.sub(r'<[^>]+>', '', html_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # 길이 제한
        if len(text_content) > 2000:
            text_content = text_content[:2000] + "..."
        
        formatted_result = f"""판례 상세내용 (사건번호: {case_id})

내용
{text_content}

API URL: {url}

참고: 이 판례는 HTML 형식으로 제공됩니다."""
        
        return TextContent(type="text", text=formatted_result)
    except Exception as e:
        return TextContent(type="text", text=f"HTML 판례 응답 처리 중 오류: {str(e)}") 