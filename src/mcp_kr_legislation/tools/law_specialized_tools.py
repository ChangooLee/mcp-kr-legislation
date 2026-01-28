"""
법령 특수 검색 도구 모듈

분야별 전문 검색 및 시맨틱 검색 도구들을 제공합니다.
- 금융 법령 검색
- 세무 법령 검색
- 개인정보보호 법령 검색
- 조문 시맨틱 검색
- 영문 법령 요약
"""

import logging
from typing import Optional

from mcp.types import TextContent

from ..server import mcp
from ..config import legislation_config

# law_tools에서 공통 함수들 import
from .law_tools import (
    _make_legislation_request,
    get_cache_key,
    load_from_cache,
    save_to_cache,
    _sort_english_law_results,
    _fetch_english_law_with_extended_timeout,
)

# 유틸리티 함수 import
from ..utils.response_cleaner import clean_html_tags

# law_config에서 설정 import
from .law_config import (
    FINANCIAL_KEYWORDS,
    FINANCIAL_LAWS,
    FINANCIAL_SEARCH_LIMIT,
    TAX_KEYWORDS,
    TAX_LAWS,
    TAX_SEARCH_LIMIT,
    PRIVACY_KEYWORDS,
    PRIVACY_LAWS,
    PRIVACY_SEARCH_LIMIT,
)

logger = logging.getLogger(__name__)

# ===========================================
# 분야별 전문 검색 도구들
# ===========================================

@mcp.tool(
    name="search_financial_laws",
    description="""금융 관련 법령을 전문적으로 검색합니다.

매개변수:
- query: 검색어 (선택) - 예: "여신", "대출", "자본시장", "금융소비자"
- law_type: 법령 유형 (선택) - "bank", "capital", "insurance", "all"
- display: 결과 개수 (기본값: 20, 최대 50)
- include_subordinate: 하위법령 포함 여부 (기본값: True)

반환정보: 금융 분야 법령 목록, 소관부처, 시행일자, 관련도 점수

사용 예시:
- search_financial_laws()  # 전체 금융법령
- search_financial_laws("은행법")  # 은행업 관련 법령
- search_financial_laws("자본시장", "capital")  # 자본시장법 중심
- search_financial_laws("금융소비자", display=30)  # 금융소비자보호 관련

참고: 은행법, 자본시장법, 보험업법, 금융소비자보호법 등 금융 전반을 커버합니다."""
)
def search_financial_laws(
    query: Optional[str] = None,
    law_type: str = "all",
    display: int = 20,
    include_subordinate: bool = True
) -> TextContent:
    """금융 관련 법령 전문 검색"""
    try:
        result = "**금융 법령 전문 검색 결과**\n"
        result += "=" * 50 + "\n\n"
        
        # 검색 수행
        search_results = []
        
        if query:
            # 특정 키워드로 검색
            for law_name in FINANCIAL_LAWS:
                if query.lower() in law_name.lower():
                    try:
                        law_result = _make_legislation_request("law", {"query": law_name, "display": 3})
                        laws = law_result.get("LawSearch", {}).get("law", [])
                        if laws:
                            search_results.extend(laws if isinstance(laws, list) else [laws])
                    except:
                        continue
        else:
            # 전체 금융법령 검색
            for law_name in FINANCIAL_LAWS[:FINANCIAL_SEARCH_LIMIT]:
                try:
                    law_result = _make_legislation_request("law", {"query": law_name, "display": 2})
                    laws = law_result.get("LawSearch", {}).get("law", [])
                    if laws:
                        search_results.extend(laws if isinstance(laws, list) else [laws])
                except:
                    continue
        
        # 법령 유형별 필터링
        if law_type != "all" and law_type in FINANCIAL_KEYWORDS:
            filtered_results = []
            keywords = FINANCIAL_KEYWORDS[law_type]
            for law in search_results:
                law_name = law.get('법령명한글', law.get('법령명', ''))
                if any(keyword in law_name for keyword in keywords):
                    filtered_results.append(law)
            search_results = filtered_results
        
        # 결과 제한
        search_results = search_results[:display]
        
        if not search_results:
            result += "**검색 결과 없음**: 지정된 조건에 맞는 금융법령을 찾을 수 없습니다.\n"
            result += "다른 키워드나 조건을 시도해보세요.\n\n"
            result += "**추천 검색어**: 은행, 자본시장, 보험, 금융소비자, 여신, 투자\n"
            return TextContent(type="text", text=result)
        
        result += f"**검색 통계**: {len(search_results)}건 발견\n\n"
        
        # 분야별 분류
        categorized: dict = {"은행업": [], "자본시장": [], "보험업": [], "기타금융": []}
        
        for law in search_results:
            law_name = law.get('법령명한글', law.get('법령명', ''))
            if any(keyword in law_name for keyword in ["은행", "여신", "예금"]):
                categorized["은행업"].append(law)
            elif any(keyword in law_name for keyword in ["자본시장", "증권", "투자"]):
                categorized["자본시장"].append(law)
            elif any(keyword in law_name for keyword in ["보험"]):
                categorized["보험업"].append(law)
            else:
                categorized["기타금융"].append(law)
        
        # 분야별 결과 출력
        for category, laws in categorized.items():
            if laws:
                result += f"## **{category} 관련 법령**\n\n"
                for i, law in enumerate(laws, 1):
                    result += f"**{i}. {law.get('법령명한글', law.get('법령명', '제목없음'))}**\n"
                    result += f"   • 법령일련번호: {law.get('법령일련번호', 'N/A')}\n"
                    result += f"   • 시행일자: {law.get('시행일자', 'N/A')}\n"
                    result += f"   • 소관부처: {law.get('소관부처명', 'N/A')}\n"
                    mst = law.get('법령일련번호')
                    if mst:
                        result += f"   • 상세조회: get_law_detail(mst=\"{mst}\")\n"
                    result += "\n"
        
        # 관련 도구 안내
        result += "## **추가 검색 도구**\n\n"
        result += "**세무법령**: search_tax_laws()\n"
        result += "**개인정보보호**: search_privacy_laws()\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"금융법령 검색 중 오류: {e}")
        return TextContent(type="text", text=f"금융법령 검색 중 오류가 발생했습니다: {str(e)}")


@mcp.tool(
    name="search_tax_laws", 
    description="""세무 관련 법령을 전문적으로 검색합니다.

매개변수:
- query: 검색어 (선택) - 예: "소득세", "법인세", "부가가치세", "상속세"
- tax_type: 세목 유형 (선택) - "income", "corporate", "vat", "inheritance", "all"
- display: 결과 개수 (기본값: 20, 최대 50)
- include_enforcement: 시행령/시행규칙 포함 여부 (기본값: True)

반환정보: 세무 분야 법령 목록, 세목별 분류, 시행일자, 관련 조세특례

사용 예시:
- search_tax_laws()  # 전체 세무법령
- search_tax_laws("소득세")  # 소득세 관련 법령
- search_tax_laws("공제", "income")  # 소득세 공제 관련
- search_tax_laws("신고", display=30)  # 세무신고 관련

참고: 소득세법, 법인세법, 부가가치세법, 상속세법 등 주요 세법을 커버합니다."""
)
def search_tax_laws(
    query: Optional[str] = None,
    tax_type: str = "all", 
    display: int = 20,
    include_enforcement: bool = True
) -> TextContent:
    """세무 관련 법령 전문 검색"""
    try:
        result = "**세무 법령 전문 검색 결과**\n"
        result += "=" * 50 + "\n\n"
        
        # 검색 수행  
        search_results = []
        
        if query:
            # 특정 키워드로 검색
            for law_name in TAX_LAWS:
                if query.lower() in law_name.lower():
                    try:
                        law_result = _make_legislation_request("law", {"query": law_name, "display": 3})
                        laws = law_result.get("LawSearch", {}).get("law", [])
                        if laws:
                            search_results.extend(laws if isinstance(laws, list) else [laws])
                    except:
                        continue
        else:
            # 전체 세무법령 검색
            for law_name in TAX_LAWS[:TAX_SEARCH_LIMIT]:
                try:
                    law_result = _make_legislation_request("law", {"query": law_name, "display": 2})
                    laws = law_result.get("LawSearch", {}).get("law", [])
                    if laws:
                        search_results.extend(laws if isinstance(laws, list) else [laws])
                except:
                    continue
        
        # 세목별 필터링
        if tax_type != "all" and tax_type in TAX_KEYWORDS:
            filtered_results = []
            keywords = TAX_KEYWORDS[tax_type]
            for law in search_results:
                law_name = law.get('법령명한글', law.get('법령명', ''))
                if any(keyword in law_name for keyword in keywords):
                    filtered_results.append(law)
            search_results = filtered_results
        
        # 결과 제한
        search_results = search_results[:display]
        
        if not search_results:
            result += "**검색 결과 없음**: 지정된 조건에 맞는 세무법령을 찾을 수 없습니다.\n"
            result += "다른 키워드나 조건을 시도해보세요.\n\n"
            result += "**추천 검색어**: 소득세, 법인세, 부가가치세, 상속세, 공제, 신고\n"
            return TextContent(type="text", text=result)
        
        result += f"**검색 통계**: {len(search_results)}건 발견\n\n"
        
        # 세목별 분류
        categorized: dict = {"소득세": [], "법인세": [], "부가가치세": [], "상속증여세": [], "기타세목": []}
        
        for law in search_results:
            law_name = law.get('법령명한글', law.get('법령명', ''))
            if "소득세" in law_name:
                categorized["소득세"].append(law)
            elif "법인세" in law_name:
                categorized["법인세"].append(law)
            elif "부가가치세" in law_name:
                categorized["부가가치세"].append(law)
            elif any(keyword in law_name for keyword in ["상속세", "증여세"]):
                categorized["상속증여세"].append(law)
            else:
                categorized["기타세목"].append(law)
        
        # 세목별 결과 출력
        for category, laws in categorized.items():
            if laws:
                result += f"## **{category} 관련 법령**\n\n"
                for i, law in enumerate(laws, 1):
                    result += f"**{i}. {law.get('법령명한글', law.get('법령명', '제목없음'))}**\n"
                    result += f"   • 법령일련번호: {law.get('법령일련번호', 'N/A')}\n"
                    result += f"   • 시행일자: {law.get('시행일자', 'N/A')}\n"
                    result += f"   • 소관부처: {law.get('소관부처명', 'N/A')}\n"
                    mst = law.get('법령일련번호')
                    if mst:
                        result += f"   • 상세조회: get_law_detail(mst=\"{mst}\")\n"
                    result += "\n"
        
        # 관련 도구 안내
        result += "## **추가 검색 도구**\n\n"
        result += "**금융법령**: search_financial_laws()\n"
        result += "**개인정보보호**: search_privacy_laws()\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"세무법령 검색 중 오류: {e}")
        return TextContent(type="text", text=f"세무법령 검색 중 오류가 발생했습니다: {str(e)}")


@mcp.tool(
    name="search_privacy_laws",
    description="""개인정보보호 관련 법령을 전문적으로 검색합니다.

매개변수:
- query: 검색어 (선택) - 예: "수집", "이용", "제공", "동의", "안전조치"
- scope: 적용 범위 (선택) - "general", "public", "financial", "medical", "all"
- display: 결과 개수 (기본값: 15, 최대 30)
- include_guidelines: 가이드라인 포함 여부 (기본값: True)

반환정보: 개인정보보호 법령 목록, 적용 분야별 분류, 벌칙 조항, 보호조치

사용 예시:
- search_privacy_laws()  # 전체 개인정보보호 법령
- search_privacy_laws("수집")  # 개인정보 수집 관련
- search_privacy_laws("금융", "financial")  # 금융분야 개인정보보호
- search_privacy_laws("의료", "medical")  # 의료분야 개인정보보호

참고: 개인정보보호법, 정보통신망법, 신용정보법, 의료법상 개인정보 조항 등을 커버합니다."""
)
def search_privacy_laws(
    query: Optional[str] = None,
    scope: str = "all",
    display: int = 15, 
    include_guidelines: bool = True
) -> TextContent:
    """개인정보보호 관련 법령 전문 검색"""
    try:
        result = "**개인정보보호 법령 전문 검색 결과**\n"
        result += "=" * 50 + "\n\n"
        
        # 검색 수행
        search_results = []
        
        if query:
            # 특정 키워드로 검색
            for law_name in PRIVACY_LAWS:
                if query.lower() in law_name.lower():
                    try:
                        law_result = _make_legislation_request("law", {"query": law_name, "display": 2})
                        laws = law_result.get("LawSearch", {}).get("law", [])
                        if laws:
                            search_results.extend(laws if isinstance(laws, list) else [laws])
                    except:
                        continue
        else:
            # 전체 개인정보보호법령 검색
            for law_name in PRIVACY_LAWS[:PRIVACY_SEARCH_LIMIT]:
                try:
                    law_result = _make_legislation_request("law", {"query": law_name, "display": 2})
                    laws = law_result.get("LawSearch", {}).get("law", [])
                    if laws:
                        search_results.extend(laws if isinstance(laws, list) else [laws])
                except:
                    continue
        
        # 적용 범위별 필터링
        if scope != "all" and scope in PRIVACY_KEYWORDS:
            filtered_results = []
            keywords = PRIVACY_KEYWORDS[scope]
            for law in search_results:
                law_name = law.get('법령명한글', law.get('법령명', ''))
                if any(keyword in law_name for keyword in keywords):
                    filtered_results.append(law)
            search_results = filtered_results
        
        # 결과 제한
        search_results = search_results[:display]
        
        if not search_results:
            result += "**검색 결과 없음**: 지정된 조건에 맞는 개인정보보호법령을 찾을 수 없습니다.\n"
            result += "다른 키워드나 조건을 시도해보세요.\n\n"
            result += "**추천 검색어**: 개인정보, 수집, 이용, 제공, 동의, 안전조치\n"
            return TextContent(type="text", text=result)
        
        result += f"**검색 통계**: {len(search_results)}건 발견\n\n"
        
        # 분야별 분류
        categorized: dict = {"일반개인정보": [], "신용정보": [], "의료정보": [], "공공정보": [], "통신정보": []}
        
        for law in search_results:
            law_name = law.get('법령명한글', law.get('법령명', ''))
            if "개인정보 보호법" in law_name or "개인정보보호법" in law_name:
                categorized["일반개인정보"].append(law)
            elif "신용정보" in law_name:
                categorized["신용정보"].append(law)
            elif any(keyword in law_name for keyword in ["의료", "생명윤리"]):
                categorized["의료정보"].append(law)
            elif any(keyword in law_name for keyword in ["공공기관", "정보공개"]):
                categorized["공공정보"].append(law)
            elif "정보통신망" in law_name:
                categorized["통신정보"].append(law)
            else:
                categorized["일반개인정보"].append(law)
        
        # 분야별 결과 출력
        for category, laws in categorized.items():
            if laws:
                result += f"## **{category} 관련 법령**\n\n"
                for i, law in enumerate(laws, 1):
                    result += f"**{i}. {law.get('법령명한글', law.get('법령명', '제목없음'))}**\n"
                    result += f"   • 법령일련번호: {law.get('법령일련번호', 'N/A')}\n"
                    result += f"   • 시행일자: {law.get('시행일자', 'N/A')}\n"
                    result += f"   • 소관부처: {law.get('소관부처명', 'N/A')}\n"
                    mst = law.get('법령일련번호')
                    if mst:
                        result += f"   • 상세조회: get_law_detail(mst=\"{mst}\")\n"
                    result += "\n"
        
        # 관련 도구 안내
        result += "## **추가 검색 도구**\n\n"
        result += "**금융법령**: search_financial_laws()\n"
        result += "**세무법령**: search_tax_laws()\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"개인정보보호법령 검색 중 오류: {e}")
        return TextContent(type="text", text=f"개인정보보호법령 검색 중 오류가 발생했습니다: {str(e)}")


# ===========================================
# 시맨틱 검색 도구들
# ===========================================

@mcp.tool(
    name="search_law_articles_semantic",
    description="""[내부 도구] 캐시된 법령 데이터에서 의미 기반으로 조문을 검색합니다.

이 도구는 주로 다른 도구들이 내부적으로 사용합니다.
일반 사용자는 get_law_summary 도구를 사용하세요.

주요 기능:
- 법령 전체를 캐시하여 모든 조문을 검색 가능
- 키워드로 관련 조문 찾기
- 조문 번호를 몰라도 내용으로 검색 가능

매개변수:
- mst: 법령일련번호 (필수)
- query: 검색 키워드 (필수)
- target: API 타겟 (기본값: "law")
- max_results: 최대 결과 개수 (기본값: 10)

사용 시나리오:
- get_law_summary가 내부적으로 호출
- 특정 조문 번호를 찾을 때 LLM이 자동 호출"""
)
def search_law_articles_semantic(
    mst: str,
    query: str,
    target: str = "law",
    max_results: int = 10
) -> TextContent:
    """캐시된 법령에서 시맨틱 검색"""
    if not mst or not query:
        return TextContent(type="text", text="법령일련번호(mst)와 검색어(query)를 모두 입력해주세요.")
    
    try:
        # 캐시 키 생성
        cache_key = get_cache_key(f"{target}_{mst}", "full")
        cached_data = load_from_cache(cache_key)
        
        # 캐시가 없으면 API로 전체 데이터 가져오기
        if not cached_data:
            logger.info(f"캐시 없음. API로 법령 전체 조회: {target}_{mst}")
            params = {"MST": mst}
            data = _make_legislation_request(target, params, is_detail=True)
            
            if not data:
                return TextContent(type="text", text=f"법령 데이터를 가져올 수 없습니다. MST: {mst}")
            
            # 캐시 저장
            save_to_cache(cache_key, data)
            cached_data = data
        
        # 법령 정보 추출
        law_info = cached_data.get("법령", {})
        basic_info = law_info.get("기본정보", {})
        law_name = basic_info.get("법령명_한글", basic_info.get("법령명한글", ""))
        
        # 조문 데이터 추출
        articles_section = law_info.get("조문", {})
        all_articles = []
        
        if isinstance(articles_section, dict):
            if "조문단위" in articles_section:
                article_units = articles_section.get("조문단위", [])
                if not isinstance(article_units, list):
                    article_units = [article_units] if article_units else []
                all_articles = article_units
        
        # 시맨틱 검색
        search_results = []
        query_lower = query.lower()
        query_words = query_lower.split()
        
        for article in all_articles:
            if not isinstance(article, dict):
                continue
                
            article_no = article.get("조문번호", "")
            article_title = article.get("조문제목", "")
            article_content = article.get("조문내용", "")
            
            if article.get("조문여부") != "조문" and "조문여부" in article:
                continue
            
            full_text = f"{article_title} {article_content}".lower()
            
            # 점수 계산
            score = 0
            if query_lower in full_text:
                score += 10
            
            for word in query_words:
                if word in full_text:
                    if word in article_title.lower():
                        score += 3
                    else:
                        score += 1
            
            if score > 0:
                search_results.append({
                    "조문번호": article_no,
                    "조문제목": article_title,
                    "조문내용": article_content[:200] + "..." if len(article_content) > 200 else article_content,
                    "점수": score
                })
        
        # 점수 기준 정렬
        search_results.sort(key=lambda x: x["점수"], reverse=True)
        search_results = search_results[:max_results]
        
        if not search_results:
            return TextContent(type="text", text=f"'{query}'와 관련된 조문을 찾을 수 없습니다.")
        
        result = f"**{law_name}**에서 '{query}' 검색 결과 (상위 {len(search_results)}개)\n"
        result += "=" * 50 + "\n\n"
        
        for i, item in enumerate(search_results, 1):
            result += f"**{i}. 제{item['조문번호']}조"
            if item['조문제목']:
                result += f"({item['조문제목']})"
            result += f"** (관련도: {item['점수']})\n"
            result += f"{item['조문내용']}\n\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"시맨틱 검색 중 오류: {e}")
        return TextContent(type="text", text=f"검색 중 오류가 발생했습니다: {str(e)}")


@mcp.tool(
    name="search_english_law_articles_semantic",
    description="""[내부 도구] 캐시된 영문 법령 데이터에서 의미 기반으로 조문을 검색합니다.

이 도구는 주로 다른 도구들이 내부적으로 사용합니다.
일반 사용자는 get_english_law_summary 도구를 사용하세요.

주요 기능:
- 영문 법령 전체를 캐시하여 모든 조문을 검색 가능
- 영어 키워드로 관련 조문 찾기
- 조문 번호를 몰라도 내용으로 검색 가능

매개변수:
- mst: 법령일련번호 (필수)
- query: 검색 키워드 (필수) - 영어로 입력
- max_results: 최대 결과 개수 (기본값: 10)

사용 시나리오:
- get_english_law_summary가 내부적으로 호출
- 특정 조문 번호를 찾을 때 LLM이 자동 호출"""
)
def search_english_law_articles_semantic(
    mst: str,
    query: str,
    max_results: int = 10
) -> TextContent:
    """영문법령 조문 시맨틱 검색"""
    try:
        # 캐시 확인
        cache_key = get_cache_key(f"elaw_{mst}", "full")
        cached_data = load_from_cache(cache_key)
        
        if not cached_data:
            params = {"MST": mst}
            data = _make_legislation_request("elaw", params, is_detail=True)
            
            if not data or 'Law' not in data:
                return TextContent(
                    type="text", 
                    text=f"영문 법령 데이터를 찾을 수 없습니다. (MST: {mst})"
                )
            
            save_to_cache(cache_key, data)
            cached_data = data
        
        law_data = cached_data['Law']
        jo_section = law_data.get('JoSection', {})
        all_articles = []
        
        if jo_section and 'Jo' in jo_section:
            jo_data = jo_section['Jo']
            if isinstance(jo_data, list):
                all_articles = [jo for jo in jo_data if jo.get('joYn') == 'Y']
            elif isinstance(jo_data, dict) and jo_data.get('joYn') == 'Y':
                all_articles = [jo_data]
        
        if not all_articles:
            return TextContent(
                type="text",
                text=f"검색 가능한 조문이 없습니다. (MST: {mst})"
            )
        
        # 영문 시맨틱 검색
        search_results = []
        query_lower = query.lower()
        query_words = query_lower.split()
        
        for article in all_articles:
            article_no = article.get('joNo', '')
            article_content = article.get('joCts', '')
            
            if not article_content:
                continue
            
            full_text = article_content.lower()
            score = 0
            
            if query_lower in full_text:
                score += 10
            
            for word in query_words:
                if word in full_text:
                    score += 2
            
            if score > 0:
                search_results.append({
                    "article_no": article_no,
                    "content": article_content[:300] + "..." if len(article_content) > 300 else article_content,
                    "score": score
                })
        
        search_results.sort(key=lambda x: x['score'], reverse=True)
        search_results = search_results[:max_results]
        
        if not search_results:
            return TextContent(
                type="text",
                text=f"'{query}' 키워드와 관련된 조문을 찾을 수 없습니다."
            )
        
        result = f"**영문 법령 조문 검색 결과** (키워드: '{query}')\n"
        result += "=" * 50 + "\n\n"
        
        for i, item in enumerate(search_results, 1):
            result += f"**{i}. Article {item['article_no']}** (관련도: {item['score']})\n"
            result += f"{item['content']}\n\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"영문법령 시맨틱 검색 중 오류: {e}")
        return TextContent(
            type="text",
            text=f"영문법령 조문 검색 중 오류가 발생했습니다: {str(e)}"
        )


def _find_best_english_law_match(laws: list, query: str) -> dict:
    """영문 법령 검색 결과에서 가장 적합한 법령 찾기
    
    정렬 우선순위:
    1. 영문명 정확 일치
    2. 영문명 시작 일치
    3. 한글명 정확 일치
    4. 첫 번째 결과 (기본)
    """
    query_upper = query.upper().strip()
    
    # 1순위: 영문명 정확 일치
    for law in laws:
        name = clean_html_tags(law.get('법령명영문', '')).upper().strip()
        if name == query_upper:
            return law
    
    # 2순위: 영문명 시작 일치
    for law in laws:
        name = clean_html_tags(law.get('법령명영문', '')).upper().strip()
        if name.startswith(query_upper):
            return law
    
    # 3순위: 한글명 정확 일치
    for law in laws:
        korean_name = clean_html_tags(law.get('법령명한글', '')).strip()
        if korean_name == query.strip():
            return law
    
    # 4순위: 첫 번째 결과
    return laws[0]


def _deduplicate_value(value: str, delimiter: str = ',') -> str:
    """중복된 값 제거
    
    예: "개인정보보호위원회,개인정보보호위원회,개인정보보호위원회" -> "개인정보보호위원회"
    """
    if not value or delimiter not in value:
        return value
    
    items = [item.strip() for item in value.split(delimiter)]
    unique_items = list(dict.fromkeys(items))  # 순서 유지하면서 중복 제거
    
    return ', '.join(unique_items) if len(unique_items) > 1 else unique_items[0]


@mcp.tool(
    name="get_english_law_summary",
    description="""[최우선 사용] 영문 법령 내용을 묻는 모든 질문에 대한 통합 응답 도구입니다.

다음과 같은 질문에 자동으로 이 도구를 사용하세요:
- "Show me the English version of ○○ law"
- "What are the contract provisions in Korean Civil Act?"
- "Explain Korean Commercial Act in English"
- "Find articles about ○○ in Korean law (in English)"

특징:
- 한 번의 호출로 영문 법령 정보부터 특정 내용까지 모두 제공
- 내부적으로 필요한 모든 도구를 자동 호출
- 조문 번호를 몰라도 영어 키워드로 관련 조문 자동 검색
- 캐시 지원으로 재조회 시 즉시 응답
- 확장된 타임아웃(90초)으로 대용량 법령도 조회 가능

매개변수:
- law_name: 법령명 (필수) - 영어 또는 한국어 가능
  예: "Banking Act", "Income Tax Act", "은행법", "소득세법"
- keyword: 찾고자 하는 내용 (선택) - 영어로 입력
  예: "contract", "property", "liability", "company"
- show_detail: 찾은 조문의 전체 내용 표시 여부 (기본값: False)

⚠️ 대용량 법령 안내:
- 민법(246569), 상법(267558) 등 조문이 많은 법령은 첫 조회에 30-60초 소요
- 두 번째 조회부터는 캐시로 즉시 응답
- 타임아웃 발생 시 자동 재시도 (최대 2회)

실제 사용 예시:
1. "Show me Korean Civil Act in English, especially about contract formation"
   → get_english_law_summary("Civil Act", "contract", True)

2. "What does Korean Commercial Act say about company formation?"
   → get_english_law_summary("Commercial Act", "company formation", True)

3. "Explain Korean Civil Act in English"
   → get_english_law_summary("Civil Act")

다른 도구 대신 이 도구를 사용하세요:
- search_english_law + get_english_law_detail 조합 대신 → get_english_law_summary
- 영문 법령 관련 질문은 모두 이 도구로 처리"""
)
def get_english_law_summary(
    law_name: str,
    keyword: Optional[str] = None,
    show_detail: bool = False
) -> TextContent:
    """영문 법령 통합 요약 (캐시 지원, 확장 타임아웃, 재시도)"""
    import requests
    
    try:
        # 1단계: 영문 법령 검색 (충분히 많은 결과 검색 후 정렬)
        search_params = {
            "OC": legislation_config.oc,
            "type": "JSON", 
            "target": "elaw",
            "query": law_name,
            "search": 1,
            "display": 20,  # 충분한 결과 확보
            "page": 1
        }
        
        search_data = _make_legislation_request("elaw", search_params, is_detail=False)
        
        if not search_data or 'LawSearch' not in search_data or 'law' not in search_data['LawSearch']:
            return TextContent(
                type="text",
                text=f"'{law_name}'에 해당하는 영문 법령을 찾을 수 없습니다."
            )
        
        # 정확도 기반 정렬 적용
        search_data = _sort_english_law_results(search_data, law_name)
        
        laws = search_data['LawSearch']['law']
        if not laws:
            return TextContent(
                type="text",
                text=f"'{law_name}'에 해당하는 영문 법령을 찾을 수 없습니다."
            )
        
        # 정렬된 결과에서 첫 번째 선택 (정확 매칭이 이미 상위로 정렬됨)
        if isinstance(laws, list):
            current_law = laws[0]
        else:
            current_law = laws
        mst = current_law.get('법령일련번호')
        
        if not mst:
            return TextContent(
                type="text",
                text=f"법령일련번호를 찾을 수 없습니다."
            )
        
        mst_str = str(mst)
        
        # 2단계: 기본 법령 정보 조회 (캐시 우선, 확장 타임아웃)
        cache_key = get_cache_key(f"elaw_{mst_str}", "full")
        cached_data = load_from_cache(cache_key)
        
        if cached_data:
            logger.info(f"캐시에서 영문법령 요약 조회: MST={mst_str}")
            detail_data = cached_data
        else:
            logger.info(f"API에서 영문법령 요약 조회: MST={mst_str}")
            # 확장된 타임아웃으로 조회 (재시도 포함)
            max_retries = 2
            detail_data = None
            
            for attempt in range(max_retries + 1):
                try:
                    detail_data = _fetch_english_law_with_extended_timeout(mst_str, timeout=90)
                    if detail_data:
                        # 캐시 저장
                        save_to_cache(cache_key, detail_data)
                        logger.info(f"영문법령 캐시 저장: MST={mst_str}")
                        break
                except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
                    if attempt < max_retries:
                        logger.warning(f"영문법령 조회 타임아웃 (재시도 {attempt + 1}/{max_retries}): MST={mst_str}")
                        continue
                    else:
                        # 모든 재시도 실패
                        logger.error(f"영문법령 조회 최종 실패: MST={mst_str}")
                        timeout_msg = f"**영문 법령 조회 시간 초과** (MST: {mst_str})\n\n"
                        timeout_msg += "이 법령은 조문이 매우 많아 조회에 시간이 오래 걸립니다.\n\n"
                        timeout_msg += "**대안 방법:**\n"
                        timeout_msg += f"1. 특정 키워드로 조문 검색:\n"
                        timeout_msg += f"   `search_english_law_articles_semantic(mst=\"{mst_str}\", query=\"키워드\")`\n\n"
                        timeout_msg += f"2. 상세 조회 도구 사용:\n"
                        timeout_msg += f"   `get_english_law_detail(mst=\"{mst_str}\", max_articles=30)`"
                        return TextContent(type="text", text=timeout_msg)
                except Exception as e:
                    logger.error(f"영문법령 조회 중 오류: {e}")
                    if attempt < max_retries:
                        continue
                    else:
                        return TextContent(
                            type="text",
                            text=f"영문 법령 조회 중 오류가 발생했습니다: {str(e)}"
                        )
            
            if not detail_data:
                return TextContent(
                    type="text",
                    text=f"영문 법령 데이터를 가져올 수 없습니다. (MST: {mst_str})"
                )
        
        # 기본 정보 포맷팅 - HTML 태그 정제 및 중복 제거 적용
        result = "**영문 법령 요약**\n"
        result += "=" * 50 + "\n\n"
        
        # HTML 태그 정제
        english_name = clean_html_tags(current_law.get('법령명영문', 'N/A'))
        korean_name = clean_html_tags(current_law.get('법령명한글', 'N/A'))
        
        # 소관부처 중복 제거
        ministry = current_law.get('소관부처명', 'N/A')
        ministry = _deduplicate_value(ministry)
        
        result += "**기본 정보:**\n"
        result += f"• 영문명: {english_name}\n"
        result += f"• 한글명: {korean_name}\n" 
        result += f"• 법령ID: {current_law.get('법령ID', 'N/A')}\n"
        result += f"• MST: {mst}\n"
        result += f"• 공포일자: {current_law.get('공포일자', 'N/A')}\n"
        result += f"• 시행일자: {current_law.get('시행일자', 'N/A')}\n"
        result += f"• 소관부처: {ministry}\n\n"
        
        # 3단계: 키워드가 있으면 시맨틱 검색
        if keyword:
            # detail_data는 이미 캐시에서 가져왔거나 API로 가져온 데이터
            if detail_data and 'Law' in detail_data:
                law_data = detail_data['Law']
                jo_section = law_data.get('JoSection', {})
                
                if jo_section and 'Jo' in jo_section:
                    jo_data = jo_section['Jo']
                    all_articles = []
                    
                    if isinstance(jo_data, list):
                        all_articles = [jo for jo in jo_data if jo.get('joYn') == 'Y']
                    elif isinstance(jo_data, dict) and jo_data.get('joYn') == 'Y':
                        all_articles = [jo_data]
                    
                    if all_articles:
                        keyword_lower = keyword.lower()
                        matching_articles = []
                        
                        for article in all_articles[:20]:
                            content = article.get('joCts', '').lower()
                            if any(word in content for word in keyword_lower.split()):
                                matching_articles.append(article)
                        
                        if matching_articles:
                            result += f"**'{keyword}' 관련 조문** (상위 {min(3, len(matching_articles))}개):\n\n"
                            
                            for i, article in enumerate(matching_articles[:3], 1):
                                article_no = article.get('joNo', '')
                                content = article.get('joCts', '')
                                
                                if show_detail:
                                    result += f"**Article {article_no}:** (전체 내용)\n"
                                    result += f"{content}\n\n"
                                else:
                                    preview = content[:200] + "..." if len(content) > 200 else content
                                    result += f"**Article {article_no}:** (미리보기)\n"
                                    result += f"{preview}\n\n"
                        else:
                            result += f"**'{keyword}' 관련 조문을 찾을 수 없습니다.**\n\n"
        
        # 4단계: 일반 정보
        if detail_data and 'Law' in detail_data:
            law_data = detail_data['Law']
            jo_section = law_data.get('JoSection', {})
            
            if jo_section and 'Jo' in jo_section:
                jo_data = jo_section['Jo']
                if isinstance(jo_data, list):
                    article_count = len([jo for jo in jo_data if jo.get('joYn') == 'Y'])
                    result += f"**전체 조문 개수**: {article_count}개\n"
                else:
                    result += f"**전체 조문 개수**: 1개\n"
        
        result += f"\n**상세 조회**: get_english_law_detail(law_id=\"{mst}\")"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"영문법령 요약 중 오류: {e}")
        return TextContent(
            type="text",
            text=f"영문 법령 요약 중 오류가 발생했습니다: {str(e)}"
        )


logger.info("법령 특수 검색 도구가 로드되었습니다! (6개 도구)")
