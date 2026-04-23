"""
한국 법제처 OPEN API MCP 도구

search_simple_law의 성공 패턴을 적용한 안전하고 간단한 모든 도구들
모든 카테고리: 법령, 부가서비스, 행정규칙, 자치법규, 판례관련, 위원회결정문, 
조약, 별표서식, 학칙공단, 법령용어, 맞춤형, 지식베이스, 기타, 중앙부처해석
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

def _normalize_search_query(query: str) -> str:
    """검색어 정규화 - 법령명 검색 최적화"""
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

def _create_search_variants(query: str) -> list[str]:
    """검색어 변형 생성 - 범용적 법률 검색 최적화"""
    variants = []
    
    # 원본
    variants.append(query)
    
    # 정규화된 버전
    normalized = _normalize_search_query(query)
    if normalized != query:
        variants.append(normalized)
    
    # 공백 포함/제거 변형
    if " " in query:
        variants.append(query.replace(" ", ""))
    
    # "법" 추가/제거 변형
    if not query.endswith("법") and len(query) > 2:
        variants.append(query + "법")
    if query.endswith("법") and len(query) > 2:
        variants.append(query[:-1])
    
    # 키워드 분리 검색 (긴 검색어의 경우)
    if len(query) > 6:
        keywords = query.split()
        if len(keywords) > 1:
            # 첫 번째 키워드만
            variants.append(keywords[0])
            # 마지막 키워드만
            variants.append(keywords[-1])
            # 상위 2개 키워드
            if len(keywords) >= 2:
                variants.append(" ".join(keywords[:2]))
    
    # 중복 제거하면서 순서 유지
    unique_variants = []
    for variant in variants:
        if variant and variant not in unique_variants:
            unique_variants.append(variant)
            
    return unique_variants[:8]  # 적절한 개수로 제한

def _smart_search(target: str, query: str, display: int = 20, page: int = 1) -> dict:
    """지능형 다단계 검색 - 정확도 우선에서 점진적 확장"""
    if not query:
        return {"LawSearch": {target: []}}
    
    search_attempts = []
    variants = _create_search_variants(query)
    
    # 1단계: 정확한 법령명 검색 (search=1)
    for variant in variants[:2]:  # 상위 2개 변형만
        search_attempts.append({
            "query": variant,
            "search": 1,  # 법령명 검색
            "sort": "lasc",  # 법령명 오름차순 (관련도 높음)
            "display": min(display, 20)
        })
    
    # 2단계: 본문 검색 (search=2) - 더 넓은 범위
    for variant in variants[:1]:  # 가장 좋은 변형만
        search_attempts.append({
            "query": variant,
            "search": 2,  # 본문검색
            "sort": "lasc",
            "display": min(display, 30)
        })
    
    # 3단계: 키워드 분리 검색
    keywords = query.replace(" ", "").split("보호")  # 예: "개인정보보호법" -> ["개인정보", "법"]
    if len(keywords) > 1:
        main_keyword = keywords[0]  # "개인정보"
        search_attempts.append({
            "query": main_keyword,
            "search": 2,
            "sort": "lasc", 
            "display": min(display, 40)
        })
    
    # 검색 시도
    best_result = None
    best_count = 0
    
    for attempt in search_attempts:
        try:
            data = _make_legislation_request(target, attempt)
            
            if isinstance(data, dict) and data.get('LawSearch'):
                items = data['LawSearch'].get(target, [])
                if isinstance(items, dict):  # 단일 결과를 리스트로 변환
                    items = [items]
                
                # 관련성 점수 계산
                relevant_count = 0
                for item in items:
                    title = item.get('법령명한글', '').lower()
                    if any(keyword.lower() in title for keyword in variants[:2]):
                        relevant_count += 1
                
                # 최고 품질 결과 선택
                current_best_items: list = best_result.get('LawSearch', {}).get(target, []) if best_result else []
                if relevant_count > best_count or (relevant_count == best_count and len(items) > len(current_best_items)):
                    best_result = data
                    best_count = relevant_count
                    
                # 충분히 좋은 결과면 조기 종료
                if relevant_count >= 3 and attempt["search"] == 1:
                    break
                    
        except Exception as e:
            logger.warning(f"검색 시도 실패: {attempt} - {e}")
            continue
    
    return best_result or {"LawSearch": {target: []}}

def _generate_api_url(target: str, params: dict, is_detail: bool = False) -> str:
    """API URL 생성 함수
    
    Args:
        target: API 대상 (law, prec, ppc, expc 등)
        params: 요청 파라미터
        is_detail: True면 상세조회(lawService.do), False면 검색(lawSearch.do)
    """
    try:
        from urllib.parse import urlencode
        
        # API 키 설정
        oc = os.getenv("LEGISLATION_API_KEY", "lchangoo")
        
        # 기본 파라미터 설정
        base_params = {
            "OC": oc,
            "type": "JSON"
        }
        base_params.update(params)
        base_params["target"] = target
        
        # URL 결정: 상세조회 vs 검색
        if is_detail and ("ID" in params or "MST" in params):
            # 상세조회: lawService.do 사용
            url = legislation_config.service_base_url
        else:
            # 검색: lawSearch.do 사용
            url = legislation_config.search_base_url
        
        return f"{url}?{urlencode(base_params)}"
        
    except Exception as e:
        logger.error(f"URL 생성 실패: {e}")
        return ""

def _make_legislation_request(target: str, params: dict, is_detail: bool = False) -> dict:
    """법제처 API 공통 요청 함수
    
    Args:
        target: API 대상 (law, prec, ppc, expc 등)
        params: 요청 파라미터
        is_detail: True면 상세조회(lawService.do), False면 검색(lawSearch.do)
    """
    try:
        import requests
        
        # API 키 설정
        oc = os.getenv("LEGISLATION_API_KEY", "lchangoo")
        
        # 기본 파라미터 설정
        base_params = {
            "OC": oc
        }
        base_params.update(params)
        
        # JSON 응답 강제 사용
        base_params["type"] = "JSON"
        
        # URL 결정: 상세조회 vs 검색
        if is_detail and ("ID" in params or "MST" in params):
            # 상세조회: lawService.do 사용
            url = legislation_config.service_base_url
        else:
            # 검색: lawSearch.do 사용
            url = legislation_config.search_base_url
        
        base_params["target"] = target
        
        # Referer 헤더 필수 (일부 API에서 404 방지)
        headers = {"Referer": "https://open.law.go.kr/"}
        response = requests.get(url, params=base_params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except Exception as e:
        logger.error(f"API 요청 실패: {e}")
        return {"error": str(e)}

def _has_meaningful_content(data: dict) -> bool:
    """응답 데이터에 의미있는 내용이 있는지 확인"""
    if not data or "error" in data:
        return False
    
    # PrecService에 판례 데이터가 있는지 확인
    if "PrecService" in data:
        service_data = data["PrecService"]
        prec_data = service_data.get("판례", {})
        if prec_data and prec_data.get("전문"):
            return True
    
    # 기타 유의미한 데이터 키들 확인
    meaningful_keys = ["전문", "판시사항", "판결요지", "내용", "본문"]
    for key in meaningful_keys:
        if key in data and data[key]:
            return True
    
    return False

def _format_html_precedent_response(data: dict, case_id: str, url: str) -> str:
    """HTML 판례 응답을 포맷팅"""
    result = f"🔗 **API 호출 URL**: {url}\n\n"
    
    if "error" in data:
        return f"오류: {data['error']}\n\nAPI URL: {url}"
    
    # HTML 응답 처리
    if isinstance(data, dict):
        # HTML 내용이 있는지 확인
        html_content = None
        for key, value in data.items():
            if isinstance(value, str) and ("<" in value or len(value) > 100):
                html_content = value
                break
        
        if html_content:
            result += f"📄 **판례 상세내용 (ID: {case_id})**\n\n"
            
            # HTML에서 텍스트 추출 시도
            try:
                import re
                # 간단한 HTML 태그 제거 및 텍스트 추출
                text_content = re.sub(r'<[^>]+>', '', html_content)
                text_content = re.sub(r'\s+', ' ', text_content).strip()
                
                if len(text_content) > 200:
                    result += f"**내용**: {text_content[:2000]}{'...' if len(text_content) > 2000 else ''}\n\n"
                else:
                    result += f"**내용**: {text_content}\n\n"
                    
                result += "안내: 국세청 판례는 HTML 형태로 제공됩니다. 전체 내용은 위 URL에서 확인하세요."
            except:
                result += "HTML 형태로 판례 내용이 조회되었습니다.\n"
                result += "안내: 국세청 판례는 HTML 형태로만 제공됩니다. 전체 내용은 위 URL에서 확인하세요."
        else:
            # 일반적인 딕셔너리 응답 처리
            result += f"**판례 응답 (ID: {case_id})**\n\n"
            import json
            result += f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)[:1500]}{'...' if len(json.dumps(data, ensure_ascii=False)) > 1500 else ''}\n```"
    else:
        result += f"**HTML 응답 내용**:\n{str(data)[:1000]}{'...' if len(str(data)) > 1000 else ''}"
    
    return result

def _safe_format_law_detail(data: dict, search_term: str, url: str) -> str:
    """법령 상세 조회를 위한 안전한 포맷팅"""
    try:
        result = f"API 호출 URL: {url}\n\n"
        
        if "error" in data:
            return f"오류: {data['error']}\n\nAPI URL: {url}"
        
        # 법령 상세 조회 결과 처리
        if "LawService" in data:
            service_data = data["LawService"]
            law_data = service_data.get("법령", {})
            
            if law_data:
                result += f"법령 상세내용 ({search_term})\n\n"
                result += f"법령명: {law_data.get('법령명', law_data.get('법령명한글', '미지정'))}\n"
                result += f"법령구분: {law_data.get('법령구분명', '미지정')}\n"
                result += f"소관부처: {law_data.get('소관부처명', '미지정')}\n"
                result += f"법령ID: {law_data.get('법령ID', '미지정')}\n"
                result += f"공포일자: {law_data.get('공포일자', '미지정')}\n"
                result += f"시행일자: {law_data.get('시행일자', '미지정')}\n"
                result += f"공포번호: {law_data.get('공포번호', '미지정')}\n"
                result += f"현행연혁코드: {law_data.get('현행연혁코드', '미지정')}\n\n"
                
                # 조문 내용 안전하게 처리
                if law_data.get('조문'):
                    result += f"【조문내용】\n"
                    jo_content = law_data['조문']
                    if isinstance(jo_content, list):
                        for i, jo in enumerate(jo_content[:10], 1):  # 최대 10개 조문
                            try:
                                if isinstance(jo, dict):
                                    jo_text = jo.get('조문내용', '')
                                    if jo_text:
                                        result += f"\n조문 {i}: {jo_text}\n"
                                elif isinstance(jo, str):
                                    result += f"\n조문 {i}: {jo}\n"
                            except:
                                continue
                    elif isinstance(jo_content, dict):
                        for key, value in jo_content.items():
                            if isinstance(value, str) and value.strip():
                                result += f"\n{key}: {value}\n"
                    result += "\n"
                    
                # 제개정이유 안전하게 처리
                if law_data.get('제개정이유'):
                    result += f"【제개정이유】\n"
                    reason_data = law_data['제개정이유']
                    if isinstance(reason_data, dict):
                        for key, value in reason_data.items():
                            if value and str(value).strip():
                                result += f"{key}: {value}\n"
                    elif isinstance(reason_data, str):
                        result += f"{reason_data}\n"
                    result += "\n"
                        
            else:
                result += "법령 상세내용을 찾을 수 없습니다.\n"
                
        # MST 파라미터 사용시의 다른 구조 처리
        elif "법령" in data and isinstance(data["법령"], dict):
            law_data = data["법령"]
            basic_info = law_data.get("기본정보", {})
            
            result += f"법령 상세내용 ({search_term})\n\n"
            result += f"법령명: {basic_info.get('법령명_한글', '미지정')}\n"
            result += f"법령ID: {basic_info.get('법령ID', '미지정')}\n"
            result += f"공포일자: {basic_info.get('공포일자', '미지정')}\n"
            result += f"시행일자: {basic_info.get('시행일자', '미지정')}\n\n"
             
            # 조문 내용 안전하게 처리
            if law_data.get("조문"):
                result += f"【조문내용】\n"
                jo_data = law_data["조문"]
                if isinstance(jo_data, dict) and jo_data.get("조문단위"):
                    jo_units = jo_data["조문단위"]
                    if isinstance(jo_units, list):
                        for i, unit in enumerate(jo_units[:10], 1):
                            try:
                                if isinstance(unit, dict):
                                    content = unit.get('조문내용', '')
                                    if content:
                                        result += f"\n조문 {i}: {content}\n"
                            except:
                                continue
                result += "\n"
        else:
            # 기본 fallback - 전체 JSON 출력
            import json
            result += f"전체 응답 데이터:\n{json.dumps(data, ensure_ascii=False, indent=2)[:2000]}\n"
            
        return result
        
    except Exception as e:
        import json
        return f"법령 상세 조회 포맷팅 오류: {str(e)}\n\n원본 데이터:\n{json.dumps(data, ensure_ascii=False, indent=2)[:1000]}\n\nAPI URL: {url}"

def _format_search_results(data: dict, search_type: str, query: str = "", url: str = "") -> str:
    """검색 결과를 풍부하고 체계적으로 포맷팅 (이모티콘 최소화, 정보 최대화)"""
    
    if "error" in data:
        return f"오류: {data['error']}\n\nAPI URL: {url}"
    
    try:
        result = ""
        
        # API 호출 URL 정보
        if url:
            result += f"API 호출 URL: {url}\n\n"
        
        # 법령 검색 결과 (LawSearch)
        if "LawSearch" in data:
            search_data = data["LawSearch"]
            total_count = search_data.get("totalCnt", 0)
            keyword = search_data.get("키워드", query)
            result += f"'{keyword}' 법령 검색 결과 (총 {total_count}건)\n\n"
            
            # 단일 객체 또는 배열 처리 (다양한 타겟 지원)
            if search_type in ["eflaw", "elaw"]:
                # 시행일법령과 영문법령은 'law' 키 사용
                law_data = search_data.get("law")
            elif search_type == "eflawjosub":
                # 시행일법령 조항호목은 'eflawjosub' 키 사용
                law_data = search_data.get("eflawjosub")
            else:
                # 기타 타겟은 해당 키 또는 'law' 키 사용
                law_data = search_data.get(search_type) or search_data.get("law")
                
            if isinstance(law_data, dict):
                items = [law_data]
            elif isinstance(law_data, list):
                items = law_data
            else:
                items = []
            
            if items:
                for i, item in enumerate(items[:10], 1):
                    if isinstance(item, dict):
                        result += f"{i}. {item.get('법령명한글', '법령명 없음')}\n"
                        result += f"   법령구분: {item.get('법령구분명', '미지정')}\n"
                        result += f"   소관부처: {item.get('소관부처명', '미지정')}\n"
                        result += f"   법령ID: {item.get('법령ID', '미지정')}\n"
                        result += f"   현행연혁: {item.get('현행연혁코드', '미지정')}\n"
                        result += f"   공포일자: {item.get('공포일자', '미지정')}\n"
                        result += f"   시행일자: {item.get('시행일자', '미지정')}\n"
                        result += f"   공포번호: {item.get('공포번호', '미지정')}\n"
                        result += f"   제개정구분: {item.get('제개정구분명', '미지정')}\n"
                        result += f"   법령일련번호: {item.get('법령일련번호', '미지정')}\n"
                        
                        # 상세링크 처리
                        detail_link = item.get('법령상세링크', '')
                        if detail_link:
                            result += f"   상세조회 URL: http://www.law.go.kr{detail_link}\n"
                        elif item.get('법령ID'):
                            result += f"   상세조회 URL: {legislation_config.service_base_url}?OC={legislation_config.oc}&type=JSON&target=law&ID={item['법령ID']}\n"
                        result += "\n"
            else:
                result += "검색된 법령이 없습니다.\n"
                
        # 판례 검색 결과 (PrecSearch)
        elif "PrecSearch" in data:
            search_data = data["PrecSearch"]
            total_count = search_data.get("totalCnt", 0)
            keyword = search_data.get("키워드", query)
            result += f"'{keyword}' 판례 검색 결과 (총 {total_count}건)\n\n"
            
            # 단일 객체 또는 배열 처리 (슬라이스 오류 방지)
            prec_data = search_data.get("prec")
            if isinstance(prec_data, dict):
                items = [prec_data]
            elif isinstance(prec_data, list):
                items = prec_data
            elif isinstance(prec_data, str):
                # 문자열인 경우 빈 리스트로 변환 (슬라이스 오류 방지)
                logger.warning(f"판례 검색 결과가 문자열로 반환됨: {prec_data[:100]}...")
                items = []
            else:
                items = []
                
            if items:
                for i, item in enumerate(items[:10], 1):
                    if isinstance(item, dict):
                        result += f"{i}. {item.get('사건명', '사건명 없음')}\n"
                        result += f"   사건번호: {item.get('사건번호', '미지정')}\n"
                        result += f"   법원명: {item.get('법원명', '미지정')}\n"
                        result += f"   선고일자: {item.get('선고일자', '미지정')}\n"
                        result += f"   사건종류: {item.get('사건종류명', '미지정')}\n"
                        result += f"   판결유형: {item.get('판결유형', '미지정')}\n"
                        result += f"   데이터출처: {item.get('데이터출처명', '미지정')}\n"
                        result += f"   판례일련번호: {item.get('판례일련번호', '미지정')}\n"
                        
                        # 상세링크 처리
                        detail_link = item.get('판례상세링크', '')
                        if detail_link:
                            result += f"   상세조회 URL: http://www.law.go.kr{detail_link}\n"
                        result += "\n"
            else:
                result += "검색된 판례가 없습니다.\n"
        
        # 해석례 검색 결과 (Expc)
        elif "Expc" in data:
            search_data = data["Expc"]
            total_count = search_data.get("totalCnt", 0)
            keyword = search_data.get("키워드", query)
            result += f"'{keyword}' 해석례 검색 결과 (총 {total_count}건)\n\n"
            
            # 단일 객체 또는 배열 처리 (슬라이스 오류 방지)
            expc_data = search_data.get("expc")
            if isinstance(expc_data, dict):
                items = [expc_data]
            elif isinstance(expc_data, list):
                items = expc_data
            elif isinstance(expc_data, str):
                # 문자열인 경우 빈 리스트로 변환 (슬라이스 오류 방지)
                logger.warning(f"해석례 검색 결과가 문자열로 반환됨: {expc_data[:100]}...")
                items = []
            else:
                items = []
                
            if items:
                for i, item in enumerate(items[:10], 1):
                    if isinstance(item, dict):
                        result += f"{i}. {item.get('안건명', '안건명 없음')}\n"
                        result += f"   안건번호: {item.get('안건번호', '미지정')}\n"
                        result += f"   회신기관: {item.get('회신기관명', '미지정')}\n"
                        result += f"   질의기관: {item.get('질의기관명', '미지정')}\n"
                        result += f"   회신일자: {item.get('회신일자', '미지정')}\n"
                        result += f"   해석례일련번호: {item.get('법령해석례일련번호', '미지정')}\n"
                        
                        # 상세링크 처리
                        detail_link = item.get('법령해석례상세링크', '')
                        if detail_link:
                            result += f"   상세조회 URL: http://www.law.go.kr{detail_link}\n"
                        result += "\n"
            else:
                result += "검색된 해석례가 없습니다.\n"
                
        # 행정규칙 검색 결과 (AdmRulSearch)
        elif "AdmRulSearch" in data:
            search_data = data["AdmRulSearch"]
            total_count = search_data.get("totalCnt", 0)
            keyword = search_data.get("키워드", query)
            result += f"'{keyword}' 행정규칙 검색 결과 (총 {total_count}건)\n\n"
            
            # 단일 객체 또는 배열 처리 (슬라이스 오류 방지)
            admrul_data = search_data.get("admrul")
            if isinstance(admrul_data, dict):
                items = [admrul_data]
            elif isinstance(admrul_data, list):
                items = admrul_data
            elif isinstance(admrul_data, str):
                # 문자열인 경우 빈 리스트로 변환 (슬라이스 오류 방지)
                logger.warning(f"행정규칙 검색 결과가 문자열로 반환됨: {admrul_data[:100]}...")
                items = []
            else:
                items = []
                
            if items:
                for i, item in enumerate(items[:10], 1):
                    if isinstance(item, dict):
                        result += f"{i}. {item.get('행정규칙명', '행정규칙명 없음')}\n"
                        result += f"   행정규칙ID: {item.get('행정규칙ID', '미지정')}\n"
                        result += f"   행정규칙종류: {item.get('행정규칙종류', '미지정')}\n"
                        result += f"   소관부처: {item.get('소관부처명', '미지정')}\n"
                        result += f"   발령일자: {item.get('발령일자', '미지정')}\n"
                        result += f"   시행일자: {item.get('시행일자', '미지정')}\n"
                        result += f"   발령번호: {item.get('발령번호', '미지정')}\n"
                        result += f"   제개정구분: {item.get('제개정구분명', '미지정')}\n"
                        result += f"   현행연혁구분: {item.get('현행연혁구분', '미지정')}\n"
                        result += f"   행정규칙일련번호: {item.get('행정규칙일련번호', '미지정')}\n"
                        
                        # 상세링크 처리
                        detail_link = item.get('행정규칙상세링크', '')
                        if detail_link:
                            result += f"   상세조회 URL: http://www.law.go.kr{detail_link}\n"
                        result += "\n"
            else:
                result += "검색된 행정규칙이 없습니다.\n"
                
        # 금융위원회 결정문 (Fsc)
        elif "Fsc" in data:
            search_data = data["Fsc"]
            total_count = search_data.get("totalCnt", 0)
            keyword = search_data.get("키워드", query)
            result += f"금융위원회 '{keyword}' 검색 결과 (총 {total_count}건)\n\n"
            
            # 금융위원회 결정문 데이터 처리 (슬라이스 오류 방지)
            fsc_data = search_data.get("fsc", [])
            if isinstance(fsc_data, dict):
                items = [fsc_data]
            elif isinstance(fsc_data, list):
                items = fsc_data
            elif isinstance(fsc_data, str):
                # 문자열인 경우 빈 리스트로 변환 (슬라이스 오류 방지)
                logger.warning(f"금융위원회 결정문 검색 결과가 문자열로 반환됨: {fsc_data[:100]}...")
                items = []
            else:
                items = []
                
            if items:
                for i, item in enumerate(items[:10], 1):
                    if isinstance(item, dict):
                        result += f"{i}. {item.get('안건명', '안건명 없음')}\n"
                        result += f"   의결번호: {item.get('의결번호', '미지정')}\n"
                        result += f"   기관명: {item.get('기관명', '미지정')}\n"
                        result += f"   결정문일련번호: {item.get('결정문일련번호', '미지정')}\n"
                        
                        detail_link = item.get('결정문상세링크', '')
                        if detail_link:
                            result += f"   상세조회 URL: http://www.law.go.kr{detail_link}\n"
                        result += "\n"
            else:
                result += "검색된 금융위원회 결정문이 없습니다.\n"
                
        # 금융위원회 결정문 상세조회 (FscService)
        elif "FscService" in data:
            service_data = data["FscService"]
            decision_data = service_data.get("의결서", {})
            
            if decision_data:
                result += f"금융위원회 결정문 상세내용\n\n"
                result += f"기관명: {decision_data.get('기관명', '금융위원회')}\n"
                result += f"결정문일련번호: {decision_data.get('결정문일련번호', '미지정')}\n"
                result += f"안건명: {decision_data.get('안건명', '미지정')}\n"
                result += f"의결일자: {decision_data.get('의결일자', '미지정')}\n"
                result += f"회의종류: {decision_data.get('회의종류', '미지정')}\n"
                result += f"결정구분: {decision_data.get('결정', '미지정')}\n\n"
                
                # 주문
                if decision_data.get('주문'):
                    result += f"【주문】\n{decision_data['주문']}\n\n"
                
                # 이유
                if decision_data.get('이유'):
                    result += f"【이유】\n{decision_data['이유']}\n\n"
                
                # 별지 (상세 내용)
                if decision_data.get('별지'):
                    result += f"【별지】\n{decision_data['별지']}\n\n"
                
                # 기타 정보
                other_fields = ['결정요지', '배경', '주요내용', '신청인', '위원서명']
                for field in other_fields:
                    if decision_data.get(field) and decision_data[field].strip():
                        result += f"【{field}】\n{decision_data[field]}\n\n"
                        
            else:
                result += "금융위원회 결정문 상세내용을 찾을 수 없습니다.\n"
                
        # 개인정보보호위원회 결정문 (Ppc)  
        elif "Ppc" in data:
            search_data = data["Ppc"]
            total_count = search_data.get("totalCnt", 0)
            keyword = search_data.get("키워드", query)
            agency = search_data.get("기관명", "개인정보보호위원회")
            result += f"{agency} '{keyword}' 검색 결과 (총 {total_count}건)\n\n"
            
            # 개인정보보호위원회 결정문 데이터 처리 (슬라이스 오류 방지)
            ppc_data = search_data.get("ppc", [])
            if isinstance(ppc_data, dict):
                items = [ppc_data]
            elif isinstance(ppc_data, list):
                items = ppc_data
            elif isinstance(ppc_data, str):
                # 문자열인 경우 빈 리스트로 변환 (슬라이스 오류 방지)
                logger.warning(f"개인정보보호위원회 결정문 검색 결과가 문자열로 반환됨: {ppc_data[:100]}...")
                items = []
            else:
                items = []
                
            if items:
                for i, item in enumerate(items[:10], 1):
                    if isinstance(item, dict):
                        result += f"{i}. {item.get('안건명', '안건명 없음')}\n"
                        result += f"   의안번호: {item.get('의안번호', '미지정')}\n"
                        result += f"   의결일: {item.get('의결일', '미지정')}\n"
                        result += f"   결정구분: {item.get('결정구분', '미지정')}\n"
                        result += f"   회의종류: {item.get('회의종류', '미지정')}\n"
                        result += f"   결정문일련번호: {item.get('결정문일련번호', '미지정')}\n"
                        
                        detail_link = item.get('결정문상세링크', '')
                        if detail_link:
                            result += f"   상세조회 URL: http://www.law.go.kr{detail_link}\n"
                        result += "\n"
            else:
                result += "검색된 개인정보보호위원회 결정문이 없습니다.\n"
                
        # 개인정보보호위원회 결정문 상세조회 (PpcService)
        elif "PpcService" in data:
            service_data = data["PpcService"]
            decision_data = service_data.get("의결서", {})
            
            if decision_data:
                result += f"개인정보보호위원회 결정문 상세내용\n\n"
                result += f"기관명: {decision_data.get('기관명', '개인정보보호위원회')}\n"
                result += f"결정문일련번호: {decision_data.get('결정문일련번호', '미지정')}\n"
                result += f"안건명: {decision_data.get('안건명', '미지정')}\n"
                result += f"의결일자: {decision_data.get('의결일자', '미지정')}\n"
                result += f"회의종류: {decision_data.get('회의종류', '미지정')}\n"
                result += f"결정구분: {decision_data.get('결정', '미지정')}\n"
                result += f"위원서명: {decision_data.get('위원서명', '미지정')}\n\n"
                
                # 주문
                if decision_data.get('주문'):
                    result += f"【주문】\n{decision_data['주문']}\n\n"
                
                # 이유
                if decision_data.get('이유'):
                    result += f"【이유】\n{decision_data['이유']}\n\n"
                
                # 별지 (상세 내용)
                if decision_data.get('별지'):
                    result += f"【별지】\n{decision_data['별지']}\n\n"
                
                # 기타 정보
                other_fields = ['결정요지', '배경', '주요내용', '신청인', '이의제기방법및기간']
                for field in other_fields:
                    if decision_data.get(field) and decision_data[field].strip():
                        result += f"【{field}】\n{decision_data[field]}\n\n"
                        
            else:
                result += "개인정보보호위원회 결정문 상세내용을 찾을 수 없습니다.\n"
                
        # 오류 응답 처리 (공통)
        elif "Law" in data and isinstance(data["Law"], str):
            result += f"조회 결과: {data['Law']}\n"
            
        # 법령 상세조회 (LawService)
        elif "LawService" in data:
            service_data = data["LawService"]
            law_data = service_data.get("법령", {})
            
            if law_data:
                result += f"법령 상세내용\n\n"
                result += f"법령명: {law_data.get('법령명', law_data.get('법령명한글', '미지정'))}\n"
                result += f"법령구분: {law_data.get('법령구분명', '미지정')}\n"
                result += f"소관부처: {law_data.get('소관부처명', '미지정')}\n"
                result += f"법령ID: {law_data.get('법령ID', '미지정')}\n"
                result += f"공포일자: {law_data.get('공포일자', '미지정')}\n"
                result += f"시행일자: {law_data.get('시행일자', '미지정')}\n"
                result += f"공포번호: {law_data.get('공포번호', '미지정')}\n"
                result += f"현행연혁코드: {law_data.get('현행연혁코드', '미지정')}\n\n"
                
                # 조문 내용 (배열 형태)
                if law_data.get('조문') and isinstance(law_data['조문'], list):
                    result += f"【조문내용】\n"
                    for jo in law_data['조문'][:20]:  # 최대 20개 조문
                        if isinstance(jo, dict):
                            result += f"\n{jo.get('조문내용', '')}\n"
                            if jo.get('항'):
                                for hang in jo['항']:
                                    if isinstance(hang, dict):
                                        result += f"{hang.get('항내용', '')}\n"
                                        if hang.get('호'):
                                            for ho in hang['호']:
                                                if isinstance(ho, dict):
                                                    result += f"{ho.get('호내용', '')}\n"
                    result += "\n"
                    
                # 제개정이유
                if law_data.get('제개정이유') and law_data['제개정이유'].get('제개정이유내용'):
                    result += f"【제개정이유】\n"
                    for reason_item in law_data['제개정이유']['제개정이유내용']:
                        if isinstance(reason_item, list):
                            for item in reason_item:
                                result += f"{item}\n"
                    result += "\n"
                    
            else:
                result += "법령 상세내용을 찾을 수 없습니다.\n"
                
        # 법령 상세조회 (MST 파라미터 사용시 - 다른 구조)
        elif "법령" in data and isinstance(data["법령"], dict):
            law_data = data["법령"]
            basic_info = law_data.get("기본정보", {})
            
            result += f"법령 상세내용\n\n"
            result += f"법령명: {basic_info.get('법령명_한글', '미지정')}\n"
            result += f"법령ID: {basic_info.get('법령ID', '미지정')}\n"
            result += f"법종구분: {basic_info.get('법종구분', {}).get('content', '미지정')}\n"
            result += f"공포일자: {basic_info.get('공포일자', '미지정')}\n"
            result += f"시행일자: {basic_info.get('시행일자', '미지정')}\n"
            result += f"공포번호: {basic_info.get('공포번호', '미지정')}\n"
            result += f"제개정구분: {basic_info.get('제개정구분', '미지정')}\n\n"
             
            # 조문 내용 (개선된 구조 처리)
            if law_data.get("조문"):
                 result += f"【조문내용】\n"
                 jo_units = law_data["조문"].get("조문단위", [])
                 
                 # 단일 조문과 여러 조문 모두 처리
                 if isinstance(jo_units, dict):
                     jo_units = [jo_units]
                 elif not isinstance(jo_units, list):
                     jo_units = []
                 
                 for jo_unit in jo_units[:30]:  # 최대 30개 조문
                     if isinstance(jo_unit, dict):
                         # 조문 제목과 번호
                         jo_num = jo_unit.get('조문번호', '')
                         jo_title = jo_unit.get('조문제목', '')
                         if jo_num and jo_title:
                             result += f"\n제{jo_num}조({jo_title})\n"
                         elif jo_unit.get('조문내용'):
                             result += f"\n{jo_unit['조문내용']}\n"
                         
                         # 항별 내용
                         if jo_unit.get('항'):
                             for hang in jo_unit['항']:
                                 if isinstance(hang, dict):
                                     hang_content = hang.get('항내용', '')
                                     if hang_content:
                                         result += f"{hang_content}\n"
                                     
                                     # 호별 내용
                                     if hang.get('호'):
                                         for ho in hang['호']:
                                             if isinstance(ho, dict):
                                                 ho_content = ho.get('호내용', '')
                                                 if ho_content:
                                                     result += f"{ho_content}\n"
                 result += "\n"
            
            # 부칙
            if law_data.get("부칙"):
                result += f"【부칙】\n"
                buchi_data = law_data["부칙"].get("부칙단위", {})
                if buchi_data.get("부칙내용"):
                    for content_item in buchi_data["부칙내용"]:
                        if isinstance(content_item, list):
                            for line in content_item:
                                result += f"{line}\n"
                        else:
                            result += f"{content_item}\n"
                result += "\n"
            
            # 개정문
            if law_data.get("개정문") and law_data["개정문"].get("개정문내용"):
                result += f"【개정문】\n{law_data['개정문']['개정문내용']}\n\n"
                
        # 판례 상세조회 (PrecService)
        elif "PrecService" in data:
            service_data = data["PrecService"]
            prec_data = service_data.get("판례", {})
            
            if prec_data:
                result += f"판례 상세내용\n\n"
                result += f"사건명: {prec_data.get('사건명', '미지정')}\n"
                result += f"사건번호: {prec_data.get('사건번호', '미지정')}\n"
                result += f"선고일자: {prec_data.get('선고일자', '미지정')}\n"
                result += f"법원명: {prec_data.get('법원명', '미지정')}\n"
                result += f"사건종류: {prec_data.get('사건종류명', '미지정')}\n"
                result += f"판례일련번호: {prec_data.get('판례일련번호', '미지정')}\n\n"
                
                # 판시사항
                if prec_data.get('판시사항'):
                    result += f"【판시사항】\n{prec_data['판시사항']}\n\n"
                
                # 판결요지
                if prec_data.get('판결요지'):
                    result += f"【판결요지】\n{prec_data['판결요지']}\n\n"
                
                # 참조조문
                if prec_data.get('참조조문'):
                    result += f"【참조조문】\n{prec_data['참조조문']}\n\n"
                
                # 전문
                if prec_data.get('전문'):
                    result += f"【전문】\n{prec_data['전문']}\n\n"
                    
            else:
                result += "판례 상세내용을 찾을 수 없습니다.\n"
                
        # 법령해석례 상세조회 (ExpcService)
        elif "ExpcService" in data:
            service_data = data["ExpcService"]
            expc_data = service_data.get("해석례", {})
            
            if expc_data:
                result += f"법령해석례 상세내용\n\n"
                result += f"해석례명: {expc_data.get('해석례명', '미지정')}\n"
                result += f"조회수: {expc_data.get('조회수', '미지정')}\n"
                result += f"해석일자: {expc_data.get('해석일자', '미지정')}\n"
                result += f"해석기관: {expc_data.get('해석기관', '미지정')}\n"
                result += f"해석례일련번호: {expc_data.get('해석례일련번호', '미지정')}\n\n"
                
                # 질의요지
                if expc_data.get('질의요지'):
                    result += f"【질의요지】\n{expc_data['질의요지']}\n\n"
                
                # 회답
                if expc_data.get('회답'):
                    result += f"【회답】\n{expc_data['회답']}\n\n"
                
                # 관련법령
                if expc_data.get('관련법령'):
                    result += f"【관련법령】\n{expc_data['관련법령']}\n\n"
                    
            else:
                result += "법령해석례 상세내용을 찾을 수 없습니다.\n"
                
        # 공정거래위원회 결정문 (Ftc)
        elif "Ftc" in data:
            search_data = data["Ftc"]
            total_count = search_data.get("totalCnt", 0)
            keyword = search_data.get("키워드", query)
            agency = search_data.get("기관명", "공정거래위원회")
            result += f"{agency} '{keyword}' 검색 결과 (총 {total_count}건)\n\n"
            
            # 단일 객체 또는 배열 처리
            ftc_data = search_data.get("ftc", {})
            if isinstance(ftc_data, dict):
                items = [ftc_data]
            elif isinstance(ftc_data, list):
                items = ftc_data
            else:
                items = []
                
            if items:
                for i, item in enumerate(items[:10], 1):
                    if isinstance(item, dict):
                        result += f"{i}. {item.get('사건명', '사건명 없음')}\n"
                        result += f"   사건번호: {item.get('사건번호', '미지정')}\n"
                        result += f"   결정번호: {item.get('결정번호', '미지정')}\n"
                        result += f"   결정일자: {item.get('결정일자', '미지정')}\n"
                        result += f"   문서유형: {item.get('문서유형', '미지정')}\n"
                        result += f"   결정문일련번호: {item.get('결정문일련번호', '미지정')}\n"
                        
                        detail_link = item.get('결정문상세링크', '')
                        if detail_link:
                            result += f"   상세조회 URL: http://www.law.go.kr{detail_link}\n"
                        result += "\n"
            else:
                result += "검색된 공정거래위원회 결정문이 없습니다.\n"
                
        # 공정거래위원회 결정문 상세조회 (FtcService)
        elif "FtcService" in data:
            service_data = data["FtcService"]
            decision_data = service_data.get("의결서", {})
            
            if decision_data:
                result += f"공정거래위원회 결정문 상세내용\n\n"
                result += f"기관명: {decision_data.get('기관명', '공정거래위원회')}\n"
                result += f"결정문일련번호: {decision_data.get('결정문일련번호', '미지정')}\n"
                result += f"사건명: {decision_data.get('사건명', '미지정')}\n"
                result += f"사건번호: {decision_data.get('사건번호', '미지정')}\n"
                result += f"결정일자: {decision_data.get('결정일자', '미지정')}\n"
                result += f"문서유형: {decision_data.get('문서유형', '미지정')}\n"
                result += f"결정번호: {decision_data.get('결정번호', '미지정')}\n\n"
                
                # 주문
                if decision_data.get('주문'):
                    result += f"【주문】\n{decision_data['주문']}\n\n"
                
                # 이유
                if decision_data.get('이유'):
                    result += f"【이유】\n{decision_data['이유']}\n\n"
                
                # 별지 (상세 내용)
                if decision_data.get('별지'):
                    result += f"【별지】\n{decision_data['별지']}\n\n"
                
                # 기타 정보
                other_fields = ['결정요지', '배경', '주요내용', '관련법령', '처분내용']
                for field in other_fields:
                    if decision_data.get(field) and decision_data[field].strip():
                        result += f"【{field}】\n{decision_data[field]}\n\n"
                        
            else:
                result += "공정거래위원회 결정문 상세내용을 찾을 수 없습니다.\n"
                
        # 기타 모든 API 응답 처리 (OrdinSearch, 기타 위원회 등)
        else:
            # 상세 조회 응답 패턴 확인 (Service로 끝나는 키들)
            service_keys = [k for k in data.keys() if k.endswith("Service")]
            if service_keys:
                service_key = service_keys[0]
                service_data = data[service_key]
                
                # 일반적인 상세 조회 처리
                if isinstance(service_data, dict):
                    # 주요 데이터 키 찾기 (의결서, 판례, 해석례 등)
                    content_keys = ["의결서", "판례", "해석례", "결정문", "용어", "규칙", "조례"]
                    content_data = None
                    content_type = "내용"
                    
                    for key in content_keys:
                        if key in service_data:
                            content_data = service_data[key]
                            content_type = key
                            break
                    
                    if content_data and isinstance(content_data, dict):
                        result += f"{content_type} 상세내용\n\n"
                        
                        # 기본 정보 출력
                        basic_fields = ["제목", "명칭", "안건명", "사건명", "결정문일련번호", "ID"]
                        for field in basic_fields:
                            if field in content_data and content_data[field]:
                                result += f"{field}: {content_data[field]}\n"
                        
                        result += "\n"
                        
                        # 주요 내용 출력
                        content_fields = ["주문", "이유", "내용", "본문", "전문", "질의요지", "회답", "정의"]
                        for field in content_fields:
                            if field in content_data and content_data[field] and str(content_data[field]).strip():
                                result += f"【{field}】\n{content_data[field]}\n\n"
                        
                        # 기타 필드들
                        other_fields = [k for k in content_data.keys() 
                                      if k not in basic_fields + content_fields 
                                      and content_data[k] and str(content_data[k]).strip()]
                        for field in other_fields:
                            result += f"【{field}】\n{content_data[field]}\n\n"
                    else:
                        result += f"{content_type} 상세내용을 찾을 수 없습니다.\n"
                else:
                    result += "상세내용을 찾을 수 없습니다.\n"
            else:
                # 일반 검색 결과 처리
                main_keys = [k for k in data.keys() if k not in ["error", "message"]]
                if main_keys:
                    main_key = main_keys[0]
                    search_data = data[main_key]
                    
                    if isinstance(search_data, dict):
                        total_count = search_data.get("totalCnt", "미지정")
                        keyword = search_data.get("키워드", query)
                        result += f"'{keyword}' 검색 결과 (총 {total_count}건)\n\n"
                    
                        # 데이터 배열 찾기 (첫 번째 배열 또는 단일 객체)
                        items_found = False
                        for key, value in search_data.items():
                            if isinstance(value, list) and value:
                                items = value[:10]  # 최대 10개
                                items_found = True
                                break
                            elif isinstance(value, dict) and 'id' in value:
                                items = [value]  # 단일 객체를 리스트로 감싸기
                                items_found = True
                                break
                        
                        if items_found:
                            for i, item in enumerate(items, 1):
                                if isinstance(item, dict):
                                    # 제목/이름 필드 찾기
                                    title_fields = [
                                        "법령명한글", "법령명", "판례명", "사건명", "안건명", "제목",
                                        "별표명", "조약명", "용어명", "질의요지", "해석명", "규칙명",
                                        "결정문제목", "의결서제목", "행정규칙명", "자치법규명", "조례명"
                                    ]
                                    title = "제목 없음"
                                    for field in title_fields:
                                        if field in item and item[field]:
                                            title = item[field]
                                            break
                                    
                                    result += f"{i}. {title}\n"
                                    
                                    # 모든 필드 출력 (title 제외)
                                    for field, value in item.items():
                                        if field not in title_fields and value and str(value).strip():
                                            # 한글 필드명을 적절히 번역
                                            if field.endswith('링크'):
                                                if str(value).startswith('/'):
                                                    result += f"   {field}: http://www.law.go.kr{value}\n"
                                                else:
                                                    result += f"   {field}: {value}\n"
                                            else:
                                                result += f"   {field}: {value}\n"
                                    
                                    result += "\n"
                        else:
                            result += "검색된 결과가 없습니다.\n"
                    else:
                        # search_data가 dict가 아닌 경우 전체 JSON 출력
                        result += f"전체 응답 데이터:\n{json.dumps(data, ensure_ascii=False, indent=2)[:1500]}\n"
                else:
                    # 메인 키를 찾을 수 없는 경우
                    result += f"전체 응답 데이터:\n{json.dumps(data, ensure_ascii=False, indent=2)[:1500]}\n"
        

                
        return result
        
    except Exception as e:
        logger.error(f"결과 포맷팅 실패: {e}")
        return f"**원본 응답 데이터**:\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)[:1000]}{'...' if len(json.dumps(data, ensure_ascii=False)) > 1000 else ''}\n```\n\n**API URL**: {url}\n\n**포맷팅 오류**: {str(e)}"

# ===========================================
# 1. 법령 관련 API (16개)
# ===========================================

# ===========================================
# 기본 법령 도구들은 basic_law_tools.py로 분리됨
# ===========================================

# get_law_detail은 basic_law_tools.py로 분리됨

@mcp.tool(
    name="search_all_legal_documents",
    description="""모든 종류의 법적 문서를 통합 검색합니다. 법령, 판례, 해석례, 위원회 결정문을 포괄적으로 검색합니다.

매개변수:
- query: 검색어 (필수)
- display: 각 카테고리별 결과 개수 (기본값: 5)
- include_law: 법령 포함 여부 (기본값: True)
- include_precedent: 판례 포함 여부 (기본값: True)
- include_interpretation: 해석례 포함 여부 (기본값: True)
- include_committee: 위원회 결정문 포함 여부 (기본값: True)

사용 예시: search_all_legal_documents("개인정보보호"), search_all_legal_documents("금융규제", display=10, include_law=False)""",
    tags={"통합검색", "법령", "판례", "해석례", "위원회", "종합분석", "법적문서"}
)
def search_all_legal_documents(
    query: Optional[str] = None,
    display: int = 5,
    include_law: bool = True,
    include_precedent: bool = True,
    include_interpretation: bool = True,
    include_committee: bool = True
) -> TextContent:
    """통합 법률 문서 검색 - 정확도 개선 버전"""
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요. 예: '개인정보보호', '금융규제', '노동법' 등")
    
    search_query = query.strip()
    
    results = []
    results.append(f"'{search_query}' 통합 검색 결과\n")
    results.append("=" * 50 + "\n")
    
    try:
        total_results = 0
        
        display = max(1, min(display, 20))

        # 1. 스마트 법령 검색 (정확도 개선)
        if include_law:
            try:
                law_data = _smart_search("law", search_query, display=display)
                law_url = _generate_api_url("law", {"query": search_query, "display": display})

                # 결과 유효성 검사
                if law_data and isinstance(law_data, dict) and law_data.get('LawSearch'):
                    law_count = law_data['LawSearch'].get('totalCnt', 0)
                    try:
                        law_count = int(law_count)
                    except (ValueError, TypeError):
                        law_count = 0
                    if law_count > 0:
                        law_result = _format_search_results(law_data, "law", search_query, display)
                        results.append("**법령 검색 결과:**\n")
                        results.append(law_result + "\n")
                        total_results += law_count
                    else:
                        results.append("**법령 검색 결과:** 관련 법령을 찾을 수 없습니다.\n\n")
                else:
                    results.append("**법령 검색 결과:** 검색 중 오류가 발생했습니다.\n\n")
            except Exception as e:
                results.append(f"**법령 검색 오류:** {str(e)}\n\n")
        
        # 2. 판례 검색 (안정성 강화)
        if include_precedent:
            try:
                prec_params = {"query": search_query, "display": 4, "search": 2}  # 본문검색으로 정확도 향상
                prec_data = _make_legislation_request("prec", prec_params)
                prec_url = _generate_api_url("prec", prec_params)
                
                if prec_data and isinstance(prec_data, dict) and prec_data.get('PrecSearch'):
                    prec_count = prec_data['PrecSearch'].get('totalCnt', 0)
                    try:
                        prec_count = int(prec_count)
                    except (ValueError, TypeError):
                        prec_count = 0
                    if prec_count > 0:
                        prec_result = _format_search_results(prec_data, "prec", search_query, 20)
                        results.append("**판례 검색 결과:**\n")
                        results.append(prec_result + "\n")
                        total_results += prec_count
                    else:
                        results.append("**판례 검색 결과:** 관련 판례를 찾을 수 없습니다.\n\n")
                else:
                    results.append("**판례 검색 결과:** 검색 중 오류가 발생했습니다.\n\n")
            except Exception as e:
                results.append(f"**판례 검색 오류:** {str(e)}\n\n")
        
        # 3. 해석례 검색 (안정성 강화)
        if include_interpretation:
            try:
                interp_params = {"query": search_query, "display": 4}
                interp_data = _make_legislation_request("expc", interp_params)
                interp_url = _generate_api_url("expc", interp_params)
                
                if interp_data and isinstance(interp_data, dict) and interp_data.get('Expc'):
                    interp_count = interp_data['Expc'].get('totalCnt', 0)
                    try:
                        interp_count = int(interp_count)
                    except (ValueError, TypeError):
                        interp_count = 0
                    if interp_count > 0:
                        interp_result = _format_search_results(interp_data, "expc", search_query, 20)
                        results.append("**해석례 검색 결과:**\n")
                        results.append(interp_result + "\n")
                        total_results += interp_count
                    else:
                        results.append("**해석례 검색 결과:** 관련 해석례를 찾을 수 없습니다.\n\n")
                else:
                    results.append("**해석례 검색 결과:** 검색 중 오류가 발생했습니다.\n\n")
            except Exception as e:
                results.append(f"**해석례 검색 오류:** {str(e)}\n\n")
        
        # 4. 주요 위원회 결정문 검색 (안정성 강화)
        committee_results = 0
        if include_committee:
            committee_targets = [
                ("ppc", "개인정보보호위원회"),
                ("fsc", "금융위원회"), 
                ("ftc", "공정거래위원회"),
                ("acr", "국민권익위원회"),
                ("nhrck", "국가인권위원회")
            ]
            
            results.append("**위원회 결정문 검색 결과:**\n")
            
            for target, name in committee_targets:
                try:
                    committee_params = {"query": search_query, "display": 3, "search": 2}  # 본문검색으로 정확도 향상
                    committee_data = _make_legislation_request(target, committee_params)
                    committee_url = _generate_api_url(target, committee_params)
                    
                    # 결과 유효성 검사 강화
                    if committee_data and isinstance(committee_data, dict) and not committee_data.get("error"):
                        # 각 위원회별 응답 구조 확인 (실제 키는 Ppc, Fsc, Ftc, Acr, Nhrck 등)
                        search_key = target.title()  # Ppc, Fsc, Ftc 등
                        if search_key in committee_data:
                            total_cnt = committee_data[search_key].get('totalCnt', 0)
                            try:
                                total_cnt = int(total_cnt)
                            except (ValueError, TypeError):
                                total_cnt = 0
                            
                            if total_cnt > 0:
                                committee_result = _format_search_results(committee_data, target, search_query, 20)
                                if "결과가 없습니다" not in committee_result and "검색된" not in committee_result:
                                    results.append(f"**{name}:**\n")
                                    results.append(committee_result + "\n")
                                    committee_results += total_cnt
                        else:
                            results.append(f"**{name}:** 관련 결정문이 없습니다.\n")
                    else:
                        results.append(f"**{name}:** 검색 중 오류가 발생했습니다.\n")
                except Exception as e:
                    results.append(f"**{name}:** 검색 실패 - {str(e)}\n")
                    continue
            
            total_results += committee_results
        
        # 검색 총계 및 요약 추가
        results.append("\n" + "=" * 50)
        results.append(f"\n**검색 총계**: {total_results:,}건의 문서를 찾았습니다.")
        
        if total_results == 0:
            results.append(f"\n\n**검색 팁**: '{search_query}' 키워드로 결과가 없습니다. 다음을 시도해보세요:")
            results.append("\n- 더 일반적인 키워드 사용 (예: '개인정보' → '정보보호')")
            results.append("\n- 유사어나 동의어 시도")
            results.append("\n- 키워드를 짧게 줄이기")
            results.append("\n- 영문/한글 번역 시도")
        
        return TextContent(type="text", text="".join(results))
        
    except Exception as e:
        error_msg = f"통합 검색 중 오류가 발생했습니다: {str(e)}"
        return TextContent(type="text", text=error_msg)

logger.info("121개 법제처 OPEN API 도구가 모두 로드되었습니다!") 

# ===========================================
# 추가 누락된 API 도구들 (125개 완성을 위해)
# ===========================================

