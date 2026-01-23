#!/usr/bin/env python3
"""
법령 조회 최적화 유틸리티
- 대용량 응답 처리를 위한 캐싱 시스템
- 필요한 정보만 추출하는 압축 기능
"""

import json
import os
import hashlib
import re
import requests  # type: ignore
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List, Tuple
from pathlib import Path
from bs4 import BeautifulSoup  # type: ignore

logger = logging.getLogger(__name__)

# 캐시 시스템 설정
CACHE_DIR = Path.home() / ".cache" / "mcp-kr-legislation"
CACHE_DAYS = 7  # 캐시 유효 기간
MAX_CACHE_SIZE_MB = 100  # 최대 캐시 크기 100MB

def ensure_cache_dir() -> bool:
    """캐시 디렉토리 확인 및 생성"""
    try:
        # 절대 경로로 변환
        abs_cache_dir = CACHE_DIR.resolve()
        abs_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 쓰기 권한 테스트
        test_file = abs_cache_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        
        return True
    except Exception as e:
        logger.warning(f"캐시 디렉토리 생성/쓰기 실패: {e}")
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
    
    # 파일 수정 시간 확인
    file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    expiry_time = datetime.now() - timedelta(days=CACHE_DAYS)
    
    return file_time > expiry_time

def save_to_cache(cache_key: str, data: Dict[str, Any]):
    """데이터를 캐시에 저장"""
    try:
        ensure_cache_dir()
        cache_path = get_cache_path(cache_key)
        
        # 메타데이터 추가
        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "data": data
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"캐시 저장 완료: {cache_key}")
        
    except Exception as e:
        logger.error(f"캐시 저장 실패: {e}")

def load_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """캐시에서 데이터 로드"""
    try:
        cache_path = get_cache_path(cache_key)
        
        if not is_cache_valid(cache_path):
            return None
            
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        logger.info(f"캐시 로드 완료: {cache_key}")
        return cache_data.get("data")
        
    except Exception as e:
        logger.error(f"캐시 로드 실패: {e}")
        return None

def format_date(date_str: str) -> str:
    """날짜 형식을 YYYY-MM-DD로 통일"""
    if date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str

def extract_law_summary(law_data: Dict[str, Any]) -> Dict[str, Any]:
    """법령 데이터에서 요약 정보만 추출"""
    if not law_data:
        return {}
    
    law_info = law_data.get("법령", {})
    basic_info = law_info.get("기본정보", {})
    
    # 소관부처 정보 추출 - dict인 경우와 string인 경우 모두 처리
    ministry_info = basic_info.get("소관부처", "")
    if isinstance(ministry_info, dict):
        ministry = ministry_info.get("content", ministry_info.get("소관부처명", "미지정"))
    else:
        ministry = ministry_info or basic_info.get("소관부처명", "미지정")
    
    # 법령일련번호 추출 개선
    mst = (basic_info.get("법령일련번호") or 
           basic_info.get("법령MST") or
           law_info.get("법령키", "")[:10] if law_info.get("법령키") else None)
    
    # 조문 미리보기 (처음 10개만)
    articles_data = law_info.get("조문", {})
    articles_preview = []
    
    if isinstance(articles_data, dict):
        articles = articles_data.get("조문단위", [])
        # 리스트가 아닌 경우 리스트로 변환
        if not isinstance(articles, list):
            articles = [articles] if articles else []
    else:
        articles = []
    
    # 실제 조문만 필터링 (조문여부가 "조문"인 것만)
    actual_articles = [a for a in articles if isinstance(a, dict) and a.get("조문여부") == "조문"]
    
    for article in actual_articles[:50]:  # 10개에서 50개로 확대
        article_no = article.get("조문번호", "")
        article_title = article.get("조문제목", "")
        article_content = article.get("조문내용", "")
        
        # HTML 태그 제거 및 정리
        import re
        if article_content:
            article_content = re.sub(r'<[^>]+>', '', article_content)
            # 조문 번호/제목 중복 제거 (조문내용에 "제N조(제목)" 형태가 포함된 경우)
            article_content = re.sub(r'^제\d+조(?:의\d+)?(?:\([^)]*\))?\s*', '', article_content)
            article_content = article_content.strip()[:100]
            if len(article.get("조문내용", "")) > 100:
                article_content += "..."
        
        # 미리보기: 제목 + 내용 (조문번호는 format_law_summary에서 추가됨)
        if article_title:
            preview = f"({article_title}) {article_content}"
        else:
            preview = article_content
        
        articles_preview.append({
            "조문번호": article_no,
            "조문제목": article_title,
            "미리보기": preview
        })
    
    # 제개정이유 추출
    revision_reason = []
    revision_section = law_info.get("개정문", {})
    if revision_section:
        reason_content = revision_section.get("개정문내용", [])
        if isinstance(reason_content, list) and reason_content:
            revision_reason = reason_content[0][:3] if len(reason_content[0]) >= 3 else reason_content[0]
    
    return {
        "법령명": basic_info.get("법령명_한글", basic_info.get("법령명한글", "")),
        "법령ID": basic_info.get("법령ID", ""),
        "법령일련번호": mst,
        "공포일자": format_date(basic_info.get("공포일자", "")),
        "시행일자": format_date(basic_info.get("시행일자", "")),
        "소관부처": ministry,
        "제개정구분": basic_info.get("제개정구분", ""),
        "조문개수": len(actual_articles),
        "조문미리보기": articles_preview,
        "제개정이유": revision_reason
    }

def extract_law_articles(law_data: Dict[str, Any], start_article: int = 1, count: int = 20) -> Dict[str, Any]:
    """법령 조문만 추출 (페이징 지원)"""
    try:
        law_info = law_data.get("법령", {})
        articles = law_info.get("조문", {})
        
        if not isinstance(articles, dict):
            return {"조문": {}, "총개수": 0}
        
        # 조문 키들을 정렬 (제1조, 제2조, ...)
        article_keys = sorted(articles.keys(), key=lambda x: extract_article_number(x))
        
        # 페이징 처리
        start_idx = start_article - 1
        end_idx = start_idx + count
        selected_keys = article_keys[start_idx:end_idx]
        
        # 선택된 조문만 추출
        selected_articles = {key: articles[key] for key in selected_keys if key in articles}
        
        return {
            "조문": selected_articles,
            "총개수": len(articles),
            "현재페이지": f"{start_article}-{start_article + len(selected_articles) - 1}",
            "기본정보": law_info.get("기본정보", {})
        }
        
    except Exception as e:
        logger.error(f"조문 추출 실패: {e}")
        return {"조문": {}, "총개수": 0}

def extract_article_number(article_key: str) -> int:
    """조문 키에서 숫자 추출 (정렬용)"""
    try:
        # "제1조", "제2조의2" 등에서 숫자 추출
        import re
        match = re.search(r'제(\d+)조', article_key)
        return int(match.group(1)) if match else 999999
    except:
        return 999999

def fetch_law_data(law_id: str, oc: str = "lchangoo", use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """법령 데이터 조회 (캐싱 지원)"""
    try:
        cache_key = get_cache_key(law_id, "full")
        
        # 캐시 확인
        if use_cache:
            cached_data = load_from_cache(cache_key)
            if cached_data:
                logger.info(f"캐시에서 법령 조회: {law_id}")
                return cached_data
        
        # API 호출
        url = "http://www.law.go.kr/DRF/lawService.do"
        params = {
            "OC": oc,
            "type": "JSON",
            "target": "law",
            "MST": law_id
        }
        
        logger.info(f"API에서 법령 조회: {law_id}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # 캐시에 저장
        if use_cache:
            save_to_cache(cache_key, data)
        
        return data
        
    except Exception as e:
        logger.error(f"법령 조회 실패: {e}")
        return None

def format_law_summary(summary_data: Dict[str, Any], search_term: str = "") -> str:
    """법령 요약 정보 포맷팅"""
    try:
        if not summary_data:
            return "법령 정보를 찾을 수 없습니다."
        
        # extract_law_summary가 평평한 구조로 반환하므로 직접 접근
        # 만약 중첩 구조인 경우 기존 로직 유지
        if "기본정보" in summary_data:
            basic_info = summary_data.get("기본정보", {})
            # 기본 정보 추출 (중첩 구조)
            law_name = basic_info.get("법령명_한글", basic_info.get("법령명한글", basic_info.get("법령명", "이름 없음")))
            law_id = basic_info.get("법령ID", "ID 없음")
            announce_date = basic_info.get("공포일자", "")
            enforce_date = basic_info.get("시행일자", "")
            ministry = basic_info.get("소관부처", "")
        else:
            # 평평한 구조에서 직접 추출
            law_name = summary_data.get("법령명", "이름 없음")
            law_id = summary_data.get("법령ID", "ID 없음")
            announce_date = summary_data.get("공포일자", "")
            enforce_date = summary_data.get("시행일자", "")
            ministry = summary_data.get("소관부처", "")
        
        # 소관부처 처리 (딕셔너리일 수 있음)
        if isinstance(ministry, dict):
            ministry = ministry.get("소관부처명", ministry.get("부처명", "미지정"))
        elif not ministry:
            ministry = "미지정"
        
        result = f"**{law_name}** 요약\n"
        result += "=" * 50 + "\n\n"
        result += f"**기본 정보:**\n"
        result += f"• **법령ID**: {law_id}\n"
        result += f"• **공포일자**: {announce_date}\n"
        result += f"• **시행일자**: {enforce_date}\n"
        result += f"• **소관부처**: {ministry}\n\n"
        
        # 조문 미리보기 (평평한 구조 대응)
        articles_preview = summary_data.get("조문미리보기", summary_data.get("조문_미리보기", {}))
        total_articles = summary_data.get("조문개수", summary_data.get("조문_총개수", 0))
        
        if articles_preview:
            # articles_preview가 리스트인 경우와 딕셔너리인 경우 모두 처리
            if isinstance(articles_preview, list):
                result += f"**조문 미리보기** (총 {total_articles}개 조문 중 처음 {len(articles_preview)}개):\n\n"
                
                for i, article_info in enumerate(articles_preview, 1):
                    if isinstance(article_info, dict):
                        article_no = article_info.get("조문번호", f"{i}")
                        preview_text = article_info.get("미리보기", "")
                        # 조문번호 + 미리보기 (중복 방지)
                        result += f"**제{article_no}조**: {preview_text}\n\n"
                    else:
                        result += f"**조문{i}**: {str(article_info)}\n\n"
            else:
                # 기존 딕셔너리 처리 로직
                result += f"**조문 미리보기** (총 {total_articles}개 조문 중 처음 {len(articles_preview)}개):\n\n"
                
                for i, (article_key, article_content) in enumerate(articles_preview.items(), 1):
                    # 조문 제목과 내용을 간략히 표시
                    if isinstance(article_content, dict):
                        article_text = article_content.get("조문내용", str(article_content))
                    else:
                        article_text = str(article_content)
                    
                    # 내용이 너무 길면 줄임
                    if len(article_text) > 200:
                        article_text = article_text[:200] + "..."
                    
                    result += f"**{article_key}**: {article_text}\n\n"
        
        # 제개정 이유
        enactment_reason = summary_data.get("제개정이유", "")
        if enactment_reason:
            # 딕셔너리 구조인 경우 처리
            if isinstance(enactment_reason, dict):
                reason_content = enactment_reason.get("제개정이유내용", [])
                if isinstance(reason_content, list) and reason_content:
                    reason_text = " ".join(str(item) for item in reason_content[:3])  # 처음 3개 항목만
                else:
                    reason_text = str(reason_content)
            else:
                reason_text = str(enactment_reason)
            
            if reason_text and len(reason_text.strip()) > 0:
                result += f"**제개정 이유:**\n{reason_text[:500]}{'...' if len(reason_text) > 500 else ''}\n\n"
        
        # 추가 정보
        original_size = summary_data.get("원본크기_kb", 0)
        result += f"**전체 조문 보기**: `get_law_articles` 도구를 사용하세요.\n"
        result += f"**원본 데이터 크기**: {original_size}KB\n"
        
        return result
        
    except Exception as e:
        logger.error(f"법령 요약 포맷팅 실패: {e}")
        return f"법령 정보 처리 중 오류: {str(e)}"

def format_law_articles(articles_data: Dict[str, Any], page_info: str = "") -> str:
    """법령 조문 포맷팅"""
    try:
        if not articles_data:
            return "조문 정보를 찾을 수 없습니다."
        
        articles = articles_data.get("조문", {})
        total_count = articles_data.get("총개수", 0)
        current_page = articles_data.get("현재페이지", "")
        basic_info = articles_data.get("기본정보", {})
        
        law_name = basic_info.get("법령명_한글", basic_info.get("법령명한글", basic_info.get("법령명", "이름 없음")))
        
        result = f"**{law_name}** 조문\n"
        result += "=" * 50 + "\n\n"
        
        if current_page:
            result += f"**📄 조문 {current_page}** (총 {total_count}개 조문)\n\n"
        
        # 조문 내용 출력
        for article_key, article_content in articles.items():
            result += f"## **{article_key}**\n\n"
            
            if isinstance(article_content, dict):
                # 조문 구조가 복잡한 경우
                content = article_content.get("조문내용", str(article_content))
            else:
                content = str(article_content)
            
            result += f"{content}\n\n"
            result += "-" * 30 + "\n\n"
        
        # 페이지 네비게이션 정보
        if total_count > len(articles):
            result += f"**더 많은 조문 보기**: 다음 페이지의 조문을 보려면 `get_law_articles`를 다시 호출하세요.\n"
        
        return result
        
    except Exception as e:
        logger.error(f"조문 포맷팅 실패: {e}")
        return f"조문 정보 처리 중 오류: {str(e)}"


# =============================================================================
# HTML 파싱 관련 함수들 (HTML 응답 API 지원)
# =============================================================================

def extract_mst_from_url(url: str) -> Optional[str]:
    """URL에서 MST 값을 추출합니다."""
    try:
        # MST=숫자 패턴 찾기
        match = re.search(r'MST=(\d+)', url)
        if match:
            return match.group(1)
        
        # ID=숫자 패턴도 시도 (일부 API에서 사용)
        match = re.search(r'ID=(\d+)', url)
        if match:
            return match.group(1)
            
        return None
    except Exception as e:
        logger.error(f"MST 추출 실패: {e}")
        return None


def clean_html_text(text: str) -> str:
    """HTML 태그를 제거하고 텍스트를 정리합니다."""
    try:
        # BeautifulSoup으로 HTML 태그 제거
        soup = BeautifulSoup(text, 'html.parser')
        clean_text = soup.get_text()
        
        # 여러 공백을 하나로 줄이기
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # 앞뒤 공백 제거
        return clean_text.strip()
        
    except Exception as e:
        logger.error(f"HTML 텍스트 정리 실패: {e}")
        return text.strip()