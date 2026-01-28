"""
법령 도구 포맷팅 유틸리티

반복되는 포맷팅 로직을 중앙 관리합니다.
"""

from typing import Dict, List, Optional, Any
from .law_config import CHANGE_DETAILS, FIELD_MAPPINGS


def format_law_item(
    law: Dict[str, Any],
    index: Optional[int] = None,
    include_detail_hint: bool = True,
    detail_fields: Optional[List[str]] = None
) -> str:
    """
    법령 검색 결과 단일 항목 포맷팅
    
    Args:
        law: 법령 정보 딕셔너리
        index: 항목 번호 (None이면 번호 없이 출력)
        include_detail_hint: 상세조회 힌트 포함 여부
        detail_fields: 출력할 필드 목록 (None이면 기본값 사용)
    
    Returns:
        포맷팅된 문자열
    """
    result = ""
    
    # 법령명 추출
    law_name = _get_law_name(law)
    
    # 항목 헤더
    if index is not None:
        result += f"**{index}. {law_name}**\n"
    else:
        result += f"**{law_name}**\n"
    
    # 기본 필드
    if detail_fields is None:
        detail_fields = ["법령일련번호", "시행일자", "소관부처명"]
    
    for field in detail_fields:
        value = _get_field_value(law, field)
        if value:
            result += f"   • {field}: {value}\n"
    
    # 상세조회 힌트
    if include_detail_hint:
        mst = law.get('법령일련번호') or law.get('MST') or law.get('mst')
        if mst:
            result += f"   • 상세조회: get_law_detail(mst=\"{mst}\")\n"
    
    result += "\n"
    return result


def format_law_list(
    laws: List[Dict[str, Any]],
    title: str,
    include_detail_hint: bool = True,
    detail_fields: Optional[List[str]] = None
) -> str:
    """
    법령 목록 포맷팅
    
    Args:
        laws: 법령 정보 리스트
        title: 섹션 제목
        include_detail_hint: 상세조회 힌트 포함 여부
        detail_fields: 출력할 필드 목록
    
    Returns:
        포맷팅된 문자열
    """
    if not laws:
        return ""
    
    result = f"## {title}\n\n"
    
    for i, law in enumerate(laws, 1):
        result += format_law_item(
            law, 
            index=i,
            include_detail_hint=include_detail_hint,
            detail_fields=detail_fields
        )
    
    return result


def format_article_item(
    article: Dict[str, Any],
    index: Optional[int] = None,
    include_content: bool = True,
    max_content_length: int = 500
) -> str:
    """
    조문 정보 포맷팅
    
    Args:
        article: 조문 정보 딕셔너리
        index: 항목 번호
        include_content: 조문 내용 포함 여부
        max_content_length: 내용 최대 길이
    
    Returns:
        포맷팅된 문자열
    """
    result = ""
    
    # 조문번호
    article_no = article.get('조문번호') or article.get('articleNo') or '?'
    article_title = article.get('조문제목') or article.get('articleTitle') or ''
    
    # 헤더
    if index is not None:
        result += f"**{index}. 제{article_no}조"
    else:
        result += f"**제{article_no}조"
    
    if article_title:
        result += f"({article_title})"
    result += "**\n"
    
    # 내용
    if include_content:
        content = article.get('조문내용') or article.get('content') or ''
        if content:
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            result += f"{content}\n"
    
    result += "\n"
    return result


def format_change_history_item(
    change: Dict[str, Any],
    index: int,
    context_func: Optional[callable] = None
) -> str:
    """
    변경 이력 항목 포맷팅
    
    Args:
        change: 변경 이력 정보
        index: 항목 번호
        context_func: 배경 설명 함수 (연도, 변경사유를 받아 문자열 반환)
    
    Returns:
        포맷팅된 문자열
    """
    result = ""
    
    # 변경사유 및 일자
    change_reason = change.get('변경사유') or change.get('제개정구분명') or '변경'
    change_date = change.get('조문변경일') or change.get('시행일자') or ''
    
    # 날짜 포맷팅
    formatted_date = _format_date(change_date)
    
    # 변경 상세 정보
    change_info = CHANGE_DETAILS.get(change_reason, {'icon': '[변경]', 'desc': '조문 변경'})
    icon = change_info['icon']
    
    result += f"**{index}. {icon} {change_reason}** ({formatted_date})\n"
    
    # 배경 설명
    if context_func:
        year = change_date[:4] if len(change_date) >= 4 else '2024'
        context = context_func(year, change_reason)
        result += f"   변경 배경: {context}\n"
    
    # 시행일자
    ef_date = change.get('시행일자', '')
    if ef_date:
        result += f"   시행일자: {_format_date(ef_date)}\n"
    
    # 제개정구분
    revision = change.get('제개정구분명', '')
    if revision:
        result += f"   제개정구분: {revision}\n"
    
    # 공포일자
    announce_date = change.get('공포일자', '')
    if announce_date:
        result += f"   공포일자: {_format_date(announce_date)}\n"
    
    # 소관부처
    ministry = change.get('소관부처명', '')
    if ministry:
        result += f"   소관부처: {ministry}\n"
    
    result += "\n"
    return result


def format_categorized_laws(
    categorized: Dict[str, List[Dict[str, Any]]],
    category_icon: str = "🏷️",
    include_detail_hint: bool = True
) -> str:
    """
    카테고리별로 분류된 법령 목록 포맷팅
    
    Args:
        categorized: 카테고리 → 법령 리스트 딕셔너리
        category_icon: 카테고리 앞에 표시할 아이콘
        include_detail_hint: 상세조회 힌트 포함 여부
    
    Returns:
        포맷팅된 문자열
    """
    result = ""
    
    for category, laws in categorized.items():
        if laws:
            result += f"## {category_icon} **{category} 관련 법령**\n\n"
            for i, law in enumerate(laws, 1):
                result += format_law_item(
                    law,
                    index=i,
                    include_detail_hint=include_detail_hint
                )
    
    return result


def categorize_laws(
    laws: List[Dict[str, Any]],
    categories: Dict[str, List[str]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    법령을 카테고리별로 분류
    
    Args:
        laws: 법령 리스트
        categories: 카테고리명 → 키워드 리스트 딕셔너리
    
    Returns:
        카테고리 → 법령 리스트 딕셔너리
    """
    # 결과 초기화 (카테고리 순서 유지)
    categorized: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in categories.keys()}
    
    for law in laws:
        law_name = _get_law_name(law)
        categorized_flag = False
        
        for category, keywords in categories.items():
            # 빈 키워드 목록은 기타 카테고리
            if not keywords:
                continue
            
            if any(keyword in law_name for keyword in keywords):
                categorized[category].append(law)
                categorized_flag = True
                break
        
        # 어느 카테고리에도 속하지 않으면 마지막 카테고리(기타)에 추가
        if not categorized_flag:
            # 빈 키워드 목록을 가진 카테고리 찾기 (fallback)
            for category, keywords in categories.items():
                if not keywords:
                    categorized[category].append(law)
                    break
    
    return categorized


# =============================================================================
# 내부 유틸리티 함수
# =============================================================================

def _get_law_name(law: Dict[str, Any]) -> str:
    """법령 딕셔너리에서 법령명 추출"""
    for key in ['법령명한글', '법령명', '제목', 'title', '명칭', 'name']:
        if key in law and law[key]:
            return str(law[key])
    return "제목없음"


def _get_field_value(data: Dict[str, Any], field_name: str) -> Optional[str]:
    """
    필드명에 대응하는 값 추출 (다양한 키 이름 지원)
    """
    # FIELD_MAPPINGS에서 대응 키 찾기
    if field_name in FIELD_MAPPINGS:
        for key in FIELD_MAPPINGS[field_name]:
            if key in data and data[key]:
                return str(data[key])
    
    # 직접 키 검색
    if field_name in data and data[field_name]:
        return str(data[field_name])
    
    return None


def _format_date(date_str: str) -> str:
    """날짜 문자열 포맷팅 (YYYYMMDD → YYYY-MM-DD)"""
    if not date_str:
        return "N/A"
    
    date_str = str(date_str).strip()
    
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    
    return date_str
