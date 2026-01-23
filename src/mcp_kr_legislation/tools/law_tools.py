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
    # 공통 유틸리티
    clean_html_tags, safe_get_nested_value
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

def _make_legislation_request(target: str, params: dict, is_detail: bool = False, timeout: int = 10) -> dict:
    """법제처 API 요청 공통 함수"""
    try:
        # 시간이 많이 걸리는 API들은 더 긴 타임아웃 설정
        if target in ["lsHstInf", "lsStmd", "lawHst"]:  # 변경이력, 체계도, 법령연혁
            timeout = max(timeout, 60)  # 최소 60초
        
        # URL 생성 - 올바른 target 파라미터 사용
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
            if target in ["elaw", "ordinance", "ordinanceApp"]:
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
            
            change_details = {
                '제정': {'icon': '[제정]', 'desc': '신규 법령 제정'},
                '전부개정': {'icon': '[전부개정]', 'desc': '법령 전면 개정'},
                '일부개정': {'icon': '[일부개정]', 'desc': '부분 조문 개정'},
                '조문변경': {'icon': '[조문변경]', 'desc': '조문 내용 변경'},
                '타법개정': {'icon': '[타법개정]', 'desc': '타법 제정에 따른 개정'},
                '폐지': {'icon': '[폐지]', 'desc': '법령 폐지'}
            }
            
            change_info = change_details.get(변경사유, {'icon': '[변경]', 'desc': '조문 변경'})
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
        
        # 금융·세무·개인정보보호 도메인 키워드 매핑
        domain_keywords = {
            "은행": ["은행", "금융", "여신", "대출", "예금"],
            "금융": ["금융", "은행", "증권", "보험", "여신", "대출"],
            "소득세": ["소득세", "세무", "세금", "과세", "공제"],
            "법인세": ["법인세", "세무", "세금", "과세"],
            "부가가치세": ["부가가치세", "부가세", "세무", "세금"],
            "개인정보": ["개인정보", "프라이버시", "정보보호", "개인정보보호"],
            "자본시장": ["자본시장", "증권", "투자", "금융투자"]
        }
        
        # 도메인별 확장 키워드 생성
        expanded_keywords = set([query_normalized])
        for domain, keywords in domain_keywords.items():
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
            
            # 추가 필터링 - 명백히 무관한 법령 제외
            irrelevant_patterns = [
                "10.27법난", "법난", "4.19혁명", "혁명", "6.25사변", "사변",
                "독립유공자", "국가유공자", "보훈", "참전", "전몰", "순국",
                "선거", "정당", "국정감사", "국정조사"
            ]
            
            for pattern in irrelevant_patterns:
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
        elif target == "lnkLsOrd" and 'OrdinSearch' in data:
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
        elif 'LawSearch' in data and target not in ["thdCmp", "licbyl", "trty", "lsRlt", "ordinfd", "ordin", "admrul", "admrulOldAndNew", "lnkLsOrd", "prec", "expc", "decc", "couseLs"]:
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
        elif target in data:
            # 직접 타겟 구조
            target_data = data[target]
        else:
            # 단일 키 구조 확인
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
            elif target == "lnkLsOrd":
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
        
        if total_count > max_results:
            result += f"더 많은 결과가 있습니다. 검색어를 구체화하거나 페이지 번호를 조정해보세요.\n"
        
        return result
        
    except Exception as e:
        logger.error(f"결과 포맷팅 오류: {e}")
        return f"검색 결과 처리 중 오류가 발생했습니다: {str(e)}"

def _format_effective_law_articles(data: dict, law_id: str, article_no: Optional[str] = None, 
                                  paragraph_no: Optional[str] = None, item_no: Optional[str] = None, 
                                  subitem_no: Optional[str] = None) -> str:
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
                result += f"**{i}. 제{article.get('조문번호', '?')}조"
                
                # 조문 제목
                if article.get('조문제목'):
                    result += f": {article.get('조문제목')}"
                    
                result += "**\n\n"
                
                # 시행일자 정보
                if article.get('조문시행일자'):
                    date_str = article.get('조문시행일자')
                    # YYYYMMDD -> YYYY-MM-DD 변환
                    if len(date_str) == 8:
                        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        result += f"**시행일자:** {formatted_date}\n\n"
                
                # 조문 키 정보
                if article.get('조문키'):
                    result += f"🔑 **조문키:** {article.get('조문키')}\n\n"
                
                # 조문 변경 여부
                if article.get('조문변경여부'):
                    result += f"**변경여부:** {article.get('조문변경여부')}\n\n"
                
                # 조문 상세 내용을 위한 안내
                result += f"**상세 내용 보기:**\n"
                result += f"   get_law_article_by_key(mst=\"{law_id}\", target=\"eflaw\", article_key=\"제{article.get('조문번호')}조\")\n\n"
                
                result += "-" * 40 + "\n\n"
        
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
    
    # 일반 키워드를 구체적인 법령명으로 매핑
    keyword_mapping = {
        "금융": ["은행법", "자본시장과 금융투자업에 관한 법률", "보험업법", "여신전문금융업법", "금융소비자 보호에 관한 법률"],
        "은행": ["은행법", "금융실명거래 및 비밀보장에 관한 법률", "예금자보호법", "한국은행법"],
        "세무": ["소득세법", "법인세법", "부가가치세법", "상속세 및 증여세법", "조세특례제한법"],
        "세금": ["소득세법", "법인세법", "부가가치세법", "지방세법", "관세법"],
        "개인정보": ["개인정보 보호법", "정보통신망 이용촉진 및 정보보호 등에 관한 법률", "신용정보의 이용 및 보호에 관한 법률"],
        "투자": ["자본시장과 금융투자업에 관한 법률", "간접투자자산 운용업법", "집합투자업법"],
        "보험": ["보험업법", "보험업 감독규정", "생명보험법", "손해보험법"]
    }
    
    # 일반 키워드인 경우 구체적인 법령들로 검색
    if search_query.lower() in keyword_mapping:
        suggested_laws = keyword_mapping[search_query.lower()]
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
                data = _make_legislation_request("law", params, is_detail=False)
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
                data = _make_legislation_request("law", params, is_detail=False)
                
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
                data = _make_legislation_request("law", params, is_detail=False)
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
    
    try:
        # 기본 파라미터 설정 - 다른 검색 도구와 동일한 패턴 사용
        params = {
            "OC": legislation_config.oc,  # 직접 OC 포함
            "type": "JSON",               # 직접 type 포함
            "target": "elaw",            # 영문법령은 target이 'elaw'
            "query": search_query,
            "search": search,
            "display": min(display, 100),
            "page": page
        }
        
        # 선택적 파라미터 추가
        optional_params = {
            "sort": sort,
            "lawType": law_type,
            "promulgateDate": promulgate_date,
            "enforceDate": enforce_date
        }
        
        for key, value in optional_params.items():
            if value is not None:
                params[key] = value
        
        # API 요청 - 영문법령은 is_detail=False로 명시
        data = _make_legislation_request("elaw", params, is_detail=False)
        result = _format_search_results(data, "elaw", search_query)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"영문법령 검색 중 오류: {e}")
        return TextContent(type="text", text=f"영문법령 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_english_law_detail", description="""영문 법령의 상세 내용을 조회합니다.

언제 사용:
- 영문 법령의 전체 조문과 상세 내용을 확인할 때
- search_law_unified 또는 search_english_law로 MST를 확보한 후 상세 조회할 때

매개변수:
- mst: 법령일련번호(MST) (필수) - 영문법령 검색 결과에서 'MST' 또는 '법령일련번호' 필드값 사용

반환정보: 영문법령 전체 조문, 법령 구조, 조문별 영문 내용, 시행일자

권장 워크플로우:
1단계: search_law_unified("Civil Act", target="elaw") → MST 확인
2단계: get_english_law_detail(mst="204485") → 영문법령 전체 내용 조회

또는:
1단계: search_english_law("Civil Act") → MST 확인  
2단계: get_english_law_detail(mst="204485") → 영문법령 전체 내용 조회

사용 예시: get_english_law_detail(mst="204485")""")
def get_english_law_detail(mst: Annotated[Union[str, int], "법령일련번호(MST)"] = "") -> TextContent:
    """영문법령 상세내용 조회"""
    if not mst:
        return TextContent(type="text", text="법령일련번호(MST)를 입력해주세요.")
    
    try:
        # API 요청 파라미터 - 한글 법령과 동일한 단순한 패턴 사용
        params = {"MST": str(mst)}
        data = _make_legislation_request("elaw", params, is_detail=True)
        
        # 영문 법령 전용 포맷팅
        result = _format_english_law_detail(data, str(mst))
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"영문법령 상세조회 중 오류: {e}")
        return TextContent(type="text", text=f"영문법령 상세조회 중 오류가 발생했습니다: {str(e)}")

def _format_english_law_detail(data: dict, law_id: str) -> str:
    """영문 법령 상세 정보 포맷팅"""
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
        
        # 3. 조문 표시 우선순위: 실제 조문 > 부칙
        if main_articles:
            result += f"**법령 조문** ({len(main_articles)}개)\n\n"
            display_count = min(10, len(main_articles))  # 실제 조문은 더 많이 표시
            
            for i, article in enumerate(main_articles[:display_count], 1):
                article_content = article.get('joCts', '')
                article_no = article.get('joNo', str(i))
                
                if article_content:
                    # 내용이 너무 길면 앞부분만 표시
                    preview = article_content[:800]  # 조문은 조금 더 길게
                    if len(article_content) > 800:
                        preview += "..."
                    
                    result += f"**Article {article_no}:**\n"
                    result += f"{preview}\n\n"
            
            if len(main_articles) > display_count:
                result += f"... (총 {len(main_articles)}개 조문 중 {display_count}개만 표시)\n\n"
                
        elif addenda_articles:
            result += f"**부칙 및 경과조치** ({len(addenda_articles)}개)\n\n"
            display_count = min(3, len(addenda_articles))  # 부칙은 적게 표시
            
            for i, article in enumerate(addenda_articles[:display_count], 1):
                article_content = article.get('arCts', '')
                
                if article_content:
                    preview = article_content[:500]
                    if len(article_content) > 500:
                        preview += "..."
                    
                    result += f"**부칙 {article.get('No', i)}:**\n"
                    result += f"{preview}\n\n"
        else:
            return f"조문 내용을 찾을 수 없습니다. (MST: {law_id})"
        
        # 4. 부가 정보
        if 'BylSection' in law_data and law_data['BylSection']:
            result += f"**별표/서식**: 있음\n"
        
        result += f"\n**MST**: {law_id}\n"
        
        if main_articles:
            result += f"**전체 조문 개수**: {len(main_articles)}개"
            if addenda_articles:
                result += f" (+ 부칙 {len(addenda_articles)}개)"
        elif addenda_articles:
            result += f"**부칙 개수**: {len(addenda_articles)}개"
        
        return result
        
    except Exception as e:
        logger.error(f"영문법령 포맷팅 중 오류: {e}")
        return f"법령 정보 처리 중 오류가 발생했습니다: {str(e)}"

@mcp.tool(
    name="search_effective_law", 
    description="""시행일 기준 법령을 검색합니다.
    
매개변수:
- query: 검색어 (선택) - 법령명
- search: 검색범위 (1=법령명, 2=본문검색)
- display: 결과 개수 (max=100)
- page: 페이지 번호
- status_type: 시행상태 (100=시행, 200=미시행, 300=폐지)
- law_id: 법령ID
- sort: 정렬 옵션
- effective_date_range: 시행일자 범위 (20090101~20090130)
- date: 공포일자 (YYYYMMDD)
- revision_type: 제개정 종류
- ministry_code: 소관부처 코드
- law_type_code: 법령종류 코드

반환정보: 법령명, 시행일자, 시행상태, 법령ID, 공포일자, 소관부처

사용 예시: search_effective_law("소득세법", status_type=100), search_effective_law("개인정보보호법", status_type=200)""",
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
        data = _make_legislation_request("eflaw", params, is_detail=False)
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
        data = _make_legislation_request("lsAbrv", params)
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
        data = _make_legislation_request("delHst", params, is_detail=False)
        result = _format_search_results(data, "delHst", "삭제된 법령 데이터")
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"삭제된 법령 데이터 검색 중 오류: {e}")
        return TextContent(type="text", text=f"삭제된 법령 데이터 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="search_law_articles", description="""법령의 조문을 검색합니다.

매개변수:
- mst: 법령일련번호(MST) (필수) - search_law 도구의 결과에서 'MST' 또는 '법령일련번호' 필드값 사용
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 조문번호, 조문제목, 조문내용 일부, 조문ID

사용 예시:
- search_law_articles(mst="267581")  # 은행법 조문 목록
- search_law_articles(mst="248613", display=50)  # 개인정보보호법 조문 50개
- search_law_articles(mst="248613", page=2)  # 개인정보보호법 2페이지""")
def search_law_articles(
    mst: Annotated[Union[str, int], "법령일련번호(MST) - search_law 결과에서 사용"],
    display: Annotated[int, "결과 개수 (최대 100)"] = 20,
    page: Annotated[int, "페이지 번호"] = 1
) -> TextContent:
    """법령 조문 검색 (현행법령 본문 조항호목 조회)
    
    Args:
        mst: 법령일련번호(MST)
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
            detail_data = _make_legislation_request("law", detail_params, is_detail=True)
            
            if detail_data and "법령" in detail_data:
                # 법령 상세 정보에서 조문 추출
                result = _format_law_detail_articles(detail_data, mst_str)
                return TextContent(type="text", text=result)
        except Exception as e:
            logger.warning(f"MST로 조문 조회 실패: {e}")
        
        # 2단계: MST 실패시 ID로 시도  
        try:
            # 법령ID가 MST인지 ID인지 확인 후 적절한 검색 수행
            if len(mst_str) >= 6 and mst_str.isdigit():
                # MST 형태인 경우 - 해당 MST로 직접 상세 조회 재시도
                detail_params = {"MST": mst_str}
                detail_data = _make_legislation_request("law", detail_params, is_detail=True)
                
                if detail_data and "법령" in detail_data:
                    result = _format_law_detail_articles(detail_data, mst_str, mst_str)
                    return TextContent(type="text", text=result)
            else:
                # 일반 ID 형태인 경우 - ID로 검색
                search_params = {
                    "query": f"법령ID:{mst_str}",
                    "display": 5,
                    "type": "JSON"
                }
                search_data = _make_legislation_request("law", search_params, is_detail=False)
                
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
                                detail_data = _make_legislation_request("law", detail_params, is_detail=True)
                                
                                if detail_data and "법령" in detail_data:
                                    result = _format_law_detail_articles(detail_data, mst_str, law_mst)
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


def _format_law_detail_articles(detail_data: dict, law_id: str, actual_mst: str = "") -> str:
    """법령 상세 정보에서 조문만 추출하여 포맷팅"""
    try:
        law_info = detail_data.get("법령", {})
        basic_info = law_info.get("기본정보", {})
        law_name = basic_info.get("법령명_한글", basic_info.get("법령명한글", ""))
        
        result = f"**법령 조문 목록** (상세 조회 방식)\n\n"
        result += f"**요청 ID**: {law_id}\n"
        if actual_mst:
            result += f"**실제 MST**: {actual_mst}\n"
        result += f"**법령명**: {law_name}\n\n"
        
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
                actual_articles.append(article)
        
        if actual_articles:
            result += f"**총 {len(actual_articles)}개 조문**\n\n"
            
            for i, article in enumerate(actual_articles[:20], 1):  # 처음 20개만 표시
                article_no = article.get("조문번호", "")
                article_title = article.get("조문제목", "")
                article_content = article.get("조문내용", "")
                
                result += f"**{i}. 제{article_no}조"
                if article_title:
                    result += f"({article_title})"
                result += "**\n"
                
                # 조문 내용 미리보기
                if article_content:
                    content_preview = article_content.strip()[:200]
                    if len(article_content) > 200:
                        content_preview += "..."
                    result += f"   {content_preview}\n\n"
                else:
                    result += "   (내용 없음)\n\n"
            
            if len(actual_articles) > 20:
                result += f"... 외 {len(actual_articles) - 20}개 조문\n\n"
            
            result += f"**특정 조문 상세 보기**:\n"
            result += f"```\nget_law_article_by_key(mst=\"{actual_mst or law_id}\", target=\"law\", article_key=\"제1조\")\n```"
        else:
            result += "**조문을 찾을 수 없습니다.**\n\n"
            result += "**가능한 원인**:\n"
            result += "- 해당 법령에 조문이 없음 (규칙, 고시 등)\n"
            result += "- 법령ID가 올바르지 않음\n"
            result += "- API 응답 구조 변경\n\n"
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
        data = _make_legislation_request("oldAndNew", params)
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
        data = _make_legislation_request("oldAndNew", params, is_detail=True)
        
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
        data = _make_legislation_request("thdCmp", params)
        search_term = query or "3단비교"
        result = _format_search_results(data, "thdCmp", search_term)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"3단비교 검색 중 오류: {e}")
        return TextContent(type="text", text=f"3단비교 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_three_way_comparison_detail", description="""3단비교 본문을 조회합니다.

매개변수:
- mst: 법령일련번호 (search_three_way_comparison 결과에서 획득)
- knd: 비교종류 (1=위임조문, 2=인용조문, 기본값: 1)

반환정보: 상위법령-하위법령-조문의 3단 비교 내용

사용 예시:
- get_three_way_comparison_detail("222549")  # 위임조문 비교
- get_three_way_comparison_detail("222549", knd=2)  # 인용조문 비교

참고: search_three_way_comparison으로 먼저 목록을 검색한 후 법령일련번호를 사용하세요.""")
def get_three_way_comparison_detail(
    mst: Annotated[str, "법령일련번호 (MST)"],
    knd: Annotated[int, "비교종류 (1=위임조문, 2=인용조문)"] = 1,
) -> TextContent:
    """3단비교 본문 조회"""
    try:
        params = {"MST": str(mst), "knd": knd}
        data = _make_legislation_request("thdCmp", params, is_detail=True)
        
        if not data:
            return TextContent(type="text", text=f"법령일련번호 {mst}에 해당하는 3단비교 정보를 찾을 수 없습니다.")
        
        # 응답 포맷팅
        result = _format_three_way_comparison_detail(data, mst, knd)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"3단비교 본문 조회 중 오류: {e}")
        return TextContent(type="text", text=f"3단비교 본문 조회 중 오류가 발생했습니다: {str(e)}")

def _format_three_way_comparison_detail(data: dict, mst: str, knd: int) -> str:
    """3단비교 본문 포맷팅"""
    knd_name = "위임조문" if knd == 1 else "인용조문"
    lines = [f"# 3단비교 상세 - {knd_name} (MST: {mst})\n"]
    
    # 응답 구조 확인 (LspttnThdCmpLawXService)
    service_data = data.get("LspttnThdCmpLawXService", {})
    if not service_data:
        return f"MST {mst}에 해당하는 3단비교 정보가 없습니다."
    
    # 위임조문삼단비교 또는 인용조문삼단비교
    comparison_key = "위임조문삼단비교" if knd == 1 else "인용조문삼단비교"
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

@mcp.tool(name="search_deleted_history", description="""삭제 이력을 검색합니다.

매개변수:
- query: 검색어 (선택) - 법령명 또는 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 삭제항목명, 삭제일시, 삭제유형, 삭제사유

사용 예시:
- search_deleted_history()  # 전체 삭제 이력
- search_deleted_history("폐지")  # 폐지 관련 삭제 이력
- search_deleted_history("2024", display=50)  # 2024년 관련 삭제 이력

참고: 법령 데이터의 삭제 이력을 추적하고 감사할 때 사용합니다.""")
def search_deleted_history(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """삭제 이력 검색
    
    Args:
        query: 검색어
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
        
        # API 요청 - 올바른 target: delHst
        data = _make_legislation_request("delHst", params)
        search_term = query or "삭제 이력"
        result = _format_search_results(data, "delHst", search_term)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"삭제 이력 검색 중 오류: {e}")
        return TextContent(type="text", text=f"삭제 이력 검색 중 오류가 발생했습니다: {str(e)}")

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
        data = _make_legislation_request("oneview", params)
        search_term = query or "한눈보기"
        result = _format_search_results(data, "oneview", search_term)
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"한눈보기 검색 중 오류: {e}")
        return TextContent(type="text", text=f"한눈보기 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_one_view_detail", description="""한눈보기 본문(전체 목록)을 조회합니다.

매개변수:
- display: 결과 개수 (최대 100, 기본값: 50)

반환정보: 법령별 한눈보기 이미지 링크, 조문 정보

사용 예시:
- get_one_view_detail()  # 전체 한눈보기 목록
- get_one_view_detail(display=100)  # 더 많은 결과

참고: 복잡한 법령의 핵심 내용을 시각적으로 정리한 자료입니다.""")
def get_one_view_detail(
    display: Annotated[int, "결과 개수 (최대 100)"] = 50,
) -> TextContent:
    """한눈보기 본문 조회"""
    try:
        params = {"display": min(display, 100)}
        data = _make_legislation_request("oneview", params, is_detail=True)
        
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
        data = _make_legislation_request("lsStmd", params, is_detail=False)
        
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
        
        if cached_data:
            return TextContent(type="text", text=cached_data.get("summary", "캐시된 데이터를 읽을 수 없습니다."))
        
        # API 요청 (target="lsStmd"가 가장 정확함)
        params = {"MST": mst_str}
        data = _make_legislation_request("lsStmd", params, is_detail=True)
        
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

@mcp.tool(name="get_law_system_diagram_full", description="""법령 체계도 전체 상세 정보를 조회합니다. (대용량 데이터)

매개변수:
- mst_id: 법령일련번호(MST) - search_law_system_diagram 도구의 결과에서 'MST' 필드값 사용

반환정보: 체계도 전체 데이터 (기본정보, 관련법령, 상하위법 등 모든 상세 정보)

사용 예시: get_law_system_diagram_full(mst_id="248613")

주의: 매우 큰 데이터이므로 필요한 경우에만 사용. 일반적으로는 get_law_system_diagram_detail 권장""")
def get_law_system_diagram_full(mst_id: Union[str, int]) -> TextContent:
    """법령 체계도 전체 상세 정보 조회 (캐시 활용)
    
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
        
        if cached_data and "full_data" in cached_data:
            # 캐시된 전체 데이터 사용
            full_data = cached_data["full_data"]
            result = _format_system_diagram_detail({"법령체계도": full_data}, mst_str, "lsStmd")
            return TextContent(type="text", text=result)
        
        # 캐시에 없으면 API 요청
        params = {"MST": mst_str}
        data = _make_legislation_request("lsStmd", params, is_detail=True)
        
        if data and "법령체계도" in data:
            diagram_data = data["법령체계도"]
            
            # 전체 데이터 포맷팅
            result = _format_system_diagram_detail(data, mst_str, "lsStmd")
            
            # 캐시 저장 (요약본과 함께, 안전한 처리)
            try:
                summary = _format_system_diagram_summary(diagram_data, mst_str)
                cache_data = {
                    "full_data": diagram_data,
                    "summary": summary,
                    "data_size": len(str(diagram_data))
                }
                save_to_cache(cache_key, cache_data)
            except (NameError, Exception) as e:
                logger.warning(f"캐시 저장 실패: {e}")
                # 캐시 저장 실패해도 계속 진행
            
            return TextContent(type="text", text=result)
        else:
            return TextContent(type="text", text=f"""**법령 체계도 전체 조회 결과**

**MST**: {mst_id}

**결과**: 체계도 전체 정보를 찾을 수 없습니다.

**가능한 원인**:
1. 해당 법령에 체계도가 제공되지 않음
2. MST ID가 올바르지 않음
3. 체계도 데이터가 아직 구축되지 않음

**대안 방법**:
1. **요약 정보**: get_law_system_diagram_detail(mst_id="{mst_str}")
2. **법령 기본정보**: get_law_detail(mst="{mst_str}")
3. **관련법령 검색**: search_related_law(query="법령명")

**법제처 웹사이트 직접 확인**: http://www.law.go.kr/LSW/lsStmdInfoP.do?lsiSeq={mst_str}""")
        
    except Exception as e:
        logger.error(f"법령 체계도 전체 조회 중 오류: {e}")
        return TextContent(type="text", text=f"법령 체계도 전체 조회 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_delegated_law", description="""위임법령을 조회합니다.

매개변수:
- law_id: 법령일련번호(MST) - search_law 도구의 결과에서 'MST' 필드값 사용 (MST 우선, ID는 MST가 없을 때만)

사용 예시: get_delegated_law(law_id="248613")""")
def get_delegated_law(law_id: Union[str, int]) -> TextContent:
    """위임법령 조회
    
    Args:
        law_id: 법령ID 또는 법령일련번호
    """
    if not law_id:
        return TextContent(type="text", text="법령ID를 입력해주세요.")
    
    try:
        mst_str = str(law_id)
        
        # 여러 API 접근 방법 시도
        api_attempts = [
            {"target": "lsDelegated", "param": "MST", "endpoint": "detail"},
            {"target": "law", "param": "MST", "endpoint": "detail"},  # 전체 법령에서 위임정보 추출
            {"target": "lsDelegated", "param": "ID", "endpoint": "detail"}   # ID로 시도
        ]
        
        for attempt in api_attempts:
            try:
                params = {
                    attempt["param"]: mst_str,
                    "type": "JSON"
                }
                
                if attempt["endpoint"] == "detail":
                    data = _make_legislation_request(attempt["target"], params, is_detail=True)
                else:
                    data = _make_legislation_request(attempt["target"], params, is_detail=False)
                
                # 유의미한 위임법령 데이터가 있는지 확인
                if data and _has_delegated_law_content(data):
                    result = _format_delegated_law(data, mst_str, attempt["target"])
                    return TextContent(type="text", text=result)
                    
            except Exception as e:
                logger.warning(f"위임법령 조회 시도 실패 ({attempt}): {e}")
                continue
        
        # 모든 시도 실패시 관련법령 검색으로 대안 제시
        try:
            # 해당 법령명을 찾아서 관련 법령 검색 시도
            detail_params = {"MST": mst_str}
            detail_data = _make_legislation_request("law", detail_params, is_detail=True)
            
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
                related_data = _make_legislation_request("law", related_search_params, is_detail=False)
                
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
                        
                        result += f"""**참고**: 위임법령 API가 작동하지 않아 관련법령 검색으로 시행령/시행규칙을 찾았습니다."""
                        
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
        
        # 관련법령 요약
        related_laws = diagram_data.get('관련법령', [])
        if related_laws:
            count = len(related_laws) if isinstance(related_laws, list) else 1
            result += f"**🔗 관련법령**: {count}건\n"
            if isinstance(related_laws, list) and related_laws:
                result += f"- 첫 번째: {related_laws[0].get('법령명', '정보없음')}\n"
                if count > 1:
                    result += f"- 기타 {count-1}건 추가\n"
            result += "\n"
        
        # 상하위법 요약
        hierarchy_laws = diagram_data.get('상하위법', [])
        if hierarchy_laws:
            count = len(hierarchy_laws) if isinstance(hierarchy_laws, list) else 1
            result += f"**상하위법**: {count}건\n"
            if isinstance(hierarchy_laws, list) and hierarchy_laws:
                result += f"- 첫 번째: {hierarchy_laws[0].get('법령명', '정보없음')}\n"
                if count > 1:
                    result += f"- 기타 {count-1}건 추가\n"
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

언제 사용:
- 시행일 법령의 특정 조문 내용을 상세히 조회할 때
- 법령의 항, 호, 목 단위까지 세부적으로 분석할 때

매개변수:
- mst: 시행일법령MST - search_effective_law 도구의 결과에서 'MST' 필드값 사용
- article_no: 조번호 (선택) - 예: "1", "제1조"
- paragraph_no: 항번호 (선택) - 예: "1" 
- item_no: 호번호 (선택) - 예: "1"
- subitem_no: 목번호 (선택) - 예: "가", "나"
- display: 결과 개수 (기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 조문내용, 항내용, 호내용, 목내용, 시행일자

권장 워크플로우:
1. search_effective_law("개인정보보호법") → MST 확인
2. get_effective_law_articles(mst="248613", article_no="15") → 제15조 상세 조회

사용 예시: get_effective_law_articles(mst="248613", article_no="15")""")
def get_effective_law_articles(
    mst: Union[str, int],
    article_no: Optional[str] = None,
    paragraph_no: Optional[str] = None,
    item_no: Optional[str] = None,
    subitem_no: Optional[str] = None,
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
        display: 결과 개수
        page: 페이지 번호
    """
    if not mst:
        return TextContent(type="text", text="법령일련번호(MST)를 입력해주세요.")
    
    try:
        # API 요청 파라미터 (필수 파라미터 포함)
        params = {
            "OC": legislation_config.oc,  # 필수: 기관코드
            "type": "JSON",               # 필수: 출력형태
            "target": "eflawjosub",       # 필수: 시행일 법령 조항호목 조회용
            "MST": str(mst),             # 필수: 법령일련번호
            "display": min(display, 100),
            "page": page
        }
        
        # 특정 조문 파라미터는 서버 필터링이 작동하지 않으므로 클라이언트에서 필터링
        # API 호출 시에는 전체 조문을 가져옴
        
        # API 요청 - 상세 조회 API 사용
        data = _make_legislation_request("eflawjosub", params, is_detail=True)
        
        # eflawjosub 전용 포맷팅 - 실제 조문 내용 반환
        result = _format_effective_law_articles(data, str(mst), article_no, paragraph_no, item_no, subitem_no)
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

@mcp.tool(name="get_current_law_articles", description="""현행법령의 특정 조문을 조회합니다.

매개변수:
- mst: 법령일련번호(MST) - search_law 도구의 결과에서 'MST' 필드값 사용
- article_no: 조문번호 (선택) - 예: "1", "제1조"
- start_article: 시작 조문 번호 (기본값: 1)
- count: 조회할 조문 개수 (기본값: 5)

사용 예시: get_current_law_articles(mst="248613", article_no="1")""")
def get_current_law_articles(
    mst: Union[str, int],
    article_no: Optional[str] = None,
    start_article: int = 1,
    count: int = 5
) -> TextContent:
    """현행법령 조문 조회
    
    Args:
        mst: 법령일련번호(MST)
        article_no: 특정 조문 번호 (예: "50" 또는 "제50조")
        start_article: 시작 조문 번호 (article_no가 없을 때)
        count: 조회할 조문 개수 (article_no가 없을 때)
    """
    if not mst:
        return TextContent(type="text", text="법령일련번호(MST)를 입력해주세요.")
    
    try:
        # 캐시 확인 또는 API 호출
        cache_key = get_cache_key(f"law_{mst}", "full")
        law_data = load_from_cache(cache_key)
        
        if not law_data:
            # 캐시가 없으면 API 호출
            params = {
                "target": "law",
                "MST": str(mst),
                "type": "JSON",
                "OC": legislation_config.oc
            }
            
            response = law_client._make_request("http://www.law.go.kr/DRF/lawService.do", params)
            if not response:
                return TextContent(type="text", text="API 응답이 없습니다.")
            
            law_data = response
            # 캐시 저장
            save_to_cache(cache_key, law_data)
        
        # 법령 정보 추출
        law_info = law_data.get("법령", {})
        law_name = law_info.get("기본정보", {}).get("법령명_한글", "")
        
        # 조문 정보 파싱
        articles = law_info.get("조문", {})
        article_units = []
        
        if isinstance(articles, dict) and "조문단위" in articles:
            article_units = articles.get("조문단위", [])
            # 리스트가 아닌 경우 리스트로 변환
            if not isinstance(article_units, list):
                article_units = [article_units] if article_units else []
        elif isinstance(articles, list):
            article_units = articles
        
        # 실제 조문만 필터링
        actual_articles = [
            a for a in article_units 
            if a.get("조문여부") == "조문"
        ]
        
        if not actual_articles:
            return TextContent(type="text", text=f"법령 '{law_name}'의 조문 정보가 없습니다.")
        
        result = f"**{law_name}** 조문 조회\n\n"
        
        if article_no:
            # 특정 조문 조회
            import re
            numbers = re.findall(r'\d+', str(article_no))
            target_num = numbers[0] if numbers else ""
            
            found = False
            for article in actual_articles:
                if article.get("조문번호") == target_num:
                    found = True
                    result += format_article_detail(article)
                    break
            
            if not found:
                result += f"제{article_no}조를 찾을 수 없습니다."
        else:
            # 범위 조회
            total = len(actual_articles)
            end_idx = min(start_article + count - 1, total)
            
            result += f"**전체 조문**: {total}개\n"
            result += f"**조회 범위**: 제{start_article}조 ~ 제{end_idx}조\n\n"
            result += "---\n\n"
            
            for i in range(start_article - 1, end_idx):
                if i < len(actual_articles):
                    article = actual_articles[i]
                    result += format_article_summary(article)
                    result += "\n---\n\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"현행법령 조문 조회 중 오류: {e}")
        return TextContent(type="text", text=f"조회 중 오류가 발생했습니다: {str(e)}")

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

매개변수:
- effective_law_id: 시행일법령MST - search_effective_law 도구의 결과에서 'MST' 필드값 사용 (MST 우선, ID는 MST가 없을 때만)

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
            data = _make_legislation_request(target, params, is_detail=True)
            
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

@mcp.tool(name="get_law_appendix_detail", description="""법령 별표서식 상세내용을 조회합니다.

매개변수:
- appendix_id: 별표서식ID - search_law_appendix 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_law_appendix_detail(appendix_id="123456")""")
def get_law_appendix_detail(appendix_id: Union[str, int]) -> TextContent:
    """법령 별표서식 상세내용 조회
    
    Args:
        appendix_id: 별표서식ID
    """
    if not appendix_id:
        return TextContent(type="text", text="별표서식ID를 입력해주세요.")
    
    try:
        # API 요청 파라미터
        params = {"target": "lawAppendix", "MST": str(appendix_id)}
        url = _generate_api_url("lsBylInfoGuide", params)
        
        # API 요청
        data = _make_legislation_request("lsBylInfoGuide", params)
        result = _safe_format_law_detail(data, str(appendix_id), url)
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"법령 별표서식 상세조회 중 오류: {e}")
        return TextContent(type="text", text=f"법령 별표서식 상세조회 중 오류가 발생했습니다: {str(e)}")

# linkage_tools.py에서 이동할 도구들
@mcp.tool(name="search_daily_article_revision", description="""특정 조문의 변경이력을 시간순으로 조회합니다.

매개변수:
- mst: 법령일련번호 (필수) - search_law_unified로 먼저 확인
- article_no: 조문번호 (필수) - "제1조", "제15조" 형식 또는 "000100" 6자리 형식
- display: 결과 개수 (기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 변경일자, 제개정구분, 공포일자, 시행일자

사용법:
1. search_law_unified("개인정보보호법")로 MST 확인
2. search_daily_article_revision(mst="248613", article_no="제15조")

예시:
search_daily_article_revision(mst="248613", article_no="제15조")
search_daily_article_revision(mst="267581", article_no="제86조")""")
def search_daily_article_revision(
    mst: str,
    article_no: str,
    display: int = 20,
    page: int = 1
) -> TextContent:
    """조문별 변경 이력 검색
    
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
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"조문별 변경이력 검색 중 오류: {e}")
        return TextContent(type="text", text=f"조문별 변경이력 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="search_article_change_history", description="""조문의 상세 변경이력과 정책적 배경을 조회합니다.

매개변수:
- mst: 법령일련번호 (필수) - search_law_unified로 먼저 확인
- article_no: 조문번호 (필수) - "제1조", "제15조" 형식 또는 "000100" 6자리 형식
- display: 결과 개수 (기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 변경일자, 변경사유, 제개정구분, 소관부처, 정책적 배경
주의: API 제약으로 실제 조문 텍스트는 제공되지 않음

사용법:
1. search_law_unified("개인정보보호법")로 MST 확인
2. search_article_change_history(mst="248613", article_no="제15조")
3. 실제 조문 내용이 필요하면 get_law_article_by_key 사용

예시:
search_article_change_history(mst="248613", article_no="제15조")
search_article_change_history(mst="267581", article_no="제34조")""")
def search_article_change_history(mst: str, article_no: str, display: int = 20, page: int = 1) -> TextContent:
    """조문별 변경이력 검색 (상세 비교 특화)
    
    Args:
        mst: 법령일련번호(MST) (필수)
        article_no: 조번호 6자리 (필수)
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
        
        # MST인지 ID인지 확인 후 적절한 값 사용 (search_daily_article_revision과 동일한 로직)
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
        
        search_query = f"조문 상세 변경이력 (MST: {mst}, {article_display})"
        
        # 응답 데이터 검증
        if data and _has_meaningful_content(data):
            result = _format_search_results(data, "lsJoHstInf", search_query)
        else:
            # 데이터가 없을 때 search_daily_article_revision 추천
            result = f"""**조문 상세 변경이력 검색 결과**

**MST**: {mst} (변환된 ID: {actual_law_id})
**조문**: {article_display}

**결과**: 변경이력이 없습니다.

**대안 도구 사용**:
```
search_daily_article_revision(mst="{mst}", article_no="{article_no}")
```

**참고**: 
- search_article_change_history: 상세 비교에 특화
- search_daily_article_revision: 일반적인 변경이력 조회

**다른 방법**:
1. **전체 법령 연혁**: search_law_history("법령명")
2. **법령 비교**: compare_law_versions("법령명")
3. **조문 상세**: get_law_article_by_key(mst="{mst}", article_key="{article_display}")

**문제 해결**: MST를 ID로 변환했습니다 ({mst} → {actual_law_id})"""
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"조문별 변경이력 검색 중 오류: {e}")
        return TextContent(type="text", text=f"조문별 변경이력 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="search_law_ordinance_link", description="""법령 목록을 검색합니다. (주의: 자치법규 연계 정보는 제공되지 않음)

매개변수:
- query: 검색어 (선택) - 법령명 또는 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 법령명, 법령ID, 법령구분명, 공포일자, 시행일자

주의사항: 이 API는 법령-자치법규 연계 정보를 제공하지 않고, 일반적인 법령 목록만 반환합니다.

대안 방법:
- search_law("법령명")  # 기본 법령 검색
- search_related_law("법령명")  # 관련 법령 검색

사용 예시:
- search_law_ordinance_link()  # 전체 법령 목록
- search_law_ordinance_link("건축법")  # 건축법 관련 법령들""")
def search_law_ordinance_link(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """법령 목록 검색 (주의: 자치법규 연계 정보 제공 안함)
    
    Args:
        query: 검색어 (법령명)
        display: 결과 개수
        page: 페이지 번호
    """
    try:
        # 기본 파라미터 설정 (올바른 target 사용)
        params = {
            "display": min(display, 100),
            "page": page,
            "type": "JSON"
        }
        
        # 검색어가 있는 경우 추가
        if query and query.strip():
            search_query = query.strip()
            params["query"] = search_query
        else:
            search_query = "전체 법령 목록"
        
        # API 요청 - 올바른 target 사용
        try:
            data = _make_legislation_request("lnkLs", params, is_detail=False)
        except Exception as e:
            # lnkLs 실패시 대안 방법 시도
            logger.warning(f"lnkLs API 실패, 대안 방법 시도: {e}")
            return TextContent(type="text", text=f"""**법령 목록 조회 실패**

**검색어**: {search_query}

⚠️ **API 연결 문제**: {str(e)}

**중요 안내**: 이 API는 법령-자치법규 연계 정보를 제공하지 않습니다.

**가능한 원인**:
1. API 엔드포인트 일시적 장애
2. 네트워크 연결 문제
3. 서비스 점검 중

**대안 방법**:
1. **관련법령 검색**: search_related_law(query="{query or '법령명'}")
2. **일반 법령 검색**: search_law(query="{query or '법령명'}")
3. **잠시 후 재시도**: 같은 명령을 다시 실행해보세요

**참고**: 실제 법령-자치법규 연계 정보는 법제처 웹사이트에서 직접 확인하시기 바랍니다.""")
        
        # 응답 데이터 검증 및 포맷팅
        if data and _has_meaningful_content(data):
            result = _format_search_results(data, "lnkLs", search_query)
            # API 한계에 대한 명확한 안내 추가
            result += f"""

⚠️ **API 한계**: 이 API는 법령-자치법규 연계 정보를 제공하지 않고, 일반적인 법령 목록만 반환합니다.

**실제 자치법규 연계 정보**를 원하신다면:
1. **관련법령 검색**: search_related_law(query="{query or '법령명'}")
2. **일반 법령 검색**: search_law(query="{query or '법령명'}")
3. **법제처 웹사이트**: http://www.law.go.kr 에서 직접 검색"""
        else:
            # 데이터 없을 때 대안 검색 제안
            result = f"""**법령 목록 검색 결과**

**검색어**: {search_query}

**결과**: 검색 결과가 없습니다.

⚠️ **중요 안내**: 이 API는 법령-자치법규 연계 정보를 제공하지 않습니다.

**실제 법령-자치법규 연계 정보**를 원하신다면:
1. **관련법령 검색**: search_related_law(query="{query or '법령명'}")
2. **일반 법령 검색**: search_law(query="{query or '법령명'}")
3. **지자체 조례 정보**: 각 지자체 홈페이지에서 직접 검색

**검색 팁**:
- 법령명 일부만 입력 (예: "은행법" → "은행")
- 일반적인 키워드 사용 (예: "건축", "환경", "교통")

**참고**: 법령-자치법규 연계 데이터는 법제처 API에서 제한적으로만 제공됩니다."""
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"법령 목록 검색 중 오류: {e}")
        return TextContent(type="text", text=f"법령 목록 검색 중 오류가 발생했습니다: {str(e)}")



@mcp.tool(name="search_ordinance_law_link", description="""자치법규 기준 법령 연계 정보를 검색합니다.

매개변수:
- query: 검색어 (선택) - 자치법규명 또는 키워드
- display: 결과 개수 (최대 100, 기본값: 20)
- page: 페이지 번호 (기본값: 1)

반환정보: 자치법규명, 자치법규ID, 연계된 법령명, 법령ID, 지자체명, 연계유형

사용 예시:
- search_ordinance_law_link()  # 전체 자치법규-법령 연계
- search_ordinance_law_link("서울특별시")  # 서울시 조례의 상위 법령
- search_ordinance_law_link("주차장 조례")  # 특정 조례의 근거 법령

참고: 특정 자치법규가 어떤 상위 법령에 근거하는지 파악할 때 사용합니다.""")
def search_ordinance_law_link(query: Optional[str] = None, display: int = 20, page: int = 1) -> TextContent:
    """자치법규 기준 법령 연계 정보 검색
    
    Args:
        query: 검색어 (자치법규명)
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
            search_query = "자치법규-법령 연계정보"
        
        # API 요청 - 올바른 target: lnkLs (법령 기준 자치법규 연계)
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
            from ..utils.legislation_utils import load_from_cache, save_to_cache, get_cache_key
            cache_key = get_cache_key(f"lsRlt_{search_query}_{display}_{page}", "related_law")
            cached_data = load_from_cache(cache_key)
            if cached_data:
                logger.info(f"관련법령 캐시 히트: {search_query}")
                result = _format_search_results(cached_data, "lsRlt", search_query)
                return TextContent(type="text", text=result + "\n\n(캐시된 결과)")
        except ImportError:
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

# custom_tools.py에서 이동할 도구들


# specialized_tools.py에서 이동할 도구
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

# ===========================================
# 새로운 통합 도구들 (최적화된 계층적 접근)
# ===========================================

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
        
        data = _make_legislation_request(target, params, is_detail=False)
        
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
            data = _make_legislation_request("law", params, is_detail=True)
            
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

반환정보: 요청한 범위의 조문들의 전체 내용

사용 예시:
- get_law_articles_range(mst="265959", target="law", start_article=50, count=5)
  # 제50조부터 제54조까지 5개 조문 조회

참고: 페이징 방식으로 여러 조문을 효율적으로 탐색할 수 있습니다."""
)
def get_law_articles_range(
    mst: str,
    target: str,
    start_article: int = 1,
    count: int = 5
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
            cached_data = _make_legislation_request(target, params, is_detail=True)
            
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
            
            # 조문 내용 추출
            article_content = article.get("조문내용", "")
            if article_content and article_content.strip():
                # HTML 태그 제거
                clean_content = re.sub(r'<[^>]+>', '', article_content)
                result += clean_content + "\n\n"
            
            # 항 내용 처리 - 더 명확하게
            hangs = article.get("항", [])
            
            if hangs and isinstance(hangs, list):
                for hang in hangs:
                    if isinstance(hang, dict):
                        hang_num = hang.get("항번호", "")
                        hang_content = hang.get("항내용", "")
                        if hang_content:
                            # HTML 태그 제거
                            clean_hang = re.sub(r'<[^>]+>', '', hang_content)
                            clean_hang = clean_hang.strip()
                            if clean_hang:
                                result += f"{clean_hang}\n\n"
            
            result += "-" * 30 + "\n\n"
        
        return TextContent(type="text", text=result.strip())
        
    except Exception as e:
        logger.error(f"조문 범위 조회 중 오류: {e}")
        return TextContent(type="text", text=f"조문 범위 조회 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(
    name="compare_law_versions",
    description="""동일 법령의 현행 버전과 시행일 버전을 비교합니다.

매개변수:
- law_name: 법령명 (필수) - 비교할 법령의 이름

반환정보:
- 현행 버전 정보: 공포일자, 시행일자, 제개정구분
- 시행일 버전 정보: 공포일자, 시행일자, 제개정구분  
- 주요 변경사항: 조문별 차이점 요약

사용 예시:
- compare_law_versions("개인정보보호법")
- compare_law_versions("소득세법")

참고: 최근 시행일 버전과 현행 버전을 자동으로 비교합니다."""
)
def compare_law_versions(law_name: str) -> TextContent:
    """법령 버전 비교"""
    if not law_name:
        return TextContent(type="text", text="법령명을 입력해주세요.")
    
    try:
        # 현행법령 검색
        current_data = _make_legislation_request("law", {"query": law_name, "display": 1})
        current_items = current_data.get("LawSearch", {}).get("law", [])
        
        if not current_items:
            return TextContent(type="text", text=f"'{law_name}'을(를) 찾을 수 없습니다.")
        
        current_law = current_items[0] if isinstance(current_items, list) else current_items
        law_id = current_law.get("법령ID")
        
        # 시행일법령 검색
        eflaw_data = _make_legislation_request("eflaw", {"query": law_name, "display": 5})
        eflaw_items = eflaw_data.get("LawSearch", {}).get("law", [])
        
        if not isinstance(eflaw_items, list):
            eflaw_items = [eflaw_items] if eflaw_items else []
        
        result = f"🔄 **{law_name}** 버전 비교\n"
        result += "=" * 50 + "\n\n"
        
        # 현행법령 정보
        result += "**📌 현행법령:**\n"
        result += f"• 법령일련번호: {current_law.get('법령일련번호')}\n"
        result += f"• 공포일자: {current_law.get('공포일자')}\n"
        result += f"• 시행일자: {current_law.get('시행일자')}\n"
        result += f"• 제개정구분: {current_law.get('제개정구분명')}\n\n"
        
        # 시행일법령 목록
        result += "**시행일법령 이력:**\n"
        for i, eflaw in enumerate(eflaw_items[:3], 1):
            status = eflaw.get('현행연혁코드', '')
            result += f"\n{i}. "
            if status == "시행예정":
                result += "- "
            elif status == "현행":
                result += "- "
            else:
                result += "- "
            
            result += f"{status} (시행일: {eflaw.get('시행일자')})\n"
            result += f"   • 법령일련번호: {eflaw.get('법령일련번호')}\n"
            result += f"   • 공포일자: {eflaw.get('공포일자')}\n"
            result += f"   • 제개정구분: {eflaw.get('제개정구분명')}\n"
        
        result += "\n**상세 비교**: 각 버전의 상세 내용은 get_law_detail로 조회하세요.\n"
        result += f"**조문별 Before/After 비교**: compare_article_before_after(\"{law_name}\", \"제1조\")로 상세 비교 가능\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"버전 비교 중 오류: {e}")
        return TextContent(type="text", text=f"버전 비교 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(
    name="compare_article_before_after",
    description="""특정 조문의 현행법령과 시행일법령을 비교합니다.

매개변수:
- law_name: 법령명 (필수) - 예: "은행법", "소득세법", "개인정보보호법"
- article_no: 조문번호 (필수) - 예: "제1조", "제34조", "제86조"
- show_context: 전후 조문도 함께 표시 여부 (기본값: False)

반환정보: 현행법령 조문 내용, 시행일법령 조문 내용, 변경사항 분석

사용법:
compare_article_before_after("은행법", "제34조")
compare_article_before_after("개인정보보호법", "제15조")

예시:
compare_article_before_after("소득세법", "제86조")"""
)
def compare_article_before_after(law_name: str, article_no: str, show_context: bool = False) -> TextContent:
    """조문별 Before/After 비교 (신구법 대조표)"""
    if not law_name or not article_no:
        return TextContent(type="text", text="법령명과 조문번호를 모두 입력해주세요.")
    
    try:
        # 1단계: 법령 검색으로 MST 확보
        search_params = {
            "query": law_name,
            "display": 5,
            "search": 1
        }
        
        current_law_data = _make_legislation_request("law", search_params)
        if not current_law_data or 'LawSearch' not in current_law_data:
            return TextContent(type="text", text=f"'{law_name}' 법령을 찾을 수 없습니다.")
        
        laws = current_law_data['LawSearch'].get('law', [])
        if not laws:
            return TextContent(type="text", text=f"'{law_name}' 법령을 찾을 수 없습니다.")
        
        # 첫 번째 검색 결과 사용
        current_law = laws[0] if isinstance(laws, list) else laws
        current_mst = current_law.get('법령일련번호') or current_law.get('MST')
        
        if not current_mst:
            return TextContent(type="text", text="법령일련번호를 찾을 수 없습니다.")
        
        # 2단계: 현행법령 조문 조회
        current_article = _get_article_content(current_mst, article_no, "law")
        
        # 3단계: 시행일법령 조문 조회
        eflaw_article = _get_article_content(current_mst, article_no, "eflaw")
        
        # 4단계: 비교 결과 생성
        result = f"**{law_name} {article_no} 신구법 대조표**\n"
        result += "=" * 60 + "\n\n"
        
        # 현행법령 내용
        result += "## 신법 (현행법령)\n"
        if current_article and "조회할 수 없습니다" not in current_article:
            result += f"```\n{current_article}\n```\n\n"
        else:
            result += "현행법령 조문을 조회할 수 없습니다.\n\n"
        
        # 시행일법령 내용  
        result += "## 구법 (이전 버전)\n"
        if eflaw_article and "조회할 수 없습니다" not in eflaw_article:
            result += f"```\n{eflaw_article}\n```\n\n"
        else:
            result += "이전 버전 조문을 조회할 수 없습니다.\n\n"
        
        # 5단계: 변경사항 분석
        if current_article and eflaw_article and "조회할 수 없습니다" not in current_article and "조회할 수 없습니다" not in eflaw_article:
            result += "## 변경사항 분석\n"
            result += _analyze_article_changes(current_article, eflaw_article, law_name, article_no)
            result += "\n"
        
        # 3. 분석 가이드
        result += "## 분석 가이드\n\n"
        
        # 분야별 분석 포인트
        if "은행법" in law_name or "금융" in law_name:
            result += "**금융업 영향 분석 포인트**:\n"
            result += "- 대출규제 변경사항\n- 여신업무 절차 변화\n- 금융감독 강화 내용\n- 고객보호 의무 변경\n\n"
        elif "소득세" in law_name or "법인세" in law_name or "세" in law_name:
            result += "**세무 영향 분석 포인트**:\n"
            result += "- 세율 및 과세표준 변경\n- 공제·감면 제도 변화\n- 신고납부 절차 개선\n- 가산세 및 벌칙 조정\n\n"
        elif "개인정보" in law_name:
            result += "**개인정보보호 영향 분석 포인트**:\n"
            result += "- 수집·이용 동의 절차 변경\n- 안전조치 기준 강화\n- 처리업무 위탁 규정 변화\n- 과징금·과태료 조정\n\n"
        
        # 6. 관련 도구 안내
        result += "\n## 추가 참고사항\n\n"
        result += f"관련 해석례: search_interpretation(\"{law_name} {article_no}\")\n"
        result += f"관련 판례: search_precedent(\"{law_name} {article_no}\")\n"
        result += f"부처 해석: 소관부처별 법령해석 도구 활용\n"
        result += f"전체 버전 비교: compare_law_versions(\"{law_name}\")\n"
        
        if show_context:
            result += f"\n**전후 조문 조회**: get_law_articles_range로 {article_no} 전후 조문 확인 가능\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"조문 Before/After 비교 중 오류: {e}")
        return TextContent(type="text", text=f"조문 Before/After 비교 중 오류가 발생했습니다: {str(e)}")

def _normalize_article_number(article_no: str) -> str:
    """조문 번호를 6자리 형식으로 정규화"""
    try:
        import re
        
        # 이미 6자리 숫자 형식인 경우
        if re.match(r'^\d{6}$', article_no):
            return article_no
        
        # "제N조" 형식 처리
        match = re.match(r'^제(\d+)조(?:의(\d+))?$', article_no)
        if match:
            main_num = int(match.group(1))
            sub_num = int(match.group(2)) if match.group(2) else 0
            
            # 6자리 형식으로 변환: NNNNSS (NNNN=조번호, SS=의N)
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

def _get_article_content(mst: str, article_no: str, target: str) -> str:
    """특정 조문의 내용을 조회 - law_tools_utils 유틸리티 재사용"""
    try:
        # 캐시 확인
        cache_key = get_cache_key(f"{target}_{mst}", "full")
        cached_data = load_from_cache(cache_key)
        
        if not cached_data:
            # API 호출
            params = {"MST": str(mst)}
            cached_data = _make_legislation_request(target, params, is_detail=True)
            
            if cached_data:
                save_to_cache(cache_key, cached_data)
        
        if not cached_data:
            return "조회할 수 없습니다"
        
        # 법령 데이터 구조 추출
        law_data = None
        if '법령' in cached_data:
            law_data = cached_data['법령']
        elif 'Law' in cached_data:
            law_data = cached_data['Law']
        elif isinstance(cached_data, dict):
            law_data = cached_data
            
        if not law_data:
            return "조회할 수 없습니다"
        
        # 조문단위 배열 추출
        articles_data = []
        if isinstance(law_data, dict):
            articles_section = law_data.get('조문', {})
            if isinstance(articles_section, dict) and '조문단위' in articles_section:
                articles_data = articles_section.get('조문단위', [])
            elif '조문단위' in law_data:
                articles_data = law_data.get('조문단위', [])
        
        if not isinstance(articles_data, list):
            articles_data = [articles_data] if articles_data else []
        
        if not articles_data:
            return "조문 구조를 찾을 수 없습니다"
        
        # 조문 번호 정규화 (유틸리티 함수 사용)
        article_num = normalize_article_key(article_no)
        
        # 조문 찾기 (유틸리티 함수 사용)
        found_article = find_article_in_data(articles_data, article_num)
        
        if not found_article:
            return "해당 조문을 찾을 수 없습니다"
        
        # 조문 내용 추출 및 포맷팅
        content_fields = ['조문내용', 'joContent', '내용', 'content', 'joCts']
        content = ""
        
        for field in content_fields:
            if field in found_article and found_article[field]:
                content = found_article[field]
                break
        
        # 조문내용이 짧으면 (제목만 있는 경우) 항 데이터에서 내용 추출
        content_str = str(content) if content else ""
        if len(content_str) < 100:
            # 항 데이터 추출
            hang_data = found_article.get('항', [])
            if hang_data:
                if not isinstance(hang_data, list):
                    hang_data = [hang_data]
                
                hang_contents = []
                for hang in hang_data:
                    if isinstance(hang, dict):
                        hang_content = hang.get('항내용', hang.get('content', ''))
                        if hang_content:
                            hang_contents.append(str(hang_content))
                
                if hang_contents:
                    # 조문 제목 + 항 내용 결합
                    content = content_str + "\n" + "\n".join(hang_contents)
        
        if not content:
            return "조문 내용이 없습니다"
        
        # 리스트인 경우 조인
        if isinstance(content, list):
            content = '\n'.join(str(item) for item in content if item)
        
        # HTML 태그 제거
        content = clean_html_tags(str(content))
        content = content.strip()
        
        if not content:
            return "조문 내용이 비어있습니다"
        
        return content
        
    except Exception as e:
        logger.error(f"조문 내용 조회 중 오류: {e}")
        return "조회 중 오류가 발생했습니다"

def _extract_article_summary(article_content: str) -> str:
    """조문 내용에서 요약 추출"""
    try:
        if not article_content or "조회할 수 없습니다" in article_content:
            return "조회 불가"
        
        # 조문 내용이 너무 길면 첫 200자만 표시
        content = article_content.replace('\n', ' ').strip()
        if len(content) > 200:
            content = content[:200] + "..."
        
        return content
    except:
        return "내용 분석 실패"

def _analyze_article_changes(current_content: str, previous_content: str, law_name: str, article_no: str) -> str:
    """조문 변경사항 분석"""
    try:
        result = ""
        
        # 기본 변경 분석
        if "조회할 수 없습니다" in current_content or "조회할 수 없습니다" in previous_content:
            result += "**조문 비교 제한**: 일부 버전의 조문을 조회할 수 없어 정확한 비교가 어렵습니다.\n\n"
            result += "**대안**: search_law_history로 연혁을 확인하거나 search_daily_article_revision으로 변경이력을 추적하세요.\n"
            return result
        
        # 내용 길이 비교
        current_len = len(current_content)
        previous_len = len(previous_content)
        
        if current_len > previous_len * 1.2:
            result += "📈 **내용 확대**: 조문 내용이 크게 확장되었습니다.\n"
        elif current_len < previous_len * 0.8:
            result += "📉 **내용 축소**: 조문 내용이 간소화되었습니다.\n"
        else:
            result += "**내용 수정**: 조문의 표현이나 세부 내용이 변경되었습니다.\n"
        
        # 금융·세무·개인정보보호 키워드 분석
        domain_keywords = {
            "금융": ["여신", "대출", "예금", "금융", "은행", "신용", "자본"],
            "세무": ["소득", "세금", "과세", "공제", "세율", "신고", "부가가치세"],
            "개인정보": ["개인정보", "수집", "이용", "제공", "동의", "처리", "보호"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in law_name for keyword in keywords):
                result += f"\n**{domain} 분야 주요 변경점**:\n"
                for keyword in keywords:
                    if keyword in current_content and keyword not in previous_content:
                        result += f"  • '{keyword}' 관련 규정 신설\n"
                    elif keyword not in current_content and keyword in previous_content:
                        result += f"  • '{keyword}' 관련 규정 삭제\n"
                break
        
        return result
        
    except Exception as e:
        return f"변경사항 분석 중 오류: {str(e)}"

def _analyze_practical_impact(law_name: str, article_no: str, current_content: str, previous_content: str) -> str:
    """실무 영향 분석"""
    try:
        result = ""
        
        # 법령별 실무 영향 분석
        if "은행" in law_name:
            result += "🏦 **금융기관 실무 영향**:\n"
            result += "  • 여신업무 프로세스 재검토 필요\n"
            result += "  • 리스크 관리 체계 업데이트\n"
            result += "  • 금융감독원 보고체계 확인\n"
            result += "  • 내부통제 절차 점검\n\n"
            
        elif "소득세" in law_name:
            result += "💰 **세무 실무 영향**:\n"
            result += "  • 소득공제 계산 방식 변경 검토\n"
            result += "  • 세무신고 프로그램 업데이트\n"
            result += "  • 급여 시스템 반영 사항 확인\n"
            result += "  • 연말정산 절차 변경 대응\n\n"
            
        elif "개인정보" in law_name:
            result += "**개인정보보호 실무 영향**:\n"
            result += "  • 개인정보 처리방침 업데이트\n"
            result += "  • 동의서 양식 재검토\n"
            result += "  • 기술적·관리적 보호조치 점검\n"
            result += "  • 직원 교육 프로그램 개선\n\n"
        
        # 공통 실무 영향
        result += "**공통 주의사항**:\n"
        result += "  • 시행일자 확인 및 경과조치 검토\n"
        result += "  • 관련 하위법령(시행령, 시행규칙) 동반 개정 확인\n"
        result += "  • 업무 매뉴얼 및 지침서 업데이트\n"
        result += "  • 고객 안내 및 홍보 자료 준비\n"
        
        return result
        
    except Exception as e:
        return f"실무 영향 분석 중 오류: {str(e)}"

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
        # 금융 분야 핵심 키워드
        financial_keywords = {
            "bank": ["은행", "여신", "예금", "신용", "대출", "담보"],
            "capital": ["자본시장", "증권", "투자", "펀드", "상장", "공모"],
            "insurance": ["보험", "보험업", "생명보험", "손해보험", "보험료"],
            "fintech": ["핀테크", "전자금융", "결제", "송금", "가상자산"]
        }
        
        # 금융 관련 법령명 목록
        financial_laws = [
            "은행법", "자본시장과 금융투자업에 관한 법률", "보험업법",
            "금융소비자보호법", "전자금융거래법", "여신전문금융업법",
            "상호저축은행법", "금융회사부실자산 등의 효율적 처리를 위한 특별법",
            "금융산업의 구조개선에 관한 법률", "외국환거래법",
            "금융실명거래 및 비밀보장에 관한 법률", "신용정보의 이용 및 보호에 관한 법률"
        ]
        
        result = "🏦 **금융 법령 전문 검색 결과**\n"
        result += "=" * 50 + "\n\n"
        
        # 검색 수행
        search_results = []
        
        if query:
            # 특정 키워드로 검색
            for law_name in financial_laws:
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
            for law_name in financial_laws[:10]:  # 상위 10개 법령
                try:
                    law_result = _make_legislation_request("law", {"query": law_name, "display": 2})
                    laws = law_result.get("LawSearch", {}).get("law", [])
                    if laws:
                        search_results.extend(laws if isinstance(laws, list) else [laws])
                except:
                    continue
        
        # 법령 유형별 필터링
        if law_type != "all" and law_type in financial_keywords:
            filtered_results = []
            keywords = financial_keywords[law_type]
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
                result += f"## 🏷️ **{category} 관련 법령**\n\n"
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
        result += "## 🔗 **추가 검색 도구**\n\n"
        result += "💰 **세무법령**: search_tax_laws()\n"
        result += "**개인정보보호**: search_privacy_laws()\n"
        result += "🏛️ **금융위원회 결정문**: search_financial_committee()\n"
        result += "📚 **금융 관련 판례**: search_precedent(\"금융\")\n"
        
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
        # 세무 분야 핵심 키워드
        tax_keywords = {
            "income": ["소득세", "근로소득", "사업소득", "이자소득", "배당소득"],
            "corporate": ["법인세", "기업소득", "법인소득", "법인신고"],
            "vat": ["부가가치세", "부가세", "매입세액", "매출세액"], 
            "inheritance": ["상속세", "증여세", "상속재산", "증여재산"],
            "local": ["지방세", "취득세", "재산세", "자동차세"]
        }
        
        # 세무 관련 법령명 목록
        tax_laws = [
            "소득세법", "법인세법", "부가가치세법", "상속세 및 증여세법",
            "국세기본법", "국세징수법", "조세범처벌법", "조세특례제한법",
            "지방세법", "관세법", "개별소비세법", "교육세법",
            "농어촌특별세법", "증권거래세법", "인지세법", "종합부동산세법"
        ]
        
        result = "💰 **세무 법령 전문 검색 결과**\n"
        result += "=" * 50 + "\n\n"
        
        # 검색 수행  
        search_results = []
        
        if query:
            # 특정 키워드로 검색
            for law_name in tax_laws:
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
            for law_name in tax_laws[:8]:  # 상위 8개 법령
                try:
                    law_result = _make_legislation_request("law", {"query": law_name, "display": 2})
                    laws = law_result.get("LawSearch", {}).get("law", [])
                    if laws:
                        search_results.extend(laws if isinstance(laws, list) else [laws])
                except:
                    continue
        
        # 세목별 필터링
        if tax_type != "all" and tax_type in tax_keywords:
            filtered_results = []
            keywords = tax_keywords[tax_type]
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
                result += f"## 🏷️ **{category} 관련 법령**\n\n"
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
        result += "## 🔗 **추가 검색 도구**\n\n"
        result += "🏦 **금융법령**: search_financial_laws()\n"
        result += "**개인정보보호**: search_privacy_laws()\n"
        result += "🏛️ **국세청 해석례**: search_nts_interpretation()\n"
        result += "**기획재정부 해석례**: search_moef_interpretation()\n"
        
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
        # 개인정보보호 분야 핵심 키워드
        privacy_keywords = {
            "general": ["개인정보보호", "개인정보", "정보보호", "프라이버시"],
            "public": ["공공기관", "행정정보", "전자정부", "정보공개"],
            "financial": ["신용정보", "금융정보", "신용평가", "금융거래"],
            "medical": ["의료정보", "환자정보", "건강정보", "의료기록"],
            "online": ["정보통신망", "온라인", "인터넷", "전자상거래"]
        }
        
        # 개인정보보호 관련 법령명 목록
        privacy_laws = [
            "개인정보 보호법", "정보통신망 이용촉진 및 정보보호 등에 관한 법률",
            "신용정보의 이용 및 보호에 관한 법률", "공공기관의 개인정보 보호에 관한 법률",
            "의료법", "전자정부법", "정보공개법", "생명윤리 및 안전에 관한 법률",
            "통계법", "위치정보의 보호 및 이용 등에 관한 법률"
        ]
        
        result = "**개인정보보호 법령 전문 검색 결과**\n"
        result += "=" * 50 + "\n\n"
        
        # 검색 수행
        search_results = []
        
        if query:
            # 특정 키워드로 검색
            for law_name in privacy_laws:
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
            for law_name in privacy_laws[:6]:  # 상위 6개 법령
                try:
                    law_result = _make_legislation_request("law", {"query": law_name, "display": 2})
                    laws = law_result.get("LawSearch", {}).get("law", [])
                    if laws:
                        search_results.extend(laws if isinstance(laws, list) else [laws])
                except:
                    continue
        
        # 적용 범위별 필터링
        if scope != "all" and scope in privacy_keywords:
            filtered_results = []
            keywords = privacy_keywords[scope]
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
                result += f"## 🏷️ **{category} 관련 법령**\n\n"
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
        result += "## 🔗 **추가 검색 도구**\n\n"
        result += "🏦 **금융법령**: search_financial_laws()\n"
        result += "💰 **세무법령**: search_tax_laws()\n"
        result += "🏛️ **개인정보보호위원회**: search_privacy_committee()\n"
        result += "📚 **개인정보 관련 판례**: search_precedent(\"개인정보\")\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"개인정보보호법령 검색 중 오류: {e}")
        return TextContent(type="text", text=f"개인정보보호법령 검색 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(
    name="get_practical_law_guide",
    description="""법령의 실무 적용 가이드를 종합적으로 제공합니다.

매개변수:
- law_name: 법령명 (필수) - 예: "은행법", "소득세법", "개인정보보호법"
- focus_area: 집중 분야 (선택) - "compliance", "risk", "procedure", "penalty"
- include_cases: 실제 사례 포함 여부 (기본값: True)
- detail_level: 상세도 (선택) - "basic", "intermediate", "expert"

반환정보:
- 핵심 조문 요약: 실무에서 가장 중요한 조문들
- 준수 체크리스트: 컴플라이언스 확인 사항
- 리스크 포인트: 위반 시 벌칙 및 주의사항
- 관련 자료: 해석례, 판례, 가이드라인, FAQ
- 실무 프로세스: 업무 절차 및 매뉴얼 안내
- 최신 변경사항: 최근 개정 내용 및 영향

사용 예시:
- get_practical_law_guide("은행법", "compliance")  # 은행업 컴플라이언스 가이드
- get_practical_law_guide("소득세법", "procedure")  # 세무신고 절차 가이드
- get_practical_law_guide("개인정보보호법", "risk")  # 개인정보보호 리스크 가이드

참고: 금융·세무·개인정보보호 분야의 실무진을 위한 종합 가이드를 제공합니다."""
)
def get_practical_law_guide(
    law_name: str,
    focus_area: str = "compliance",
    include_cases: bool = True,
    detail_level: str = "intermediate"
) -> TextContent:
    """법령 실무 적용 가이드"""
    if not law_name:
        return TextContent(type="text", text="법령명을 입력해주세요.")
    
    try:
        result = f"💼 **{law_name} 실무 적용 가이드**\n"
        result += "=" * 60 + "\n\n"
        
        # 법령 기본 정보 조회
        # MCP 도구 간 직접 호출 대신 사용자 안내
        result += f"**법령 요약 조회**: get_law_summary(law_name=\"{law_name}\")\n\n"
        
        # 1. 핵심 조문 요약
        result += "## **핵심 조문 요약**\n\n"
        
        if "은행" in law_name:
            result += "### 🏦 **은행업 핵심 규정**\n"
            result += "• **제34조 (여신한도)**: 동일인에 대한 여신한도 제한\n"
            result += "• **제35조 (대주주 거래제한)**: 대주주와의 거래 제한 규정\n"
            result += "• **제52조 (경영지도)**: 금융감독원의 경영지도 권한\n"
            result += "• **제58조 (업무보고)**: 정기/수시 업무보고 의무\n\n"
            
        elif "소득세" in law_name:
            result += "### 💰 **소득세 핵심 규정**\n"
            result += "• **제12조 (거주자)**: 과세대상자 구분 기준\n"
            result += "• **제16조 (이자소득)**: 금융소득 과세 방법\n"
            result += "• **제86조 (근로소득공제)**: 근로소득공제 계산법\n"
            result += "• **제100조 (과세표준)**: 종합소득 과세표준 산정\n\n"
            
        elif "개인정보" in law_name:
            result += "### **개인정보보호 핵심 규정**\n"
            result += "• **제15조 (수집·이용)**: 개인정보 수집·이용 원칙\n"
            result += "• **제17조 (제공)**: 개인정보 제3자 제공 규정\n"
            result += "• **제22조 (동의방법)**: 동의를 받는 방법\n"
            result += "• **제29조 (안전조치)**: 기술적·관리적 보호조치\n\n"
        
        # 2. 컴플라이언스 체크리스트 (focus_area에 따라)
        result += f"## **{focus_area.upper()} 체크리스트**\n\n"
        
        if focus_area == "compliance":
            result += _get_compliance_checklist(law_name)
        elif focus_area == "risk":
            result += _get_risk_checklist(law_name)
        elif focus_area == "procedure":
            result += _get_procedure_checklist(law_name)
        elif focus_area == "penalty":
            result += _get_penalty_checklist(law_name)
        else:
            result += _get_compliance_checklist(law_name)  # 기본값
        
        # 3. 관련 자료 및 도구 연계
        result += "\n## 🔗 **관련 자료 및 도구**\n\n"
        
        result += "### 📚 **해석례 및 판례**\n"
        result += f"• **부처 해석례**: {_get_ministry_tools(law_name)}\n"
        result += f"• **판례 검색**: search_precedent(\"{law_name}\")\n"
        result += f"• **위원회 결정문**: {_get_committee_tools(law_name)}\n\n"
        
        result += "### 🏛️ **감독기관 자료**\n"
        result += f"{_get_supervisory_resources(law_name)}\n\n"
        
        result += "### **실무 도구**\n"
        result += f"• **조문별 비교**: compare_article_before_after(\"{law_name}\", \"제1조\")\n"
        result += f"• **연혁 추적**: search_law_history(\"{law_name}\")\n"
        result += f"• **관련법령**: search_related_law(\"{law_name}\")\n"
        result += f"• **별표서식**: search_law_appendix(query=\"{law_name}\")\n\n"
        
        # 4. 최신 변경사항
        result += "## 🆕 **최신 변경사항 및 주의사항**\n\n"
        
        result += "### **최근 개정 내용**\n"
        result += f"• **변경이력 확인**: search_law_change_history(\"20240101\")\n"
        result += f"• **시행일 법령**: search_effective_law(\"{law_name}\")\n"
        result += f"• **조문 변경**: search_daily_article_revision(law_id=\"법령ID\", article_no=\"제1조\")\n\n"
        
        result += "### **실무 주의사항**\n"
        if "은행" in law_name:
            result += "• 금융감독원 감독규정과 병행 확인 필요\n"
            result += "• Basel III 등 국제 기준과의 정합성 검토\n"
            result += "• 여신심사 및 리스크관리 체계 점검\n"
            
        elif "소득세" in law_name:
            result += "• 국세청 예규 및 해석사례 확인 필수\n"
            result += "• 세무프로그램 업데이트 상황 점검\n"
            result += "• 원천징수 및 연말정산 절차 변경사항 확인\n"
            
        elif "개인정보" in law_name:
            result += "• 개인정보보호위원회 가이드라인 확인 필수\n"
            result += "• 기술적 보호조치 기준 업데이트 확인\n"
            result += "• 동의서 양식 및 처리방침 정기 검토\n"
        
        # 5. 상세도에 따른 추가 정보
        if detail_level == "expert":
            result += "\n## 🎓 **전문가 레벨 추가 정보**\n\n"
            result += f"• **심화 분석**: search_all_legal_documents(\"{law_name}\")\n"
            result += f"• **AI 검색**: search_legal_ai(\"{law_name}\", \"all\")\n"
            result += f"• **영문법령**: search_english_law(\"{law_name}\")\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"실무 가이드 생성 중 오류: {e}")
        return TextContent(type="text", text=f"실무 가이드 생성 중 오류가 발생했습니다: {str(e)}")

def _get_compliance_checklist(law_name: str) -> str:
    """컴플라이언스 체크리스트 생성"""
    if "은행" in law_name:
        return """### 🏦 **은행업 컴플라이언스 체크리스트**
☐ 여신한도 준수 여부 확인 (동일인 자기자본 25% 한도)
☐ 대주주 거래제한 준수 여부 점검
☐ 금융감독원 보고 의무 이행 상황 확인
☐ 내부통제시스템 운영 상태 점검
☐ 리스크관리체계 적정성 검토
☐ 임직원 행동강령 준수 교육 실시"""
        
    elif "소득세" in law_name:
        return """### 💰 **세무 컴플라이언스 체크리스트**
☐ 원천징수 의무 이행 여부 확인
☐ 세무신고 기한 준수 상황 점검  
☐ 소득공제 요건 충족 여부 검토
☐ 세무조정 항목 정확성 확인
☐ 가산세 부과 방지를 위한 사전 점검
☐ 세무대리인 자격 및 권한 확인"""
        
    elif "개인정보" in law_name:
        return """### **개인정보보호 컴플라이언스 체크리스트**
☐ 개인정보 수집·이용 동의 적법성 확인
☐ 개인정보 처리방침 게시 및 고지 상태 점검
☐ 기술적·관리적 보호조치 이행 여부 확인
☐ 개인정보보호 담당자 지정 및 교육 실시
☐ 개인정보 파기 절차 및 기록 관리 점검
☐ 개인정보 침해신고센터 신고 대응체계 구축"""
    
    return "법령별 체크리스트를 준비 중입니다."

def _get_risk_checklist(law_name: str) -> str:
    """리스크 체크리스트 생성"""
    if "은행" in law_name:
        return """### **은행업 리스크 체크리스트**
🔴 **고위험 영역**:
• 여신한도 위반 → 과태료 1천만원 이하
• 대주주 거래제한 위반 → 과태료 5천만원 이하
• 허위보고 → 과태료 5천만원 이하

🟡 **중위험 영역**:
• 업무보고 지연 → 과태료 500만원 이하
• 내부통제 미비 → 금융감독원 제재조치
• 리스크관리 소홀 → 경영개선명령"""
        
    elif "소득세" in law_name:
        return """### **세무 리스크 체크리스트**
🔴 **고위험 영역**:
• 원천징수 불이행 → 미납세액의 40% 가산세
• 신고불성실 → 무신고·과소신고 가산세 20-40%
• 납부지연 → 연 1.8% 이자 상당 가산세

🟡 **중위험 영역**:
• 세무조정 오류 → 경정청구 또는 수정신고 필요
• 공제요건 미충족 → 추징세액 발생
• 장부기록 미비 → 추계과세 위험"""
        
    elif "개인정보" in law_name:
        return """### **개인정보보호 리스크 체크리스트**
🔴 **고위험 영역**:
• 개인정보 무단 수집·이용 → 5년 이하 징역 또는 5천만원 이하 벌금
• 개인정보 무단 제공 → 5년 이하 징역 또는 5천만원 이하 벌금
• 대규모 개인정보 유출 → 과징금 3억원 이하

🟡 **중위험 영역**:
• 보호조치 미이행 → 과태료 3천만원 이하  
• 동의철회 미처리 → 과태료 3천만원 이하
• 처리방침 미게시 → 과태료 1천만원 이하"""
    
    return "법령별 리스크 체크리스트를 준비 중입니다."

def _get_procedure_checklist(law_name: str) -> str:
    """절차 체크리스트 생성"""
    if "은행" in law_name:
        return """### **은행업 절차 체크리스트**
1. **인가 절차**: 금융위원회 인가신청 → 심사 → 인가증 교부
2. **여신심사**: 신용평가 → 담보평가 → 한도설정 → 승인
3. **리스크관리**: 위험측정 → 한도관리 → 모니터링 → 보고
4. **감독보고**: 정기보고(월/분기/반기/연) + 수시보고
5. **내부통제**: 통제환경 → 위험평가 → 통제활동 → 모니터링"""
        
    elif "소득세" in law_name:
        return """### **세무신고 절차 체크리스트**
1. **소득확정**: 소득금액 계산 → 필요경비 차감 → 소득금액 확정
2. **소득공제**: 인적공제 → 연금보험료공제 → 특별공제 → 표준공제
3. **세액계산**: 과세표준 × 세율 → 세액공제 → 결정세액
4. **신고납부**: 신고서 작성 → 기한 내 신고 → 세액납부
5. **사후관리**: 세무조사 대응 → 경정청구 → 불복신청"""
        
    elif "개인정보" in law_name:
        return """### **개인정보보호 절차 체크리스트**
1. **수집단계**: 수집목적 명시 → 동의획득 → 최소수집 원칙
2. **이용단계**: 목적 범위 내 이용 → 보유기간 준수 → 처리현황 통지
3. **제공단계**: 제공동의 획득 → 제공사실 통지 → 수탁업체 관리
4. **보관단계**: 접근권한 관리 → 암호화 → 접속기록 보관
5. **파기단계**: 파기사유 발생 → 파기방법 결정 → 파기완료 확인"""
    
    return "법령별 절차 체크리스트를 준비 중입니다."

def _get_penalty_checklist(law_name: str) -> str:
    """벌칙 체크리스트 생성"""
    if "은행" in law_name:
        return """### ⚖️ **은행법 벌칙 체크리스트**
**형사처벌**:
• 무허가 은행업 영위: 5년 이하 징역 또는 1억원 이하 벌금
• 허위보고: 3년 이하 징역 또는 3천만원 이하 벌금

**행정제재**:
• 여신한도 위반: 과태료 1천만원 이하
• 대주주 거래제한 위반: 과태료 5천만원 이하
• 업무보고 불이행: 과태료 500만원 이하

**금융감독원 제재**:
• 경영개선명령 • 경영진 문책 • 업무정지명령"""
        
    elif "소득세" in law_name:
        return """### ⚖️ **소득세법 벌칙 체크리스트**
**형사처벌**:
• 조세포탈: 2년 이하 징역 또는 포탈세액의 2배 이하 벌금
• 허위신고: 3년 이하 징역 또는 3천만원 이하 벌금

**가산세**:
• 무신고 가산세: 무신고 세액의 20%
• 과소신고 가산세: 과소신고 세액의 10%  
• 납부지연 가산세: 연 1.8% 이자 상당

**기타 제재**:
• 세무조사 • 추징 • 체납처분"""
        
    elif "개인정보" in law_name:
        return """### ⚖️ **개인정보보호법 벌칙 체크리스트**
**형사처벌**:
• 개인정보 무단 처리: 5년 이하 징역 또는 5천만원 이하 벌금
• 거짓·기타 부정한 수단으로 처리: 3년 이하 징역 또는 3천만원 이하 벌금

**과징금**:
• 법 위반 시: 관련 매출액의 3% 이하 또는 3억원 이하

**과태료**:
• 기술적 보호조치 미이행: 3천만원 이하
• 처리방침 미공개: 1천만원 이하

**기타 제재**:
• 시정명령 • 운영중단 • 개인정보보호위원회 제재"""
    
    return "법령별 벌칙 체크리스트를 준비 중입니다."

def _get_ministry_tools(law_name: str) -> str:
    """부처별 해석례 도구 안내"""
    if "은행" in law_name or "금융" in law_name:
        return "search_moef_interpretation() (기획재정부)"
    elif "소득세" in law_name or "세" in law_name:
        return "search_nts_interpretation() (국세청), search_kcs_interpretation() (관세청)"
    elif "개인정보" in law_name:
        return "search_mohw_interpretation() (보건복지부), search_molit_interpretation() (국토교통부)"
    return "해당 법령 소관부처 해석례 도구"

def _get_committee_tools(law_name: str) -> str:
    """위원회별 결정문 도구 안내"""
    if "은행" in law_name or "금융" in law_name:
        return "search_financial_committee() (금융위원회)"
    elif "개인정보" in law_name:
        return "search_privacy_committee() (개인정보보호위원회)"
    elif "공정" in law_name:
        return "search_monopoly_committee() (공정거래위원회)"
    return "관련 위원회 결정문 도구"

def _get_supervisory_resources(law_name: str) -> str:
    """감독기관 자료 안내"""
    if "은행" in law_name or "금융" in law_name:
        return """• **금융감독원**: 감독규정, 검사매뉴얼, 모범규준
• **한국은행**: 통화신용정책, 지급결제제도
• **예금보험공사**: 예금보험제도, 부실은행 정리"""
        
    elif "소득세" in law_name or "세" in law_name:
        return """• **국세청**: 세법해석사례, 예규, 고시
• **기획재정부**: 조세정책, 세제개편안
• **조세심판원**: 심판례, 결정례"""
        
    elif "개인정보" in law_name:
        return """• **개인정보보호위원회**: 가이드라인, 표준 개인정보 처리방침
• **방송통신위원회**: 정보통신 관련 가이드라인  
• **금융위원회**: 금융분야 개인정보보호 가이드라인"""
    
    return "해당 법령 관련 감독기관 자료"

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
            else:
                # 조문이 직접 딕셔너리로 되어있는 경우
                for key, value in articles_section.items():
                    if isinstance(value, dict) and "조문내용" in value:
                        all_articles.append({
                            "조문번호": key.replace("제", "").replace("조", ""),
                            "조문제목": value.get("조문제목", ""),
                            "조문내용": value.get("조문내용", "")
                        })
        
        # 시맨틱 검색 (개선된 키워드 매칭)
        search_results = []
        query_lower = query.lower()
        
        # 복합 키워드 처리
        query_words = []
        main_words = query_lower.split()
        query_words.extend(main_words)
        
        # 복합어 분해 (예: "야근수당" → "야근", "수당")
        for word in main_words:
            if len(word) >= 4:
                for i in range(len(word) - 1):
                    sub_word = word[i:i+2]
                    if sub_word not in query_words:
                        query_words.append(sub_word)
        
        # 관련 키워드 매핑
        related_keywords = {
            "근로시간": ["근로", "시간", "40시간", "8시간", "1주", "1일"],
            "야근": ["연장", "초과", "시간외", "연장근로"],
            "수당": ["가산", "임금", "100분의", "50", "보수"],
            "온라인": ["전자", "정보통신", "인터넷", "웹", "사이트"],
            "쇼핑몰": ["판매", "거래", "상거래", "전자상거래", "통신판매"]
        }
        
        for article in all_articles:
            if not isinstance(article, dict):
                continue
                
            article_no = article.get("조문번호", "")
            article_title = article.get("조문제목", "")
            article_content = article.get("조문내용", "")
            
            # 조문 여부 확인
            if article.get("조문여부") != "조문" and "조문여부" in article:
                continue
            
            # 전체 텍스트 생성
            full_text = f"{article_title} {article_content}".lower()
            
            # 점수 계산 (개선된 알고리즘)
            score = 0
            matched_words = set()
            
            # 전체 쿼리가 포함되어 있으면 최고 점수
            if query_lower in full_text:
                score += 10
                matched_words.add(query_lower)
            
            # 개별 단어 매칭
            for word in query_words:
                if word in full_text and word not in matched_words:
                    # 제목에 있으면 가중치 더 높게
                    if word in article_title.lower():
                        score += 3
                    else:
                        score += 1
                    matched_words.add(word)
            
            # 관련 키워드 보너스
            for main_key, related in related_keywords.items():
                if main_key in query_lower:
                    for rel_word in related:
                        if rel_word in full_text and rel_word not in matched_words:
                            score = int(score + 0.5)
            
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
        
        # 결과 포맷팅
        if not search_results:
            return TextContent(type="text", text=f"'{query}'와 관련된 조문을 찾을 수 없습니다.")
        
        result = f"**{law_name}**에서 '{query}' 검색 결과 (상위 {len(search_results)}개)\n"
        result += "=" * 50 + "\n\n"
        
        for i, item in enumerate(search_results, 1):
            result += f"**{i}. 제{item['조문번호']}조"
            if item['조문제목']:
                result += f"({item['조문제목']})"
            result += f"** (관련도: {item['점수']})\n"
            result += f"{item['조문내용']}\n"
            result += f"→ 전체 내용: get_law_article_by_key(mst=\"{mst}\", target=\"{target}\", article_key=\"제{item['조문번호']}조\")\n\n"
        
        result += f"\n캐시 정보: {cache_key} (총 {len(all_articles)}개 조문 검색)"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"시맨틱 검색 중 오류: {e}")
        return TextContent(type="text", text=f"검색 중 오류가 발생했습니다: {str(e)}")

# 전역 클라이언트 인스턴스
law_client = LegislationClient()

# get_law_summary 도구는 optimized_law_tools.py로 이동됨 - 중복 제거

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
            # 캐시가 없으면 API 호출하여 전체 법령 데이터 가져오기
            params = {"MST": mst}
            data = _make_legislation_request("elaw", params, is_detail=True)
            
            if not data or 'Law' not in data:
                return TextContent(
                    type="text", 
                    text=f"영문 법령 데이터를 찾을 수 없습니다. (MST: {mst})"
                )
            
            # 캐시에 저장
            save_to_cache(cache_key, data)
            cached_data = data
        
        law_data = cached_data['Law']
        
        # JoSection에서 실제 조문 추출
        jo_section = law_data.get('JoSection', {})
        all_articles = []
        
        if jo_section and 'Jo' in jo_section:
            jo_data = jo_section['Jo']
            if isinstance(jo_data, list):
                # 실제 조문만 필터링 (joYn='Y'인 것들)
                all_articles = [jo for jo in jo_data if jo.get('joYn') == 'Y']
            elif isinstance(jo_data, dict) and jo_data.get('joYn') == 'Y':
                all_articles = [jo_data]
        
        if not all_articles:
            return TextContent(
                type="text",
                text=f"검색 가능한 조문이 없습니다. (MST: {mst})"
            )
        
        # 영문 시맨틱 검색 (키워드 매칭)
        search_results = []
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # 영문 관련 키워드 매핑
        related_keywords = {
            "contract": ["agreement", "covenant", "obligation", "performance"],
            "property": ["ownership", "possession", "title", "estate"],
            "commercial": ["business", "trade", "commerce", "merchant"],
            "civil": ["private", "individual", "personal", "civilian"],
            "liability": ["responsibility", "accountable", "damages", "compensation"],
            "company": ["corporation", "enterprise", "firm", "business"]
        }
        
        for article in all_articles:
            article_no = article.get('joNo', '')
            article_content = article.get('joCts', '')
            
            if not article_content:
                continue
            
            # 전체 텍스트 생성
            full_text = article_content.lower()
            
            # 점수 계산
            score = 0
            matched_words = set()
            
            # 전체 쿼리가 포함되어 있으면 최고 점수
            if query_lower in full_text:
                score += 10
                matched_words.add(query_lower)
            
            # 개별 단어 매칭
            for word in query_words:
                if word in full_text and word not in matched_words:
                    score += 2
                    matched_words.add(word)
            
            # 관련 키워드 보너스
            for main_key, related in related_keywords.items():
                if main_key in query_lower:
                    for rel_word in related:
                        if rel_word in full_text and rel_word not in matched_words:
                            score = int(score + 0.5)
            
            if score > 0:
                search_results.append({
                    "article_no": article_no,
                    "content": article_content[:300] + "..." if len(article_content) > 300 else article_content,
                    "score": score
                })
        
        # 점수순으로 정렬
        search_results.sort(key=lambda x: x['score'], reverse=True)
        search_results = search_results[:max_results]
        
        if not search_results:
            return TextContent(
                type="text",
                text=f"'{query}' 키워드와 관련된 조문을 찾을 수 없습니다."
            )
        
        # 결과 포맷팅
        result = f"**영문 법령 조문 검색 결과** (키워드: '{query}')\n"
        result += "=" * 50 + "\n\n"
        
        for i, item in enumerate(search_results, 1):
            result += f"**{i}. Article {item['article_no']}** (관련도: {item['score']:.1f})\n"
            result += f"{item['content']}\n\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"영문법령 시맨틱 검색 중 오류: {e}")
        return TextContent(
            type="text",
            text=f"영문법령 조문 검색 중 오류가 발생했습니다: {str(e)}"
        )

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

매개변수:
- law_name: 법령명 (필수) - 영어 또는 한국어 가능
  예: "Banking Act", "Income Tax Act", "은행법", "소득세법"
- keyword: 찾고자 하는 내용 (선택) - 영어로 입력
  예: "contract", "property", "liability", "company"
- show_detail: 찾은 조문의 전체 내용 표시 여부 (기본값: False)

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
    """영문 법령 통합 요약"""
    try:
        # 1단계: 영문 법령 검색 (내부 호출 시뮬레이션)
        # search_english_law 로직 직접 구현
        search_params = {
            "OC": legislation_config.oc,
            "type": "JSON", 
            "target": "elaw",
            "query": law_name,
            "search": 1,
            "display": 5,
            "page": 1
        }
        
        search_data = _make_legislation_request("elaw", search_params, is_detail=False)
        
        # 검색 결과에서 첫 번째 법령 선택
        if not search_data or 'LawSearch' not in search_data or 'law' not in search_data['LawSearch']:
            return TextContent(
                type="text",
                text=f"'{law_name}'에 해당하는 영문 법령을 찾을 수 없습니다."
            )
        
        laws = search_data['LawSearch']['law']
        if not laws:
            return TextContent(
                type="text",
                text=f"'{law_name}'에 해당하는 영문 법령을 찾을 수 없습니다."
            )
        
        current_law = laws[0] if isinstance(laws, list) else laws
        mst = current_law.get('법령일련번호')
        
        if not mst:
            return TextContent(
                type="text",
                text=f"법령일련번호를 찾을 수 없습니다."
            )
        
        # 2단계: 기본 법령 정보 조회
        detail_params = {"MST": mst}
        detail_data = _make_legislation_request("elaw", detail_params, is_detail=True)
        
        # 기본 정보 포맷팅
        result = "**영문 법령 요약**\n"
        result += "=" * 50 + "\n\n"
        
        result += "**기본 정보:**\n"
        result += f"• 영문명: {current_law.get('법령명영문', 'N/A')}\n"
        result += f"• 한글명: {current_law.get('법령명한글', 'N/A')}\n" 
        result += f"• 법령ID: {current_law.get('법령ID', 'N/A')}\n"
        result += f"• MST: {mst}\n"
        result += f"• 공포일자: {current_law.get('공포일자', 'N/A')}\n"
        result += f"• 시행일자: {current_law.get('시행일자', 'N/A')}\n"
        result += f"• 소관부처: {current_law.get('소관부처명', 'N/A')}\n\n"
        
        # 3단계: 키워드가 있으면 시맨틱 검색
        if keyword:
            # search_english_law_articles_semantic 로직 직접 구현
            cache_key = get_cache_key(f"elaw_{mst}", "full")
            cached_data = load_from_cache(cache_key)
            
            if not cached_data:
                cached_data = detail_data
                save_to_cache(cache_key, cached_data)
            
            if cached_data and 'Law' in cached_data:
                law_data = cached_data['Law']
                jo_section = law_data.get('JoSection', {})
                
                if jo_section and 'Jo' in jo_section:
                    jo_data = jo_section['Jo']
                    all_articles = []
                    
                    if isinstance(jo_data, list):
                        all_articles = [jo for jo in jo_data if jo.get('joYn') == 'Y']
                    elif isinstance(jo_data, dict) and jo_data.get('joYn') == 'Y':
                        all_articles = [jo_data]
                    
                    if all_articles:
                        # 간단한 키워드 검색
                        keyword_lower = keyword.lower()
                        matching_articles = []
                        
                        for article in all_articles[:20]:  # 처음 20개만 검색
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
            text=f"영문법령 요약 중 오류가 발생했습니다: {str(e)}"
        )