"""
응답 데이터 정제 유틸리티

HTML 태그 제거 및 LLM 친화적 응답 생성을 위한 함수들
"""

import re
import html
from typing import Any, Dict, List, Optional, Union


def clean_html_tags(text: str) -> str:
    """
    HTML 태그를 제거합니다.
    
    Args:
        text: HTML 태그가 포함될 수 있는 텍스트
        
    Returns:
        태그가 제거된 순수 텍스트
        
    Examples:
        >>> clean_html_tags('<strong class="tbl_tx_type">민법</strong>')
        '민법'
        >>> clean_html_tags('일반 텍스트')
        '일반 텍스트'
    """
    if not text or not isinstance(text, str):
        return text or ""
    
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    
    # HTML 엔티티 디코딩
    text = html.unescape(text)
    
    # 연속 공백 정리
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def clean_dict_values(data: Dict[str, Any], fields_to_clean: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    딕셔너리의 문자열 값에서 HTML 태그를 제거합니다.
    
    Args:
        data: 정제할 딕셔너리
        fields_to_clean: 정제할 필드 목록 (None이면 모든 문자열 필드)
        
    Returns:
        정제된 딕셔너리
    """
    if not data or not isinstance(data, dict):
        return data or {}
    
    result = {}
    for key, value in data.items():
        if fields_to_clean and key not in fields_to_clean:
            result[key] = value
        elif isinstance(value, str):
            result[key] = clean_html_tags(value)
        elif isinstance(value, dict):
            result[key] = clean_dict_values(value, fields_to_clean)
        elif isinstance(value, list):
            result[key] = clean_list_values(value, fields_to_clean)
        else:
            result[key] = value
    
    return result


def clean_list_values(data: List[Any], fields_to_clean: Optional[List[str]] = None) -> List[Any]:
    """
    리스트 내 딕셔너리의 문자열 값에서 HTML 태그를 제거합니다.
    
    Args:
        data: 정제할 리스트
        fields_to_clean: 정제할 필드 목록
        
    Returns:
        정제된 리스트
    """
    if not data or not isinstance(data, list):
        return data or []
    
    result = []
    for item in data:
        if isinstance(item, dict):
            result.append(clean_dict_values(item, fields_to_clean))
        elif isinstance(item, str):
            result.append(clean_html_tags(item))
        elif isinstance(item, list):
            result.append(clean_list_values(item, fields_to_clean))
        else:
            result.append(item)
    
    return result


def clean_search_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    검색 결과에서 HTML 태그를 제거합니다.
    
    법령명, 사건명 등 주요 필드에서 <strong> 등의 태그를 제거합니다.
    
    Args:
        result: API 검색 결과 딕셔너리
        
    Returns:
        정제된 검색 결과
    """
    # 정제가 필요한 필드들
    fields_to_clean = [
        "법령명", "법령명한글", "법령명_한글", "법령명_영문",
        "사건명", "안건명", "결정문명", "행정규칙명", "자치법규명",
        "조약명", "용어명", "해석명", "조문내용", "조문제목",
        "판결요지", "결정요지", "이유", "참조조문", "참조판례",
    ]
    
    return clean_dict_values(result, fields_to_clean)


def truncate_for_llm(text: str, max_chars: int = 2000, suffix: str = "...") -> str:
    """
    LLM 토큰 최적화를 위해 텍스트를 적절한 길이로 자릅니다.
    
    Args:
        text: 원본 텍스트
        max_chars: 최대 문자 수
        suffix: 잘린 경우 붙일 접미사
        
    Returns:
        적절한 길이로 잘린 텍스트
    """
    if not text or len(text) <= max_chars:
        return text or ""
    
    # 문장 단위로 자르기 시도
    truncated = text[:max_chars]
    
    # 마지막 문장 끝 찾기
    last_period = max(
        truncated.rfind('.'),
        truncated.rfind('。'),
        truncated.rfind('\n')
    )
    
    if last_period > max_chars * 0.7:  # 70% 이상 위치에 문장 끝이 있으면
        truncated = truncated[:last_period + 1]
    
    return truncated + suffix


def format_for_llm(data: Union[Dict, List, str], max_items: int = 10) -> str:
    """
    LLM에게 제공하기 좋은 형태로 데이터를 포맷팅합니다.
    
    Args:
        data: 포맷팅할 데이터
        max_items: 리스트인 경우 최대 항목 수
        
    Returns:
        포맷팅된 문자열
    """
    if isinstance(data, str):
        return truncate_for_llm(data)
    
    if isinstance(data, list):
        items = data[:max_items]
        result_parts = []
        for i, item in enumerate(items, 1):
            if isinstance(item, dict):
                # 주요 필드만 추출
                key_fields = ["법령명", "법령명한글", "사건명", "안건명", "법령일련번호", 
                             "판례일련번호", "결정문일련번호", "선고일자", "의결일"]
                item_str = ", ".join(
                    f"{k}: {clean_html_tags(str(v)[:100])}" 
                    for k, v in item.items() 
                    if k in key_fields and v
                )
                result_parts.append(f"{i}. {item_str}")
            else:
                result_parts.append(f"{i}. {clean_html_tags(str(item)[:200])}")
        
        if len(data) > max_items:
            result_parts.append(f"... 외 {len(data) - max_items}건")
        
        return "\n".join(result_parts)
    
    if isinstance(data, dict):
        # 딕셔너리를 읽기 좋은 형태로
        lines = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                continue  # 중첩 데이터는 생략
            v_str = clean_html_tags(str(v))[:200]
            lines.append(f"- {k}: {v_str}")
        return "\n".join(lines)
    
    return str(data)


def extract_key_info(result: Dict[str, Any], category: str = "law") -> Dict[str, Any]:
    """
    API 응답에서 핵심 정보만 추출합니다.
    
    Args:
        result: API 응답 딕셔너리
        category: 데이터 카테고리 (law, prec, committee 등)
        
    Returns:
        핵심 정보만 담긴 딕셔너리
    """
    # 카테고리별 핵심 필드
    key_fields = {
        "law": ["법령명", "법령명한글", "법령일련번호", "시행일자", "공포일자", "소관부처명"],
        "prec": ["사건명", "사건번호", "판례일련번호", "선고일자", "법원명"],
        "detc": ["사건명", "사건번호", "헌재결정례일련번호", "종국일자"],
        "committee": ["안건명", "결정문명", "의결일", "결정문일련번호"],
        "admrul": ["행정규칙명", "행정규칙일련번호", "시행일자", "소관부처명"],
        "ordin": ["자치법규명", "자치법규일련번호", "시행일자", "지자체기관명"],
    }
    
    fields = key_fields.get(category, list(key_fields["law"]))
    
    extracted = {}
    for field in fields:
        if field in result:
            value = result[field]
            if isinstance(value, str):
                value = clean_html_tags(value)
            extracted[field] = value
    
    return extracted


def summarize_search_results(
    items: List[Dict[str, Any]], 
    category: str = "law",
    max_items: int = 5
) -> str:
    """
    검색 결과를 LLM 친화적인 요약 형태로 변환합니다.
    
    Args:
        items: 검색 결과 리스트
        category: 데이터 카테고리
        max_items: 표시할 최대 항목 수
        
    Returns:
        요약된 텍스트
    """
    if not items:
        return "검색 결과가 없습니다."
    
    lines = [f"총 {len(items)}건 검색됨 (상위 {min(len(items), max_items)}건 표시)"]
    lines.append("")
    
    for i, item in enumerate(items[:max_items], 1):
        info = extract_key_info(item, category)
        
        # 카테고리별 포맷
        if category == "law":
            name = info.get("법령명한글") or info.get("법령명", "N/A")
            date = info.get("시행일자", "N/A")
            lines.append(f"{i}. {name} (시행: {date})")
        elif category == "prec":
            name = info.get("사건명", "N/A")
            date = info.get("선고일자", "N/A")
            court = info.get("법원명", "")
            lines.append(f"{i}. {name} ({court}, {date})")
        elif category == "detc":
            name = info.get("사건명", "N/A")
            date = info.get("종국일자", "N/A")
            lines.append(f"{i}. {name} ({date})")
        elif category == "committee":
            name = info.get("안건명") or info.get("결정문명", "N/A")
            date = info.get("의결일", "N/A")
            lines.append(f"{i}. {name} ({date})")
        else:
            # 기본 포맷
            first_value = next((v for v in info.values() if v), "N/A")
            lines.append(f"{i}. {first_value}")
    
    if len(items) > max_items:
        lines.append(f"\n... 외 {len(items) - max_items}건")
    
    return "\n".join(lines)
