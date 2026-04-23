#!/usr/bin/env python3
"""
캐싱 기능을 활용한 최적화된 법령 조회 도구들
- 대용량 응답 문제 해결
- 필요한 정보만 추출하여 사용자 친화적 제공
- 7일간 캐시 유지로 성능 최적화
"""

import logging
from typing import Optional, Union, List, Dict, Annotated
from mcp import types
from mcp.types import TextContent

# FastMCP 서버 인스턴스 가져오기
from ..server import mcp
from ..utils.legislation_utils import (
    fetch_law_data, 
    extract_law_summary, 
    format_law_summary,
    extract_law_articles,
    format_law_articles,
    extract_article_number
)

logger = logging.getLogger(__name__)

@mcp.tool(
    name="get_law_summary", 
    description="""법령의 기본정보와 조문 요약을 조회합니다.

언제 사용:
- 법령의 기본 정보가 필요할 때
- 조문 미리보기로 법령 전체 구조를 파악할 때
- 정확한 MST(법령일련번호)를 알고 있을 때

언제 사용 안함:
- 특정 키워드로 조문을 찾을 때 → get_law_summary (law_tools.py) 사용
- 법령 검색이 필요할 때 → search_law_unified 사용

매개변수:
- law_id: 법령일련번호(MST) (선택) - 예: "248613"
- law_name: 법령명 (선택) - 예: "은행법", "소득세법", "개인정보보호법"
※ 둘 중 하나는 반드시 입력

반환정보: 법령명, 기본정보, 조문 미리보기, 제개정 이유, 총 조문 수

사용 예시:
- get_law_summary(law_id="248613")  # 개인정보보호법
- get_law_summary(law_name="은행법")
- get_law_summary(law_name="소득세법")""",
    tags={"법령요약", "캐싱", "최적화", "금융", "세무", "개인정보", "은행법", "소득세법"}
)
def get_law_summary(
    law_id: Optional[str] = None,
    law_name: Optional[str] = None
) -> TextContent:
    """법령 요약 정보 조회 (캐싱 최적화)"""
    if not law_id and not law_name:
        return TextContent(
            type="text", 
                    text="법령ID(MST) 또는 법령명 중 하나를 입력해주세요.\n\n"
             "예시:\n"
                 "- get_law_summary(law_id=\"248613\")  # 개인정보보호법\n"
                 "- get_law_summary(law_name=\"은행법\")\n"
                 "- get_law_summary(law_name=\"소득세법\")"
        )
    
    try:
        # 법령명으로 검색하는 경우 법령일련번호를 먼저 찾아야 함
        if law_name and not law_id:
            from .law_tools import _make_legislation_request
            
            # 법령 검색 API로 정확한 법령ID 찾기
            logger.info(f"법령명으로 검색: {law_name}")
            search_params = {
                "OC": "lchangoo",
                "type": "JSON",
                "query": law_name,
                "display": 5
            }
            
            search_result = _make_legislation_request("law", search_params, use_cache=True)
            # 응답 구조: LawSearch.law
            law_search = search_result.get("LawSearch", {}) if search_result else {}
            if law_search and law_search.get("law"):
                laws = law_search.get("law", [])
                if isinstance(laws, dict):
                    laws = [laws]
                
                # 법령명 일치 우선
                target_law = None
                for law in laws:
                    # 직접 필드 접근 (LawSearch 응답 구조)
                    api_law_name = (law.get("법령명한글") or 
                                  law.get("법령명_한글") or 
                                  law.get("법령명", ""))
                    
                    # 정확한 이름 매칭
                    if api_law_name == law_name:
                        target_law = law
                        break
                    # 부분 매칭 (공백 제거 후 비교)
                    clean_api_name = api_law_name.replace(" ", "")
                    clean_law_name = law_name.replace(" ", "")
                    if clean_law_name in clean_api_name or clean_api_name in clean_law_name:
                        if not target_law:  # 첫 번째 부분 일치만 사용
                            target_law = law
                
                if target_law:
                    # 직접 필드 접근
                    law_id = target_law.get("법령일련번호") or target_law.get("법령MST")
                    
                    actual_law_name = (target_law.get("법령명한글") or 
                                     target_law.get("법령명_한글") or 
                                     target_law.get("법령명", ""))
                    logger.info(f"법령 검색 성공: {actual_law_name} (MST: {law_id})")
                else:
                    return TextContent(
                        type="text",
                        text=f"'{law_name}'와 일치하는 법령을 찾을 수 없습니다.\n\n"
                             f"다른 검색어로 시도해보세요:\n"
                             f"- 정확한 법령명 사용\n"
                             f"- 핵심 키워드만 입력 (예: '개인정보', '근로기준' 등)\n"
                             f"- search_law 도구로 먼저 검색해보세요."
                    )
            else:
                return TextContent(
                    type="text",
                    text=f"'{law_name}' 검색 중 오류가 발생했습니다.\n\n"
                         f"search_law 도구로 먼저 검색해보세요."
                )
        
        if not law_id:
            return TextContent(
                type="text",
                text="법령일련번호를 찾을 수 없습니다."
            )
        
        # 캐시에서 법령 데이터 조회 (없으면 자동으로 API 호출)
        law_data = fetch_law_data(str(law_id), use_cache=True)
        
        if not law_data:
            return TextContent(
                type="text",
                text=f"법령을 조회할 수 없습니다. (ID: {law_id})\n\n"
                     f"법령ID가 올바른지 확인하거나 search_law 도구로 검색해보세요."
            )
        
        # 요약 정보 추출 및 포맷팅
        summary = extract_law_summary(law_data)
        formatted = format_law_summary(summary, str(law_name or law_id))
        
        return TextContent(type="text", text=formatted)
        
    except Exception as e:
        logger.error(f"법령 요약 조회 실패: {e}")
        return TextContent(
            type="text",
            text=f"법령 요약 조회 중 오류가 발생했습니다: {str(e)}\n\n"
                 f"잠시 후 다시 시도해주세요."
        )

def get_law_articles_summary(
    law_id: Optional[str] = None,
    law_name: Optional[str] = None,
    start_article: int = 1,
    count: int = 20
) -> TextContent:
    """법령 조문 요약/목차만 반환 (페이징 지원)"""
    if not law_id and not law_name:
        return TextContent(
            type="text",
            text="법령ID(MST) 또는 법령명 중 하나를 입력해주세요."
        )
    try:
        # 법령명으로 검색하는 경우 API로 법령일련번호 찾기
        if law_name and not law_id:
            from .law_tools import _make_legislation_request
            search_params = {
                "OC": "lchangoo",
                "type": "JSON",
                "query": law_name,
                "display": 10
            }
            search_result = _make_legislation_request("law", search_params, use_cache=True)
            
            if search_result and "LawSearch" in search_result:
                laws = search_result["LawSearch"].get("law", [])
                if isinstance(laws, dict):
                    laws = [laws]
                
                # 정확 매치 우선 정렬
                query_normalized = law_name.replace(" ", "").lower()
                best_match = None
                for law in laws:
                    found_name = law.get("법령명한글", "")
                    name_normalized = found_name.replace(" ", "").lower()
                    if name_normalized == query_normalized:
                        best_match = law
                        break
                    elif not best_match and query_normalized in name_normalized:
                        best_match = law
                
                if not best_match and laws:
                    best_match = laws[0]
                    
                if best_match:
                    law_id = best_match.get("법령일련번호")
            
            if not law_id:
                return TextContent(
                    type="text",
                    text=f"'{law_name}'에 대한 법령일련번호를 찾을 수 없습니다.\n"
                         f"search_law(query=\"{law_name}\") 도구로 먼저 검색해보세요."
                )
        law_data = fetch_law_data(str(law_id), use_cache=True)
        if not law_data:
            return TextContent(type="text", text=f"법령을 조회할 수 없습니다. (ID: {law_id})")
        # 법령명 검증
        basic_info = law_data.get("법령", {}).get("기본정보", {})
        actual_law_name = basic_info.get("법령명_한글") or basic_info.get("법령명한글") or basic_info.get("법령명")
        if law_name and actual_law_name and law_name != actual_law_name:
            return TextContent(
                type="text",
                text=f"[경고] 요청한 법령명({law_name})과 실제 데이터의 법령명({actual_law_name})이 다릅니다.\n"
                     f"law_id: {law_id}\n정확한 법령명을 확인해주세요."
            )
        # 조문 요약 생성
        articles = law_data.get("법령", {}).get("조문", {})
        if not articles:
            return TextContent(
                type="text",
                text=f"법령 '{actual_law_name}'의 조문 정보가 없습니다."
            )
        
        # 조문단위 배열 추출
        article_units = []
        if isinstance(articles, dict) and "조문단위" in articles:
            article_units = articles.get("조문단위", [])
        elif isinstance(articles, list):
            article_units = articles
        else:
            article_units = []
            
        if not article_units:
            return TextContent(
                type="text",
                text=f"법령 '{actual_law_name}'의 조문 정보가 없습니다."
            )
        
        # 실제 조문만 필터링 (부칙 제외)
        actual_articles = [
            a for a in article_units 
            if a.get("조문여부") == "조문"
        ]
        
        if not actual_articles:
            return TextContent(
                type="text",
                text=f"법령 '{actual_law_name}'의 조문 정보가 없습니다."
            )
        
        # 조문 번호로 정렬
        actual_articles.sort(key=lambda x: int(x.get("조문번호", "999")))
        
        total_articles = len(actual_articles)
        end_article = min(start_article + count - 1, total_articles)
        
        result = f"**{actual_law_name}** 조문 요약\n\n"
        result += f"**전체 조문 수**: {total_articles}개\n"
        result += f"**현재 범위**: 제{start_article}조 ~ 제{end_article}조\n\n"
        result += "---\n\n"
        
        # 선택된 범위의 조문 요약
        for i in range(start_article - 1, end_article):
            if i < len(actual_articles):
                article = actual_articles[i]
                article_num = article.get("조문번호", "")
                article_title = article.get("조문제목", "")
                article_content = article.get("조문내용", "")
                
                # 제목이 없으면 내용의 첫 100자를 요약으로 사용
                if not article_title and article_content:
                    # HTML 태그 제거
                    import re
                    clean_content = re.sub(r'<[^>]+>', '', article_content)
                    article_title = clean_content[:100] + "..." if len(clean_content) > 100 else clean_content
                
                result += f"**제{article_num}조** {article_title}\n"
        
        result += f"\n---\n"
        result += f"**상세 조회**: `get_law_article_detail(law_id=\"{law_id}\", article_number=조번호)`로 특정 조문의 전체 내용을 확인하세요.\n"
        
        # 페이징 정보
        if end_article < total_articles:
            next_start = end_article + 1
            result += f"📄 **다음 페이지**: `get_law_articles_summary(law_id=\"{law_id}\", start_article={next_start})`\n"
        
        return TextContent(type="text", text=result)
    except Exception as e:
        logger.error(f"법령 조문 요약/목차 조회 실패: {e}")
        return TextContent(type="text", text=f"법령 조문 요약/목차 조회 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(
    name="get_law_article_detail",
    description="특정 법령의 조문 전체 내용을 반환합니다. law_id와 article_no(예: '제50조')를 입력하세요."
)
def get_law_article_detail(
    law_id: str,
    article_no: str
) -> TextContent:
    """특정 조문 전체 내용 반환"""
    if not law_id or not article_no:
        return TextContent(type="text", text="law_id와 article_no(예: '제50조')를 모두 입력하세요.")
    try:
        law_data = fetch_law_data(str(law_id), use_cache=True)
        if not law_data:
            return TextContent(type="text", text=f"법령을 조회할 수 없습니다. (ID: {law_id})")
        
        # 법령명 가져오기
        basic_info = law_data.get("법령", {}).get("기본정보", {})
        law_name = basic_info.get("법령명_한글") or basic_info.get("법령명한글") or basic_info.get("법령명", "")
        
        # 조문 정보 파싱
        articles = law_data.get("법령", {}).get("조문", {})
        
        # 조문단위 배열 추출
        article_units = []
        if isinstance(articles, dict) and "조문단위" in articles:
            article_units = articles.get("조문단위", [])
        elif isinstance(articles, list):
            article_units = articles
        else:
            article_units = []
            
        if not article_units:
            return TextContent(type="text", text=f"법령 '{law_name}'의 조문 정보가 없습니다.")
        
        # 조문 번호 정규화 (예: "제50조" -> "50", "50" -> "50")
        import re
        numbers = re.findall(r'\d+', article_no)
        target_num = numbers[0] if numbers else ""
        
        # 해당 조문 찾기
        found_article = None
        for i, article in enumerate(article_units):
            article_num = article.get("조문번호", "")
            if article_num == target_num:
                # 조문여부가 "전문"인 경우 실제 조문은 다음에 있을 수 있음
                if article.get("조문여부") == "전문" and i < len(article_units) - 1:
                    next_article = article_units[i + 1]
                    if (next_article.get("조문번호") == target_num and 
                        next_article.get("조문여부") == "조문"):
                        found_article = next_article
                        break
                elif article.get("조문여부") == "조문":
                    found_article = article
                    break
        
        if not found_article:
            return TextContent(type="text", text=f"해당 조문({article_no})을 찾을 수 없습니다.")
        
        # 조문 내용 구성
        result = f"📖 **{law_name}**\n\n"
        
        # 제목 구성
        article_title = found_article.get("조문제목", "")
        if article_title:
            result += f"## 제{target_num}조({article_title})\n\n"
        else:
            result += f"## 제{target_num}조\n\n"
        
        # 조문 내용
        content = found_article.get("조문내용", "")
        if content and len(content.strip()) > 20:  # 실제 내용이 있는 경우
            # HTML 태그 제거
            clean_content = re.sub(r'<[^>]+>', '', content)
            clean_content = clean_content.strip()
            result += clean_content + "\n\n"
        else:
            # 항 내용 처리
            hangs = found_article.get("항", [])
            if isinstance(hangs, list) and hangs:
                for hang in hangs:
                    if isinstance(hang, dict):
                        hang_content = hang.get("항내용", "")
                        if hang_content:
                            # HTML 태그 제거
                            clean_hang = re.sub(r'<[^>]+>', '', hang_content)
                            result += clean_hang.strip() + "\n\n"
                    else:
                        result += str(hang) + "\n\n"
        
        # 항/호/목 정보가 있는 경우
        # 실제 API 응답에서는 조문내용에 항/호/목이 포함되어 있을 수 있음
        
        # 시행일자 정보
        if found_article.get("조문시행일자"):
            result += f"\n**시행일자**: {found_article.get('조문시행일자')}"
        
        # 조문 이동 정보 (의미 없는 값 필터링)
        prev_article = found_article.get("조문이동이전", "")
        next_article = found_article.get("조문이동이후", "")
        
        # "000000" 같은 무의미한 값 필터링
        if prev_article and prev_article.strip() and not prev_article.strip().replace("0", "") == "":
            result += f"\n**이전 조문**: 제{prev_article.lstrip('0') or prev_article}조"
        if next_article and next_article.strip() and not next_article.strip().replace("0", "") == "":
            result += f"\n**이후 조문**: 제{next_article.lstrip('0') or next_article}조"
        
        return TextContent(type="text", text=result)
    except Exception as e:
        logger.error(f"특정 조문 전체 내용 조회 실패: {e}")
        return TextContent(type="text", text=f"특정 조문 전체 내용 조회 중 오류가 발생했습니다: {str(e)}")

# 기존 get_law_articles는 요약/목차만 반환하도록 변경(또는 안내)
@mcp.tool(
    name="get_law_articles_summary",
    description="""법령 조문 요약/목차만 반환합니다. 전체 조문이 아닌 인덱스와 요약만 제공합니다.

매개변수:
- law_id: 법령일련번호(MST) - search_law 결과의 '법령일련번호' 필드값 사용 (법령ID 아님!)
- law_name: 법령명 (law_id가 없을 때 사용)

사용 예시: get_law_articles_summary(law_id="270351")  # 270351은 법령일련번호(MST)"""
)
def get_law_articles_summary_tool(
    law_id: Optional[str] = None,
    law_name: Optional[str] = None,
    start_article: int = 1,
    count: int = 20
) -> TextContent:
    return get_law_articles_summary(law_id, law_name, start_article, count)

@mcp.tool(
    name="search_law_with_cache", 
    description="""법령을 검색하고 즉시 요약 정보를 제공합니다.

**주요 특징**:
- 검색 + 캐싱 + 요약을 한 번에 처리
- 금융, 세무, 개인정보보호 등 업무필수 법령에 특화
- 검색 결과에서 가장 관련성 높은 법령의 요약 자동 제공
- 필요시 상세 조문 조회 안내

**검색 최적화**:
- 정확한 법령명 우선 검색
- 본문 키워드 검색으로 확장
- 관련도 높은 상위 결과 선별

사용 예시:
- search_law_with_cache("은행법")        # 은행법 자동 요약
- search_law_with_cache("소득세")        # 소득세법 자동 요약
- search_law_with_cache("개인정보보호")  # 개인정보보호법 자동 요약

성능: 검색 후 즉시 캐싱으로 재검색 시 초고속""",
    tags={"검색", "캐싱", "자동요약", "금융법령", "세무법령", "개인정보", "은행법", "소득세법", "통합조회"}
)
def search_law_with_cache(query: str) -> TextContent:
    """법령 검색 + 자동 요약 (캐싱 최적화)"""
    if not query or not query.strip():
        return TextContent(
            type="text",
            text="검색어를 입력해주세요.\n\n"
                 "예시: '은행법', '소득세', '개인정보보호' 등"
        )
    
    try:
        # 실제 법령 검색을 통한 정확한 매칭
        from .law_tools import _make_legislation_request
        
        # 검색어 정규화
        normalized_query = query.strip()
        
        # 법령명 매핑 (더 정확한 검색을 위해)
        exact_law_names = {
            "개인정보": "개인정보 보호법",
            "개인정보보호": "개인정보 보호법", 
            "프라이버시": "개인정보 보호법",
            "은행": "은행법",
            "은행법": "은행법",
            "금융": "은행법",
            "대출": "은행법",
            "여신": "은행법",
            "소득세": "소득세법",
            "소득세법": "소득세법",
            "세금": "소득세법",
            "법인세": "법인세법",
            "법인세법": "법인세법",
            "부가세": "부가가치세법",
            "부가가치세": "부가가치세법",
            "자본시장": "자본시장과 금융투자업에 관한 법률",
            "투자": "자본시장과 금융투자업에 관한 법률",
            "증권": "자본시장과 금융투자업에 관한 법률"
        }
        
        # 정확한 법령명 찾기
        target_law_name = None
        for keyword, law_name in exact_law_names.items():
            if keyword in normalized_query:
                target_law_name = law_name
                break
        
        if not target_law_name:
            target_law_name = normalized_query
        
        # 실제 API로 법령 검색 (정확 매치를 찾기 위해 충분한 결과 요청)
        search_params = {
            "OC": "lchangoo",
            "type": "JSON", 
            "query": target_law_name,
            "display": 10
        }
        
        search_result = _make_legislation_request("law", search_params, use_cache=True)
        
        # 검색 결과에서 가장 적합한 법령 찾기
        target_law = None
        if search_result and "LawSearch" in search_result:
            laws = search_result["LawSearch"].get("law", [])
            if isinstance(laws, dict):
                laws = [laws]
            
            # 정확 매치 우선 정렬로 법령 찾기
            query_normalized = target_law_name.replace(" ", "").lower()
            exact_match = None
            partial_match = None
            
            for law in laws:
                found_name = law.get("법령명한글", "")
                name_normalized = found_name.replace(" ", "").lower()
                
                # 1순위: 정확 매치
                if name_normalized == query_normalized:
                    exact_match = law
                    break
                # 2순위: 부분 매치 (첫 번째만)
                elif not partial_match and (query_normalized in name_normalized or name_normalized.startswith(query_normalized)):
                    partial_match = law
            
            # 정확 매치 → 부분 매치 → 첫 번째 결과 순으로 선택
            target_law = exact_match or partial_match or (laws[0] if laws else None)
        
        if target_law:
            # 법령일련번호로 상세 정보 조회
            mst = target_law.get("법령일련번호")
            if mst:
                law_data = fetch_law_data(mst, use_cache=True)
                if law_data:
                    summary = extract_law_summary(law_data)
                    
                    # 기본 정보 추출
                    basic_info = law_data.get("법령", {}).get("기본정보", {})
                    
                    # 소관부처 정보 개선  
                    ministry_info = basic_info.get("소관부처", "")
                    if isinstance(ministry_info, dict):
                        ministry = ministry_info.get("content", ministry_info.get("소관부처명", "미지정"))
                    else:
                        ministry = ministry_info or basic_info.get("소관부처명", "미지정")
                    summary["소관부처"] = ministry
                    
                    # 법령일련번호 설정
                    summary["법령일련번호"] = mst
                    
                    formatted = format_law_summary(summary, query)
                    
                    # 실제 법령명 추출
                    actual_law_name = (basic_info.get("법령명_한글") or 
                                     basic_info.get("법령명한글") or 
                                     basic_info.get("법령명") or
                                     target_law.get("법령명한글", ""))
                    
                    formatted += f"\n**더 자세한 조문 보기**: get_law_detail(mst=\"{mst}\")를 사용하세요.\n"
                    formatted += f"**{actual_law_name} 관련 질문**: 구체적인 조항이나 시행령이 궁금하시면 말씀해주세요."
                    
                    return TextContent(type="text", text=formatted)
        
        # 매칭되지 않는 경우 일반 검색 안내
        return TextContent(
            type="text",
            text=f"'{query}' 검색 결과\n\n"
                 f"**지원되는 주요 법령들**:\n"
                 f"• **은행법**: 여신업무, 대출규제, 금융감독\n"
                 f"• **소득세법**: 소득공제, 세율, 과세표준\n" 
                 f"• **개인정보보호법**: 개인정보 수집·이용, 안전조치\n"
                 f"• **자본시장법**: 투자업 인가, 투자권유 규제\n\n"
                 f"**구체적 검색어로 다시 시도해보세요**:\n"
                 f"- '은행법', '소득세', '개인정보보호' 등\n\n"
                 f"**전체 법령 검색**: search_law(query=\"{query}\") 도구를 사용하세요."
        )
        
    except Exception as e:
        logger.error(f"법령 검색 실패: {e}")
        return TextContent(
            type="text",
            text=f"검색 중 오류가 발생했습니다: {str(e)}"
        ) 