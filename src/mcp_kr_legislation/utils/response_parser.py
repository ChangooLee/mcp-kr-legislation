"""
API 응답 구조 정규화 파서

다양한 API 응답 구조를 통일된 형태로 변환합니다.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

from .response_cleaner import clean_html_tags, clean_search_result

logger = logging.getLogger(__name__)


# API별 응답 구조 매핑
RESPONSE_STRUCTURE_MAP = {
    # 법령
    "law": ("LawSearch", "law"),
    "elaw": ("LawSearch", "law"),
    "eflaw": ("LawSearch", "law"),
    
    # 판례
    "prec": ("PrecSearch", "prec"),
    "detc": ("DetcSearch", "Detc"),
    "expc": ("Expc", "expc"),
    "decc": ("Decc", "decc"),
    
    # 위원회결정문
    "ppc": ("Ppc", "ppc"),
    "fsc": ("Fsc", "fsc"),
    "ftc": ("Ftc", "ftc"),
    "acr": ("Acr", "acr"),
    "nlrc": ("Nlrc", "nlrc"),
    "ecc": ("Ecc", "ecc"),
    "sfc": ("Sfc", "sfc"),
    "nhrck": ("Nhrck", "nhrck"),
    "kcc": ("Kcc", "kcc"),
    "iaciac": ("Iaciac", "iaciac"),
    "oclt": ("Oclt", "oclt"),
    "eiac": ("Eiac", "eiac"),
    
    # 행정규칙
    "admrul": ("AdmRulSearch", "admrul"),
    
    # 자치법규
    "ordin": ("OrdinSearch", "law"),
    "ordinfd": ("OrdinSearch", "ordinfd"),
    
    # 조약
    "trty": ("TrtySearch", "Trty"),
    
    # 법령용어
    "lstrm": ("LsTrmSearch", "lstrm"),
    "lstrmAI": ("lstrmAISearch", "법령용어"),
    
    # 중앙부처해석
    "moefCgmExpc": ("CgmExpc", "cgmExpc"),
    "molitCgmExpc": ("CgmExpc", "cgmExpc"),
    "moelCgmExpc": ("CgmExpc", "cgmExpc"),
    "mofCgmExpc": ("CgmExpc", "cgmExpc"),
    "moisCgmExpc": ("CgmExpc", "cgmExpc"),
    "meCgmExpc": ("CgmExpc", "cgmExpc"),
    "ntsCgmExpc": ("CgmExpc", "cgmExpc"),
    "kcsCgmExpc": ("CgmExpc", "cgmExpc"),
    
    # 특별행정심판
    "ttSpecialDecc": ("DeccSearch", "Decc"),
    "kmstSpecialDecc": ("DeccSearch", "Decc"),
}


def extract_items_from_response(
    result: Dict[str, Any], 
    target: Optional[str] = None
) -> Tuple[List[Dict], int, Optional[str]]:
    """
    API 응답에서 실제 데이터 항목을 추출합니다.
    
    Args:
        result: API 응답 딕셔너리
        target: API target 값 (알고 있는 경우)
        
    Returns:
        (items: 데이터 리스트, count: 전체 개수, error: 에러 메시지)
    """
    if not result:
        return [], 0, "응답 없음"
    
    # 에러 응답 확인
    if "Law" in result and isinstance(result["Law"], str):
        return [], 0, result["Law"]
    
    # target이 주어진 경우 해당 구조로 먼저 시도
    if target and target in RESPONSE_STRUCTURE_MAP:
        outer_key, inner_key = RESPONSE_STRUCTURE_MAP[target]
        if outer_key in result:
            inner = result[outer_key]
            if isinstance(inner, dict):
                items = inner.get(inner_key, [])
                if isinstance(items, dict):
                    items = [items]
                if isinstance(items, list):
                    return items, len(items), None
    
    # 알려진 모든 구조 시도
    for outer_key, inner_key in RESPONSE_STRUCTURE_MAP.values():
        if outer_key in result:
            inner = result[outer_key]
            if isinstance(inner, dict):
                items = inner.get(inner_key, [])
                if isinstance(items, dict):
                    items = [items]
                if isinstance(items, list) and items:
                    return items, len(items), None
    
    # 직접 데이터가 있는 경우
    for key in ["법령", "Law", "items", "data", "result"]:
        if key in result:
            value = result[key]
            if isinstance(value, list):
                return value, len(value), None
            elif isinstance(value, dict):
                return [value], 1, None
    
    return [], 0, "데이터 구조 파싱 실패"


def normalize_response(
    result: Dict[str, Any], 
    target: Optional[str] = None,
    clean_html: bool = True
) -> Dict[str, Any]:
    """
    API 응답을 정규화된 형태로 변환합니다.
    
    Args:
        result: 원본 API 응답
        target: API target 값
        clean_html: HTML 태그 제거 여부
        
    Returns:
        정규화된 응답:
        {
            "success": bool,
            "items": List[Dict],
            "total_count": int,
            "error": Optional[str],
            "raw_keys": List[str]  # 디버깅용
        }
    """
    items, count, error = extract_items_from_response(result, target)
    
    if clean_html and items:
        items = [clean_search_result(item) for item in items]
    
    return {
        "success": count > 0,
        "items": items,
        "total_count": count,
        "error": error,
        "raw_keys": list(result.keys()) if result else []
    }


def parse_html_detail(html_content: str, detail_type: str = "precedent") -> Dict[str, Any]:
    """
    HTML 상세 응답을 파싱하여 구조화된 데이터로 변환합니다.
    
    판례 등 JSON을 지원하지 않는 상세 조회 API의 HTML 응답을 파싱합니다.
    
    Args:
        html_content: HTML 응답 내용
        detail_type: 상세 유형 (precedent, detc, expc 등)
        
    Returns:
        파싱된 데이터 딕셔너리
    """
    if not html_content:
        return {"error": "HTML 내용 없음"}
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = {}
        
        if detail_type == "precedent":
            # 판례 HTML 파싱
            result = _parse_precedent_html(soup)
        elif detail_type == "detc":
            # 헌법재판소 결정례 파싱
            result = _parse_detc_html(soup)
        elif detail_type == "expc":
            # 법령해석례 파싱
            result = _parse_expc_html(soup)
        else:
            # 일반 HTML 파싱
            result = _parse_generic_html(soup)
        
        return result
        
    except Exception as e:
        logger.error(f"HTML 파싱 실패: {e}")
        return {"error": str(e)}


def _parse_precedent_html(soup: BeautifulSoup) -> Dict[str, Any]:
    """판례 HTML 파싱"""
    result = {}
    
    # 제목 추출
    title = soup.find('h2') or soup.find('h3') or soup.find('title')
    if title:
        result['사건명'] = clean_html_tags(title.get_text())
    
    # 테이블에서 정보 추출
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 2:
                key = clean_html_tags(cells[0].get_text())
                value = clean_html_tags(cells[1].get_text())
                if key and value:
                    result[key] = value
    
    # 본문 내용 추출 (판결요지, 이유 등)
    for section_name in ['판결요지', '이유', '주문', '판시사항']:
        section = soup.find(string=re.compile(section_name))
        if section:
            parent = section.find_parent(['div', 'p', 'td'])
            if parent:
                # 다음 형제 요소에서 내용 추출
                content = parent.find_next_sibling()
                if content:
                    result[section_name] = clean_html_tags(content.get_text())
    
    return result


def _parse_detc_html(soup: BeautifulSoup) -> Dict[str, Any]:
    """헌법재판소 결정례 HTML 파싱"""
    result = {}
    
    # 제목
    title = soup.find('h2') or soup.find('h3')
    if title:
        result['사건명'] = clean_html_tags(title.get_text())
    
    # 메타 정보 테이블
    meta_table = soup.find('table')
    if meta_table:
        rows = meta_table.find_all('tr')
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 2:
                key = clean_html_tags(cells[0].get_text())
                value = clean_html_tags(cells[1].get_text())
                if key:
                    result[key] = value
    
    # 결정요지
    for section_name in ['결정요지', '이유', '주문', '결정내용']:
        section = soup.find(string=re.compile(section_name))
        if section:
            parent = section.find_parent()
            if parent:
                next_content = parent.find_next(['div', 'p'])
                if next_content:
                    result[section_name] = clean_html_tags(next_content.get_text())
    
    return result


def _parse_expc_html(soup: BeautifulSoup) -> Dict[str, Any]:
    """법령해석례 HTML 파싱"""
    result = {}
    
    # 제목
    title = soup.find('h2') or soup.find('h3')
    if title:
        result['안건명'] = clean_html_tags(title.get_text())
    
    # 질의/회신 내용
    for section_name in ['질의요지', '회신내용', '이유', '해석내용']:
        section = soup.find(string=re.compile(section_name))
        if section:
            parent = section.find_parent()
            if parent:
                next_content = parent.find_next(['div', 'p', 'td'])
                if next_content:
                    result[section_name] = clean_html_tags(next_content.get_text())
    
    return result


def _parse_generic_html(soup: BeautifulSoup) -> Dict[str, Any]:
    """일반 HTML 파싱"""
    result = {}
    
    # 제목
    title = soup.find('h1') or soup.find('h2') or soup.find('h3')
    if title:
        result['제목'] = clean_html_tags(title.get_text())
    
    # 본문 텍스트 추출
    body = soup.find('body')
    if body:
        # 스크립트, 스타일 제거
        for script in body.find_all(['script', 'style']):
            script.decompose()
        
        text = clean_html_tags(body.get_text())
        if len(text) > 100:
            result['내용'] = text[:5000]  # 최대 5000자
    
    return result


def get_category_from_target(target: str) -> str:
    """
    API target에서 카테고리를 추출합니다.
    
    Args:
        target: API target 값
        
    Returns:
        카테고리 문자열 (law, prec, committee 등)
    """
    if target in ["law", "elaw", "eflaw"]:
        return "law"
    elif target in ["prec"]:
        return "prec"
    elif target in ["detc"]:
        return "detc"
    elif target in ["expc"]:
        return "expc"
    elif target in ["decc"]:
        return "decc"
    elif target in ["ppc", "fsc", "ftc", "acr", "nlrc", "ecc", "sfc", "nhrck", "kcc", "iaciac", "oclt", "eiac"]:
        return "committee"
    elif target in ["admrul"]:
        return "admrul"
    elif target in ["ordin", "ordinfd"]:
        return "ordin"
    elif "CgmExpc" in target:
        return "interpretation"
    elif "SpecialDecc" in target:
        return "tribunal"
    else:
        return "other"
