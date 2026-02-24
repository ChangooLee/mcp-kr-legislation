"""
law_tools.py에서 사용하는 유틸리티 함수들
도구별로 함수를 분리하여 관리
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# ===========================================
# search_law 도구 관련 함수들
# ===========================================

def format_search_law_results(data: Dict[str, Any], query: str) -> str:
    """
    search_law 도구 전용 검색 결과 포맷팅 함수
    - 정확 매치 우선 정렬 적용
    """
    try:
        result = f"**'{query}' 검색 결과**"
        
        # 데이터 구조 확인
        if not data or 'LawSearch' not in data:
            return f"{result}\n\n검색 결과가 없습니다."
        
        search_data = data['LawSearch']
        target_data = search_data.get('law', [])
        total_count = int(search_data.get('totalCnt', 0))
        
        if total_count > 0:
            result += f" (총 {total_count}건)\n\n"
        else:
            result += "\n\n검색 결과가 없습니다.\n"
            return result
        
        # 개별 항목 처리
        if not isinstance(target_data, list):
            target_data = [target_data] if target_data else []
        
        # 정확 매치 우선 정렬
        query_normalized = query.replace(" ", "").lower()
        
        def sort_key(item):
            if not isinstance(item, dict):
                return (3, "")
            title = item.get('법령명한글', '') or item.get('법령명', '') or ''
            title_normalized = title.replace(" ", "").lower()
            
            # 1순위: 정확 매치
            if title_normalized == query_normalized:
                return (0, title)
            # 2순위: 검색어로 시작
            if title_normalized.startswith(query_normalized):
                return (1, title)
            # 3순위: 검색어 포함
            if query_normalized in title_normalized:
                return (2, title)
            # 4순위: 기타
            return (3, title)
        
        sorted_data = sorted(target_data, key=sort_key)
        
        max_results = min(len(sorted_data), 20)  # 최대 20개만 표시
        
        for i, item in enumerate(sorted_data[:max_results], 1):
            if not isinstance(item, dict):
                continue
            
            # 제목 추출
            title = item.get('법령명한글', '') or item.get('법령명', '') or '제목 없음'
            result += f"**{i}. {title}**\n"
            
            # 메타데이터 추가
            mst = item.get('법령일련번호', '') or item.get('MST', '')
            law_id = item.get('법령ID', '')
            promulgate_date = item.get('공포일자', '')
            enforce_date = item.get('시행일자', '')
            ministry = item.get('소관부처명', '')
            law_type = item.get('법령구분명', '')
            revision = item.get('제개정구분명', '')
            
            if law_id:
                result += f"   법령ID: {law_id}\n"
            if mst:
                result += f"   법령일련번호: {mst}\n"
            if promulgate_date:
                result += f"   공포일자: {promulgate_date}\n"
            if enforce_date:
                result += f"   시행일자: {enforce_date}\n"
            if ministry:
                result += f"   소관부처명: {ministry}\n"
            if law_type:
                result += f"   법령구분명: {law_type}\n"
            if revision:
                result += f"   제개정구분명: {revision}\n"
            if mst:
                result += f"   상세조회: get_law_detail(mst=\"{mst}\")\n"
            
            result += "\n"
        
        if total_count > max_results:
            result += f"더 많은 결과가 있습니다. 검색어를 구체화하거나 페이지 번호를 조정해보세요.\n"
        
        return result
        
    except Exception as e:
        logger.error(f"search_law 결과 포맷팅 중 오류: {e}")
        return f"**검색 결과 포맷팅 오류**\n\n{str(e)}"


def normalize_search_query(query: str) -> str:
    """
    search_law 도구 전용 검색어 정규화 함수
    """
    if not query:
        return query
        
    # 기본 정규화
    normalized = query.strip()
    
    # 공백 제거 (법령명은 보통 공백 없이)
    normalized = normalized.replace(" ", "")
    
    # 일반적인 법령 접미사 정규화
    law_suffixes = {
        "에관한법률": "법",
        "에관한법": "법", 
        "시행령": "령",
        "시행규칙": "규칙",
        "에관한규정": "규정",
        "에관한규칙": "규칙"
    }
    
    for old_suffix, new_suffix in law_suffixes.items():
        if normalized.endswith(old_suffix):
            normalized = normalized[:-len(old_suffix)] + new_suffix
            break
    
    return normalized


def create_search_variants(query: str) -> List[str]:
    """
    search_law 도구 전용 검색어 변형 생성 함수
    """
    if not query:
        return [query]
    
    variants = [query]
    normalized = normalize_search_query(query)
    if normalized != query:
        variants.append(normalized)
    
    # 추가 변형들
    if query not in normalized:
        if query.endswith('법'):
            variants.extend([query + '률', query[:-1] + '에관한법률'])
        elif query.endswith('령'):
            variants.extend([query[:-1] + '시행령'])
        elif query.endswith('규칙'):
            variants.extend([query[:-2] + '시행규칙'])
    
    return list(set(variants))


# ===========================================
# get_law_detail 도구 관련 함수들
# ===========================================

def extract_law_summary_from_detail(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    get_law_detail 도구 전용 법령 상세 데이터에서 요약 정보 추출 함수
    """
    try:
        summary = {}
        
        # 법령 기본 정보 추출
        law_info = data.get("법령", {})
        basic_info = law_info.get("기본정보", {})
        
        # 기본 정보
        summary['법령명'] = basic_info.get("법령명_한글", "") or basic_info.get("법령명한글", "")
        summary['법령ID'] = basic_info.get("법령ID", "")
        summary['법령일련번호'] = basic_info.get("법령일련번호", "")
        summary['공포일자'] = basic_info.get("공포일자", "")
        summary['시행일자'] = basic_info.get("시행일자", "")
        summary['소관부처'] = basic_info.get("소관부처명", "") or basic_info.get("소관부처", "")
        
        # 조문 인덱스 생성
        articles_section = law_info.get("조문", {})
        article_units = []
        
        if isinstance(articles_section, dict) and "조문단위" in articles_section:
            article_units = articles_section.get("조문단위", [])
        elif isinstance(articles_section, list):
            article_units = articles_section
        
        if not isinstance(article_units, list):
            article_units = [article_units] if article_units else []
        
        # 조문 인덱스 생성 (최대 50개)
        article_index = []
        article_count = 0
        
        for article in article_units[:50]:
            if isinstance(article, dict) and article.get("조문여부") == "조문":
                article_no = article.get("조문번호", "")
                article_title = article.get("조문제목", "")
                article_content = article.get("조문내용", "")
                
                if article_no:
                    key = f"제{article_no}조"
                    if article_title:
                        key += f"({article_title})"
                    
                    # 항/호/목 개수 계산
                    hangs = article.get("항", [])
                    if isinstance(hangs, dict):
                        hangs = [hangs]
                    elif not isinstance(hangs, list):
                        hangs = []
                    
                    hang_count = len(hangs)
                    ho_count = 0
                    mok_count = 0
                    
                    for hang in hangs:
                        if isinstance(hang, dict):
                            hos = hang.get("호", [])
                            if isinstance(hos, dict):
                                hos = [hos]
                            elif not isinstance(hos, list):
                                hos = []
                            ho_count += len(hos)
                            
                            for ho in hos:
                                if isinstance(ho, dict):
                                    moks = ho.get("목", [])
                                    if isinstance(moks, dict):
                                        moks = [moks]
                                    elif not isinstance(moks, list):
                                        moks = []
                                    mok_count += len(moks)
                    
                    # 구조 정보 문자열 생성
                    structure_info = ""
                    if hang_count > 0 or ho_count > 0:
                        parts = []
                        if hang_count > 0:
                            parts.append(f"{hang_count}개 항")
                        if ho_count > 0:
                            parts.append(f"{ho_count}개 호")
                        if mok_count > 0:
                            parts.append(f"{mok_count}개 목")
                        structure_info = f" [{', '.join(parts)}]"
                    
                    # 조문 내용 미리보기 (100자로 축소, 구조 정보 추가)
                    preview = ""
                    if article_content:
                        if isinstance(article_content, str):
                            clean_content = re.sub(r'<[^>]+>', '', article_content)
                            preview = clean_content[:100].strip()
                        elif isinstance(article_content, list):
                            content_str = ' '.join(str(item) for item in article_content if item)
                            clean_content = re.sub(r'<[^>]+>', '', content_str)
                            preview = clean_content[:100].strip()
                    
                    summary_text = f"{key}{structure_info}"
                    if preview:
                        summary_text += f" - {preview}..."
                    
                    article_index.append({
                        'key': key,
                        'summary': summary_text,
                        'structure': {
                            '항': hang_count,
                            '호': ho_count,
                            '목': mok_count
                        } if (hang_count + ho_count + mok_count) > 0 else None
                    })
                    article_count += 1
        
        summary['조문_인덱스'] = article_index
        summary['조문_총개수'] = len(article_units)
        
        # 제개정이유
        reason_section = law_info.get("제개정이유", "")
        if isinstance(reason_section, dict):
            reason = reason_section.get("제개정이유", "")
        else:
            reason = reason_section
        summary['제개정이유'] = reason
        
        # 원본 크기 (대략적)
        summary['원본크기'] = len(json.dumps(data, ensure_ascii=False))
        
        return summary
        
    except Exception as e:
        logger.error(f"get_law_detail 요약 추출 중 오류: {e}")
        return {
            '법령명': '추출 실패',
            '법령ID': '',
            '법령일련번호': '',
            '공포일자': '',
            '시행일자': '',
            '소관부처': '',
            '조문_인덱스': [],
            '조문_총개수': 0,
            '제개정이유': '',
            '원본크기': 0
        }


def format_law_detail_summary(summary: Dict[str, Any], mst: str, target: str = "law") -> str:
    """
    get_law_detail 도구 전용 법령 상세 요약 포맷팅 함수
    """
    try:
        law_name = summary.get('법령명', '')
        law_id_val = summary.get('법령ID', '')
        
        if not law_name and not law_id_val:
            return (
                f"법령일련번호(MST) '{mst}'에 해당하는 법령을 찾을 수 없습니다.\n\n"
                f"**해결 방법:**\n"
                f"1. search_law 도구로 먼저 검색하여 올바른 법령일련번호를 확인하세요.\n"
                f"   예: search_law(query=\"개인정보보호법\")\n"
                f"2. 검색 결과의 '법령일련번호' 값을 사용하세요.\n"
                f"   예: get_law_detail(mst=\"270351\")"
            )
        
        result = f"**{law_name or '제목없음'}** 상세\n"
        result += "=" * 50 + "\n\n"
        
        result += "**기본 정보:**\n"
        result += f"• 법령ID: {law_id_val}\n"
        result += f"• 법령일련번호: {summary.get('법령일련번호')}\n"
        result += f"• 공포일자: {summary.get('공포일자')}\n"
        result += f"• 시행일자: {summary.get('시행일자')}\n"
        result += f"• 소관부처: {summary.get('소관부처')}\n\n"
        
        # 조문 인덱스
        article_index = summary.get('조문_인덱스', [])
        total_articles = summary.get('조문_총개수', 0)
        
        if article_index:
            result += f"**조문 인덱스** (총 {total_articles}개 중 첫 {len(article_index)}개)\n\n"
            for item in article_index:
                result += f"• {item['summary']}\n"
            result += "\n"
        
        # 제개정이유
        reason = summary.get('제개정이유', '')
        if reason:
            result += f"**제개정이유:**\n{str(reason)[:500]}{'...' if len(str(reason)) > 500 else ''}\n\n"
        
        result += f"**특정 조문 보기**: get_law_article_by_key(mst=\"{mst}\", target=\"{target}\", article_key=\"제1조\")\n"
        result += f"**원본 크기**: {summary.get('원본크기', 0):,} bytes\n"
        
        return result
        
    except Exception as e:
        logger.error(f"get_law_detail 상세 요약 포맷팅 중 오류: {e}")
        return f"상세 요약 포맷팅 중 오류가 발생했습니다: {str(e)}"


# ===========================================
# get_law_article_by_key 도구 관련 함수들
# ===========================================

def normalize_article_key(article_key: str) -> str:
    """
    get_law_article_by_key 도구 전용 조문 키 정규화 함수
    """
    if not article_key:
        return ""
    
    # 제X조 → X 형태로 변환
    match = re.search(r'제(\d+)조', article_key)
    if match:
        return match.group(1)
    
    # 숫자만 있는 경우 그대로 반환
    if article_key.isdigit():
        return article_key
    
    return article_key


def find_article_in_data(article_units: List[Dict], article_num: str) -> Optional[Dict]:
    """
    get_law_article_by_key 도구 전용 조문 데이터에서 특정 조문 찾기 함수
    """
    if not isinstance(article_units, list):
        return None
    
    for i, article in enumerate(article_units):
        if not isinstance(article, dict):
            continue
            
        if article.get("조문번호") == article_num:
            # 조문여부가 "전문"인 경우 실제 조문은 다음에 있을 수 있음
            if article.get("조문여부") == "전문" and i < len(article_units) - 1:
                # 다음 항목 확인
                next_article = article_units[i + 1]
                if (next_article.get("조문번호") == article_num and 
                    next_article.get("조문여부") == "조문"):
                    return next_article
            elif article.get("조문여부") == "조문":
                return article
    
    return None


def get_available_articles(article_units: List[Dict], limit: int = 10) -> List[str]:
    """
    get_law_article_by_key 도구 전용 사용 가능한 조문 번호들 추출 함수
    """
    available_articles = []
    
    if not isinstance(article_units, list):
        return available_articles
    
    for article in article_units[:limit]:
        if isinstance(article, dict) and article.get("조문여부") == "조문":
            no = article.get("조문번호", "")
            if no:
                available_articles.append(f"제{no}조")
    
    return available_articles


def format_article_content(found_article: Dict, law_name: str, article_key: str) -> str:
    """
    get_law_article_by_key 도구 전용 조문 내용 포맷팅 함수
    - 항/호/목 번호 중복 출력 방지
    - format_article_body 공통 함수 사용
    """
    try:
        article_no = found_article.get("조문번호", "")
        article_title = found_article.get("조문제목", "")
        key = f"제{article_no}조" if article_no else article_key
        
        result = f"📄 **{law_name}** - {key}"
        if article_title:
            result += f"({article_title})"
        result += "\n\n"
        
        # 공통 함수로 본문 포맷팅
        result += format_article_body(found_article, include_details=True)
        
        # 추가 정보
        if found_article.get("조문시행일자"):
            result += f"\n\n📅 시행일자: {found_article.get('조문시행일자')}"
        if found_article.get("조문변경여부") == "Y":
            result += f"\n최근 변경된 조문입니다."
        
        return result
        
    except Exception as e:
        logger.error(f"get_law_article_by_key 조문 내용 포맷팅 중 오류: {e}")
        return f"조문 내용 포맷팅 중 오류가 발생했습니다: {str(e)}"


# ===========================================
# 공통 유틸리티 함수들
# ===========================================

def clean_html_tags(text: str) -> str:
    """
    HTML 태그 제거 공통 함수
    """
    if not isinstance(text, str):
        return str(text) if text else ""
    
    return re.sub(r'<[^>]+>', '', text).strip()


def format_article_body(article: Dict, include_details: bool = True) -> str:
    """
    조문 본문(항/호/목) 포맷팅 공통 함수
    
    Args:
        article: 조문 데이터 딕셔너리
        include_details: True면 항/호/목 전체 포함, False면 조문 내용만
    
    Returns:
        포맷팅된 조문 본문 문자열
    """
    result = ""
    
    # 조문 내용 추출
    article_content = article.get("조문내용", "")
    if article_content:
        # 리스트인 경우 문자열로 변환
        if isinstance(article_content, list):
            article_content = ' '.join(str(item) for item in article_content if item)
        
        # 문자열인지 확인 후 처리
        if isinstance(article_content, str) and article_content.strip():
            clean_content = clean_html_tags(article_content)
            result += clean_content + "\n\n"
    
    if not include_details:
        return result
    
    # 항, 호, 목 구조 처리
    hangs = article.get("항", [])
    # dict인 경우 리스트로 변환
    if isinstance(hangs, dict):
        hangs = [hangs]
    elif not isinstance(hangs, list):
        hangs = []
    
    if hangs:
        for hang in hangs:
            if isinstance(hang, dict):
                # 항 내용 처리
                hang_content = hang.get("항내용", "")
                if hang_content:
                    # 리스트인 경우 문자열로 변환
                    if isinstance(hang_content, list):
                        hang_content = ' '.join(str(item) for item in hang_content if item)
                    
                    # 문자열인지 확인 후 HTML 태그 제거
                    if isinstance(hang_content, str):
                        clean_hang = clean_html_tags(hang_content)
                        if clean_hang:
                            result += f"{clean_hang}\n\n"
                
                # 호 처리 (항내용 유무와 무관하게 처리)
                hos = hang.get("호", [])
                # dict인 경우 리스트로 변환
                if isinstance(hos, dict):
                    hos = [hos]
                elif not isinstance(hos, list):
                    hos = []
                
                if hos:
                    for ho in hos:
                        if isinstance(ho, dict):
                            ho_content = ho.get("호내용", "")
                            if ho_content:
                                # 리스트인 경우 문자열로 변환
                                if isinstance(ho_content, list):
                                    ho_content = ' '.join(str(item) for item in ho_content if item)
                                
                                # 문자열인지 확인 후 HTML 태그 제거
                                if isinstance(ho_content, str):
                                    clean_ho = clean_html_tags(ho_content)
                                    if clean_ho:
                                        result += f"  {clean_ho}\n"
                            
                            # 목 처리
                            moks = ho.get("목", [])
                            # dict인 경우 리스트로 변환
                            if isinstance(moks, dict):
                                moks = [moks]
                            elif not isinstance(moks, list):
                                moks = []
                            
                            if moks:
                                for mok in moks:
                                    if isinstance(mok, dict):
                                        mok_content = mok.get("목내용", "")
                                        if mok_content:
                                            # 리스트인 경우 문자열로 변환
                                            if isinstance(mok_content, list):
                                                mok_content = ' '.join(str(item) for item in mok_content if item)
                                            
                                            # 문자열인지 확인 후 HTML 태그 제거
                                            if isinstance(mok_content, str):
                                                clean_mok = clean_html_tags(mok_content)
                                                if clean_mok:
                                                    result += f"    {clean_mok}\n"
                    result += "\n"
    
    return result


NARROWING_THRESHOLD = 1000


def extract_total_count(data: Dict[str, Any]) -> int:
    """API 응답에서 totalCnt 추출 (페이지 단위가 아닌 전체 건수)"""
    for val in data.values():
        if isinstance(val, dict):
            tc = val.get("totalCnt")
            if tc:
                try:
                    return int(tc)
                except (ValueError, TypeError):
                    pass
    return 0


def format_result_guidance(total_count: int, query: str) -> str:
    """검색 결과 건수에 따른 안내 메시지 생성

    - totalCount > 1000: 검색어 구체화 안내
    - totalCount == 0: 대안 검색 안내
    - 그 외: 빈 문자열 반환
    """
    if total_count > NARROWING_THRESHOLD:
        return (
            f"\n---\n"
            f"전체 {total_count:,}건 중 일부만 표시됩니다. "
            f"더 구체적인 검색어를 사용하거나, 날짜 범위/정렬 등 "
            f"고급 검색 파라미터를 활용하면 정확한 결과를 얻을 수 있습니다."
        )
    elif total_count == 0:
        return (
            f"\n---\n"
            f"'{query}' 검색 결과가 없습니다. "
            f"다른 검색어를 시도하거나, 유사한 키워드로 검색해보세요."
        )
    return ""


def safe_get_nested_value(data: Dict, keys: List[str], default: Any = "") -> Any:
    """
    중첩된 딕셔너리에서 안전하게 값 추출하는 공통 함수
    """
    try:
        result = data
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return default
        return result
    except:
        return default