"""
한국 법제처 OPEN API - 법령 관련 통합 도구들

현행법령, 시행일법령, 법령연혁, 영문법령, 조문, 체계도, 연계정보, 맞춤형 등
모든 법령 관련 도구들을 통합 제공합니다. (총 29개 도구)
"""

import logging
import json
import os
import requests  # type: ignore
from urllib.parse import urlencode
from typing import Optional, Union, Dict, Any, List, Annotated
from mcp.types import TextContent
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import re

try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    BeautifulSoup = None  # type: ignore
    HAS_BEAUTIFULSOUP = False

from ..server import mcp
from ..config import legislation_config
from ..apis.client import LegislationClient
from ..utils.law_tools_utils import (
    # search_law 도구 관련
    format_search_law_results, normalize_search_query, create_search_variants,
    # get_law_detail 도구 관련  
    extract_law_summary_from_detail, format_law_detail_summary,
    # get_law_article_by_key 도구 관련
    normalize_article_key, find_article_in_data, get_available_articles, format_article_content,
    # get_law_articles_range 도구 관련
    format_article_body,
    # 공통 유틸리티
    clean_html_tags, safe_get_nested_value,
    extract_total_count, format_result_guidance
)
from .law_config import (
    DOMAIN_KEYWORDS,
    KEYWORD_TO_LAW_MAPPING,
    IRRELEVANT_PATTERNS,
    CHANGE_DETAILS,
    FIELD_MAPPINGS,
    FINANCIAL_KEYWORDS,
    FINANCIAL_LAWS,
    FINANCIAL_CATEGORIES,
    TAX_KEYWORDS,
    TAX_LAWS,
    TAX_CATEGORIES,
    PRIVACY_KEYWORDS,
    PRIVACY_LAWS,
    PRIVACY_CATEGORIES,
    SLOW_API_TARGETS,
    DEFAULT_TIMEOUT,
    SLOW_API_TIMEOUT,
    FINANCIAL_SEARCH_LIMIT,
    TAX_SEARCH_LIMIT,
    PRIVACY_SEARCH_LIMIT,
)
from .law_formatters import (
    format_law_item,
    format_law_list,
    format_categorized_laws,
    categorize_laws,
)


logger = logging.getLogger(__name__)

# ===========================================
# 캐시 시스템 (최적화용)
# ===========================================

# 홈 디렉토리의 .cache 사용 (권한 문제 해결)
CACHE_DIR = Path.home() / ".cache" / "mcp-kr-legislation"
CACHE_DAYS = 7  # 캐시 유효 기간 (일)

def ensure_cache_dir():
    """캐시 디렉토리 생성"""
    try:
        # 홈 디렉토리의 .cache 사용
        cache_path = CACHE_DIR
        cache_path.mkdir(parents=True, exist_ok=True)
        
        # 디렉토리 쓰기 권한 확인
        test_file = cache_path / ".test"
        try:
            test_file.touch()
            test_file.unlink()
            logger.info(f"캐시 디렉토리 준비 완료: {cache_path}")
            return True
        except Exception as e:
            logger.warning(f"캐시 디렉토리에 쓰기 권한이 없습니다: {cache_path} - {e}")
            return False
        
    except Exception as e:
        logger.error(f"캐시 디렉토리 생성 실패: {e}")
        return False

def get_cache_key(law_id: str, section: str = "all") -> str:
    """캐시 키 생성"""
    key_string = f"{law_id}_{section}"
    return hashlib.md5(key_string.encode()).hexdigest()

def get_cache_path(cache_key: str) -> Path:
    """캐시 파일 경로 생성"""
    return CACHE_DIR / f"{cache_key}.json"

def is_cache_valid(cache_path: Path) -> bool:
    """캐시 유효성 확인"""
    if not cache_path.exists():
        return False
    from datetime import timedelta
    file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    expiry_time = datetime.now() - timedelta(days=CACHE_DAYS)
    return file_time > expiry_time

def save_to_cache(cache_key: str, data: Any):
    """캐시에 데이터 저장"""
    try:
        if not ensure_cache_dir():
            logger.warning("캐시 디렉토리를 생성할 수 없어 캐시 저장을 건너뜁니다.")
            return
        
        cache_file = get_cache_path(cache_key)
        
        # 캐시 데이터 구조
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"캐시 저장 완료: {cache_key}")
    except Exception as e:
        logger.warning(f"캐시 저장 중 오류 (서비스는 계속됨): {e}")

def load_from_cache(cache_key: str) -> Optional[Any]:
    """캐시에서 데이터 로드"""
    try:
        cache_file = get_cache_path(cache_key)
        
        if not cache_file.exists():
            return None
            
        if not is_cache_valid(cache_file):
            cache_file.unlink()  # 만료된 캐시 삭제
            return None
            
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            logger.info(f"캐시 로드 완료: {cache_key}")
            return cache_data.get("data")
            
    except Exception as e:
        logger.warning(f"캐시 로드 중 오류 (API 호출로 대체됨): {e}")
        return None

# ===========================================
# 공통 유틸리티 함수들
# ===========================================

def extract_article_number(article_key: str) -> int:
    """조문 키에서 숫자 추출 (정렬용)"""
    try:
        import re
        match = re.search(r'제(\d+)조', article_key)
        return int(match.group(1)) if match else 999999
    except:
        return 999999

# 유틸리티 함수들은 utils/law_tools_utils.py로 이동됨

def _make_legislation_request(target: str, params: dict, is_detail: bool = False, timeout: int = 10, use_cache: bool = False) -> dict:
    """법제처 API 요청 공통 함수. use_cache=True이면 결과를 캐싱합니다."""
    cache_key = None
    if use_cache:
        params_for_key = {k: v for k, v in params.items() if k not in ("OC", "type")}
        cache_key = get_cache_key(
            f"{target}_{'detail' if is_detail else 'search'}_{json.dumps(params_for_key, sort_keys=True)}",
            "list"
        )
        cached = load_from_cache(cache_key)
        if cached and isinstance(cached, dict):
            return cached

    try:
        if target in ["lsHstInf", "lsStmd", "lawHst"]:
            timeout = max(timeout, 60)
        
        url = _generate_api_url(target, params, is_detail)
        
        # 디버깅: 법령약칭과 삭제된 법령 URL 로그
        if target in ["lsAbrv", "delHst"]:
            logger.info(f"{target} API 요청 URL: {url}")
        
        # 디버깅을 위한 로그 추가 (영문 법령의 경우)
        if target == "elaw":
            logger.info(f"영문법령 API 요청 URL: {url}")
        
        # 요청 실행 - Referer 헤더 필수 (일부 API에서 404 방지)
        headers = {"Referer": "https://open.law.go.kr/"}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # 응답 내용 확인 (영문 법령의 경우)
        if target == "elaw":
            logger.info(f"영문법령 응답 상태: {response.status_code}")
            logger.info(f"영문법령 Content-Type: {response.headers.get('Content-Type', 'None')}")
            if not response.text:
                logger.error("영문법령 API 빈 응답")
                return {"error": "영문법령 API가 빈 응답을 반환했습니다"}
        
        # HTML 오류 페이지 체크
        if response.headers.get('Content-Type', '').startswith('text/html'):
            if '사용자인증에 실패' in response.text or '페이지 접속에 실패' in response.text:
                raise ValueError("API 인증 실패 - OC(기관코드)를 확인하세요")
            elif target == "elaw":
                logger.error(f"영문법령 HTML 응답: {response.text[:500]}")
                raise ValueError("영문법령 API가 HTML을 반환했습니다. API 엔드포인트나 파라미터를 확인하세요.")
            else:
                raise ValueError("HTML 응답 반환 - JSON 응답이 예상됨")
        
        # JSON 파싱
        try:
            # 빈 응답 체크
            if not response.text or response.text.strip() == "":
                logger.warning(f"{target} API가 빈 응답을 반환했습니다")
                return {"error": f"{target} API가 빈 응답을 반환했습니다"}
            
            data = response.json()
        except json.JSONDecodeError as e:
            # 특정 타겟들에 대한 상세한 오류 처리
            if target in ["elaw", "ordinance", "ordinbyl"]:
                logger.error(f"{target} JSON 파싱 오류: {str(e)}")
                logger.error(f"응답 내용 (처음 500자): {response.text[:500]}")
                return {"error": f"{target} API JSON 파싱 실패: {str(e)}"}
            raise
        
        # 응답 구조 확인
        if not isinstance(data, dict):
            raise ValueError("Invalid JSON response structure")
        
        # 빈 응답 체크
        if not data:
            logger.warning(f"빈 응답 반환 - target: {target}, params: {params}")
            return {}
        
        # 오류 코드 체크
        if 'LawSearch' in data:
            # resultCode가 없는 API들: elaw, lsHstInf, lsJoHstInf 등
            targets_without_result_code = ["elaw", "lsHstInf", "lsJoHstInf"]
            
            if target not in targets_without_result_code:
                result_code = data['LawSearch'].get('resultCode')
                if result_code and result_code != '00':
                    result_msg = data['LawSearch'].get('resultMsg', '알 수 없는 오류')
                    raise ValueError(f"API 오류: {result_msg} (코드: {result_code})")
            else:
                # resultCode가 없는 API들은 totalCnt로 결과 유무 판단
                total_cnt = data['LawSearch'].get('totalCnt', '0')
                if str(total_cnt) == '0' and 'law' not in data['LawSearch']:
                    # 실제로 결과가 없는 경우만 처리 (빈 검색 결과는 오류가 아님)
                    pass
        
        if use_cache and cache_key and data:
            try:
                save_to_cache(cache_key, data)
            except Exception:
                pass
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API 요청 실패: {e}")
        raise
    except Exception as e:
        logger.error(f"데이터 처리 실패: {e}")
        raise

def _generate_api_url(target: str, params: dict, is_detail: bool = False) -> str:
    """올바른 법제처 API URL 생성"""
    try:
        # 기본 파라미터 설정
        base_params = {
            "OC": legislation_config.oc,
            "target": target  # 핵심: target 파라미터 반드시 포함
        }
        base_params.update(params)
        
        # JSON 응답 강제 사용
        base_params["type"] = "JSON"
        
        # 검색 API에서 query가 있는 경우 section 파라미터 추가 (성공한 curl 테스트 기반)
        if not is_detail and "query" in base_params and target == "law":
            if "section" not in base_params:
                base_params["section"] = "lawNm"  # 법령명 검색
        
        # URL 결정: 상세조회 vs 검색
        if is_detail and ("ID" in params or "MST" in params):
            # 상세조회: lawService.do 사용  
            base_url = legislation_config.service_base_url
        else:
            # 검색: lawSearch.do 사용
            base_url = legislation_config.search_base_url
    
        query_string = urlencode(base_params, safe=':', encoding='utf-8')
        return f"{base_url}?{query_string}"
        
    except Exception as e:
        logger.error(f"URL 생성 실패: {e}")
        return ""



def _format_law_service_history(data: dict, search_query: str) -> str:
    """lsJoHstInf API 전용 포맷팅 함수 - 조문별 변경 이력 (고도화)"""
    try:
        if 'LawService' not in data:
            return f"""'{search_query}'에 대한 조문 변경이력을 찾을 수 없습니다.

대안 방법:
1. **법령ID 확인**: search_law("법령명")로 정확한 법령ID 확인
2. **조번호 형식**: 6자리 형식 사용 (예: "000100"은 제1조)
3. **버전 비교**: compare_law_versions("법령명")로 전체 변경 내역 확인"""
        
        service_data = data['LawService']
        law_name = service_data.get('법령명한글', '법령명 없음')
        law_id = service_data.get('법령ID', '')
        total_count = int(service_data.get('totalCnt', 0))
        history_list = service_data.get('law', [])
        
        # 중복 제거 로직 추가
        if history_list:
            seen_entries = set()
            unique_history = []
            
            for item in history_list:
                # 중복 판별 키 생성 (법령일련번호 + 시행일자 + 제개정구분)
                law_info = item.get('법령정보', {})
                mst = law_info.get('법령일련번호', '')
                effective_date = law_info.get('시행일자', '')
                revision_type = law_info.get('제개정구분명', '')
                
                duplicate_key = f"{mst}_{effective_date}_{revision_type}"
                
                if duplicate_key not in seen_entries:
                    seen_entries.add(duplicate_key)
                    unique_history.append(item)
            
            history_list = unique_history
            total_count = len(unique_history)
        
        if not history_list:
            return f"""'{search_query}'에 대한 변경이력이 없습니다.

**데이터 부재 원인 분석**:
- 해당 조문이 제정 이후 변경되지 않았을 가능성
- 법령ID나 조번호 형식 오류 가능성
- 최근 제정된 법령으로 변경 이력이 짧을 가능성

**추천 대안**:
1. **전체 법령 버전 비교**: compare_law_versions("{law_name}")
2. **법령 연혁 검색**: search_law_history("{law_name}")
3. **조문 내용 확인**: get_law_article_by_key(mst="{law_id}", article_key="제N조")"""
        
        result = f"**{law_name} 조문 변경이력** (총 {total_count}건)\n"
        result += f"**검색조건:** {search_query}\n"
        result += f"🏛️ **법령ID:** {law_id}\n"
        result += "=" * 60 + "\n\n"
        
        # 시간순 정렬 (최신순)
        sorted_history = sorted(history_list, key=lambda x: x.get('조문정보', {}).get('조문변경일', ''), reverse=True)
        
        for i, item in enumerate(sorted_history, 1):
            조문정보 = item.get('조문정보', {})
            법령정보 = item.get('법령정보', {})
            
            # 변경사유와 변경일자
            변경사유 = 조문정보.get('변경사유', '')
            조문변경일 = 조문정보.get('조문변경일', '')
            조문번호 = 조문정보.get('조문번호', '')
            
            # 법령 정보
            법령일련번호 = 법령정보.get('법령일련번호', '')
            시행일자 = 법령정보.get('시행일자', '')
            제개정구분명 = 법령정보.get('제개정구분명', '')
            공포일자 = 법령정보.get('공포일자', '')
            소관부처명 = 법령정보.get('소관부처명', '')
            
            # 날짜 포맷팅
            formatted_변경일 = f"{조문변경일[:4]}-{조문변경일[4:6]}-{조문변경일[6:8]}" if len(조문변경일) == 8 else 조문변경일
            formatted_시행일 = f"{시행일자[:4]}-{시행일자[4:6]}-{시행일자[6:8]}" if len(시행일자) == 8 else 시행일자
            formatted_공포일 = f"{공포일자[:4]}-{공포일자[4:6]}-{공포일자[6:8]}" if len(공포일자) == 8 else 공포일자
            
            # 변경사유별 아이콘과 배경 설명 (연도별 맥락 고려)
            def get_context_by_period(year, change_type):
                """연도와 변경 유형에 따른 구체적 배경 제공"""
                year_int = int(year) if year.isdigit() else 2024
                
                if change_type == '제정':
                    if year_int <= 1960:
                        return '국가 기본 법제 체계 구축 시기'
                    elif year_int <= 1980:
                        return '경제 발전과 사회 변화에 따른 법제 정비'
                    elif year_int <= 2000:
                        return '민주화와 국제화에 따른 법제 현대화'
                    else:
                        return '디지털 시대와 글로벌 기준에 맞춘 새로운 법적 근거 마련'
                elif change_type == '전부개정':
                    if year_int <= 1980:
                        return '사회경제 구조 변화에 따른 법령 체계 전면 재편'
                    elif year_int <= 2000:
                        return '국제 기준 부합과 규제 합리화를 위한 전면 개정'
                    else:
                        return '4차 산업혁명과 디지털 전환에 따른 법체계 혁신'
                elif change_type == '일부개정':
                    if year_int >= 2020:
                        return 'COVID-19 대응 및 디지털 뉴딜 정책 반영'
                    elif year_int >= 2010:
                        return '규제 개선과 국민 편의 증진을 위한 부분 개정'
                    else:
                        return '법령 운용상 나타난 문제점 보완 및 개선'
                else:
                    return '법령 적용상 문제점 해결 또는 명확화'
            
            # 연도 추출
            change_year = 조문변경일[:4] if len(조문변경일) >= 4 else '2024'
            
            # 변경사유 상세 정보 (law_config.py에서 가져옴)
            change_info = CHANGE_DETAILS.get(변경사유, {'icon': '[변경]', 'desc': '조문 변경'})
            icon = change_info['icon']
            desc = change_info['desc']
            context = get_context_by_period(change_year, 변경사유)
            
            result += f"**{i}. {icon} {변경사유}** ({formatted_변경일})\n"
            result += f"   변경 배경: {context}\n"
            result += f"   시행일자: {formatted_시행일}\n"
            result += f"   제개정구분: {제개정구분명}\n"
            result += f"   공포일자: {formatted_공포일}\n"
            if 소관부처명:
                result += f"   소관부처: {소관부처명}\n"
            result += f"   법령일련번호: {법령일련번호}\n"
            
            # 조문 링크 정보
            조문링크 = 조문정보.get('조문링크', '')
            if 조문링크:
                result += f"   상세조회: get_law_article_by_key(mst=\"{법령일련번호}\", target=\"eflaw\", article_key=\"제{int(조문번호[:4])}조\")\n"
            
            result += "\n"
        
        # 정책 변화 패턴 분석
        result += "\n" + "=" * 60 + "\n"
        result += "**정책 변화 패턴 분석:**\n"
        
        # 변경 빈도 분석
        years = set()
        change_types: dict[str, int] = {}
        for item in sorted_history:
            조문정보 = item.get('조문정보', {})
            조문변경일 = 조문정보.get('조문변경일', '')
            변경사유 = 조문정보.get('변경사유', '')
            
            if len(조문변경일) >= 4:
                years.add(조문변경일[:4])
            if 변경사유:
                change_types[변경사유] = change_types.get(변경사유, 0) + 1
        
        if years:
            recent_years = sorted(years, reverse=True)[:3]
            result += f"- 활발한 개정 기간: {', '.join(recent_years)}년\n"
        
        if change_types:
            main_changes = sorted(change_types.items(), key=lambda x: x[1], reverse=True)[:2]
            result += f"- 주요 변경 유형: {', '.join([f'{k}({v}회)' for k, v in main_changes])}\n"
        
        # 컴플라이언스 영향 분석
        result += f"- 법무 영향: 조문 변경에 따른 업무 프로세스 재검토 필요\n"
        result += f"- 리스크 평가: 변경 내용의 소급 적용 및 경과 조치 확인 권장\n"
        
        # 실무 활용 가이드 
        result += f"\n**활용 가이드:**\n"
        result += f"• 특정 시점의 조문 내용: get_law_article_by_key(mst=\"법령일련번호\", target=\"eflaw\", article_key=\"조문번호\")\n"
        result += f"• 법령 전체 버전 비교: compare_law_versions(\"{law_name}\")\n"
        result += f"• 관련 해석**: search_law_interpretation(\"{law_name}\")\n"
        
        # 과도기 적용 안내
        result += "\n**과도기 적용 주의사항:**\n"
        result += "- 개정 법령의 소급 적용 여부 및 경과 조치 확인 필수\n"
        result += "- 시행일 이전 체결된 계약 등에 대한 적용 기준 검토\n"
        result += "- 관련 하위 법령(시행령, 시행규칙) 개정 일정 확인\n"
        
        return result
        
    except Exception as e:
        logger.error(f"조문 변경이력 포맷팅 중 오류: {e}")
        return f"'{search_query}' 조문 변경이력 포맷팅 중 오류가 발생했습니다: {str(e)}"

def _filter_law_history_results(data: dict, query: str) -> dict:
    """법령연혁 검색 결과를 키워드로 필터링"""
    try:
        if 'LawSearch' not in data or 'law' not in data['LawSearch']:
            return data
        
        laws = data['LawSearch']['law']
        if not isinstance(laws, list):
            return data
        
        # 검색어 정규화 (공백 제거, 소문자 변환)
        query_normalized = query.replace(" ", "").lower()
        
        # 금융·세무·개인정보보호 도메인 키워드 매핑 (law_config.py에서 가져옴)
        # 도메인별 확장 키워드 생성
        expanded_keywords = set([query_normalized])
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if domain in query_normalized:
                expanded_keywords.update(keywords)
        
        filtered_laws = []
        for law in laws:
            # 법령명 추출
            law_name = ""
            for key in ['법령명한글', '법령명', '제목', 'title', '명칭', 'name']:
                if key in law and law[key]:
                    law_name = str(law[key])
                    break
            
            law_name_normalized = law_name.replace(" ", "").lower()
            
            # 키워드 매칭 체크
            is_relevant = False
            for keyword in expanded_keywords:
                if keyword in law_name_normalized:
                    is_relevant = True
                    break
            
            # 추가 필터링 - 명백히 무관한 법령 제외 (law_config.py에서 가져옴)
            for pattern in IRRELEVANT_PATTERNS:
                if pattern in law_name:
                    is_relevant = False
                    break
            
            if is_relevant:
                filtered_laws.append(law)
        
        # 필터링된 결과로 데이터 업데이트
        if filtered_laws:
            data['LawSearch']['law'] = filtered_laws
            data['LawSearch']['totalCnt'] = len(filtered_laws)
        else:
            # 정확한 매칭이 없는 경우 원본 유지하되 경고 메시지 추가
            logger.warning(f"'{query}' 키워드로 관련 법령을 찾지 못했습니다. 전체 결과를 반환합니다.")
        
        return data
        
    except Exception as e:
        logger.error(f"법령연혁 필터링 중 오류: {e}")
        return data  # 오류 시 원본 데이터 반환

def _sort_english_law_results(data: dict, query: str) -> dict:
    """영문법령 검색 결과를 정확도 기반으로 정렬
    
    정렬 우선순위:
    1. 정확 일치 (CIVIL ACT == CIVIL ACT)
    2. 시작 일치 (CIVIL ACT로 시작)
    3. 포함 (CIVIL 포함)
    """
    try:
        if not data or 'LawSearch' not in data:
            return data
        
        search_data = data.get('LawSearch', {})
        laws = search_data.get('law', [])
        
        if not laws or not isinstance(laws, list):
            return data
        
        query_upper = query.upper().strip()
        
        def relevance_score(item):
            # 영문명 우선, 없으면 한글명
            name = (item.get('법령명영문') or item.get('법령명한글') or '').upper().strip()
            # HTML 태그 제거 (간단한 처리)
            import re
            name = re.sub(r'<[^>]+>', '', name)
            
            if name == query_upper:
                return 0  # 정확 일치 - 최우선
            if name.startswith(query_upper):
                return 1  # 시작 일치
            if query_upper in name:
                return 2  # 포함
            return 3  # 기타
        
        # 정렬
        sorted_laws = sorted(laws, key=relevance_score)
        
        # 정렬된 결과로 교체
        data['LawSearch']['law'] = sorted_laws
        
        return data
        
    except Exception as e:
        logger.warning(f"영문법령 검색 결과 정렬 중 오류: {e}")
        return data  # 오류 시 원본 반환

def _format_search_results(data: dict, target: str, search_query: str, max_results: int = 50) -> str:
    """검색 결과 포맷팅 공통 함수"""
    try:
        # target_data 초기화
        target_data = []
        
        # 특별한 루트 키를 사용하는 타겟들
        if target == "oldAndNew" and 'OldAndNewLawSearch' in data:
            search_data = data['OldAndNewLawSearch']
            target_data = search_data.get('oldAndNew', [])
        elif target == "thdCmp" and 'thdCmpLawSearch' in data:
            search_data = data['thdCmpLawSearch']
            target_data = search_data.get('thdCmp', [])
        elif target == "licbyl" and 'licBylSearch' in data:
            search_data = data['licBylSearch']
            target_data = search_data.get('licbyl', [])
        elif target == "trty" and 'TrtySearch' in data:
            search_data = data['TrtySearch'] 
            target_data = search_data.get('Trty', [])  # 주의: 'Trty' (대문자 T)
        elif target == "lsRlt" and 'lsRltSearch' in data:
            # 관련법령은 lsRltSearch 루트키를 사용
            search_data = data['lsRltSearch']
            law_item = search_data.get('법령', {})
            if isinstance(law_item, dict) and law_item:
                # 관련법령 데이터 추출
                related_laws = law_item.get('관련법령', [])
                if isinstance(related_laws, list):
                    target_data = related_laws
                else:
                    target_data = []
            else:
                target_data = []
        elif target == "lsRlt" and 'Law' in data:
            # 일부 검색어에서는 Law 키로 "데이터 없음" 메시지 반환
            law_data = data['Law']
            if isinstance(law_data, str) and "일치하는" in law_data:
                target_data = []
            else:
                target_data = []
        elif target == "ordinfd" and 'ordinFdList' in data:
            # 자치법규는 ordinFdList 루트키와 ordinFd 데이터키 사용
            search_data = data['ordinFdList']
            target_data = search_data.get('ordinFd', [])
        elif target == "ordin" and 'OrdinSearch' in data:
            # 자치법규는 OrdinSearch 루트키와 law 데이터키 사용
            search_data = data['OrdinSearch']
            target_data = search_data.get('law', [])
        elif target == "admrul" and 'AdmRulSearch' in data:
            # 행정규칙은 AdmRulSearch 루트키와 admrul 데이터키 사용
            search_data = data['AdmRulSearch']
            target_data = search_data.get('admrul', [])
        elif target == "admrulOldAndNew" and 'OldAndNewLawSearch' in data:
            # 행정규칙 신구법비교는 OldAndNewLawSearch 루트키와 oldAndNew 데이터키 사용
            search_data = data['OldAndNewLawSearch']
            target_data = search_data.get('oldAndNew', [])
            # 안전장치: 리스트가 아닌 경우 빈 리스트로 변환 (수정됨)
            if not isinstance(target_data, list):
                target_data = []
        elif target == "lnkOrd" and 'OrdinSearch' in data:
            # 법령-자치법규 연계는 OrdinSearch 루트키와 law 데이터키 사용
            search_data = data['OrdinSearch']
            target_data = search_data.get('law', [])
        # 판례/해석례 특별 루트 키 우선 처리
        elif target == "prec" and 'PrecSearch' in data:
            search_data = data['PrecSearch']
            target_data = search_data.get('prec', [])
        elif target == "expc" and 'Expc' in data:
            search_data = data['Expc']
            target_data = search_data.get('expc', [])
        elif target == "decc" and 'Decc' in data:
            search_data = data['Decc']
            target_data = search_data.get('decc', [])
        elif target == "couseLs" and '맞춤형분류' in data:
            # 맞춤형 법령은 맞춤형분류 루트키와 법령 데이터키 사용
            search_data = data['맞춤형분류']
            law_data = search_data.get('법령', {})
            # 단일 객체를 배열로 변환
            target_data = [law_data] if law_data else []
        # 다양한 응답 구조 처리 (특정 타겟들 제외)
        elif 'LawSearch' in data and target not in ["thdCmp", "licbyl", "trty", "lsRlt", "ordinfd", "ordin", "admrul", "admrulOldAndNew", "lnkOrd", "prec", "expc", "decc", "couseLs"]:
            # 기본 검색 구조
            if target == "elaw":
                # 영문 법령은 'law' 키 사용
                target_data = data['LawSearch'].get('law', [])
            elif target == "eflaw":
                # 시행일 법령도 'law' 키 사용
                target_data = data['LawSearch'].get('law', [])
            elif target == "eflawjosub":
                # 시행일 법령 조항호목은 'eflawjosub' 키 사용
                target_data = data['LawSearch'].get('eflawjosub', [])
            elif target == "lsHstInf":
                # 법령 변경이력은 'law' 키 사용
                target_data = data['LawSearch'].get('law', [])
            elif target == "lsHistory":
                # 법령 연혁은 HTML 파싱된 경우 'law' 키 사용
                target_data = data['LawSearch'].get('law', [])
            elif target == "lnkLs":
                # 법령-자치법규 연계는 'law' 키 사용
                target_data = data['LawSearch'].get('law', [])
            elif target == "lsAbrv":
                # 법령약칭도 'law' 키 사용
                target_data = data['LawSearch'].get('law', [])
            elif target == "delHst":
                # 삭제된 법령 데이터도 'law' 키 사용
                target_data = data['LawSearch'].get('law', [])

            elif target in ["ppc", "fsc", "ftc", "acr", "nlrc", "ecc", "sfc", "nhrck", "kcc", "iaciac", "oclt", "eiac"]:
                # 위원회 결정문 타겟들 처리
                target_data = data['LawSearch'].get(target, [])
                # 위원회 데이터는 종종 문자열로 반환되므로 안전하게 처리
                if isinstance(target_data, str):
                    if target_data.strip() == "" or "검색 결과가 없습니다" in target_data:
                        target_data = []
                    else:
                        logger.warning(f"위원회 타겟 {target}이 문자열로 반환됨: {target_data[:100]}...")
                        target_data = []
            elif target in ["detc"]:
                # 기타 판례 타겟들 처리
                target_data = data['LawSearch'].get(target, [])
                # 판례 데이터도 종종 문자열로 반환되므로 안전하게 처리
                if isinstance(target_data, str):
                    if target_data.strip() == "" or "검색 결과가 없습니다" in target_data:
                        target_data = []
                    else:
                        logger.warning(f"판례 타겟 {target}이 문자열로 반환됨: {target_data[:100]}...")
                        target_data = []
            else:
                target_data = data['LawSearch'].get(target, [])
        elif 'LawService' in data:
            # lawService.do 응답 구조
            service_data = data['LawService']
            if target == "lsJoHstInf":
                # 조문별 변경이력은 특별한 포맷팅 필요
                return _format_law_service_history(data, search_query)
            else:
                # 다른 서비스들
                target_data = service_data.get(target, [])
                if not isinstance(target_data, list):
                    target_data = [target_data] if target_data else []
        elif '법령' in data:
            # 상세조회 응답 구조 (lawService.do)
            target_data = data['법령']
            if isinstance(target_data, dict):
                # 조문 데이터가 있는 경우 추출
                if '조문' in target_data:
                    target_data = target_data['조문']
                else:
                    target_data = [target_data]
        elif 'lstrmAISearch' in data and target == "lstrmAI":
            search_data = data['lstrmAISearch']
            target_data = search_data.get('법령용어', [])
        elif target in data:
            target_data = data[target]
        else:
            keys = list(data.keys())
            if len(keys) == 1:
                target_data = data[keys[0]]
            else:
                target_data = []
        
        # 리스트가 아닌 경우 처리 (슬라이스 오류 방지)
        if not isinstance(target_data, list):
            if isinstance(target_data, dict):
                target_data = [target_data]
            elif isinstance(target_data, str):
                # 문자열인 경우 빈 리스트로 변환
                logger.warning(f"검색 결과가 문자열로 반환됨 (타겟: {target}): {target_data[:100]}...")
                target_data = []
            elif target_data is None:
                # None인 경우 빈 리스트로 변환
                logger.warning(f"검색 결과가 None으로 반환됨 (타겟: {target})")
                target_data = []
            else:
                # 기타 예상치 못한 타입들
                logger.warning(f"예상치 못한 타입으로 반환됨 (타겟: {target}): {type(target_data)}")
                target_data = []
        
        if not target_data:
            # 디버깅을 위한 상세 정보 추가
            if 'LawSearch' in data:
                available_keys = list(data['LawSearch'].keys())
                total_cnt = data['LawSearch'].get('totalCnt', 0)
                return f"'{search_query}'에 대한 검색 결과 파싱 실패.\n\n**디버깅 정보:**\n- 총 {total_cnt}건 검색됨\n- 사용 가능한 키: {available_keys}\n- 타겟: {target}\n\n**해결방법:** _format_search_results 함수의 타겟 처리 로직을 확인하세요."
            else:
                return f"'{search_query}'에 대한 검색 결과가 없습니다."
        
        # 안전한 슬라이싱을 위해 리스트인지 재확인
        if not isinstance(target_data, list):
            logger.error(f"슬라이싱 전 예상치 못한 타입: {type(target_data)} (값: {str(target_data)[:100]}...)")
            return f"'{search_query}' 검색 결과 처리 중 오류가 발생했습니다."
        
        # 법령 검색인 경우 정확 매치 우선 정렬
        if target in ["law", "elaw", "eflaw"]:
            query_normalized = search_query.replace(" ", "").lower()
            
            def sort_key(item):
                if not isinstance(item, dict):
                    return (3, "")
                title = item.get('법령명한글', '') or item.get('법령명', '') or item.get('법령명영문', '') or ''
                title_normalized = title.replace(" ", "").lower()
                # HTML 태그 제거 후 비교
                title_normalized = re.sub(r'<[^>]+>', '', title_normalized)
                
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
            
            target_data = sorted(target_data, key=sort_key)
        
        # 결과 개수 제한
        limited_data = target_data[:max_results]
        total_count = len(target_data)
        
        result = f"**'{search_query}' 검색 결과** (총 {total_count}건"
        if total_count > max_results:
            result += f", 상위 {max_results}건 표시"
        result += ")\n\n"
        
        for i, item in enumerate(limited_data, 1):
            result += f"**{i}. "
            
            # 제목 추출 (실제 API 응답 키 이름들 - 언더스코어 없음)
            title_keys = [
                '법령명한글', '법령명', '제목', 'title', '명칭', 'name',
                '현행법령명', '법령명국문', '국문법령명', 'lawNm', 'lawName',
                '법령명전체', '법령제목', 'lawTitle',
                '신구법명',  # 신구법비교용
                '법령약칭명',  # 법령약칭용
                '조약명한글', '조약명',  # 조약용
                '별표명', '서식명', '별표서식명',  # 별표서식용
                '삼단비교법령명', '3단비교법령명',  # 3단비교용
                '관련법령명', '기준법령명',  # 관련법령용
                '분류명',  # 자치법규용
                '행정규칙명',  # 행정규칙용
                '신구법명',  # 행정규칙 신구법비교용
                '자치법규명',  # 연계 자치법규용
                '안건명',  # 해석례용
                '사건명',  # 판례용
                '재판사건명'  # 판례용
            ]
            
            # 맞춤형 법령인 경우 기본정보에서 법령명 추출
            if target == "couseLs" and "기본정보" in item:
                basic_info = item["기본정보"]
                if isinstance(basic_info, dict):
                    title = basic_info.get("법령명한글", "") or basic_info.get("법령명", "")
            # 영문 법령인 경우 영문명을 먼저 표시
            elif target == "elaw" and '법령명영문' in item and item['법령명영문']:
                title = item['법령명영문']
                # HTML 태그 제거 (검색 결과에 <strong> 등이 포함될 수 있음)
                title = re.sub(r'<[^>]+>', '', title)
                # 한글명도 함께 표시
                if '법령명한글' in item and item['법령명한글']:
                    korean_title = re.sub(r'<[^>]+>', '', item['법령명한글'])
                    title += f" ({korean_title})"
            else:
                title = None
                for key in title_keys:
                    if key in item and item[key] and str(item[key]).strip():
                        title = str(item[key]).strip()
                        break
            
            # delHst 타겟은 법령명이 없으므로 별도 처리
            if not title and target == "delHst":
                구분 = item.get('구분명', '법령')
                일련번호 = item.get('일련번호', '')
                title = f"삭제된 {구분} (일련번호: {일련번호})"
            
            # 디버깅: 실제 키 이름들 확인
            if not title:
                # 응답에서 사용 가능한 모든 키 확인
                available_keys = list(item.keys()) if isinstance(item, dict) else []
                logger.info(f"사용 가능한 키들: {available_keys}")
                # 법령명으로 보이는 키들 찾기 (구분명 제외)
                potential_title_keys = [k for k in available_keys if ('법령' in str(k) or 'title' in str(k).lower()) and k != '구분명']
                if potential_title_keys:
                    title = str(item.get(potential_title_keys[0], '')).strip()
            
            if title:
                result += f"{title}**\n"
            else:
                result += "제목 없음**\n"
            
            # 상세 정보 추가 (실제 API 응답 키 이름들)
            detail_fields = {
                '법령ID': ['법령ID', 'ID', 'lawId', 'mstSeq'],  # 'id' 제외 (순번과 혼동 방지)
                '법령일련번호': ['법령일련번호', 'MST', 'mst', 'lawMst', '법령MST', '일련번호'],  # delHst용 일련번호 추가
                '신구법일련번호': ['신구법일련번호', '신구법MST'],  # 행정규칙 신구법비교용
                '행정규칙일련번호': ['행정규칙일련번호', '행정규칙MST'],  # 행정규칙용
                '조약일련번호': ['조약일련번호', '조약MST'],  # 조약용
                '자치법규일련번호': ['자치법규일련번호', '자치법규MST'],  # 자치법규용
                '법령약칭명': ['법령약칭명', '약칭명', 'abbreviation'],  # 법령 약칭용
                '공포일자': ['공포일자', 'date', 'announce_date', '공포일', 'promulgateDate', '공포년월일'],
                '시행일자': ['시행일자', 'ef_date', 'effective_date', '시행일', 'enforceDate', '시행년월일'], 
                '삭제일자': ['삭제일자'],  # delHst용
                '구분명': ['구분명'],  # delHst용
                '소관부처명': ['소관부처명', 'ministry', 'department', '소관부처', 'ministryNm', '주무부처'],
                '법령구분명': ['법령구분명', 'type', 'law_type', '법령구분', 'lawType', '법령종류'],
                '제개정구분명': ['제개정구분명', 'revision', '제개정구분', 'revisionType', '개정구분']
            }
            
            # 3단비교 전용 필드 추가
            if target == "thdCmp":
                detail_fields.update({
                    '인용조문수': ['인용조문수', '인용조문', 'citationCount', 'citation'],
                    '위임조문수': ['위임조문수', '위임조문', 'delegationCount', 'delegation'],
                    '상위법령명': ['상위법령명', '상위법령', 'upperLaw', 'parentLaw'],
                    '하위법령명': ['하위법령명', '하위법령', 'lowerLaw', 'childLaw'],
                    '비교일자': ['비교일자', '비교일', 'comparisonDate', 'compareDate']
                })
            
            for display_name, field_keys in detail_fields.items():
                value = None
                
                # 맞춤형 법령인 경우 기본정보에서 먼저 찾기
                if target == "couseLs" and "기본정보" in item:
                    basic_info = item["기본정보"]
                    if isinstance(basic_info, dict):
                        for key in field_keys:
                            if key in basic_info and basic_info[key]:
                                raw_value = basic_info[key]
                                break
                        else:
                            raw_value = None
                    else:
                        raw_value = None
                else:
                    # 일반적인 필드 검색
                    for key in field_keys:
                        if key in item and item[key]:
                            raw_value = item[key]
                            break
                    else:
                        raw_value = None
                
                if raw_value:
                    # 소관부처명 중복 처리
                    if display_name == '소관부처명':
                        if isinstance(raw_value, list):
                            # 리스트인 경우 중복 제거 후 첫 번째 항목만 사용
                            unique_values = list(dict.fromkeys(raw_value))  # 순서 유지하며 중복 제거
                            value = str(unique_values[0]).strip() if unique_values else ""
                        elif isinstance(raw_value, str):
                            # 문자열인 경우 콤마로 분할 후 중복 제거
                            if ',' in raw_value:
                                parts = [p.strip() for p in raw_value.split(',') if p.strip()]
                                unique_parts = list(dict.fromkeys(parts))  # 순서 유지하며 중복 제거
                                value = unique_parts[0] if unique_parts else ""
                            else:
                                value = str(raw_value).strip()
                        else:
                            value = str(raw_value).strip()
                    else:
                        # 다른 필드는 기존 방식대로
                        value = str(raw_value).strip()
                
                if value:
                    result += f"   {display_name}: {value}\n"
            
            # 법령일련번호와 법령ID 모두 있는 경우 상세조회 가이드 추가
            mst = None
            law_id = None
            
            # MST 찾기
            for key in ['법령일련번호', 'MST', 'mst', 'lawMst']:
                if key in item and item[key]:
                    mst = item[key]
                    break
            
            # 법령ID 찾기 (타겟별 특별 처리)
            if target == "lsRlt":
                # 관련법령은 관련법령ID 사용 (id는 순번일 뿐)
                for key in ['관련법령ID', '법령ID', 'ID', 'lawId']:
                    if key in item and item[key]:
                        law_id = item[key]
                        break
            else:
                # 기타 타겟은 기존 방식
                for key in ['법령ID', 'ID', 'id', 'lawId']:
                    if key in item and item[key]:
                        law_id = item[key]
                        break
            
            # 상세조회 가이드 (타겟별 특별 처리)
            if target == "oldAndNew":
                # 신구법비교는 신구법일련번호 사용 (id는 순번일 뿐)
                comparison_mst = None
                for key in ['신구법일련번호', '신구법MST', 'MST']:
                    if key in item and item[key]:
                        comparison_mst = item[key]
                        break
                if comparison_mst:
                    result += f"   상세조회: get_old_and_new_law_detail(mst=\"{comparison_mst}\")\n"
                else:
                    result += f"   참고: 상세조회용 일련번호를 확인할 수 없습니다.\n"
            elif target == "admrulOldAndNew":
                # 행정규칙 신구법비교는 신구법일련번호 사용
                comparison_id = None
                for key in ['신구법일련번호', '신구법MST']:
                    if key in item and item[key]:
                        comparison_id = item[key]
                        break
                if comparison_id:
                    result += f"   상세조회: get_administrative_rule_comparison_detail(comparison_id=\"{comparison_id}\")\n"
                else:
                    result += f"   상세조회: get_administrative_rule_comparison_detail(comparison_id=\"{law_id}\")\n"
            elif target == "admrul":
                # 행정규칙은 행정규칙일련번호 사용
                rule_id = None
                for key in ['행정규칙일련번호', '행정규칙MST']:
                    if key in item and item[key]:
                        rule_id = item[key]
                        break
                if rule_id:
                    result += f"   상세조회: get_administrative_rule_detail(rule_id=\"{rule_id}\")\n"
                else:
                    result += f"   상세조회: get_administrative_rule_detail(rule_id=\"{law_id}\")\n"
            elif target == "trty":
                # 조약은 조약일련번호 사용
                treaty_id = None
                for key in ['조약일련번호', '조약MST']:
                    if key in item and item[key]:
                        treaty_id = item[key]
                        break
                if treaty_id:
                    result += f"   상세조회: get_treaty_detail(treaty_id=\"{treaty_id}\")\n"
                else:
                    result += f"   상세조회: get_treaty_detail(treaty_id=\"{law_id}\")\n"
            elif target == "lnkOrd":
                # 연계 자치법규는 자치법규일련번호 사용
                ordinance_id = None
                for key in ['자치법규일련번호', '자치법규MST']:
                    if key in item and item[key]:
                        ordinance_id = item[key]
                        break
                if ordinance_id:
                    result += f"   상세조회: get_local_ordinance_detail(ordinance_id=\"{ordinance_id}\")\n"
                else:
                    result += f"   상세조회: get_local_ordinance_detail(ordinance_id=\"{law_id}\")\n"
            elif target == "delHst":
                # 삭제된 법령 데이터는 상세조회 불가 (삭제되었으므로)
                del_seq = item.get('일련번호', '')
                if del_seq:
                    result += f"   참고: 삭제된 법령입니다. 일련번호 {del_seq}로 복원 필요 시 법제처에 문의하세요.\n"
            elif target == "thdCmp":
                # 3단비교는 MST와 knd 파라미터 사용
                thd_mst = None
                
                # 다양한 필드명으로 MST 찾기
                mst_keys = [
                    '법령일련번호', 'MST', 'mst', 'lawMst', '법령MST', 
                    '일련번호', '법령일련번호(MST)', '법령일련번호MST',
                    'thdCmpMST', '3단비교MST', '비교법령일련번호',
                    '법령일련번호MST', '법령일련번호_MST'
                ]
                
                for key in mst_keys:
                    if key in item and item[key]:
                        thd_mst = str(item[key]).strip()
                        if thd_mst:
                            break
                
                # MST를 찾지 못한 경우 디버깅 정보 로깅 및 fallback 시도
                if not thd_mst:
                    available_keys = list(item.keys()) if isinstance(item, dict) else []
                    logger.debug(f"3단비교 MST 미발견. 사용 가능한 키: {available_keys}")
                    
                    # 법령ID가 있으면 법령ID로 MST 찾기 시도
                    if law_id:
                        thd_mst = _find_mst_from_law_id(law_id, item)
                    
                    # 여전히 MST를 찾지 못한 경우 법령명으로 검색 안내
                    if not thd_mst:
                        law_name = (item.get('법령명한글') or 
                                   item.get('법령명') or 
                                   item.get('삼단비교법령명') or
                                   item.get('3단비교법령명'))
                        if law_name:
                            # HTML 태그 제거
                            law_name_clean = clean_html_tags(law_name)
                            result += f"   참고: MST를 찾기 위해 법령명으로 검색 중...\n"
                            result += f"   → `search_law(\"{law_name_clean}\")`로 MST 확인 후 사용\n"
                        else:
                            result += f"   참고: 상세조회용 일련번호를 확인할 수 없습니다.\n"
                            if available_keys:
                                logger.warning(f"3단비교 MST 미발견. 항목 키: {available_keys[:10]}")
                
                if thd_mst:
                    result += f"   • 법령일련번호(MST): {thd_mst}\n"
                    result += f"   상세조회: get_three_way_comparison_detail(mst=\"{thd_mst}\", knd=1)  # 인용조문\n"
                    result += f"   상세조회: get_three_way_comparison_detail(mst=\"{thd_mst}\", knd=2)  # 위임조문\n"
            elif mst:
                result += f"   상세조회: get_law_detail(mst=\"{mst}\")\n"
            elif law_id:
                result += f"   상세조회: get_law_detail(law_id=\"{law_id}\")\n"
            
            # 맞춤형 법령인 경우 조문 정보 추가
            if target == "couseLs" and "조문" in item:
                articles = item["조문"]
                if "조문단위" in articles:
                    article_units = articles["조문단위"]
                    if article_units:
                        result += f"\n**관련 조문** ({len(article_units)}개):\n"
                        for article in article_units:
                            article_no = article.get('조문번호', '')
                            article_title = article.get('조문제목', '')
                            result += f"- 제{article_no}조: {article_title}\n"
            
            result += "\n"
        
        api_total = extract_total_count(data)
        result += format_result_guidance(api_total, search_query)
        
        return result
        
    except Exception as e:
        logger.error(f"결과 포맷팅 오류: {e}")
        return f"검색 결과 처리 중 오류가 발생했습니다: {str(e)}"

def _format_effective_law_articles(data: dict, law_id: str, article_no: Optional[str] = None, 
                                  paragraph_no: Optional[str] = None, item_no: Optional[str] = None, 
                                  subitem_no: Optional[str] = None, include_content: bool = True) -> str:
    """시행일법령 조항호목 전용 포맷팅 함수 - 실제 API 구조 기반"""
    try:
        result = f"**시행일 법령 조항호목 조회** (법령ID: {law_id})\n"
        result += "=" * 50 + "\n\n"
        
        # 시행일법령과 일반법령 모두 지원하는 구조 처리
        articles_data = []
        law_data = None
        
        # 1. 일반 법령 구조 ("법령" 키)
        if '법령' in data:
            law_data = data['법령']
            if '조문' in law_data:
                articles_section = law_data['조문']
                if isinstance(articles_section, dict) and '조문단위' in articles_section:
                    article_units = articles_section['조문단위']
                    if isinstance(article_units, list):
                        articles_data = article_units
                    else:
                        articles_data = [article_units]
        
        # 2. 시행일법령 구조 ("Law" 키)
        elif 'Law' in data:
            law_data_raw = data['Law']
            if isinstance(law_data_raw, dict):
                law_data = law_data_raw
                # 시행일법령의 조문 구조 탐색
                if '조문' in law_data:
                    articles_section = law_data['조문']
                    if isinstance(articles_section, dict) and '조문단위' in articles_section:
                        article_units = articles_section['조문단위']
                        if isinstance(article_units, list):
                            articles_data = article_units
                        else:
                            articles_data = [article_units]
                # 직접 조문 데이터가 있는지 확인
                elif '조문단위' in law_data:
                    article_units = law_data['조문단위']
                    if isinstance(article_units, list):
                        articles_data = article_units
                    else:
                        articles_data = [article_units]
            elif isinstance(law_data_raw, str):
                # 오류 메시지인 경우
                return f"**시행일법령 조회 결과**\n\n**법령ID**: {law_id}\n\n⚠️ **오류**: {law_data_raw}\n\n**대안 방법**: get_law_detail(mst=\"{law_id}\")"
        
        # 3. 기타 가능한 구조 탐색
        else:
            for key, value in data.items():
                if isinstance(value, dict) and ('조문' in value or '조문단위' in value):
                    law_data = value
                    if '조문' in value:
                        articles_section = value['조문']
                        if isinstance(articles_section, dict) and '조문단위' in articles_section:
                            article_units = articles_section['조문단위']
                            if isinstance(article_units, list):
                                articles_data = article_units
                            else:
                                articles_data = [article_units]
                    elif '조문단위' in value:
                        article_units = value['조문단위']
                        if isinstance(article_units, list):
                            articles_data = article_units
                        else:
                            articles_data = [article_units]
                    break
        
        if not articles_data:
            # 응답 구조 디버깅 정보 추가
            available_keys = list(data.keys()) if data else []
            law_keys = []
            if '법령' in data:
                law_keys = list(data['법령'].keys())
            
            return (f"조항호목 데이터를 찾을 수 없습니다.\n\n"
                   f"**검색 조건:**\n"
                   f"• 법령ID: {law_id}\n"
                   f"• 조번호: {article_no or '전체'}\n"
                   f"• 항번호: {paragraph_no or '전체'}\n"
                   f"• 호번호: {item_no or '전체'}\n"
                   f"• 목번호: {subitem_no or '전체'}\n\n"
                   f"**응답 구조 분석:**\n"
                   f"• 최상위 키: {available_keys}\n"
                   f"• 법령 키: {law_keys}\n\n"
                   f"**대안 방법:**\n"
                   f"- get_law_article_by_key(mst=\"{law_id}\", target=\"eflaw\", article_key=\"제{article_no or '1'}조\")")
        
        # 클라이언트 사이드 필터링
        filtered_articles = []
        for article in articles_data:
            # 조문여부가 "조문"인 것만 (전문 제외)
            if article.get('조문여부') != '조문':
                continue
                
            # 조번호 필터링
            if article_no and article.get('조문번호') != str(article_no).replace('제', '').replace('조', ''):
                continue
                
            # TODO: 항호목 필터링은 추후 구현 (현재 API에 해당 정보 없음)
            
            filtered_articles.append(article)
        
        # 검색 조건 표시
        result += f"**검색 조건:**\n"
        result += f"• 조번호: {article_no or '전체'}\n"
        result += f"• 항번호: {paragraph_no or '전체'}\n"
        result += f"• 호번호: {item_no or '전체'}\n"
        result += f"• 목번호: {subitem_no or '전체'}\n\n"
        
        if not filtered_articles:
            result += f"**조회 결과:** 조건에 맞는 조문이 없습니다.\n\n"
            
            # 사용 가능한 조문 번호들 표시
            available_articles = []
            for article in articles_data:
                if article.get('조문여부') == '조문':
                    no = article.get('조문번호', '')
                    title = article.get('조문제목', '')
                    if no:
                        available_articles.append(f"제{no}조: {title}")
            
            if available_articles:
                result += f"**사용 가능한 조문:**\n"
                for art in available_articles[:10]:  # 처음 10개만 표시
                    result += f"• {art}\n"
                if len(available_articles) > 10:
                    result += f"• ... 외 {len(available_articles) - 10}개\n"
        else:
            result += f"**조회 결과:** (총 {len(filtered_articles)}건)\n\n"
            
            for i, article in enumerate(filtered_articles, 1):
                article_no_str = article.get('조문번호', '?')
                article_title = article.get('조문제목', '')
                
                result += f"### 제{article_no_str}조"
                if article_title:
                    result += f"({article_title})"
                result += "\n\n"
                
                # 시행일자 정보
                if article.get('조문시행일자'):
                    date_str = article.get('조문시행일자')
                    # YYYYMMDD -> YYYY-MM-DD 변환
                    if len(date_str) == 8:
                        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        result += f"**시행일자:** {formatted_date}\n"
                
                # include_content=True인 경우 항/호/목 전체 내용 포함
                if include_content:
                    # format_article_body 함수로 항/호/목 포맷팅
                    article_body = format_article_body(article, include_details=True)
                    if article_body.strip():
                        result += f"\n{article_body}"
                else:
                    # include_content=False인 경우 인덱스만
                    if article.get('조문키'):
                        result += f"🔑 조문키: {article.get('조문키')}\n"
                    if article.get('조문변경여부'):
                        result += f"변경여부: {article.get('조문변경여부')}\n"
                
                result += "\n" + "-" * 40 + "\n\n"
        
        return result
    
    except Exception as e:
        logger.error(f"시행일법령 조항호목 포맷팅 중 오류: {e}")
        return f"조항호목 데이터 포맷팅 중 오류가 발생했습니다: {str(e)}"

def _safe_format_law_detail(data: dict, search_term: str, url: str) -> str:
    """법령 상세내용 안전 포맷팅"""
    try:
        result = f"**법령 상세 정보** (검색어: {search_term})\n"
        result += "=" * 50 + "\n\n"
        
        # 데이터 구조 탐지 및 처리
        law_info = None
        
        # target을 포함한 구조에서 law 데이터 찾기
        if 'LawSearch' in data and 'law' in data['LawSearch']:
            law_data = data['LawSearch']['law']
            if isinstance(law_data, list) and law_data:
                law_info = law_data[0]
            elif isinstance(law_data, dict):
                law_info = law_data
        
        # 직접 law 키 확인
        elif 'law' in data:
            law_data = data['law']
            if isinstance(law_data, list) and law_data:
                law_info = law_data[0]
            elif isinstance(law_data, dict):
                law_info = law_data
        
        # 법령 키 확인 (상세조회 API 응답)
        elif '법령' in data:
            law_data = data['법령']
            if isinstance(law_data, dict):
                law_info = law_data
        
        # 단일 객체 구조 확인
        elif len(data) == 1:
            key = list(data.keys())[0]
            law_data = data[key]
            if isinstance(law_data, list) and law_data:
                law_info = law_data[0]
            elif isinstance(law_data, dict):
                law_info = law_data
        
        if not law_info:
            return f"법령 정보를 찾을 수 없습니다.\n\nAPI URL: {url}"
        
        # 기본 정보 출력 (더 많은 키 이름 추가)
        basic_fields = {
            '법령명': [
                '법령명_한글', '법령명한글', '법령명', '제목', 'title', '명칭', 'name',
                '현행법령명', '법령명_국문', '국문법령명', 'lawNm', 'lawName', '법령명전체'
            ],
            '법령ID': ['법령ID', 'ID', 'id', 'lawId', 'mstSeq'],
            '공포일자': ['공포일자', 'announce_date', 'date', '공포일', 'promulgateDate', '공포년월일'],
            '시행일자': ['시행일자', 'effective_date', 'ef_date', '시행일', 'enforceDate', '시행년월일'],
            '소관부처': ['소관부처명', 'ministry', 'department', '소관부처', 'ministryNm', '주무부처'],
            '법령구분': ['법령구분명', 'law_type', 'type', '법령구분', 'lawType', '법령종류']
        }
        
        for field_name, field_keys in basic_fields.items():
            value = None
            
            # 기본정보 키에서 찾기 (상세조회 API 응답)
            if '기본정보' in law_info and isinstance(law_info['기본정보'], dict):
                basic_info = law_info['기본정보']
                for key in field_keys:
                    if key in basic_info and basic_info[key]:
                        value = basic_info[key]
                        # 소관부처의 경우 content 추출
                        if isinstance(value, dict) and 'content' in value:
                            value = value['content']
                        break
            
            # 직접 law_info에서 찾기 (검색 API 응답)
            if not value:
                for key in field_keys:
                    if key in law_info and law_info[key]:
                        value = law_info[key]
                        break
            
            if value:
                result += f"**{field_name}**: {value}\n"
        
        result += "\n" + "=" * 50 + "\n\n"
        
        # 조문 내용 출력 (구조화된 조문 처리)
        content = None
        
        # 상세조회 API 응답의 조문단위 처리
        if '조문' in law_info and isinstance(law_info['조문'], dict):
            article_data = law_info['조문']
            if '조문단위' in article_data and isinstance(article_data['조문단위'], list):
                articles = article_data['조문단위']
                content = str(articles)  # 전체 조문 데이터
        
        # 기존 필드에서 조문 내용 찾기
        if not content:
            content_fields = [
                '조문', 'content', 'text', '내용', 'body', '본문', '법령내용', 
                'lawCn', 'lawContent', '조문내용', '전문', 'fullText',
                '법령본문', '조문본문', 'articleContent'
            ]
            
            for field in content_fields:
                if field in law_info and law_info[field] and str(law_info[field]).strip():
                    content = str(law_info[field]).strip()
                    break
        
        # 디버깅: 조문 내용을 찾을 수 없는 경우 사용 가능한 키들 로그
        if not content and isinstance(law_info, dict):
            available_keys = list(law_info.keys())
            logger.info(f"조문 내용을 찾을 수 없음. 사용 가능한 키들: {available_keys}")
            # 내용으로 보이는 키들 찾기
            potential_content_keys = [k for k in available_keys if '내용' in str(k) or '조문' in str(k) or 'content' in str(k).lower()]
            if potential_content_keys:
                content = str(law_info.get(potential_content_keys[0], '')).strip()
        
        if content:
            result += "**조문 내용:**\n\n"
            result += str(content)
            result += "\n\n"
        else:
            result += "조문 내용을 찾을 수 없습니다.\n\n"
        
        # 추가 정보 (상세조회 API 응답 구조 처리)
        additional_fields = {
            '부칙': ['부칙', 'appendix'],
            '개정문': ['개정문', 'revision_text'],
            '제개정이유': ['제개정이유', 'enactment_reason'],
            '주요내용': ['주요내용', 'main_content']
        }
        
        for field_name, field_keys in additional_fields.items():
            value = None
            
            # 직접 키에서 찾기 (상세조회 API 응답)
            for key in field_keys:
                if key in law_info and law_info[key]:
                    value = law_info[key]
                    break
            
            if value:
                result += f"**{field_name}:**\n{value}\n\n"
        
        result += "=" * 50 + "\n"
        result += f"**API URL**: {url}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"법령 상세내용 포맷팅 오류: {e}")
        return f"법령 상세내용 처리 중 오류: {str(e)}\n\nAPI URL: {url}"

# ===========================================
# 법령 관련 통합 도구들 (29개)
# ===========================================

@mcp.tool(
    name="search_law",
    description="""법령을 검색합니다. 가장 기본적인 법령 검색 도구입니다.

[중요] query 입력 가이드:
- 올바른 예: "은행법", "소득세법", "개인정보 보호법", "금융"
- 잘못된 예: "은행법에서 대출 규제 조항을 찾아줘" (문장 형태 금지)
- 키워드만 입력하세요. 문장을 입력하면 검색이 실패합니다.

매개변수:
- query: 법령명 또는 키워드만 입력 (문장 금지)
- search: 1=법령명 검색(기본), 2=본문 검색
- display: 결과 개수 (기본 20, 최대 100)

반환정보: 법령명, MST(법령일련번호), 공포일자, 시행일자

사용 예시:
- search_law("은행법")
- search_law("개인정보")
- search_law("세금", search=2)  # 본문 검색""",
    tags={"법령검색", "법률", "대통령령", "시행령", "현행법"}
)
def search_law(
    query: Annotated[Optional[str], "검색어 (법령명)"] = None,
    search: Annotated[int, "검색범위 (1=법령명, 2=본문)"] = 1,
    display: Annotated[int, "결과 개수 (최대 100)"] = 20,
    page: Annotated[int, "페이지 번호"] = 1,
    sort: Annotated[Optional[str], "정렬 (lasc, ldes, dasc, ddes, nasc, ndes, efasc, efdes)"] = None,
    date: Annotated[Optional[str], "공포일자 (YYYYMMDD)"] = None,
    ef_date_range: Annotated[Optional[str], "시행일자 범위 (20090101~20090130)"] = None,
    announce_date_range: Annotated[Optional[str], "공포일자 범위 (20090101~20090130)"] = None,
    announce_no_range: Annotated[Optional[str], "공포번호 범위 (306~400)"] = None,
    revision_type: Annotated[Optional[str], "제개정 종류 (300201, 300202, 300203 등)"] = None,
    announce_no: Annotated[Optional[str], "공포번호"] = None,
    ministry_code: Annotated[Optional[str], "소관부처 코드"] = None,
    law_type_code: Annotated[Optional[str], "법령종류 코드"] = None,
    law_chapter: Annotated[Optional[str], "법령분류 (01~44)"] = None,
    alphabetical: Annotated[Optional[str], "사전식 검색 (ga, na, da, ra, ma 등)"] = None
) -> TextContent:
    """법령 목록 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어 (법령명) - 필수 입력
        search: 검색범위 (1=법령명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=법령오름차순, ldes=법령내림차순, dasc=공포일자오름차순, ddes=공포일자내림차순, nasc=공포번호오름차순, ndes=공포번호내림차순, efasc=시행일자오름차순, efdes=시행일자내림차순)
        date: 공포일자 (YYYYMMDD)
        ef_date_range: 시행일자 범위 (20090101~20090130)
        announce_date_range: 공포일자 범위 (20090101~20090130)
        announce_no_range: 공포번호 범위 (306~400)
        revision_type: 제개정 종류 (300201=제정, 300202=일부개정, 300203=전부개정, 300204=폐지, 300205=폐지제정, 300206=일괄개정, 300207=일괄폐지, 300209=타법개정, 300210=타법폐지, 300208=기타)
        announce_no: 공포번호
        ministry_code: 소관부처 코드
        law_type_code: 법령종류 코드
        law_chapter: 법령분류 (01=제1편...44=제44편)
        alphabetical: 사전식 검색 (ga,na,da,ra,ma,ba,sa,a,ja,cha,ka,ta,pa,ha)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요. 예: '은행법', '소득세법', '개인정보보호법' 등")
    
    search_query = query.strip()
    
    # 일반 키워드를 구체적인 법령명으로 매핑 (law_config.py에서 가져옴)
    # 일반 키워드인 경우 구체적인 법령들로 검색
    if search_query.lower() in KEYWORD_TO_LAW_MAPPING:
        suggested_laws = KEYWORD_TO_LAW_MAPPING[search_query.lower()]
        results = []
        
        for law_name in suggested_laws:
            params = {
                "OC": legislation_config.oc,
                "type": "JSON",
                "target": "law",
                "query": law_name,
                "search": 1,
                "display": 5
            }
            
            try:
                data = _make_legislation_request("law", params, is_detail=False, use_cache=True)
                if 'LawSearch' in data and 'law' in data['LawSearch']:
                    laws = data['LawSearch']['law']
                    if isinstance(laws, list):
                        results.extend(laws[:3])  # 각 법령당 최대 3개
            except:
                continue
        
        if results:
            # 수동으로 결과 포맷팅
            formatted = f"**'{search_query}' 관련 주요 법령** (총 {len(results)}건)\n\n"
            for i, law in enumerate(results[:display], 1):
                formatted += f"**{i}. {law.get('법령명한글', '')}**\n"
                formatted += f"   법령ID: {law.get('법령ID', '')}\n"
                formatted += f"   법령일련번호: {law.get('법령일련번호', '')}\n"
                formatted += f"   공포일자: {law.get('공포일자', '')}\n"
                formatted += f"   시행일자: {law.get('시행일자', '')}\n"
                formatted += f"   소관부처명: {law.get('소관부처명', '')}\n"
                
                mst = law.get('법령일련번호')
                if mst:
                    formatted += f"   상세조회: get_law_detail(mst=\"{mst}\")\n"
                formatted += "\n"
            
            formatted += f"\n팁: 더 정확한 검색을 위해 구체적인 법령명을 사용하세요."
            return TextContent(type="text", text=formatted)
    
    try:
        oc = legislation_config.oc
        if not oc:
            raise ValueError("OC(기관코드)가 설정되지 않았습니다.")
        
        # 검색 전략 개선: 키워드가 "법"으로 끝나지 않으면 자동으로 추가
        original_query = search_query
        search_attempts = []

        # 1차 시도용 캐시 키 (동일 파라미터 재호출 시 캐시 히트)
        params_for_key = {
            "query": original_query,
            "display": min(display, 100),
            "page": page,
            "search": 1,
        }
        optional_for_key = {
            "sort": sort, "date": date, "efDateRange": ef_date_range,
            "announceDateRange": announce_date_range, "announceNoRange": announce_no_range,
            "revisionType": revision_type, "announceNo": announce_no,
            "ministryCode": ministry_code, "lawTypeCode": law_type_code,
            "lawChapter": law_chapter, "alphabetical": alphabetical,
        }
        for k, v in optional_for_key.items():
            if v is not None:
                params_for_key[k] = v
        cache_key = get_cache_key("law_search_" + json.dumps(params_for_key, sort_keys=True), "list")
        cached_data = load_from_cache(cache_key)
        if cached_data and isinstance(cached_data, dict) and "LawSearch" in cached_data:
            formatted_result = format_search_law_results(cached_data, original_query)
            return TextContent(type="text", text=formatted_result)
        
        # 1차 시도: 원본 쿼리
        search_attempts.append((original_query, 1))  # 법령명 검색
        
        # 2차 시도: "법"이 없으면 추가
        if not original_query.endswith("법"):
            search_attempts.append((original_query + "법", 1))
        
        # 3차 시도: 공백 제거
        cleaned_query = original_query.replace(" ", "")
        if cleaned_query != original_query:
            search_attempts.append((cleaned_query, 1))
            if not cleaned_query.endswith("법") and cleaned_query + "법" not in [q[0] for q in search_attempts]:
                search_attempts.append((cleaned_query + "법", 1))
        
        best_result = None
        best_count = 0
        
        for attempt_query, search_mode in search_attempts:
            # 기본 파라미터 설정
            base_params = {"OC": oc, "type": "JSON", "target": "law"}
            
            # 검색 파라미터 추가
            params = base_params.copy()
            params.update({
                "query": attempt_query,
                "search": search_mode,
                "display": min(display, 100),
                "page": page
            })
            
            # 선택적 파라미터 추가
            optional_params = {
                "sort": sort, "date": date, "efDateRange": ef_date_range,
                "announceDateRange": announce_date_range, "announceNoRange": announce_no_range,
                "revisionType": revision_type, "announceNo": announce_no,
                "ministryCode": ministry_code, "lawTypeCode": law_type_code,
                "lawChapter": law_chapter, "alphabetical": alphabetical
            }
            
            for key, value in optional_params.items():
                if value is not None:
                    params[key] = value
            
            try:
                # API 요청 - 현행법령 검색
                data = _make_legislation_request("law", params, is_detail=False, use_cache=True)
                
                # 1차 시도(원본 쿼리 법령명 검색) 결과 캐시 저장
                if attempt_query == original_query and search_mode == 1 and data:
                    try:
                        save_to_cache(cache_key, data)
                    except Exception as cache_err:
                        logger.debug("search_law cache save skip: %s", cache_err)
                
                # 결과 확인
                if 'LawSearch' in data and 'law' in data['LawSearch']:
                    results = data['LawSearch']['law']
                    total_count = int(data['LawSearch'].get('totalCnt', 0))
                    
                    # 정확한 매칭 검사
                    if isinstance(results, list) and len(results) > 0:
                        # 첫 번째 결과가 정확히 일치하는지 확인
                        first_law = results[0]
                        law_name = first_law.get('법령명한글', '')
                        
                        # 정확한 매칭이면 즉시 반환
                        if law_name and (
                            original_query in law_name or 
                            attempt_query in law_name or
                            law_name.replace(" ", "") == attempt_query.replace(" ", "")
                        ):
                            formatted_result = format_search_law_results(data, original_query)
                            
                            # 검색어가 다른 경우 안내 추가
                            if attempt_query != original_query:
                                formatted_result = f"['{original_query}' → '{attempt_query}'로 검색]\n\n" + formatted_result
                            
                            return TextContent(type="text", text=formatted_result)
                    
                    # 최선의 결과 저장 (결과 수가 적으면서 0이 아닌 경우)
                    if 0 < total_count < 20 and (best_result is None or total_count < best_count):
                        best_result = (attempt_query, data)
                        best_count = total_count
                        
            except Exception as e:
                logger.debug(f"검색 시도 실패 ({attempt_query}): {e}")
                continue
        
        # 최선의 결과가 있으면 반환
        if best_result:
            attempt_query, data = best_result
            result = _format_search_results(data, "law", original_query)
            if attempt_query != original_query:
                result = f"['{original_query}' → '{attempt_query}'로 검색]\n\n" + result
            return TextContent(type="text", text=result)
        
        # 모든 시도가 실패한 경우 본문검색으로 최종 시도
        if search == 1:
            params["search"] = 2
            params["query"] = original_query
            
            try:
                data = _make_legislation_request("law", params, is_detail=False, use_cache=True)
                result = _format_search_results(data, "law", original_query)
                
                # 본문검색임을 명시
                result = f"[법령명 검색 결과 없음 → 본문검색 결과]\n\n" + result
                return TextContent(type="text", text=result)
            except:
                pass
        
                    # 실패
        return TextContent(type="text", text=f"'{original_query}'에 대한 검색 결과가 없습니다.\n\n"
                                            f"검색 팁:\n"
                                            f"- 정확한 법령명을 입력하세요 (예: '개인정보보호법')\n"
                                            f"- 법령명 끝에 '법', '령', '규칙' 등을 포함하세요\n"
                                            f"- 띄어쓰기를 확인하세요")
        
    except Exception as e:
        logger.error(f"법령 검색 중 오류: {e}")
        return TextContent(type="text", text=f"법령 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(
    name="search_english_law", 
    description="""영문 법령을 검색합니다.

[중요] query 입력 가이드:
- 올바른 예: "Banking Act", "Civil", "Tax"
- 잘못된 예: "Find the English version of banking law" (문장 금지)
- 영문 키워드만 입력하세요.

매개변수:
- query: 영문 법령명 또는 키워드만 (문장 금지)
- display: 결과 개수 (기본 20)

반환정보: 영문법령명, 한글법령명, MST

사용 예시:
- search_english_law("Banking Act")
- search_english_law("Tax")
- search_english_law("Personal Information")""",
    tags={"영문법령", "English", "번역"}
)
def search_english_law(
    query: Annotated[Optional[str], "검색어 (영문 법령명)"] = None,
    search: Annotated[int, "검색범위 (1=법령명, 2=본문)"] = 1,
    display: Annotated[int, "결과 개수 (최대 100)"] = 20,
    page: Annotated[int, "페이지 번호"] = 1,
    sort: Annotated[Optional[str], "정렬 (lasc, ldes, dasc, ddes)"] = None,
    law_type: Annotated[Optional[str], "법령종류 (L=법률, P=대통령령, M=총리령부령)"] = None,
    promulgate_date: Annotated[Optional[str], "공포일자 (YYYYMMDD)"] = None,
    enforce_date: Annotated[Optional[str], "시행일자 (YYYYMMDD)"] = None
) -> TextContent:
    """영문법령 검색
    
    Args:
        query: 검색어 (영문 법령명)
        search: 검색범위 (1=법령명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        sort: 정렬 (lasc=법령오름차순, ldes=법령내림차순, dasc=공포일자오름차순, ddes=공포일자내림차순)
        law_type: 법령종류 (L=법률, P=대통령령, M=총리령부령)
        promulgate_date: 공포일자 (YYYYMMDD)
        enforce_date: 시행일자 (YYYYMMDD)
    """
    if not query or not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요. 예: 'Civil Act', 'Commercial Act' 등")
    
    search_query = query.strip()

    params = {
        "OC": legislation_config.oc,
        "type": "JSON",
        "target": "elaw",
        "query": search_query,
        "search": search,
        "display": min(display, 100),
        "page": page
    }

    optional_params = {
        "sort": sort,
        "lawType": law_type,
        "promulgateDate": promulgate_date,
        "enforceDate": enforce_date
    }
    for key, value in optional_params.items():
        if value is not None:
            params[key] = value

    try:
        data = _make_legislation_request("elaw", params, is_detail=False, use_cache=True)
        data = _sort_english_law_results(data, search_query)
        result = _format_search_results(data, "elaw", search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        logger.error(f"영문법령 검색 중 오류: {e}")
        return TextContent(type="text", text=f"영문법령 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_english_law_detail", description="""영문 법령의 상세 내용을 조회합니다.

언제 사용:
- 영문 법령의 전체 조문과 상세 내용을 확인할 때
- search_english_law로 MST를 확보한 후 상세 조회할 때

매개변수:
- mst: 법령일련번호(MST) (필수) - 영문법령 검색 결과에서 'MST' 필드값 사용
- max_articles: 최대 표시 조문 수 (기본값: 50, 전체 조회 시 0)
  - 대용량 법령(민법 1000+조)은 50개씩 나눠서 조회 권장
  - max_articles=0 설정 시 전체 조문 조회 (시간 오래 걸릴 수 있음)

⚠️ 대용량 법령 안내:
- 민법(246569), 상법(267558) 등 조문이 많은 법령은 전체 조회에 60초 이상 소요
- 특정 키워드 검색: search_english_law_articles_semantic(mst="MST", query="키워드")
- 일부 조문만 조회: get_english_law_detail(mst="MST", max_articles=50)

권장 워크플로우:
1단계: search_english_law("Civil Act") → MST 확인  
2단계: get_english_law_detail(mst="246569", max_articles=50) → 처음 50개 조문 조회

사용 예시:
- get_english_law_detail(mst="204485")  # 소규모 법령 전체 조회
- get_english_law_detail(mst="246569", max_articles=50)  # 민법 처음 50개 조문""")
def get_english_law_detail(
    mst: Annotated[Union[str, int], "법령일련번호(MST)"] = "",
    max_articles: Annotated[int, "최대 표시 조문 수 (0=전체)"] = 50
) -> TextContent:
    """영문법령 상세내용 조회 (캐시 지원, 확장 타임아웃)"""
    import requests
    
    if not mst:
        return TextContent(type="text", text="법령일련번호(MST)를 입력해주세요.")
    
    mst_str = str(mst)
    
    try:
        # 1. 캐시 확인
        cache_key = get_cache_key(f"elaw_{mst_str}", "full")
        cached_data = load_from_cache(cache_key)
        
        if cached_data:
            logger.info(f"캐시에서 영문법령 조회: MST={mst_str}")
            result = _format_english_law_detail(cached_data, mst_str, max_articles)
            return TextContent(type="text", text=result)
        
        # 2. API 요청 (확장된 타임아웃으로 직접 호출)
        logger.info(f"API에서 영문법령 조회: MST={mst_str}")
        data = _fetch_english_law_with_extended_timeout(mst_str)
        
        if data:
            # 캐시 저장
            save_to_cache(cache_key, data)
            logger.info(f"영문법령 캐시 저장: MST={mst_str}")
            
            # 포맷팅 및 반환
            result = _format_english_law_detail(data, mst_str, max_articles)
            return TextContent(type="text", text=result)
        else:
            return TextContent(
                type="text", 
                text=f"영문 법령을 찾을 수 없습니다. (MST: {mst_str})"
            )
        
    except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
        logger.warning(f"영문법령 상세조회 타임아웃: MST={mst_str}, {e}")
        timeout_msg = f"**영문 법령 조회 시간 초과** (MST: {mst_str})\n\n"
        timeout_msg += "이 법령은 조문이 매우 많아 전체 조회에 시간이 오래 걸립니다.\n\n"
        timeout_msg += "**대안 방법:**\n"
        timeout_msg += f"1. 특정 키워드로 조문 검색:\n"
        timeout_msg += f"   `search_english_law_articles_semantic(mst=\"{mst_str}\", query=\"키워드\")`\n\n"
        timeout_msg += f"2. 일부 조문만 조회 (재시도):\n"
        timeout_msg += f"   `get_english_law_detail(mst=\"{mst_str}\", max_articles=30)`"
        return TextContent(type="text", text=timeout_msg)
        
    except Exception as e:
        logger.error(f"영문법령 상세조회 중 오류: {e}")
        error_msg = str(e)
        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            timeout_msg = f"**영문 법령 조회 시간 초과** (MST: {mst_str})\n\n"
            timeout_msg += f"**대안:** `search_english_law_articles_semantic(mst=\"{mst_str}\", query=\"키워드\")`"
            return TextContent(type="text", text=timeout_msg)
        return TextContent(type="text", text=f"영문법령 상세조회 중 오류가 발생했습니다: {error_msg}")


def _fetch_english_law_with_extended_timeout(mst: str, timeout: int = 90) -> dict:
    """확장된 타임아웃으로 영문 법령 조회
    
    대용량 법령(민법 등)도 조회할 수 있도록 90초 타임아웃 적용
    """
    import requests
    
    url = f"{legislation_config.service_base_url}"
    params = {
        "OC": legislation_config.oc,
        "type": "JSON",
        "target": "elaw",
        "MST": mst
    }
    
    try:
        response = requests.get(
            url, 
            params=params, 
            timeout=timeout,
            headers={"Referer": "http://www.law.go.kr"}
        )
        response.raise_for_status()
        
        # JSON 파싱
        data = response.json()
        return data
        
    except requests.exceptions.Timeout:
        logger.warning(f"영문법령 확장 타임아웃도 초과: MST={mst}, timeout={timeout}s")
        raise
    except Exception as e:
        logger.error(f"영문법령 조회 오류: {e}")
        raise

def _format_english_law_detail(data: dict, law_id: str, max_articles: int = 50) -> str:
    """영문 법령 상세 정보 포맷팅
    
    Args:
        data: API 응답 데이터
        law_id: 법령 MST
        max_articles: 최대 표시 조문 수 (0=전체)
    """
    try:
        if not data or 'Law' not in data:
            return f"법령 정보를 찾을 수 없습니다. (MST: {law_id})"
        
        law_data = data['Law']
        
        # 기본 정보 추출
        result = "**영문 법령 상세 내용**\n"
        result += "=" * 50 + "\n\n"
        
        # 1. 먼저 JoSection(실제 조문) 확인
        jo_section = law_data.get('JoSection', {})
        main_articles = []
        
        if jo_section and 'Jo' in jo_section:
            jo_data = jo_section['Jo']
            if isinstance(jo_data, list):
                # 실제 조문만 필터링 (joYn='Y'인 것들)
                main_articles = [jo for jo in jo_data if jo.get('joYn') == 'Y']
            elif isinstance(jo_data, dict):
                if jo_data.get('joYn') == 'Y':
                    main_articles = [jo_data]
        
        # 2. JoSection이 없거나 비어있으면 ArSection(부칙) 확인
        addenda_articles = []
        ar_section = law_data.get('ArSection', {})
        if ar_section and 'Ar' in ar_section:
            ar_data = ar_section['Ar']
            if isinstance(ar_data, dict):
                addenda_articles = [ar_data]
            elif isinstance(ar_data, list):
                addenda_articles = ar_data
        
        # 3. 조문 표시 (max_articles 적용)
        if main_articles:
            total_count = len(main_articles)
            # max_articles=0이면 전체, 아니면 지정된 개수
            display_count = total_count if max_articles == 0 else min(max_articles, total_count)
            
            result += f"**법령 조문** (총 {total_count}개 중 {display_count}개 표시)\n\n"
            
            for i, article in enumerate(main_articles[:display_count], 1):
                article_content = article.get('joCts', '')
                article_no = article.get('joNo', str(i))
                
                if article_content:
                    # 내용이 너무 길면 앞부분만 표시
                    content_limit = 1200 if max_articles <= 20 else 600  # 적게 조회하면 더 자세히
                    preview = article_content[:content_limit]
                    if len(article_content) > content_limit:
                        preview += "..."
                    
                    result += f"### Article {article_no}\n"
                    result += f"{preview}\n\n"
            
            if total_count > display_count:
                remaining = total_count - display_count
                result += f"\n---\n**{remaining}개 조문 생략됨**\n"
                result += f"전체 조회: `get_english_law_detail(mst=\"{law_id}\", max_articles=0)`\n"
                result += f"다음 {min(50, remaining)}개: `get_english_law_detail(mst=\"{law_id}\", max_articles={display_count + 50})`\n"
                
        elif addenda_articles:
            result += f"**부칙 및 경과조치** ({len(addenda_articles)}개)\n\n"
            display_count = min(5, len(addenda_articles))
            
            for i, article in enumerate(addenda_articles[:display_count], 1):
                article_content = article.get('arCts', '')
                
                if article_content:
                    preview = article_content[:800]
                    if len(article_content) > 800:
                        preview += "..."
                    
                    result += f"**부칙 {article.get('No', i)}:**\n"
                    result += f"{preview}\n\n"
        else:
            return f"조문 내용을 찾을 수 없습니다. (MST: {law_id})"
        
        # 4. 부가 정보
        result += "\n" + "-" * 40 + "\n"
        result += f"**MST**: {law_id}\n"
        
        if main_articles:
            result += f"**전체 조문 개수**: {len(main_articles)}개"
            if addenda_articles:
                result += f" (+ 부칙 {len(addenda_articles)}개)"
            result += "\n"
            
            # 대용량 법령 안내
            if len(main_articles) > 100:
                result += f"\n💡 **팁**: 이 법령은 조문이 많습니다. 특정 내용 검색:\n"
                result += f"   `search_english_law_articles_semantic(mst=\"{law_id}\", query=\"키워드\")`"
        elif addenda_articles:
            result += f"**부칙 개수**: {len(addenda_articles)}개\n"
        
        return result
        
    except Exception as e:
        logger.error(f"영문법령 포맷팅 중 오류: {e}")
        return f"법령 정보 처리 중 오류가 발생했습니다: {str(e)}"

@mcp.tool(
    name="search_effective_law", 
    description="""시행일 기준 법령을 검색합니다.

⚠️ 중요: 이 도구의 검색 결과에서 반환되는 MST는 '시행일법령 MST'입니다.
현행법령(search_law, get_law_detail)의 MST와 다를 수 있으므로 주의하세요.
- get_effective_law_detail, get_effective_law_articles에는 반드시 이 도구의 MST를 사용하세요.
- 현행법령 MST(search_law 결과)를 사용하면 잘못된 결과가 반환됩니다.

매개변수:
- query: 검색어 (선택) - 법령명
- search: 검색범위 (1=법령명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- status_type: 시행상태 (100=시행, 200=미시행, 300=폐지)

반환정보: 법령명, 시행일자, 시행상태, 법령ID, **시행일법령MST**, 공포일자, 소관부처

권장 워크플로우:
1. search_effective_law("개인정보보호법") → 시행일법령 MST 확인
2. get_effective_law_detail(effective_law_id="MST값") → 시행일 기준 상세 조회
3. get_effective_law_articles(mst="MST값") → 시행일 기준 조문 조회

사용 예시: search_effective_law("소득세법", status_type=100)""",
    tags={"시행일법령", "시행일", "법령상태", "시행예정", "미시행", "폐지", "연혁", "효력발생", "컴플라이언스"}
)
def search_effective_law(
    query: Annotated[Optional[str], "검색어 (법령명)"] = None,
    search: Annotated[int, "검색범위 (1=법령명, 2=본문)"] = 1,
    display: Annotated[int, "결과 개수 (최대 100)"] = 20,
    page: Annotated[int, "페이지 번호"] = 1,
    status_type: Annotated[Optional[str], "시행상태 (100=시행, 200=미시행, 300=폐지)"] = None,
    law_id: Annotated[Optional[str], "법령ID"] = None,
    sort: Annotated[Optional[str], "정렬 옵션"] = None,
    effective_date_range: Annotated[Optional[str], "시행일자 범위 (YYYYMMDD~YYYYMMDD)"] = None,
    date: Annotated[Optional[str], "공포일자 (YYYYMMDD)"] = None,
    announce_date_range: Annotated[Optional[str], "공포일자 범위 (YYYYMMDD~YYYYMMDD)"] = None,
    announce_no_range: Annotated[Optional[str], "공포번호 범위"] = None,
    revision_type: Annotated[Optional[str], "제개정 종류"] = None,
    announce_no: Annotated[Optional[str], "공포번호"] = None,
    ministry_code: Annotated[Optional[str], "소관부처 코드"] = None,
    law_type_code: Annotated[Optional[str], "법령종류 코드"] = None,
    alphabetical: Annotated[Optional[str], "사전식 검색"] = None
) -> TextContent:
    """시행일법령 검색 (풍부한 검색 파라미터 지원)
    
    Args:
        query: 검색어 (법령명)
        search: 검색범위 (1=법령명, 2=본문검색)
        display: 결과 개수 (max=100)
        page: 페이지 번호
        status_type: 시행상태 (100=시행, 200=미시행, 300=폐지)
        law_id: 법령ID
        sort: 정렬 (lasc=법령오름차순, ldes=법령내림차순, dasc=공포일자오름차순, ddes=공포일자내림차순, efasc=시행일자오름차순, efdes=시행일자내림차순)
        effective_date_range: 시행일자 범위 (20090101~20090130)
        date: 공포일자 (YYYYMMDD)
        announce_date_range: 공포일자 범위 (20090101~20090130)
        announce_no_range: 공포번호 범위 (306~400)
        revision_type: 제개정 종류
        announce_no: 공포번호
        ministry_code: 소관부처 코드
        law_type_code: 법령종류 코드
        alphabetical: 사전식 검색
    """
    try:
        # OC(기관코드) 확인
        if not legislation_config.oc:
            return TextContent(type="text", text="OC(기관코드)가 설정되지 않았습니다. 법제처 API 설정을 확인해주세요.")
        
        # 기본 파라미터 설정 (필수 파라미터 포함)
        params = {
            "OC": legislation_config.oc,  # 필수: 기관코드
            "type": "JSON",               # 필수: 출력형태
            "target": "eflaw",           # 필수: 서비스 대상
            "display": min(display, 100),
            "page": page,
            "search": search
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            params["query"] = query.strip()
        
        # status_type 값 매핑 (기존 값 → API 가이드 값)
        mapped_status_type = None
        if status_type:
            status_mapping = {
                "100": "3",  # 시행 → 현행
                "200": "2",  # 미시행 → 시행예정  
                "300": "1"   # 폐지 → 연혁
            }
            mapped_status_type = status_mapping.get(str(status_type), str(status_type))
        
        # 선택적 파라미터 추가 (API 가이드에 맞게 파라미터명 수정)
        optional_params = {
            "nw": mapped_status_type,  # 연혁/시행예정/현행 구분 (1: 연혁, 2: 시행예정, 3: 현행)
            "LID": law_id,             # 법령ID
            "sort": sort,
            "efYd": effective_date_range,  # 시행일자 범위
            "date": date,              # 공포일자
            "ancYd": announce_date_range,  # 공포일자 범위
            "ancNo": announce_no_range,    # 공포번호 범위
            "rrClsCd": revision_type,      # 제개정구분
            "org": ministry_code,          # 소관부처
            "knd": law_type_code,          # 법령종류
            "gana": alphabetical           # 사전식 검색
        }
        
        for key, value in optional_params.items():
            if value is not None:
                params[key] = value
        
        # API 요청 - 검색 API 사용
        data = _make_legislation_request("eflaw", params, is_detail=False, use_cache=True)
        search_term = query or "시행일법령"
        result = _format_search_results(data, "eflaw", search_term)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"시행일법령 검색 중 오류: {e}")
        error_msg = f"시행일법령 검색 중 오류가 발생했습니다: {str(e)}\n\n"
        error_msg += "**해결방법:**\n"
        error_msg += "1. OC(기관코드) 설정 확인: 현재 설정값 = " + str(legislation_config.oc) + "\n"
        error_msg += "2. 네트워크 연결 상태 확인\n"
        error_msg += "3. 대안: search_law_unified(target='eflaw') 사용 권장\n\n"
        error_msg += "**현재 권장 워크플로우:**\n"
        error_msg += "```\n"
        error_msg += "# 시행일 법령 검색\n"
        error_msg += 'search_law_unified("개인정보보호법", target="eflaw")\n'
        error_msg += "```"
        return TextContent(type="text", text=error_msg)

@mcp.tool(name="search_law_nickname", description="""법령의 약칭을 검색합니다.

매개변수:
- start_date: 시작일자 (선택) - YYYYMMDD 형식
- end_date: 종료일자 (선택) - YYYYMMDD 형식

반환정보: 법령약칭, 정식법령명, 법령ID, 등록일자

사용 예시:
- search_law_nickname()  # 전체 약칭 목록
- search_law_nickname(start_date="20240101")  # 2024년 이후 등록된 약칭
- search_law_nickname(start_date="20230101", end_date="20231231")  # 2023년 등록 약칭

참고: 법령의 통칭이나 줄임말로 검색할 때 유용합니다. 예: '개인정보법' → '개인정보보호법'""")
def search_law_nickname(
    start_date: Annotated[Optional[str], "시작일자 (YYYYMMDD)"] = None,
    end_date: Annotated[Optional[str], "종료일자 (YYYYMMDD)"] = None
) -> TextContent:
    """법령 약칭 검색
    
    Args:
        start_date: 시작일자 (YYYYMMDD)
        end_date: 종료일자 (YYYYMMDD)
    """
    try:
        # 기본 파라미터 설정 (target은 _make_legislation_request에서 자동 추가됨)
        params = {}
        
        # 선택적 파라미터 추가 (API 가이드에 따른 올바른 매개변수명)
        if start_date:
            params["stdDt"] = start_date
        if end_date:
            params["endDt"] = end_date
        
        # API 요청
        data = _make_legislation_request("lsAbrv", params, use_cache=True)
        result = _format_search_results(data, "lsAbrv", "법령약칭")
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"법령약칭 검색 중 오류: {e}")
        return TextContent(type="text", text=f"법령약칭 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="search_deleted_law_data", description="""삭제된 법령 데이터를 검색합니다.

매개변수:
- data_type: 데이터 타입 (선택)
  - 1: 현행법령
  - 2: 시행일법령
  - 3: 법령연혁
  - 4: 영문법령
  - 5: 별표서식
- delete_date: 삭제일자 (선택) - YYYYMMDD 형식
- from_date: 시작일자 (선택) - YYYYMMDD 형식
- to_date: 종료일자 (선택) - YYYYMMDD 형식
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 삭제된 법령명, 법령ID, 삭제일자, 삭제사유, 데이터타입

사용 예시:
- search_deleted_law_data()  # 최근 삭제 데이터 전체
- search_deleted_law_data(data_type=1)  # 삭제된 현행법령만
- search_deleted_law_data(delete_date="20240101")  # 특정일 삭제 데이터
- search_deleted_law_data(from_date="20240101", to_date="20241231")  # 기간별 삭제 데이터

참고: 폐지되거나 삭제된 법령 정보를 추적할 때 사용합니다.""")
def search_deleted_law_data(
    data_type: Annotated[Optional[int], "데이터 타입 (1=현행법령, 2=시행일법령, 3=법령연혁, 4=영문법령, 5=별표서식)"] = None,
    delete_date: Annotated[Optional[str], "삭제일자 (YYYYMMDD)"] = None,
    from_date: Annotated[Optional[str], "시작일자 (YYYYMMDD)"] = None,
    to_date: Annotated[Optional[str], "종료일자 (YYYYMMDD)"] = None,
    display: Annotated[int, "결과 개수 (최대 100)"] = 20,
    page: Annotated[int, "페이지 번호"] = 1
) -> TextContent:
    """삭제된 법령 데이터 검색
    
    Args:
        data_type: 데이터 타입 (1=현행법령, 2=시행일법령, 3=법령연혁, 4=영문법령, 5=별표서식)
        delete_date: 삭제일자 (YYYYMMDD)
        from_date: 시작일자 (YYYYMMDD)
        to_date: 종료일자 (YYYYMMDD)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정 (target은 _make_legislation_request에서 자동 추가됨)
        params = {
            "display": min(display, 100),
            "page": page
        }
        
        # 선택적 파라미터 추가 (API 가이드에 따른 올바른 매개변수명)
        optional_params = {
            "knd": data_type,         # 데이터 종류 (법령:1, 행정규칙:2, 자치법규:3, 학칙공단:13)
            "delDt": delete_date,     # 데이터 삭제 일자 검색 (YYYYMMDD)
            "frmDt": from_date,       # 데이터 삭제 일자 범위 검색 시작 (YYYYMMDD)
            "toDt": to_date           # 데이터 삭제 일자 범위 검색 끝 (YYYYMMDD)
        }
        
        for key, value in optional_params.items():
            if value is not None:
                params[key] = value  # type: ignore
        
        # API 요청
        data = _make_legislation_request("delHst", params, is_detail=False, use_cache=True)
        result = _format_search_results(data, "delHst", "삭제된 법령 데이터")
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"삭제된 법령 데이터 검색 중 오류: {e}")
        return TextContent(type="text", text=f"삭제된 법령 데이터 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="search_law_articles", description="""법령의 조문을 검색합니다.

매개변수:
- mst: 법령일련번호(MST) (필수) - search_law 도구의 결과에서 'MST' 또는 '법령일련번호' 필드값 사용
- article_no: 특정 조문 번호 (선택) - 예: "1", "15" (지정 시 해당 조문만 상세 조회)
- include_content: 조문 전체 내용(항/호/목) 포함 여부 (기본값: True)
  - True: 항/호/목 전체 내용 포함 (상세 분석 시 권장)
  - False: 조문 목록/인덱스만 (목차 파악 시 권장)
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 조문번호, 조문제목, 조문내용, 항/호/목 (include_content=True 시)

사용 예시:
- search_law_articles(mst="267581")  # 은행법 조문 전체 조회
- search_law_articles(mst="248613", article_no="15")  # 개인정보보호법 제15조 상세 조회
- search_law_articles(mst="248613", include_content=False)  # 목차만 조회""")
def search_law_articles(
    mst: Annotated[Union[str, int], "법령일련번호(MST) - search_law 결과에서 사용"],
    article_no: Annotated[Optional[str], "특정 조문 번호 (선택)"] = None,
    include_content: Annotated[bool, "조문 전체 내용(항/호/목) 포함 여부"] = True,
    display: Annotated[int, "결과 개수 (최대 100)"] = 20,
    page: Annotated[int, "페이지 번호"] = 1
) -> TextContent:
    """법령 조문 검색 (현행법령 본문 조항호목 조회)
    
    Args:
        mst: 법령일련번호(MST)
        article_no: 특정 조문 번호 (선택)
        include_content: 조문 전체 내용(항/호/목) 포함 여부
        display: 결과 개수
        page: 페이지 번호
    """
    if not mst:
        return TextContent(type="text", text="법령일련번호(MST)를 입력해주세요.")
    
    try:
        mst_str = str(mst)
        
        # 조문 조회는 lawjosub API가 제한적이므로, 전체 법령에서 조문 추출하는 방식 사용
        # 1단계: 먼저 해당 법령의 전체 정보를 조회 (MST 또는 ID로)
        try:
            # MST로 법령 상세 조회 시도
            detail_params = {"MST": mst_str}
            detail_data = _make_legislation_request("law", detail_params, is_detail=True, use_cache=True)
            
            if detail_data and "법령" in detail_data:
                # 법령 상세 정보에서 조문 추출
                result = _format_law_detail_articles(detail_data, mst_str, article_no=article_no, include_content=include_content)
                return TextContent(type="text", text=result)
        except Exception as e:
            logger.warning(f"MST로 조문 조회 실패: {e}")
        
        # 2단계: MST 실패시 ID로 시도  
        try:
            # 법령ID가 MST인지 ID인지 확인 후 적절한 검색 수행
            if len(mst_str) >= 6 and mst_str.isdigit():
                # MST 형태인 경우 - 해당 MST로 직접 상세 조회 재시도
                detail_params = {"MST": mst_str}
                detail_data = _make_legislation_request("law", detail_params, is_detail=True, use_cache=True)
                
                if detail_data and "법령" in detail_data:
                    result = _format_law_detail_articles(detail_data, mst_str, mst_str, article_no=article_no, include_content=include_content)
                    return TextContent(type="text", text=result)
            else:
                # 일반 ID 형태인 경우 - ID로 검색
                search_params = {
                    "query": f"법령ID:{mst_str}",
                    "display": 5,
                    "type": "JSON"
                }
                search_data = _make_legislation_request("law", search_params, is_detail=False, use_cache=True)
                
                if search_data and "LawSearch" in search_data and "law" in search_data["LawSearch"]:
                    laws = search_data["LawSearch"]["law"]
                    if not isinstance(laws, list):
                        laws = [laws]
                    
                    # 해당 ID를 가진 법령 찾기
                    for law in laws:
                        if isinstance(law, dict):
                            law_id_field = str(law.get('ID', law.get('법령ID', '')))
                            law_mst = law.get('MST', law.get('법령일련번호', ''))
                            
                            # 정확한 매칭 확인
                            if law_id_field == mst_str and law_mst:
                                # 찾은 MST로 상세 조회
                                detail_params = {"MST": str(law_mst)}
                                detail_data = _make_legislation_request("law", detail_params, is_detail=True, use_cache=True)
                                
                                if detail_data and "법령" in detail_data:
                                    result = _format_law_detail_articles(detail_data, mst_str, law_mst, article_no=article_no, include_content=include_content)
                                    return TextContent(type="text", text=result)
        except Exception as e:
            logger.warning(f"ID 검색으로 조문 조회 실패: {e}")
        
        # 3단계: 기존 lawjosub API 시도 (최후 수단)
        try:
            params = {
                "OC": legislation_config.oc,
                "target": "lawjosub",
                "ID": mst_str,
                "display": min(display, 100),
                "page": page,
                "type": "JSON"
            }
            
            url = f"{legislation_config.search_base_url}?{urlencode(params)}"
            headers = {"Referer": "https://open.law.go.kr/"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if _has_meaningful_content(data):
                return TextContent(type="text", text=_format_law_articles(data, mst_str, url))
        except Exception as e:
            logger.warning(f"lawjosub API 조회 실패: {e}")
        
        # 모든 시도 실패 시 대안 방법 제시
        return TextContent(type="text", text=f"""**법령 조문 조회 결과**

**요청한 MST**: {mst}

**조회 상태**: 여러 API 엔드포인트로 시도했으나 조문 목록을 가져올 수 없습니다.

**대안 방법**:

1. **전체 법령 본문으로 조문 확인**:
```
get_law_detail(mst="{mst_str}")
```

2. **법령 검색으로 올바른 MST 확인**:
```
search_law(query="법령명")
```

3. **캐시된 조문 정보 조회**:
```
get_current_law_articles(mst="{mst_str}")
```

**참고**: 조항호목 API가 현재 제한적으로 작동하고 있습니다.
전체 법령 본문 조회를 통해 조문 정보를 확인하세요.""")
        
    except Exception as e:
        logger.error(f"법령조문 검색 중 오류: {e}")
        return TextContent(type="text", text=f"법령조문 검색 중 오류가 발생했습니다: {str(e)}")


def _format_law_system_diagram_results(data: dict, search_term: str) -> str:
    """법령 체계도 검색 결과 전용 포매팅"""
    try:
        result = f"**법령 체계도 검색 결과**\n\n"
        result += f"**검색어**: {search_term}\n\n"
        
        # 다양한 응답 구조 처리
        diagram_data = []
        
        # 1. LsStmdSearch 구조 확인 (실제 API 응답 구조)
        if 'LsStmdSearch' in data:
            law_search = data['LsStmdSearch']
            diagram_data = law_search.get('law', [])
        
        # 2. LawSearch 구조 확인 (레거시 지원)
        elif 'LawSearch' in data:
            law_search = data['LawSearch']
            
            # 가능한 키들 확인
            possible_keys = ['law', 'lsStmd', 'systemDiagram', 'diagram']
            for key in possible_keys:
                if key in law_search:
                    diagram_data = law_search[key]
                    break
                    
            # 키를 찾지 못한 경우 모든 키 확인
            if not diagram_data:
                for key, value in law_search.items():
                    if isinstance(value, list) and value:
                        diagram_data = value
                        break
                    elif isinstance(value, dict) and value:
                        diagram_data = [value]
                        break
        
        # 3. 직접 구조 확인
        elif 'lsStmd' in data:
            diagram_data = data['lsStmd']
        elif 'law' in data:
            diagram_data = data['law']
        else:
            # 응답 구조 분석
            for key, value in data.items():
                if isinstance(value, list) and value:
                    diagram_data = value
                    break
                elif isinstance(value, dict) and value:
                    diagram_data = [value]
                    break
        
        # 리스트가 아닌 경우 리스트로 변환
        if not isinstance(diagram_data, list):
            diagram_data = [diagram_data] if diagram_data else []
        
        if diagram_data:
            result += f"**총 {len(diagram_data)}개 체계도**\n\n"
            
            for i, item in enumerate(diagram_data[:20], 1):
                if not isinstance(item, dict):
                    continue
                
                # 법령명 추출 (다양한 키 시도)
                law_name = ""
                law_name_keys = ['법령명한글', '법령명', '현행법령명', 'lawNm', 'lawName', 'title', '제목']
                for key in law_name_keys:
                    if key in item and item[key]:
                        law_name = str(item[key]).strip()
                        break
                
                # MST 추출 (다양한 키 시도)
                mst_keys = ['MST', 'mst', '법령일련번호', 'lawSeq', 'seq', 'ID', 'id', '법령ID', 'lawId']
                mst = ""
                for key in mst_keys:
                    if key in item and item[key]:
                        mst = str(item[key]).strip()
                        break
                
                # 체계도 관련 정보 추출
                diagram_type = item.get('체계도유형', item.get('diagramType', ''))
                create_date = item.get('작성일자', item.get('createDate', ''))
                
                result += f"**{i}. {law_name if law_name else '체계도'}**\n"
                
                if mst:
                    result += f"   MST: {mst}\n"
                else:
                    # MST가 없는 경우 사용 가능한 ID 정보 표시
                    available_ids = []
                    for key in ['ID', 'id', '번호', 'no', 'seq']:
                        if key in item and item[key]:
                            available_ids.append(f"{key}={item[key]}")
                    if available_ids:
                        result += f"   식별정보: {', '.join(available_ids)}\n"
                if diagram_type:
                    result += f"   유형: {diagram_type}\n"
                if create_date:
                    result += f"   작성일: {create_date}\n"
                
                # 추가 정보 표시
                additional_info = []
                skip_keys = {'법령명한글', '법령명', '현행법령명', 'lawNm', 'lawName', 'title', '제목', 'MST', 'mst', '법령일련번호'}
                for key, value in item.items():
                    if key not in skip_keys and value and len(str(value).strip()) < 100:
                        additional_info.append(f"{key}: {value}")
                
                if additional_info:
                    result += f"   기타: {' | '.join(additional_info[:3])}\n"
                
                result += "\n"
            
            if len(diagram_data) > 20:
                result += f"... 외 {len(diagram_data) - 20}개 체계도\n\n"
            
            result += "**상세 체계도 조회**:\n"
            result += "```\nget_law_system_diagram_detail(mst_id=\"MST번호\")\n```"
            
        else:
            result += "**체계도를 찾을 수 없습니다.**\n\n"
            
            # 응답 구조 디버깅 정보
            result += "**응답 데이터 구조**:\n"
            for key in data.keys():
                result += f"- {key}: {type(data[key])}\n"
            
            result += "\n**가능한 원인**:\n"
            result += "- 해당 법령의 체계도가 아직 제공되지 않음\n"
            result += "- 검색어가 정확하지 않음\n"
            result += "- API 응답 구조 변경\n\n"
            
            result += f"**대안 방법**:\n"
            result += f"- search_law(query=\"{search_term}\") - 일반 법령 검색\n"
            result += f"- search_related_law(query=\"{search_term}\") - 관련법령 검색"
        
        return result
        
    except Exception as e:
        logger.error(f"법령 체계도 포매팅 중 오류: {e}")
        return f"**법령 체계도 포매팅 오류**\n\n**오류**: {str(e)}\n\n**검색어**: {search_term}\n\n**원본 데이터 키**: {list(data.keys()) if data else 'None'}"


def _format_law_detail_articles(detail_data: dict, law_id: str, actual_mst: str = "", 
                                article_no: Optional[str] = None, include_content: bool = True) -> str:
    """법령 상세 정보에서 조문만 추출하여 포맷팅"""
    try:
        law_info = detail_data.get("법령", {})
        basic_info = law_info.get("기본정보", {})
        law_name = basic_info.get("법령명_한글", basic_info.get("법령명한글", ""))
        
        result = f"**{law_name}** 조문 조회\n"
        result += "=" * 50 + "\n\n"
        
        # 조문 정보 추출
        articles_section = law_info.get("조문", {})
        article_units = []
        
        if isinstance(articles_section, dict) and "조문단위" in articles_section:
            article_units = articles_section.get("조문단위", [])
            if not isinstance(article_units, list):
                article_units = [article_units] if article_units else []
        elif isinstance(articles_section, list):
            article_units = articles_section
        
        # 실제 조문만 필터링
        actual_articles = []
        for article in article_units:
            if isinstance(article, dict) and article.get("조문여부") == "조문":
                # article_no가 지정된 경우 해당 조문만 필터링
                if article_no:
                    art_no = article.get("조문번호", "")
                    target_no = str(article_no).replace("제", "").replace("조", "")
                    if art_no != target_no:
                        continue
                actual_articles.append(article)
        
        if actual_articles:
            if article_no:
                result += f"**검색 조건:** 제{article_no}조\n\n"
            result += f"**조회 결과:** (총 {len(actual_articles)}건)\n\n"
            
            # include_content=False면 더 많은 조문 표시, True면 제한
            max_display = 10 if include_content else 50
            
            for i, article in enumerate(actual_articles[:max_display], 1):
                art_no = article.get("조문번호", "")
                art_title = article.get("조문제목", "")
                
                result += f"### 제{art_no}조"
                if art_title:
                    result += f"({art_title})"
                result += "\n\n"
                
                if include_content:
                    # format_article_body 함수로 항/호/목 포맷팅
                    article_body = format_article_body(article, include_details=True)
                    if article_body.strip():
                        result += f"{article_body}\n"
                else:
                    # 인덱스만 표시 (조문 내용 간략히)
                    article_content = article.get("조문내용", "")
                    if article_content:
                        clean_content = clean_html_tags(article_content)[:100]
                        result += f"{clean_content}...\n\n"
                
                result += "-" * 40 + "\n\n"
            
            if len(actual_articles) > max_display:
                result += f"... 외 {len(actual_articles) - max_display}개 조문\n\n"
                if include_content:
                    result += f"**팁:** include_content=False로 설정하면 더 많은 조문 목록을 볼 수 있습니다.\n"
        else:
            if article_no:
                result += f"**제{article_no}조를 찾을 수 없습니다.**\n\n"
            else:
                result += "**조문을 찾을 수 없습니다.**\n\n"
            result += f"**대안 방법**:\n"
            result += f"- get_law_detail(mst=\"{law_id}\") - 전체 법령 보기"
        
        return result
        
    except Exception as e:
        logger.error(f"법령 상세 조문 포맷팅 중 오류: {e}")
        return f"**조문 포맷팅 오류**\n\n**오류**: {str(e)}\n\n**법령ID**: {law_id}"

def _format_law_articles(data: dict, law_id: str, url: str = "") -> str:
    """법령 조문 정보 포매팅"""
    try:
        result = f"**법령 조문 목록**\n\n"
        result += f"**법령ID**: {law_id}\n"
        if url:
            result += f"**조회 URL**: {url}\n"
        result += "\n"
        
        # 다양한 응답 구조 처리
        articles_found = []
        law_name = ""
        
        # 1. LawService 구조 확인
        if 'LawService' in data:
            law_service = data['LawService']
            if isinstance(law_service, list) and law_service:
                law_info = law_service[0]
            elif isinstance(law_service, dict):
                law_info = law_service
            else:
                law_info = {}
                
            law_name = law_info.get('법령명', law_info.get('법령명한글', ''))
            
            # 조문 정보 추출
            if '조문' in law_info:
                articles_data = law_info['조문']
                if isinstance(articles_data, dict):
                    if '조문단위' in articles_data:
                        articles_found = articles_data['조문단위']
                    else:
                        articles_found = [articles_data]
                elif isinstance(articles_data, list):
                    articles_found = articles_data
        
        # 2. LawSearch 구조 확인 (조문 검색 결과)
        elif 'LawSearch' in data:
            law_search = data['LawSearch']
            if 'law' in law_search:
                laws = law_search['law']
                if isinstance(laws, list) and laws:
                    # 요청한 법령ID와 일치하는 법령 찾기
                    target_law = None
                    for law in laws:
                        if isinstance(law, dict):
                            # MST, ID, 법령ID 등 다양한 키로 매칭 시도
                            law_mst = str(law.get('MST', law.get('법령일련번호', '')))
                            law_id_field = str(law.get('ID', law.get('법령ID', '')))
                            
                            if law_mst == law_id or law_id_field == law_id:
                                target_law = law
                                break
                    
                    # 매칭되는 법령이 없으면 첫 번째 사용 (기존 로직)
                    law_info = target_law if target_law else laws[0]
                elif isinstance(laws, dict):
                    law_info = laws
                else:
                    law_info = {}
                    
                law_name = law_info.get('법령명한글', law_info.get('법령명', ''))
                
                # 기본 법령 정보만 있는 경우 조문은 없음
                if '조문' in law_info:
                    articles_found = law_info['조문']
        
        # 3. 직접 조문 구조
        elif '조문' in data:
            articles_found = data['조문']
            law_name = data.get('법령명', data.get('법령명한글', ''))
            
        # 법령명 표시
        if law_name:
            result += f"**법령명**: {law_name}\n\n"
        
        # 조문 목록 처리
        if not isinstance(articles_found, list):
            articles_found = [articles_found] if articles_found else []
            
        if articles_found:
            result += f"**총 {len(articles_found)}개 조문**\n\n"
            
            for i, article in enumerate(articles_found[:20], 1):  # 최대 20개만 표시
                if not isinstance(article, dict):
                    continue
                    
                # 조문 번호 추출
                article_no = (article.get('조번호') or 
                            article.get('조문번호') or 
                            article.get('articleNo') or 
                            str(i))
                
                # 조문 제목 추출
                article_title = (article.get('조제목') or 
                               article.get('조문제목') or 
                               article.get('articleTitle') or '')
                
                # 조문 내용 추출
                article_content = (article.get('조문내용') or 
                                 article.get('내용') or 
                                 article.get('content') or '')
                
                # 결과 구성
                result += f"**{i}. 제{article_no}조"
                if article_title:
                    result += f" ({article_title})"
                result += "**\n"
                
                if article_content:
                    # 내용 길이 제한
                    content_preview = article_content[:150]
                    if len(article_content) > 150:
                        content_preview += "..."
                    result += f"   {content_preview}\n\n"
                else:
                    result += "   (내용 없음)\n\n"
            
            if len(articles_found) > 20:
                result += f"... 외 {len(articles_found) - 20}개 조문\n\n"
                
            result += "**상세 조문 내용 조회**:\n"
            result += f"```\nget_law_detail(mst=\"{law_id}\")\n```"
            
        else:
            # 조문이 없는 경우 전체 데이터 구조 표시
            result += "**조문 목록을 찾을 수 없습니다.**\n\n"
            result += "**응답 데이터 구조**:\n"
            for key in data.keys():
                result += f"- {key}\n"
            result += f"\n**대안 방법**: 전체 법령 본문으로 조회하세요.\n"
            result += f"```\nget_law_detail(mst=\"{law_id}\")\n```"
        
        return result
        
    except Exception as e:
        logger.error(f"법령 조문 포매팅 중 오류: {e}")
        return f"**법령 조문 포매팅 오류**\n\n**오류**: {str(e)}\n\n**대안**: get_law_detail(mst=\"{law_id}\")를 사용하세요."

@mcp.tool(name="search_old_and_new_law", description="""신구법비교 목록을 검색합니다.

매개변수:
- query: 검색어 (선택) - 법령명 또는 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 법령명, 비교ID, 개정일자, 신구조문대비표 유무

사용 예시:
- search_old_and_new_law()  # 전체 신구법비교 목록
- search_old_and_new_law("개인정보보호법")  # 특정 법령의 신구법비교
- search_old_and_new_law("근로", display=50)  # 근로 관련 법령 비교

참고: 법령 개정 전후의 변경사항을 비교할 수 있는 자료를 검색합니다.""")
def search_old_and_new_law(
    query: Annotated[Optional[str], "검색어 (법령명)"] = None,
    display: Annotated[int, "결과 개수 (최대 100)"] = 20,
    page: Annotated[int, "페이지 번호"] = 1
) -> TextContent:
    """신구법비교 검색
    
    Args:
        query: 검색어 (법령명)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정
        params = {
            "target": "oldAndNew",
            "display": min(display, 100),
            "page": page
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            params["query"] = query.strip()
        
        # API 요청
        data = _make_legislation_request("oldAndNew", params, use_cache=True)
        search_term = query or "신구법비교"
        result = _format_search_results(data, "oldAndNew", search_term)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"신구법비교 검색 중 오류: {e}")
        return TextContent(type="text", text=f"신구법비교 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_old_and_new_law_detail", description="""신구법비교 본문을 조회합니다.

매개변수:
- mst: 법령일련번호 (search_old_and_new_law 결과에서 획득)

반환정보: 신조문/구조문 대조표, 변경사항

사용 예시:
- get_old_and_new_law_detail("122682")  # 특정 법령의 신구법 비교

참고: search_old_and_new_law로 먼저 목록을 검색한 후 법령일련번호를 사용하세요.""")
def get_old_and_new_law_detail(
    mst: Annotated[str, "법령일련번호 (MST)"],
) -> TextContent:
    """신구법비교 본문 조회"""
    try:
        params = {"MST": str(mst)}
        data = _make_legislation_request("oldAndNew", params, is_detail=True, use_cache=True)
        
        if not data:
            return TextContent(type="text", text=f"법령일련번호 {mst}에 해당하는 신구법비교 정보를 찾을 수 없습니다.")
        
        # 응답 포맷팅
        result = _format_old_and_new_detail(data, mst)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"신구법비교 본문 조회 중 오류: {e}")
        return TextContent(type="text", text=f"신구법비교 본문 조회 중 오류가 발생했습니다: {str(e)}")

def _format_old_and_new_detail(data: dict, mst: str) -> str:
    """신구법비교 본문 포맷팅"""
    lines = [f"# 신구법비교 상세 (MST: {mst})\n"]
    
    service_data = data.get("OldAndNewService", {})
    if not service_data:
        return f"MST {mst}에 해당하는 신구법비교 정보가 없습니다."
    
    # 신조문 목록
    new_articles = service_data.get("신조문목록", {}).get("조문", [])
    if isinstance(new_articles, dict):
        new_articles = [new_articles]
    
    # 구조문 목록
    old_articles = service_data.get("구조문목록", {}).get("조문", [])
    if isinstance(old_articles, dict):
        old_articles = [old_articles]
    
    lines.append(f"## 조문 비교 (신: {len(new_articles)}개, 구: {len(old_articles)}개)\n")
    
    # 신조문
    if new_articles:
        lines.append("### 신조문")
        for i, article in enumerate(new_articles[:20], 1):  # 최대 20개
            content = article.get("content", "")
            # HTML 태그 제거
            import re
            content = re.sub(r'<[^>]+>', '', content)
            lines.append(f"{i}. {content[:200]}{'...' if len(content) > 200 else ''}")
        if len(new_articles) > 20:
            lines.append(f"... 외 {len(new_articles) - 20}개")
        lines.append("")
    
    # 구조문
    if old_articles:
        lines.append("### 구조문")
        for i, article in enumerate(old_articles[:20], 1):
            content = article.get("content", "")
            import re
            content = re.sub(r'<[^>]+>', '', content)
            lines.append(f"{i}. {content[:200]}{'...' if len(content) > 200 else ''}")
        if len(old_articles) > 20:
            lines.append(f"... 외 {len(old_articles) - 20}개")
    
    return "\n".join(lines)

@mcp.tool(name="search_three_way_comparison", description="""3단비교 목록을 검색합니다.

매개변수:
- query: 검색어 (선택) - 법령명 또는 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 법령명, 비교ID, 인용조문, 위임조문, 비교일자

사용 예시:
- search_three_way_comparison()  # 전체 3단비교 목록
- search_three_way_comparison("시행령")  # 시행령 관련 3단비교
- search_three_way_comparison("건축법", display=30)

참고: 상위법령-하위법령-위임조문의 3단계 관계를 비교분석하는 자료입니다.""")
def search_three_way_comparison(
    query: Annotated[Optional[str], "검색어 (법령명)"] = None,
    display: Annotated[int, "결과 개수 (최대 100)"] = 20,
    page: Annotated[int, "페이지 번호"] = 1
) -> TextContent:
    """3단비교 검색
    
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
            params["query"] = query.strip()
        
        # API 요청 - target: thdCmp (3단비교)
        data = _make_legislation_request("thdCmp", params, use_cache=True)
        search_term = query or "3단비교"
        result = _format_search_results(data, "thdCmp", search_term)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"3단비교 검색 중 오류: {e}")
        return TextContent(type="text", text=f"3단비교 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_three_way_comparison_detail", description="""3단비교 본문을 조회합니다.

매개변수:
- mst: 법령일련번호 (search_three_way_comparison 결과에서 획득)
- knd: 비교종류 (1=인용조문, 2=위임조문, 기본값: 1)

반환정보: 상위법령-하위법령-조문의 3단 비교 내용

사용 예시:
- get_three_way_comparison_detail("222549", knd=1)  # 인용조문 비교
- get_three_way_comparison_detail("222549", knd=2)  # 위임조문 비교

참고: search_three_way_comparison으로 먼저 목록을 검색한 후 법령일련번호를 사용하세요.""")
def get_three_way_comparison_detail(
    mst: Annotated[str, "법령일련번호 (MST)"],
    knd: Annotated[int, "비교종류 (1=인용조문, 2=위임조문)"] = 1,
) -> TextContent:
    """3단비교 본문 조회 (응답 구조 디버깅 및 대안 제시)"""
    try:
        params = {"MST": str(mst), "knd": str(knd)}
        data = _make_legislation_request("thdCmp", params, is_detail=True, use_cache=True)
        
        if not data:
            return _suggest_three_way_alternatives(mst, knd)
        
        # 응답 구조 디버깅
        available_keys = list(data.keys())
        logger.debug(f"3단비교 응답 구조 (MST={mst}, knd={knd}): {available_keys}")
        
        # 다양한 응답 키 시도
        service_data = None
        service_keys = [
            "LspttnThdCmpLawXService",
            "ThdCmpService",
            "thdCmpService",
            "ThdCmpLawXService",
            "LawService",
            "Service"
        ]
        
        for key in service_keys:
            if key in data:
                service_data = data[key]
                logger.info(f"3단비교 서비스 데이터 발견: {key}")
                break
        
        # 서비스 데이터가 없으면 대안 제시
        if not service_data:
            logger.warning(f"3단비교 서비스 데이터 없음 (MST={mst}, knd={knd}). 사용 가능한 키: {available_keys}")
            return _suggest_three_way_alternatives(mst, knd, available_keys)
        
        # 응답 포맷팅
        result = _format_three_way_comparison_detail(data, mst, knd, service_data)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"3단비교 본문 조회 중 오류: {e}")
        return TextContent(type="text", text=f"3단비교 본문 조회 중 오류가 발생했습니다: {str(e)}")

def _format_three_way_comparison_detail(data: dict, mst: str, knd: int, service_data: dict = None) -> str:
    """3단비교 본문 포맷팅"""
    knd_name = "인용조문" if knd == 1 else "위임조문"
    lines = [f"# 3단비교 상세 - {knd_name} (MST: {mst})\n"]
    
    # service_data가 제공되지 않으면 data에서 찾기
    if not service_data:
        service_data = data.get("LspttnThdCmpLawXService", {})
        if not service_data:
            service_data = data.get("ThdCmpService", {})
        if not service_data:
            service_data = data.get("thdCmpService", {})
    
    if not service_data:
        return _suggest_three_way_alternatives(mst, knd, list(data.keys()))
    
    # 인용조문삼단비교 또는 위임조문삼단비교
    comparison_key = "인용조문삼단비교" if knd == 1 else "위임조문삼단비교"
    comparison_data = service_data.get(comparison_key, {})
    
    # 법률조문
    law_articles = comparison_data.get("법률조문", [])
    if isinstance(law_articles, dict):
        law_articles = [law_articles]
    
    if law_articles:
        lines.append(f"## 법률조문 ({len(law_articles)}개)\n")
        for i, article in enumerate(law_articles[:30], 1):
            title = article.get("조제목", "")
            content = article.get("조내용", "")
            no = article.get("조번호", "")
            if title:
                lines.append(f"### {title}")
            elif no:
                lines.append(f"### 제{int(no)}조")
            if content:
                lines.append(f"{content[:300]}{'...' if len(content) > 300 else ''}")
            lines.append("")
        if len(law_articles) > 30:
            lines.append(f"... 외 {len(law_articles) - 30}개 조문")
    
    # 시행령조문
    decree_articles = comparison_data.get("시행령조문", [])
    if isinstance(decree_articles, dict):
        decree_articles = [decree_articles]
    
    if decree_articles:
        lines.append(f"\n## 시행령조문 ({len(decree_articles)}개)\n")
        for i, article in enumerate(decree_articles[:20], 1):
            title = article.get("조제목", "")
            content = article.get("조내용", "")
            no = article.get("조번호", "")
            if title:
                lines.append(f"### {title}")
            elif no:
                lines.append(f"### 제{int(no)}조")
            if content:
                lines.append(f"{content[:200]}{'...' if len(content) > 200 else ''}")
            lines.append("")
        if len(decree_articles) > 20:
            lines.append(f"... 외 {len(decree_articles) - 20}개 조문")
    
    return "\n".join(lines)


def _find_mst_from_law_id(law_id: str, item: dict) -> Optional[str]:
    """법령ID로 MST 찾기 (3단비교용)
    
    Args:
        law_id: 법령ID
        item: 3단비교 검색 결과 항목
        
    Returns:
        MST 문자열 또는 None
    """
    try:
        # 법령명 추출
        law_name = (item.get('법령명한글') or 
                   item.get('법령명') or 
                   item.get('삼단비교법령명') or
                   item.get('3단비교법령명'))
        
        if not law_name:
            return None
        
        # HTML 태그 제거
        law_name_clean = clean_html_tags(law_name)
        
        # 법령명으로 검색하여 MST 찾기
        search_params = {
            "query": law_name_clean,
            "display": 5
        }
        search_data = _make_legislation_request("law", search_params, is_detail=False, use_cache=True)
        
        if search_data and 'LawSearch' in search_data:
            laws = search_data['LawSearch'].get('law', [])
            if not isinstance(laws, list):
                laws = [laws] if laws else []
            
            # 법령ID로 매칭
            for law in laws:
                if isinstance(law, dict):
                    found_id = str(law.get('법령ID', law.get('ID', '')))
                    if found_id == str(law_id):
                        mst = law.get('법령일련번호', law.get('MST', ''))
                        if mst:
                            logger.info(f"법령ID {law_id}로 MST {mst} 찾음 (법령명: {law_name_clean})")
                            return str(mst)
        
        return None
        
    except Exception as e:
        logger.warning(f"법령ID로 MST 찾기 실패: {e}")
        return None


def _suggest_three_way_alternatives(mst: str, knd: int, available_keys: list = None) -> str:
    """3단비교 데이터 없을 때 대안 제시"""
    knd_name = "인용조문" if knd == 1 else "위임조문"
    
    result = f"**3단비교 정보 없음** (MST: {mst}, {knd_name})\n"
    result += "=" * 50 + "\n\n"
    
    result += "**가능한 원인:**\n"
    result += "1. 해당 법령에 3단비교 데이터가 없음\n"
    result += "2. MST가 잘못되었거나 다른 ID 체계 필요\n"
    result += "3. 해당 법령은 3단비교 대상이 아님\n\n"
    
    if available_keys:
        result += f"**응답 구조**: {', '.join(available_keys)}\n\n"
    
    result += "**대안 방법:**\n"
    result += f"1. `search_three_way_comparison(\"법령명\")`으로 유효한 MST 확인\n"
    result += f"2. 다른 비교종류 시도:\n"
    result += f"   - 인용조문: `get_three_way_comparison_detail(mst=\"{mst}\", knd=1)`\n"
    result += f"   - 위임조문: `get_three_way_comparison_detail(mst=\"{mst}\", knd=2)`\n"
    result += f"3. 다른 법령으로 시도\n"
    result += f"4. 해당 법령의 일반 정보 조회: `get_law_detail(mst=\"{mst}\")`\n"
    
    return result


@mcp.tool(name="search_one_view", description="""한눈보기 목록을 검색합니다.

매개변수:
- query: 검색어 (선택) - 법령명 또는 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 법령명, 한눈보기ID, 주요내용, 작성일자

사용 예시:
- search_one_view()  # 전체 한눈보기 목록
- search_one_view("개인정보")  # 개인정보 관련 한눈보기
- search_one_view("세법", display=30)  # 세법 관련 한눈보기

참고: 복잡한 법령의 핵심 내용을 한눈에 파악할 수 있도록 정리한 자료입니다.""")
def search_one_view(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """한눈보기 검색
    
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
            params["query"] = query.strip()
        
        # API 요청 - 올바른 target: oneview
        data = _make_legislation_request("oneview", params, use_cache=True)
        search_term = query or "한눈보기"
        result = _format_search_results(data, "oneview", search_term)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"한눈보기 검색 중 오류: {e}")
        return TextContent(type="text", text=f"한눈보기 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_one_view_detail", description="""한눈보기 본문을 조회합니다.

매개변수:
- mst: 법령일련번호 (선택) - 특정 법령 한눈보기 조회 시 사용
- display: 결과 개수 (최대 100, 기본값: 50) - mst 미지정시 전체 목록

사용 예시:
- get_one_view_detail(mst="268283")  # 특정 법령 한눈보기
- get_one_view_detail()  # 전체 한눈보기 목록

참고: search_one_view로 먼저 목록 검색 후 MST 확인하여 사용하세요.""")
def get_one_view_detail(
    mst: Annotated[str, "법령일련번호 (선택)"] = "",
    display: Annotated[int, "결과 개수 (최대 100)"] = 50,
) -> TextContent:
    """한눈보기 본문 조회"""
    try:
        params = {}
        if mst:
            params["MST"] = str(mst)
        else:
            params["display"] = min(display, 100)
        data = _make_legislation_request("oneview", params, is_detail=True, use_cache=True)
        
        if not data:
            return TextContent(type="text", text="한눈보기 정보를 찾을 수 없습니다.")
        
        # 응답 포맷팅
        result = _format_one_view_detail(data)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"한눈보기 본문 조회 중 오류: {e}")
        return TextContent(type="text", text=f"한눈보기 본문 조회 중 오류가 발생했습니다: {str(e)}")

def _format_one_view_detail(data: dict) -> str:
    """한눈보기 본문 포맷팅"""
    lines = ["# 한눈보기 상세\n"]
    
    items_data = data.get("items", {})
    items = items_data.get("item", [])
    
    if isinstance(items, dict):
        items = [items]
    
    if not items:
        return "한눈보기 정보가 없습니다."
    
    lines.append(f"총 {len(items)}건\n")
    
    # 법령별로 그룹화
    by_law = {}
    for item in items:
        law_name = item.get("법령명", "기타")
        if law_name not in by_law:
            by_law[law_name] = []
        by_law[law_name].append(item)
    
    for law_name, law_items in list(by_law.items())[:20]:  # 최대 20개 법령
        lines.append(f"## {law_name} ({len(law_items)}건)\n")
        for item in law_items[:5]:  # 법령당 최대 5건
            title = item.get("조제목", item.get("콘텐츠제목", ""))
            link = item.get("링크URL", "")
            article_no = item.get("조번호", "")
            
            if title:
                lines.append(f"- **{title}**")
            if article_no:
                lines.append(f"  - 조문번호: 제{int(article_no)}조")
            if link:
                lines.append(f"  - [한눈보기 보기]({link})")
            lines.append("")
        if len(law_items) > 5:
            lines.append(f"  ... 외 {len(law_items) - 5}건")
            lines.append("")
    
    if len(by_law) > 20:
        lines.append(f"\n... 외 {len(by_law) - 20}개 법령")
    
    return "\n".join(lines)

@mcp.tool(name="search_law_system_diagram", description="""법령 체계도를 검색합니다.

매개변수:
- query: 검색어 (선택) - 법령명 또는 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 법령명, 체계도ID, 법령일련번호(MST), 체계도 유형, 작성일자

사용 예시:
- search_law_system_diagram()  # 전체 체계도 목록
- search_law_system_diagram("지방자치법")  # 지방자치법 체계도
- search_law_system_diagram("조세", display=30)  # 조세 관련 법령 체계도

참고: 법령의 구조와 하위법령 관계를 시각적으로 보여주는 다이어그램입니다.""")
def search_law_system_diagram(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령 체계도 검색
    
    Args:
        query: 검색어 (법령명)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정
        params = {
            "display": min(display, 100),
            "page": page,
            "type": "JSON"
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            params["query"] = query.strip()
        
        # API 호출
        data = _make_legislation_request("lsStmd", params, is_detail=False, use_cache=True)
        
        if not data or not _has_meaningful_content(data):
            search_term = query or "전체"
            return TextContent(type="text", text=f"""**법령 체계도 검색 결과**

**검색어**: {search_term}

**결과**: 검색 결과가 없습니다.

**검색 팁**:
- 정확한 법령명을 입력해보세요 (예: "민법", "형법", "상법")
- 법령명의 일부만 입력해보세요 (예: "정보보호", "근로기준")
- 체계도가 제공되는 법령은 주요 기본법에 한정될 수 있습니다

**대안 검색**:
- search_law(query="{query or '법령명'}") - 일반 법령 검색
- search_related_law(query="{query or '법령명'}") - 관련법령 검색""")
        
        # 전용 포매팅 함수 사용
        search_term = query or "법령 체계도"
        result = _format_law_system_diagram_results(data, search_term)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"법령 체계도 검색 중 오류: {e}")
        return TextContent(type="text", text=f"법령 체계도 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_law_system_diagram_detail", description="""법령 체계도 요약 정보를 조회합니다. (대용량 데이터로 요약본 제공)

매개변수:
- mst_id: 법령일련번호(MST) - search_law_system_diagram 도구의 결과에서 'MST' 필드값 사용

반환정보: 체계도 기본정보, 관련법령 요약, 상하위법 개수 등 핵심 정보

상세 조회: get_law_system_diagram_full(mst_id="...")으로 전체 정보 확인

사용 예시: get_law_system_diagram_detail(mst_id="248613")

주의: 체계도 데이터가 매우 클 수 있어 요약본을 먼저 제공합니다.""")
def get_law_system_diagram_detail(mst_id: Union[str, int]) -> TextContent:
    """법령 체계도 상세내용 조회
    
    Args:
        mst_id: 체계도 ID
    """
    if not mst_id:
        return TextContent(type="text", text="체계도 ID를 입력해주세요.")
    
    try:
        mst_str = str(mst_id)
        
        # 캐시 확인 (안전한 import)
        try:
            from ..utils.legislation_utils import load_from_cache, save_to_cache, get_cache_key
            cache_key = get_cache_key(f"diagram_{mst_str}", "summary")
            cached_data = load_from_cache(cache_key)
        except ImportError:
            logger.warning("캐시 모듈을 로드할 수 없습니다. 캐시 없이 진행합니다.")
            cached_data = None
        
        # 캐시 사용: summary 키가 있고 비어 있지 않은 문자열일 때만 사용
        if (
            isinstance(cached_data, dict)
            and "summary" in cached_data
            and isinstance(cached_data["summary"], str)
            and cached_data["summary"].strip()
        ):
            return TextContent(type="text", text=cached_data["summary"])
        
        # API 요청 (target="lsStmd"가 가장 정확함)
        params = {"MST": mst_str}
        data = _make_legislation_request("lsStmd", params, is_detail=True, use_cache=True)
        
        if data and "법령체계도" in data:
            diagram_data = data["법령체계도"]
            
            # 요약본 생성
            summary = _format_system_diagram_summary(diagram_data, mst_str)
            
            # 캐시 저장 (안전한 처리)
            try:
                cache_data = {
                    "full_data": diagram_data,
                    "summary": summary,
                    "data_size": len(str(diagram_data))
                }
                save_to_cache(cache_key, cache_data)
            except (NameError, Exception) as e:
                logger.warning(f"캐시 저장 실패: {e}")
                # 캐시 저장 실패해도 계속 진행
            
            return TextContent(type="text", text=summary)
        
        # 조회 실패시 안내
        return TextContent(type="text", text=f"""**법령 체계도 조회 결과**

**MST**: {mst_id}

**결과**: 체계도 정보를 찾을 수 없습니다.

**가능한 원인**:
1. 해당 법령에 체계도가 제공되지 않음
2. MST ID가 올바르지 않음
3. 체계도 데이터가 아직 구축되지 않음

**대안 방법**:
1. **법령 기본정보**: get_law_detail(mst="{mst_str}")
2. **관련법령 검색**: search_related_law(query="법령명")
3. **법령 목록 재확인**: search_law_system_diagram("법령명")
4. **전체 데이터 확인**: get_law_system_diagram_full(mst_id="{mst_str}")

**법제처 웹사이트 직접 확인**: http://www.law.go.kr/LSW/lsStmdInfoP.do?lsiSeq={mst_str}""")
        
    except Exception as e:
        logger.error(f"법령 체계도 요약 조회 중 오류: {e}")
        return TextContent(type="text", text=f"법령 체계도 요약 조회 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_delegated_law", description="""위임법령을 조회합니다.

매개변수:
- law_id: 법령ID (6자리, 예: 000900) - search_law 결과의 '법령ID' 필드값 사용

사용 예시: get_delegated_law(law_id="000900")

참고: 법령ID는 MST(법령일련번호)와 다릅니다. search_law 결과에서 '법령ID' 필드를 확인하세요.""")
def get_delegated_law(law_id: Union[str, int]) -> TextContent:
    """위임법령 조회
    
    Args:
        law_id: 법령ID (6자리)
    """
    if not law_id:
        return TextContent(type="text", text="법령ID를 입력해주세요. (예: 000900)")
    
    try:
        id_str = str(law_id)
        
        # ID 파라미터로 직접 조회 (API 문서 기준)
        api_attempts = [
            {"target": "lsDelegated", "param": "ID", "endpoint": "detail"},
            {"target": "lsDelegated", "param": "MST", "endpoint": "detail"},
            {"target": "law", "param": "MST", "endpoint": "detail"},  # 전체 법령에서 위임정보 추출
        ]
        
        for attempt in api_attempts:
            try:
                params = {
                    attempt["param"]: id_str,
                    "type": "JSON"
                }
                
                if attempt["endpoint"] == "detail":
                    data = _make_legislation_request(attempt["target"], params, is_detail=True, use_cache=True)
                else:
                    data = _make_legislation_request(attempt["target"], params, is_detail=False, use_cache=True)
                
                # 유의미한 위임법령 데이터가 있는지 확인
                if data and _has_delegated_law_content(data):
                    result = _format_delegated_law(data, id_str, attempt["target"])
                    return TextContent(type="text", text=result)
                    
            except Exception as e:
                logger.warning(f"위임법령 조회 시도 실패 ({attempt}): {e}")
                continue
        
        # 모든 시도 실패시 관련법령 검색으로 대안 제시
        try:
            # 해당 법령명을 찾아서 관련 법령 검색 시도
            detail_params = {"ID": id_str}
            detail_data = _make_legislation_request("law", detail_params, is_detail=True, use_cache=True)
            
            law_name = ""
            if detail_data and "법령" in detail_data:
                basic_info = detail_data["법령"].get("기본정보", {})
                law_name = basic_info.get("법령명_한글", basic_info.get("법령명한글", ""))
            
            if law_name:
                # 관련법령 검색으로 시행령, 시행규칙 찾기
                related_search_params = {
                    "query": law_name.replace("법", ""),  # "은행법" -> "은행"
                    "display": 20,
                    "type": "JSON"
                }
                related_data = _make_legislation_request("law", related_search_params, is_detail=False, use_cache=True)
                
                if related_data and "LawSearch" in related_data and "law" in related_data["LawSearch"]:
                    laws = related_data["LawSearch"]["law"]
                    if not isinstance(laws, list):
                        laws = [laws]
                    
                    # 시행령, 시행규칙 찾기
                    related_laws = []
                    for law in laws:
                        if isinstance(law, dict):
                            related_name = law.get('법령명한글', law.get('법령명', ''))
                            if related_name and law_name.replace("법", "") in related_name:
                                if "시행령" in related_name or "시행규칙" in related_name:
                                    # 실제 API 응답 키 사용
                                    mst_value = law.get('법령일련번호', law.get('MST', ''))
                                    id_value = law.get('법령ID', law.get('ID', ''))
                                    related_laws.append({
                                        "법령명": related_name,
                                        "MST": mst_value,
                                        "ID": id_value
                                    })
                    
                    if related_laws:
                        result = f"""**위임법령 조회 결과** (대안 검색)

**법령명**: {law_name}
**법령ID**: {law_id}

**검색된 관련 법령** ({len(related_laws)}개):

"""
                        for i, related in enumerate(related_laws, 1):
                            result += f"**{i}. {related['법령명']}**\n"
                            if related['MST']:
                                result += f"   MST: {related['MST']}\n"
                            if related['ID']:
                                result += f"   ID: {related['ID']}\n"
                            result += f"   상세조회: get_law_detail(mst=\"{related['MST'] or related['ID']}\")\n\n"
                        
                        result += f"""**참고**: 위임법령 전용 API가 응답하지 않아, 해당 법령과 관련된 법령(시행령·시행규칙 등) 검색 결과로 대체했습니다. 추가로 search_related_law(query="법령명")으로 관련 법령을 조회할 수 있습니다."""
                        
                        return TextContent(type="text", text=result)
        except Exception as e:
            logger.warning(f"관련법령 검색 실패: {e}")
        
        # 최종 실패시 안내
        return TextContent(type="text", text=f"""**위임법령 조회 결과**

**법령ID**: {law_id}

⚠️ **조회 상태**: 여러 API 방법으로 시도했으나 위임법령 정보를 찾을 수 없습니다.

**가능한 원인**:
1. 위임법령 API 서비스 장애
2. 해당 법령에 실제로 위임법령이 없음  
3. API 데이터베이스에 정보가 미등록됨

**대안 검색 방법**:
1. **관련법령 검색**: search_related_law(query="법령명")
2. **시행령 직접 검색**: search_law(query="법령명 시행령")
3. **시행규칙 직접 검색**: search_law(query="법령명 시행규칙")
4. **전체 법령 검색**: search_law(query="법령명")

**참고**: 은행법, 개인정보보호법 등 주요 법령은 반드시 시행령이 존재합니다.""")
        
    except Exception as e:
        logger.error(f"위임법령 조회 중 오류: {e}")
        return TextContent(type="text", text=f"위임법령 조회 중 오류가 발생했습니다: {str(e)}")


def _has_system_diagram_content(data: dict) -> bool:
    """체계도 정보가 있는지 확인"""
    try:
        if not data:
            return False
        
        # 다양한 체계도 관련 키워드 확인
        for key, value in data.items():
            if isinstance(value, dict):
                # 체계도 관련 키워드가 있는지 확인
                for sub_key in value.keys():
                    if any(keyword in sub_key for keyword in ['체계도', 'diagram', 'systemDiagram', 'lsStmd']):
                        return True
            elif isinstance(key, str) and any(keyword in key for keyword in ['체계도', 'diagram', 'systemDiagram', 'lsStmd']):
                return True
        
        return False
        
    except Exception:
        return False

def _format_system_diagram_summary(diagram_data: dict, mst_id: str) -> str:
    """체계도 데이터 요약본 포맷팅"""
    try:
        result = f"**법령 체계도 요약 (MST: {mst_id})**\n\n"
        
        # 기본정보
        basic_info = diagram_data.get('기본정보', {})
        if basic_info:
            result += "**기본정보**\n"
            result += f"- 법령명: {basic_info.get('법령명', '정보없음')}\n"
            result += f"- 법령ID: {basic_info.get('법령ID', '정보없음')}\n"
            result += f"- 법종구분: {basic_info.get('법종구분', {}).get('content', '정보없음')}\n"
            result += f"- 시행일자: {basic_info.get('시행일자', '정보없음')}\n"
            result += f"- 공포일자: {basic_info.get('공포일자', '정보없음')}\n\n"
        
        # 관련법령: 전건 명칭 나열 (최대 20건, 초과 시 "외 N건")
        _MAX_LIST = 20
        related_laws = diagram_data.get('관련법령', [])
        if related_laws:
            items = related_laws if isinstance(related_laws, list) else [related_laws]
            count = len(items)
            result += f"**🔗 관련법령**: {count}건\n"
            for item in items[:_MAX_LIST]:
                if isinstance(item, dict):
                    name = item.get('법령명', item.get('법령명_한글', '정보없음'))
                else:
                    name = str(item) if item else '정보없음'
                result += f"- {name}\n"
            if count > _MAX_LIST:
                result += f"- 외 {count - _MAX_LIST}건\n"
            result += "\n"
        
        # 상하위법: 전건 명칭 나열 (최대 20건, 초과 시 "외 N건")
        hierarchy_laws = diagram_data.get('상하위법', [])
        if hierarchy_laws:
            items = hierarchy_laws if isinstance(hierarchy_laws, list) else [hierarchy_laws]
            count = len(items)
            result += f"**상하위법**: {count}건\n"
            for item in items[:_MAX_LIST]:
                if isinstance(item, dict):
                    name = item.get('법령명', item.get('법령명_한글', '정보없음'))
                else:
                    name = str(item) if item else '정보없음'
                result += f"- {name}\n"
            if count > _MAX_LIST:
                result += f"- 외 {count - _MAX_LIST}건\n"
            result += "\n"
        
        # 데이터 크기 정보
        data_size = len(str(diagram_data))
        result += f"**데이터 정보**\n"
        result += f"- 전체 데이터 크기: {data_size:,} bytes\n"
        result += f"- 캐시됨: 재조회시 빠른 응답\n\n"
        
        # 전체 조회 안내
        result += f"**상세 조회**\n"
        result += f"- 전체 데이터: `get_law_system_diagram_full(mst_id=\"{mst_id}\")`\n"
        result += f"- 법제처 직접: http://www.law.go.kr/LSW/lsStmdInfoP.do?lsiSeq={mst_id}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"체계도 요약본 포맷팅 오류: {e}")
        return f"체계도 요약본 생성 중 오류가 발생했습니다: {str(e)}"

def _format_system_diagram_detail(data: dict, mst_id: str, target: str) -> str:
    """체계도 상세 정보 포맷팅"""
    try:
        result = f"**법령 체계도 상세 정보**\n\n"
        result += f"**MST**: {mst_id}\n"
        result += f"**API 타겟**: {target}\n\n"
        
        # 데이터 구조에 따라 체계도 정보 추출
        diagram_info = {}
        
        if target == "law" and "법령" in data:
            # 일반 법령에서 체계도 정보 찾기
            law_info = data["법령"]
            basic_info = law_info.get("기본정보", {})
            diagram_info = {
                "법령명": basic_info.get("법령명_한글", basic_info.get("법령명한글", "")),
                "법령ID": basic_info.get("법령ID", ""),
                "소관부처": basic_info.get("소관부처", "")
            }
        else:
            # 체계도 전용 API 응답에서 정보 추출
            for key, value in data.items():
                if isinstance(value, dict):
                    diagram_info.update(value)
                    break
        
        if diagram_info:
            result += "**체계도 정보:**\n"
            for key, value in diagram_info.items():
                if value:
                    result += f"• {key}: {value}\n"
            result += "\n"
        
        result += "**참고**: 체계도의 상세 이미지나 구조는 법제처 웹사이트에서 확인할 수 있습니다.\n"
        result += f"**법제처 링크**: https://www.law.go.kr/LSW/lawSearchDetail.do?lawId={mst_id}"
        
        return result
        
    except Exception as e:
        return f"**체계도 상세 포맷팅 오류**\n\n**오류**: {str(e)}\n\n**MST**: {mst_id}"

def _has_delegated_law_content(data: dict) -> bool:
    """위임법령 데이터가 유의미하게 존재하는지 확인"""
    try:
        if not data:
            return False
            
        # lsDelegated API 응답 구조 확인
        if 'LawService' in data:
            law_service = data['LawService']
            if 'DelegatedLaw' in law_service:
                delegated_law = law_service['DelegatedLaw']
                # 위임정보목록이 있고 비어있지 않은지 확인
                if '위임정보목록' in delegated_law:
                    delegation_list = delegated_law['위임정보목록']
                    return isinstance(delegation_list, list) and len(delegation_list) > 0
                return True  # 구조는 있지만 데이터가 없을 수 있음
        
        # 일반 법령 응답에서 위임정보 확인
        if '법령' in data:
            law_info = data['법령']
            # 위임관련 키워드가 있는지 확인
            for key in law_info.keys():
                if any(keyword in key for keyword in ['위임', 'delegat', '시행령', '시행규칙']):
                    return True
        
        return False
        
    except Exception:
        return False

def _format_delegated_law(data: dict, law_id: str, target: str = "lsDelegated") -> str:
    """위임법령 정보 포매팅 (실제 API 응답 구조 기반)"""
    try:
        result = f"**위임법령 조회 결과**\n\n"
        result += f"**법령ID**: {law_id}\n\n"
        
        # 실제 API 응답 구조: { "LawService": { "DelegatedLaw": {...} } }
        if 'LawService' in data and 'DelegatedLaw' in data['LawService']:
            delegated_data = data['LawService']['DelegatedLaw']
            
            # 법령정보 표시
            if '법령정보' in delegated_data:
                law_info = delegated_data['법령정보']
                result += f"📖 **법령명**: {law_info.get('법령명', '정보없음')}\n"
                result += f"🏢 **소관부처**: {law_info.get('소관부처', {}).get('content', '정보없음')}\n"
                result += f"**시행일자**: {law_info.get('시행일자', '정보없음')}\n\n"
            
            # 위임정보 목록 표시
            if '위임정보목록' in delegated_data:
                delegation_list = delegated_data['위임정보목록']
                if isinstance(delegation_list, list):
                    result += f"**총 {len(delegation_list)}개 조문의 위임정보**\n\n"
                    
                    for i, delegation in enumerate(delegation_list, 1):
                        # 조정보
                        if '조정보' in delegation:
                            jo_info = delegation['조정보']
                            result += f"**{i}. 제{jo_info.get('조문번호', '?')}조"
                            if '조문가지번호' in jo_info:
                                result += f"의{jo_info['조문가지번호']}"
                            result += f" ({jo_info.get('조문제목', '제목없음')})**\n"
                        
                        # 위임정보
                        if '위임정보' in delegation:
                            delegation_info = delegation['위임정보']
                            
                            # 단일 위임정보인 경우
                            if isinstance(delegation_info, dict):
                                delegation_info = [delegation_info]
                            
                            for j, info in enumerate(delegation_info):
                                if isinstance(info, dict):
                                    result += f"   **{info.get('위임법령제목', '제목없음')}** "
                                    result += f"({info.get('위임구분', '구분없음')})\n"
                                    result += f"   법령일련번호: {info.get('위임법령일련번호', '정보없음')}\n"
                                    
                                    # 위임법령조문정보
                                    if '위임법령조문정보' in info:
                                        jo_info_list = info['위임법령조문정보']
                                        if not isinstance(jo_info_list, list):
                                            jo_info_list = [jo_info_list]
                                        
                                        result += f"   관련 조문: {len(jo_info_list)}개\n"
                                        for jo_info in jo_info_list[:3]:  # 처음 3개만 표시
                                            result += f"      • {jo_info.get('위임법령조문제목', '제목없음')}\n"
                                        if len(jo_info_list) > 3:
                                            result += f"      • ... 외 {len(jo_info_list) - 3}개 조문\n"
                        
                        result += "\n"
                else:
                    result += "ℹ️ 위임정보가 없습니다.\n"
            else:
                result += "ℹ️ 위임정보를 찾을 수 없습니다.\n"
        else:
            result += "ℹ️ 위임법령 정보를 찾을 수 없습니다.\n"
        
        return result
        
    except Exception as e:
        logger.error(f"위임법령 포매팅 중 오류: {e}")
        return f"위임법령 포매팅 중 오류가 발생했습니다: {str(e)}\n\n원본 데이터 키: {list(data.keys()) if data else '없음'}"

# misc_tools.py에서 이동할 도구들
@mcp.tool(name="get_effective_law_articles", description="""시행일 법령의 조항호목을 조회합니다.

⚠️ 중요: 반드시 search_effective_law 결과의 MST를 사용하세요!
- 현행법령 MST(search_law 결과)와 시행일법령 MST는 다를 수 있습니다.
- 현행법령 MST를 입력하면 잘못된 법령의 조문이 반환됩니다.

언제 사용:
- 시행일 법령의 특정 조문 내용을 상세히 조회할 때
- 법령의 항, 호, 목 단위까지 세부적으로 분석할 때

매개변수:
- mst: 시행일법령MST - **반드시 search_effective_law 도구의 결과에서 'MST' 필드값 사용**
- article_no: 조번호 (선택) - 예: "1", "15"
- include_content: 조문 전체 내용(항/호/목) 포함 여부 (기본값: True)
  - True: 항/호/목 전체 내용 포함 (상세 분석 시 권장)
  - False: 조문 목록/인덱스만 (목차 파악 시 권장)

현행법령 vs 시행일법령 조문 조회 구분:
- 현행법령 조문: search_law_articles (search_law 결과의 MST 사용)
- 시행일법령 조문: get_effective_law_articles (search_effective_law 결과의 MST 사용)

권장 워크플로우:
1. search_effective_law("개인정보보호법") → 시행일법령 MST 확인
2. get_effective_law_articles(mst="해당MST", article_no="15") → 제15조 상세 조회

사용 예시: get_effective_law_articles(mst="248613", article_no="15")""")
def get_effective_law_articles(
    mst: Union[str, int],
    article_no: Optional[str] = None,
    paragraph_no: Optional[str] = None,
    item_no: Optional[str] = None,
    subitem_no: Optional[str] = None,
    include_content: bool = True,
    display: int = 20,
    page: int = 1
) -> TextContent:
    """시행일 법령 조항호목 조회
    
    Args:
        mst: 법령일련번호(MST)
        article_no: 조 번호
        paragraph_no: 항 번호
        item_no: 호 번호
        subitem_no: 목 번호
        include_content: 조문 전체 내용(항/호/목) 포함 여부
        display: 결과 개수
        page: 페이지 번호
    """
    if not mst:
        return TextContent(type="text", text="법령일련번호(MST)를 입력해주세요.")
    
    try:
        # eflaw API 사용 (시행일 법령 본문 - 항/호/목 내용 포함)
        # eflawjosub API는 조문 메타데이터만 반환하여 항/호/목 내용 없음
        params = {
            "MST": str(mst)
        }
        
        # API 요청 - eflaw (시행일 법령 본문) API 사용
        data = _make_legislation_request("eflaw", params, is_detail=True, use_cache=True)
        
        # eflawjosub 전용 포맷팅 - 실제 조문 내용 반환
        result = _format_effective_law_articles(data, str(mst), article_no, paragraph_no, item_no, subitem_no, include_content)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"시행일 법령 조항호목 조회 중 오류: {e}")
        error_msg = f"시행일 법령 조항호목 조회 중 오류가 발생했습니다: {str(e)}\n\n"
        error_msg += "**해결방법:**\n"
        error_msg += f"1. 법령MST 확인: {mst} (올바른 시행일법령MST인지 확인)\n"
        error_msg += "2. OC(기관코드) 설정 확인: " + str(legislation_config.oc) + "\n"
        error_msg += "3. 대안: get_law_article_by_key() 사용 (현행법령 조문 조회)\n\n"
        error_msg += "**권장 워크플로우:**\n"
        error_msg += "```\n"
        error_msg += "# 1단계: 시행일 법령 검색\n"
        error_msg += 'search_effective_law("개인정보보호법")\n'
        error_msg += "\n# 2단계: 조항호목 조회\n"
        error_msg += f'get_effective_law_articles(mst="{mst}", article_no="15")\n'
        error_msg += "```"
        return TextContent(type="text", text=error_msg)

@mcp.tool(name="search_effective_law_articles_raw", description="""공포일 기준 시행일법령의 조항호목 메타데이터를 직접 조회합니다. 조문번호, 조문제목 등 목차 수준의 정보를 반환합니다.

참고: 상세 조문 내용이 필요하면 get_effective_law_articles를 사용하세요.

매개변수:
- mst: 법령일련번호(MST) (필수)
- display: 결과 개수 (최대 100)
- page: 페이지 번호

사용 예시: search_effective_law_articles_raw(mst="248613")""")
def search_effective_law_articles_raw(
    mst: Annotated[Union[str, int], "법령일련번호(MST)"],
    display: int = 100,
    page: int = 1
) -> TextContent:
    """시행일법령 조항호목 메타데이터 직접 조회 (eflawjosub target)"""
    try:
        params = {"MST": str(mst), "display": min(display, 100), "page": page}
        data = _make_legislation_request("eflawjosub", params, use_cache=True)
        result = _format_search_results(data, "eflawjosub", str(mst))
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"시행일법령 조항호목 조회 중 오류: {str(e)}")


def format_article_detail(article: Dict[str, Any]) -> str:
    """조문 상세 포맷팅"""
    import re
    
    num = article.get("조문번호", "")
    title = article.get("조문제목", "")
    content = article.get("조문내용", "")
    
    # 제목 구성
    if title:
        header = f"### 제{num}조({title})"
    else:
        header = f"### 제{num}조"
    
    result = header + "\n\n"
    
    # 조문 내용 처리
    if content and len(content.strip()) > 20:  # 실제 내용이 있는 경우
        # HTML 태그 제거
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = clean_content.strip()
        result += clean_content + "\n"
    else:
        # 항 내용 처리
        hangs = article.get("항", [])
        if isinstance(hangs, list) and hangs:
            for hang in hangs:
                if isinstance(hang, dict):
                    hang_content = hang.get("항내용", "")
                    if hang_content:
                        # HTML 태그 제거
                        clean_hang = re.sub(r'<[^>]+>', '', hang_content)
                        clean_hang = clean_hang.strip()
                        result += clean_hang + "\n\n"
                else:
                    result += str(hang) + "\n\n"
    
    # 시행일자
    if article.get("조문시행일자"):
        result += f"\n**시행일자**: {article.get('조문시행일자')}"
    
    # 변경 여부
    if article.get("조문변경여부") == "Y":
        result += f"\n최근 변경된 조문입니다."
    
    return result

def format_article_summary(article: Dict[str, Any]) -> str:
    """조문 요약 포맷팅"""
    import re
    
    num = article.get("조문번호", "")
    title = article.get("조문제목", "")
    content = article.get("조문내용", "")
    
    # 제목 구성
    if title:
        result = f"**제{num}조**({title})"
    else:
        result = f"**제{num}조**"
    
    # 내용 요약 (첫 150자)
    if content:
        # HTML 태그 제거
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = clean_content.strip()
        
        if len(clean_content) > 150:
            summary = clean_content[:150] + "..."
        else:
            summary = clean_content
            
        result += f"\n  {summary}"
    
    return result

@mcp.tool(name="get_effective_law_detail", description="""시행일 법령의 상세내용을 조회합니다.

⚠️ 중요: 반드시 search_effective_law 결과의 MST를 사용하세요!
- 현행법령 MST(search_law, get_law_detail)와 시행일법령 MST는 다를 수 있습니다.
- 현행법령 MST를 입력하면 잘못된 결과가 반환됩니다.

매개변수:
- effective_law_id: 시행일법령MST - **반드시 search_effective_law 도구의 결과에서 'MST' 필드값 사용**

현행법령 vs 시행일법령 구분:
- 현행법령 상세: get_law_detail (search_law 결과의 MST 사용)
- 시행일법령 상세: get_effective_law_detail (search_effective_law 결과의 MST 사용)

권장 워크플로우:
1. search_effective_law("개인정보보호법") → 시행일법령 MST 확인
2. get_effective_law_detail(effective_law_id="해당MST")

사용 예시: get_effective_law_detail(effective_law_id="123456")""")
def get_effective_law_detail(effective_law_id: Union[str, int]) -> TextContent:
    """시행일 법령 상세내용 조회
    
    Args:
        effective_law_id: 시행일법령일련번호(MST 우선)
    """
    if not effective_law_id:
        return TextContent(type="text", text="시행일 법령ID를 입력해주세요.")
    
    try:
        # 정상 작동하는 get_law_detail과 동일한 패턴 사용
        mst = str(effective_law_id)
        target = "eflaw"
        
        # 캐시 확인
        cache_key = get_cache_key(f"{target}_{mst}", "summary")
        cached_summary = load_from_cache(cache_key)
        
        if cached_summary:
            logger.info(f"캐시에서 시행일법령 요약 조회: {target}_{mst}")
            summary = cached_summary
        else:
            # API 호출 - get_law_detail과 동일한 방식 (OC, type는 _make_legislation_request에서 처리)
            params = {"MST": mst}
            data = _make_legislation_request(target, params, is_detail=True, use_cache=True)
            
            # 전체 데이터 캐시
            full_cache_key = get_cache_key(f"{target}_{mst}", "full")
            save_to_cache(full_cache_key, data)
            
            # 요약 추출
            summary = extract_law_summary_from_detail(data)
            save_to_cache(cache_key, summary)
        
        # 오류 메시지가 있는 경우 별도 처리
        if summary.get('오류메시지'):
            return TextContent(type="text", text=f"""**시행일법령 조회 결과**

**요청 ID**: {effective_law_id}

⚠️ **조회 실패**: {summary.get('오류메시지')}

**가능한 원인**:
1. 시행일법령 ID가 올바르지 않음
2. 해당 법령이 현재 시행일법령으로 등록되지 않음  
3. API 데이터베이스에 정보가 없음

**대안 방법**:
1. **일반 법령으로 조회**: get_law_detail(mst="{effective_law_id}")
2. **시행일법령 검색**: search_effective_law("법령명")
3. **전체 법령 검색**: search_law("법령명")

**참고**: 시행일법령은 특정 일자에 시행 예정인 법령만 포함됩니다.""")
        
        # 포맷팅 - get_law_detail과 동일한 방식
        result = f"**{summary.get('법령명', '제목없음')}** 상세 (시행일법령)\n"
        result += "=" * 50 + "\n\n"
        
        result += "**기본 정보:**\n"
        result += f"• 법령ID: {summary.get('법령ID', '정보없음')}\n"
        result += f"• 법령일련번호: {summary.get('법령일련번호', '정보없음')}\n"
        result += f"• 공포일자: {summary.get('공포일자', '정보없음')}\n"
        result += f"• 시행일자: {summary.get('시행일자', '정보없음')}\n"
        result += f"• 소관부처: {summary.get('소관부처', '정보없음')}\n\n"
        
        # 조문 인덱스
        article_index = summary.get('조문_인덱스', [])
        total_articles = summary.get('조문_총개수', 0)
        
        if article_index:
            result += f"**조문 인덱스** (총 {total_articles}개 중 첫 {len(article_index)}개)\n\n"
            for item in article_index:
                result += f"• {item['key']}: {item['summary']}\n"
            result += "\n"
        
        # 제개정이유
        reason = summary.get('제개정이유', '')
        if reason:
            result += f"**제개정이유:**\n{reason}\n\n"
        
        result += f"**특정 조문 보기**: get_law_article_by_key(mst=\"{mst}\", target=\"{target}\", article_key=\"제1조\")\n"
        result += f"**원본 크기**: {summary.get('원본크기', 0):,} bytes\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"시행일 법령 상세조회 중 오류: {e}")
        error_msg = f"시행일 법령 상세조회 중 오류가 발생했습니다: {str(e)}\n\n"
        error_msg += "**해결방법:**\n"
        error_msg += f"1. 법령ID 확인: {effective_law_id} (올바른 시행일법령ID인지 확인)\n"
        error_msg += "2. OC(기관코드) 설정 확인: " + str(legislation_config.oc) + "\n"
        error_msg += "3. 대안: get_law_detail() 사용 권장\n\n"
        error_msg += "**권장 워크플로우:**\n"
        error_msg += "```\n"
        error_msg += "# 1단계: 시행일 법령 검색\n"
        error_msg += 'search_effective_law("개인정보보호법")\n'
        error_msg += "\n# 2단계: 상세 조회\n"
        error_msg += f'get_law_detail(mst="{effective_law_id}")\n'
        error_msg += "```"
        return TextContent(type="text", text=error_msg)



def _has_meaningful_content(data: dict) -> bool:
    """응답 데이터에 의미있는 내용이 있는지 확인 (법령 전용)"""
    if not data or "error" in data:
        return False
    
    # 실제 API 응답에서 확인할 수 있는 패턴들
    meaningful_patterns = [
        # 검색 결과
        ("LawSearch", "law"),
        ("LsStmdSearch", "law"),
        # 서비스 결과
        ("LawService", "DelegatedLaw"),
        ("LawService", "LawHistory"),
        ("LawService", "law"),
        # 직접 키
        ("LawHistory",),
        ("DelegatedLaw",),
        ("lawSearchList",),
        ("법령",),
        ("조문",),
    ]
    
    for pattern in meaningful_patterns:
        current_data = data
        valid = True
        
        for key in pattern:
            if key in current_data:
                current_data = current_data[key]
            else:
                valid = False
                break
        
        if valid:
            # 마지막 데이터가 의미있는지 확인
            if isinstance(current_data, list) and len(current_data) > 0:
                return True
            elif isinstance(current_data, dict) and current_data:
                return True
            elif isinstance(current_data, str) and current_data.strip():
                return True
    
    return False


def _format_law_history_detail(data: dict, history_id: str) -> str:
    """법령연혁 상세 정보 포매팅"""
    try:
        if 'LawHistory' in data:
            history_info = data['LawHistory']
            if isinstance(history_info, list) and history_info:
                history_info = history_info[0]
            
            result = f"**법령연혁 상세정보**\n\n"
            result += f"**연혁ID**: {history_id}\n"
            
            if '법령명' in history_info:
                result += f"**법령명**: {history_info['법령명']}\n"
            if '개정일자' in history_info:
                result += f"**개정일자**: {history_info['개정일자']}\n"
            if '시행일자' in history_info:
                result += f"⏰ **시행일자**: {history_info['시행일자']}\n"
            if '개정구분' in history_info:
                result += f"🔄 **개정구분**: {history_info['개정구분']}\n"
            if '개정내용' in history_info:
                result += f"**개정내용**: {history_info['개정내용']}\n"
            
            return result
        else:
            return f"'{history_id}'에 대한 법령연혁 상세 정보를 찾을 수 없습니다."
    except Exception as e:
        logger.error(f"법령연혁 상세정보 포매팅 중 오류: {e}")
        return f"법령연혁 상세정보 포매팅 중 오류가 발생했습니다: {str(e)}"

@mcp.tool(
    name="search_law_unified",
    description="""[권장] 모든 법령 검색의 시작점 - 범용 통합 검색 도구입니다.

주요 용도:
- 일반적인 키워드로 관련 법령 탐색 (예: "부동산", "교통", "개인정보")
- 법령명을 정확히 모를 때 검색
- 다양한 종류의 법령을 한 번에 검색
- 법령의 역사, 영문판, 시행일 등 다양한 관점에서 검색

매개변수:
- query: 검색어 (필수) - 법령명, 키워드, 주제 등 자유롭게 입력
- target: 검색 대상 (기본값: "law")
  - law: 현행법령
  - eflaw: 시행일법령  
  - lsHistory: 법령연혁
  - elaw: 영문법령
  - 기타 20여개 타겟 지원
- display: 결과 개수 (최대 100)
- page: 페이지 번호
- search: 검색범위 (1=법령명, 2=본문검색)

반환정보: 법령명, 법령ID, 법령일련번호(MST), 공포일자, 시행일자, 소관부처

권장 사용 순서:
1. search_law_unified("금융") → 관련 법령 목록 파악
2. 구체적인 법령명 확인 후 → search_law("은행법")로 정밀 검색

사용 예시:
- search_law_unified("금융")  # 금융 관련 모든 법령 검색
- search_law_unified("세무", search=2)  # 본문에 세무 포함된 법령
- search_law_unified("개인정보", target="law")  # 개인정보 관련 법령 검색
- search_law_unified("Income Tax Act", target="elaw")  # 영문 소득세법 검색"""
)
def search_law_unified(
    query: str,
    target: str = "law",
    display: int = 10,
    page: int = 1,
    search: int = 1,
    sort: Optional[str] = None,
    ministry_code: Optional[str] = None,
    law_type_code: Optional[str] = None
) -> TextContent:
    """통합 법령 검색"""
    if not query:
        return TextContent(type="text", text="검색어를 입력해주세요.")
    
    try:
        params = {
            "query": query,
            "display": min(display, 100),
            "page": page,
            "search": search
        }
        
        # 선택적 파라미터 추가
        if sort:
            params["sort"] = sort
        if ministry_code:
            params["ministryCode"] = ministry_code
        if law_type_code:
            params["lawTypeCode"] = law_type_code
        
        data = _make_legislation_request(target, params, is_detail=False, use_cache=True)
        
        # 응답 파싱
        search_data = data.get("LawSearch", {})
        items = search_data.get("law", search_data.get(target, []))
        if not isinstance(items, list):
            items = [items] if items else []
        
        total_count = int(search_data.get("totalCnt", 0))
        
        result = f"**'{query}' 검색 결과** (target: {target}, 총 {total_count}건)\n"
        result += "=" * 50 + "\n\n"
        
        for i, item in enumerate(items, 1):
            # 법령명
            law_name = (item.get("법령명한글") or item.get("법령명") or 
                       item.get("현행법령명") or "제목없음")
            
            # 법령일련번호 (상세조회용)
            mst = item.get("법령일련번호")
            law_id = item.get("법령ID")
            
            result += f"**{i}. {law_name}**\n"
            result += f"   • 법령ID: {law_id}\n"
            result += f"   • 법령일련번호: {mst}\n"
            result += f"   • 공포일자: {item.get('공포일자', '')}\n"
            result += f"   • 시행일자: {item.get('시행일자', '')}\n"
            result += f"   • 소관부처: {item.get('소관부처명', '')}\n"
            result += f"   • 구분: {item.get('법령구분명', '')}\n"
            result += f"   상세조회: get_law_detail(mst=\"{mst}\")\n"
            result += "\n"
        
        if total_count > len(items):
            result += f"더 많은 결과가 있습니다. page 파라미터를 조정하세요.\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"통합 검색 중 오류: {e}")
        return TextContent(type="text", text=f"검색 중 오류가 발생했습니다: {str(e)}")

# 법령 상세 조회는 get_law_detail 도구 사용

@mcp.tool(
    name="get_law_detail",
    description="""법령 상세 정보를 조회합니다.

[중요] mst 입력 가이드:
- search_law 결과의 MST(법령일련번호) 값만 입력
- 올바른 예: "248929", "270351"
- 잘못된 예: "은행법", "248929번 법령" (법령명이나 문장 금지)

매개변수:
- mst: 숫자로 된 법령일련번호만 입력

반환정보: 법령명, 공포일자, 시행일자, 조문 목록

사용 흐름:
1. search_law("은행법") → MST 확인 (예: 248929)
2. get_law_detail(mst="248929") → 상세 조회

참고: 특정 조문은 get_law_article_by_key 사용"""
)
def get_law_detail(mst: str) -> TextContent:
    """법령 상세 정보 조회"""
    if not mst:
        return TextContent(type="text", text="법령일련번호(mst)를 입력해주세요.")
    
    try:
        # 캐시 확인
        cache_key = get_cache_key(f"law_{mst}", "summary")
        cached_summary = load_from_cache(cache_key)
        
        if cached_summary:
            logger.info(f"캐시에서 요약 조회: law_{mst}")
            summary = cached_summary
        else:
            # API 호출
            params = {"MST": mst}
            data = _make_legislation_request("law", params, is_detail=True, use_cache=True)
            
            # 전체 데이터 캐시
            full_cache_key = get_cache_key(f"law_{mst}", "full")
            save_to_cache(full_cache_key, data)
            
            # 요약 추출
            summary = extract_law_summary_from_detail(data)
            save_to_cache(cache_key, summary)
        
        # 포맷팅
        result = format_law_detail_summary(summary, mst, "law")
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"법령 상세 조회 중 오류: {e}")
        return TextContent(type="text", text=f"법령 상세 조회 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(
    name="get_law_article_by_key",
    description="""특정 조문의 전체 내용을 조회합니다.

[중요] 파라미터 입력 가이드:
- mst: 숫자로 된 법령일련번호만 (예: "248929")
- target: "law" 고정
- article_key: "제15조" 또는 "15" 형식만 (문장 금지)

잘못된 예:
- article_key="동의 관련 조항" (문장 금지)
- article_key="개인정보 수집 조문" (설명 금지)

사용 흐름:
1. search_law("은행법") → MST 확인
2. get_law_detail(mst="248929") → 조문 목록 확인
3. get_law_article_by_key(mst="248929", target="law", article_key="제15조")

사용 예시:
- get_law_article_by_key(mst="248929", target="law", article_key="제34조")
- get_law_article_by_key(mst="270351", target="law", article_key="15")"""
)
def get_law_article_by_key(
    mst: str,
    target: str,
    article_key: str
) -> TextContent:
    """특정 조문 전체 내용 조회"""
    if not all([mst, target, article_key]):
        return TextContent(type="text", text="mst, target, article_key 모두 입력해주세요.")
    
    try:
        # 캐시에서 전체 데이터 조회
        full_cache_key = get_cache_key(f"{target}_{mst}", "full")
        cached_data = load_from_cache(full_cache_key)
        
        if not cached_data:
            return TextContent(
                type="text", 
                text=f"캐시된 데이터가 없습니다. 먼저 get_law_detail을 호출하세요."
            )
        
        # 조문 추출 - 실제 API 구조에 맞게
        law_info = cached_data.get("법령", {})
        articles_section = law_info.get("조문", {})
        article_units = []
        
        if isinstance(articles_section, dict) and "조문단위" in articles_section:
            article_units = articles_section.get("조문단위", [])
            # 리스트가 아닌 경우 리스트로 변환
            if not isinstance(article_units, list):
                article_units = [article_units] if article_units else []
        elif isinstance(articles_section, list):
            article_units = articles_section
        
        # 조문 번호 정규화
        article_num = normalize_article_key(article_key)
        
        # 조문 찾기
        found_article = find_article_in_data(article_units, article_num)
        
        if not found_article:
            # 사용 가능한 조문 번호들 표시
            available_articles = get_available_articles(article_units, 10)
            
            return TextContent(
                type="text",
                text=f"'{article_key}'를 찾을 수 없습니다.\n"
                     f"사용 가능한 조문: {', '.join(available_articles)} ..."
            )
        
        # 법령명 추출
        law_name = law_info.get("기본정보", {}).get("법령명_한글", "")
        
        # 조문 내용 포맷팅
        result = format_article_content(found_article, law_name, article_key)
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"조문 조회 중 오류: {e}")
        return TextContent(type="text", text=f"조문 조회 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(
    name="get_law_articles_range",
    description="""연속된 여러 조문을 한번에 조회합니다.

매개변수:
- mst: 법령일련번호 (필수) - search_law_unified, search_law 도구의 결과에서 'MST' 필드값 사용
- target: API 타겟 (필수) - get_law_detail과 동일한 값 사용
- start_article: 시작 조문 번호 (기본값: 1) - 숫자만 입력
- count: 조회할 조문 개수 (기본값: 5)
- include_details: 상세 내용 포함 여부 (기본값: True)
  - True: 항/호/목 전체 포함 (상세 분석 시 권장)
  - False: 조문 개요만 (목차/흐름 파악 시 권장)

반환정보: 요청한 범위의 조문들의 전체 내용

사용 예시:
- get_law_articles_range(mst="265959", target="law", start_article=50, count=5)
  # 제50조부터 제54조까지 5개 조문 조회 (항/호/목 포함)
- get_law_articles_range(mst="265959", target="law", start_article=1, count=10, include_details=False)
  # 제1조부터 10개 조문 개요만 조회 (목차 파악용)

참고: 페이징 방식으로 여러 조문을 효율적으로 탐색할 수 있습니다."""
)
def get_law_articles_range(
    mst: str,
    target: str,
    start_article: int = 1,
    count: int = 5,
    include_details: bool = True
) -> TextContent:
    """연속된 조문 범위 조회"""
    if not all([mst, target]):
        return TextContent(type="text", text="mst, target 모두 입력해주세요.")
    
    try:
        # 캐시에서 전체 데이터 조회
        full_cache_key = get_cache_key(f"{target}_{mst}", "full")
        cached_data = load_from_cache(full_cache_key)
        
        if not cached_data:
            # 캐시가 없으면 API 직접 호출
            params = {"MST": mst}
            cached_data = _make_legislation_request(target, params, is_detail=True, use_cache=True)
            
            # 데이터 검증 로그
            try:
                law_info = cached_data.get("법령", {})
                articles = law_info.get("조문", {}).get("조문단위", [])
                logger.info(f"API 응답 수신 - 전체 조문 수: {len(articles)}")
                
                # 첫 번째 실제 조문 확인
                for art in articles:
                    if art.get("조문여부") == "조문":
                        art_no = art.get("조문번호", "")
                        hangs = art.get("항", [])
                        logger.info(f"첫 번째 조문: 제{art_no}조, 항 개수: {len(hangs)}")
                        break
            except Exception as e:
                logger.warning(f"API 응답 검증 중 오류: {e}")
            
            # 캐시 저장 시도 (실패해도 계속 진행)
            try:
                save_to_cache(full_cache_key, cached_data)
            except:
                pass
        
        # 조문 추출
        law_info = cached_data.get("법령", {})
        articles_section = law_info.get("조문", {})
        article_units = []
        
        if isinstance(articles_section, dict) and "조문단위" in articles_section:
            article_units = articles_section.get("조문단위", [])
            # 리스트가 아닌 경우 리스트로 변환
            if not isinstance(article_units, list):
                article_units = [article_units] if article_units else []
        elif isinstance(articles_section, list):
            article_units = articles_section
        
        # 실제 조문만 필터링 (조문여부가 "조문"인 것만)
        actual_articles = []
        for i, article in enumerate(article_units):
            if article.get("조문여부") == "조문":
                actual_articles.append(article)
        
        # 시작/끝 인덱스 계산
        start_idx = None
        for idx, article in enumerate(actual_articles):
            if int(article.get("조문번호", "0")) == start_article:
                start_idx = idx
                break
        
        if start_idx is None:
            available_articles = []
            for article in actual_articles[:10]:
                no = article.get("조문번호", "")
                if no:
                    available_articles.append(f"제{no}조")
            return TextContent(
                type="text",
                text=f"제{start_article}조를 찾을 수 없습니다.\n"
                     f"사용 가능한 조문: {', '.join(available_articles)} ..."
            )
        
        end_idx = min(start_idx + count, len(actual_articles))
        selected_articles = actual_articles[start_idx:end_idx]
        
        # 조문 내용 포맷팅
        law_name = law_info.get("기본정보", {}).get("법령명_한글", "")
        
        end_article_no = int(selected_articles[-1].get("조문번호", start_article))
        result = f"📚 **{law_name}** 조문 (제{start_article}조 ~ 제{end_article_no}조)\n"
        result += "=" * 50 + "\n\n"
        
        for article in selected_articles:
            article_no = article.get("조문번호", "")
            article_title = article.get("조문제목", "")
            
            result += f"## 제{article_no}조"
            if article_title:
                result += f"({article_title})"
            result += "\n\n"
            
            # 공통 함수로 본문 포맷팅 (항/호/목 포함 여부 선택)
            result += format_article_body(article, include_details=include_details)
            
            result += "-" * 30 + "\n\n"
        
        return TextContent(type="text", text=result.strip())
        
    except Exception as e:
        logger.error(f"조문 범위 조회 중 오류: {e}")
        return TextContent(type="text", text=f"조문 범위 조회 중 오류가 발생했습니다: {str(e)}")

