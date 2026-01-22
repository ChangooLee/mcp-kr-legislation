# src/mcp_kr_legislation/utils/api_crawler.py
"""
LAW OPEN DATA (open.law.go.kr) OPEN API 활용가이드 크롤러

Playwright 기반으로 guideList.do에서 전체 API를 클릭/방문하여 정보를 추출합니다.
- 원본 구분 그대로 18개 JSON 파일로 분리 (모바일 제외)
- sub_category(분류 컬럼) 포함
- rowspan 테이블 구조 처리

사용법:
    # 의존성 설치
    uv pip install playwright beautifulsoup4 lxml
    playwright install chromium
    
    # 실행
    python src/mcp_kr_legislation/utils/api_crawler.py
    
    # 디버그 (브라우저 보이게)
    HEADLESS=0 python src/mcp_kr_legislation/utils/api_crawler.py

출력:
    - src/mcp_kr_legislation/utils/api_layout/*.json (18개 구분별 파일)
    - src/mcp_kr_legislation/utils/api_layout/_failed_apis.log (실패 목록)
    - src/mcp_kr_legislation/utils/api_layout/_crawl_summary.json (요약)

알려진 문제:
    1. HTML 테이블의 rowspan으로 인해 물리적 td 개수가 행마다 다름
       -> parse_table_with_rowspan()으로 논리적 2D 테이블 변환
    2. 일부 API 셀은 텍스트 매칭 실패로 클릭 불가
       -> _failed_apis.log 확인 후 수동 보완 필요
    3. 문서에 없는 API는 target 값을 패턴으로 추정
       - 중앙부처 법령해석: {부처영문약어}CgmExpc
       - 특별행정심판: {기관영문약어}SpecialDecc
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeoutError


GUIDE_LIST_URL = "https://open.law.go.kr/LSO/openApi/guideList.do"
OUTPUT_DIR = Path(__file__).resolve().parent / "api_layout"

# 원본 구분(모바일 제외) 18개를 그대로 파일로 분리
CATEGORY_CONFIG: Dict[str, Dict[str, str]] = {
    "법령": {"en": "law", "file": "law.json"},
    "행정규칙": {"en": "admin_rule", "file": "admin_rule.json"},
    "자치법규": {"en": "local_ordinance", "file": "local_ordinance.json"},
    "판례": {"en": "precedent", "file": "precedent.json"},
    "헌재결정례": {"en": "constitutional_court", "file": "constitutional_court.json"},
    "법령해석례": {"en": "legal_interpretation", "file": "legal_interpretation.json"},
    "행정심판례": {"en": "administrative_appeal", "file": "administrative_appeal.json"},
    "위원회 결정문": {"en": "committee", "file": "committee.json"},
    "위원회\n결정문": {"en": "committee", "file": "committee.json"},
    "조약": {"en": "treaty", "file": "treaty.json"},
    "별표ㆍ서식": {"en": "appendix", "file": "appendix.json"},
    "학칙ㆍ공단ㆍ공공기관": {"en": "school_corp", "file": "school_corp.json"},
    "학칙ㆍ공단\nㆍ공공기관": {"en": "school_corp", "file": "school_corp.json"},
    "법령용어": {"en": "legal_term", "file": "legal_term.json"},
    "맞춤형": {"en": "custom", "file": "custom.json"},
    "법령정보 지식베이스": {"en": "knowledge_base", "file": "knowledge_base.json"},
    "법령정보\n지식베이스": {"en": "knowledge_base", "file": "knowledge_base.json"},
    # "법령 간 관계", "지능형 법령검색 시스템"은 구분이 아니라 "법령정보 지식베이스"의 하위 분류(sub_category)임
    "중앙부처 1차 해석": {"en": "ministry_interpretation", "file": "ministry_interpretation.json"},
    "중앙부처\n1차 해석": {"en": "ministry_interpretation", "file": "ministry_interpretation.json"},
    "특별행정심판": {"en": "special_tribunal", "file": "special_tribunal.json"},
    # 제외
    "모바일": {"en": "mobile", "file": "mobile.json"},
}

SKIP_CATEGORY_EN = {"mobile"}

# 크롤링 실패 시 자동 보완할 API 목록
# 원인: 셀 텍스트 매칭 실패, 클릭/네비게이션 실패 등
SUPPLEMENT_APIS: Dict[str, List[dict]] = {
    "law": [
        {
            "title": "현행법령(시행일) 목록 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawSearch.do?target=eflaw",
            "target": "eflaw",
            "api_type": "목록조회",
            "sub_category": "본문",
        },
        {
            "title": "현행법령(시행일) 본문 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawService.do?target=eflaw",
            "target": "eflaw",
            "api_type": "본문조회",
            "sub_category": "본문",
        },
        {
            "title": "현행법령(시행일) 본문 조항호목 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawService.do?target=eflawjosub",
            "target": "eflawjosub",
            "api_type": "본문조회",
            "sub_category": "조항호목",
        },
    ],
    "committee": [
        {
            "title": "방송통신위원회 결정문 목록 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawSearch.do?target=kcc",
            "target": "kcc",
            "api_type": "목록조회",
            "sub_category": "방송통신위원회",
        },
        {
            "title": "방송통신위원회 결정문 본문 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawService.do?target=kcc",
            "target": "kcc",
            "api_type": "본문조회",
            "sub_category": "방송통신위원회",
        },
        {
            "title": "산업재해보상보험재심사위원회 결정문 목록 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawSearch.do?target=iaciac",
            "target": "iaciac",
            "api_type": "목록조회",
            "sub_category": "산업재해보상보험재심사위원회",
        },
        {
            "title": "산업재해보상보험재심사위원회 결정문 본문 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawService.do?target=iaciac",
            "target": "iaciac",
            "api_type": "본문조회",
            "sub_category": "산업재해보상보험재심사위원회",
        },
    ],
    "ministry_interpretation": [
        {
            "title": "과학기술정보통신부 법령해석 목록 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawSearch.do?target=msitCgmExpc",
            "target": "msitCgmExpc",
            "api_type": "목록조회",
            "sub_category": "과학기술정보통신부",
        },
        {
            "title": "과학기술정보통신부 법령해석 본문 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawService.do?target=msitCgmExpc",
            "target": "msitCgmExpc",
            "api_type": "본문조회",
            "sub_category": "과학기술정보통신부",
        },
        {
            "title": "행정중심복합도시건설청 법령해석 목록 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawSearch.do?target=naaccCgmExpc",
            "target": "naaccCgmExpc",
            "api_type": "목록조회",
            "sub_category": "행정중심복합도시건설청",
        },
        {
            "title": "행정중심복합도시건설청 법령해석 본문 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawService.do?target=naaccCgmExpc",
            "target": "naaccCgmExpc",
            "api_type": "본문조회",
            "sub_category": "행정중심복합도시건설청",
        },
    ],
    "special_tribunal": [
        {
            "title": "조세심판원 특별행정심판례 목록 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawSearch.do?target=ttSpecialDecc",
            "target": "ttSpecialDecc",
            "api_type": "목록조회",
            "sub_category": "조세심판원",
        },
        {
            "title": "조세심판원 특별행정심판례 본문 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawService.do?target=ttSpecialDecc",
            "target": "ttSpecialDecc",
            "api_type": "본문조회",
            "sub_category": "조세심판원",
        },
        {
            "title": "해양안전심판원 특별행정심판례 목록 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawSearch.do?target=kmstSpecialDecc",
            "target": "kmstSpecialDecc",
            "api_type": "목록조회",
            "sub_category": "해양안전심판원",
        },
        {
            "title": "해양안전심판원 특별행정심판례 본문 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawService.do?target=kmstSpecialDecc",
            "target": "kmstSpecialDecc",
            "api_type": "본문조회",
            "sub_category": "해양안전심판원",
        },
        {
            "title": "국민권익위원회 특별행정심판례 목록 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawSearch.do?target=acrcSpecialDecc",
            "target": "acrcSpecialDecc",
            "api_type": "목록조회",
            "sub_category": "국민권익위원회",
        },
        {
            "title": "국민권익위원회 특별행정심판례 본문 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawService.do?target=acrcSpecialDecc",
            "target": "acrcSpecialDecc",
            "api_type": "본문조회",
            "sub_category": "국민권익위원회",
        },
        {
            "title": "인사혁신처 소청심사위원회 특별행정심판재결례 목록 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawSearch.do?target=mpmSpecialDecc",
            "target": "mpmSpecialDecc",
            "api_type": "목록조회",
            "sub_category": "인사혁신처 소청심사위원회",
        },
        {
            "title": "인사혁신처 소청심사위원회 특별행정심판재결례 본문 조회 API",
            "request_url": "https://www.law.go.kr/DRF/lawService.do?target=mpmSpecialDecc",
            "target": "mpmSpecialDecc",
            "api_type": "본문조회",
            "sub_category": "인사혁신처 소청심사위원회",
        },
    ],
}


def parse_table_with_rowspan(html: str) -> List[List[dict]]:
    """
    rowspan/colspan을 처리하여 논리적 2D 테이블로 변환.
    각 셀은 {"text": str, "element": Tag or None} 형태.
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        return []
    
    rows = table.find_all("tr")
    if not rows:
        return []
    
    # 최대 컬럼 수 계산
    max_cols = 0
    for tr in rows:
        cols = 0
        for cell in tr.find_all(["td", "th"]):
            colspan = int(cell.get("colspan", 1))
            cols += colspan
        max_cols = max(max_cols, cols)
    
    # 논리적 테이블 초기화 (None으로 채움)
    logical_table: List[List[Optional[dict]]] = [
        [None for _ in range(max_cols)] for _ in range(len(rows))
    ]
    
    for row_idx, tr in enumerate(rows):
        col_idx = 0
        for cell in tr.find_all(["td", "th"]):
            # 이미 채워진 셀 건너뛰기 (이전 rowspan에 의해)
            while col_idx < max_cols and logical_table[row_idx][col_idx] is not None:
                col_idx += 1
            
            if col_idx >= max_cols:
                break
            
            rowspan = int(cell.get("rowspan", 1))
            colspan = int(cell.get("colspan", 1))
            text = _norm(cell.get_text(" ", strip=True))
            
            # rowspan x colspan 영역 채우기
            for r in range(rowspan):
                for c in range(colspan):
                    target_row = row_idx + r
                    target_col = col_idx + c
                    if target_row < len(rows) and target_col < max_cols:
                        logical_table[target_row][target_col] = {
                            "text": text,
                            "element": cell if (r == 0 and c == 0) else None,
                            "is_origin": (r == 0 and c == 0),
                        }
            
            col_idx += colspan
    
    # None을 빈 셀로 변환
    for r in range(len(logical_table)):
        for c in range(len(logical_table[r])):
            if logical_table[r][c] is None:
                logical_table[r][c] = {"text": "", "element": None, "is_origin": False}
    
    return logical_table


@dataclass
class Parameter:
    name: str
    type: str
    description: str


@dataclass
class SampleUrl:
    format: str
    url: str


@dataclass
class ApiItem:
    id: str
    title: str
    request_url: Optional[str]
    target: Optional[str]
    api_type: Optional[str]
    sub_category: Optional[str]
    parameters: List[Parameter]
    sample_urls: List[SampleUrl]


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _extract_request_url(text: str) -> Optional[str]:
    m = re.search(r"요청\s*URL\s*:\s*(https?://[^\s]+)", text)
    return m.group(1).strip() if m else None


def _extract_target_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    try:
        q = parse_qs(urlparse(url).query)
        if "target" in q and q["target"]:
            return q["target"][0]
    except Exception:
        return None
    return None


def _parse_api_type(title: str) -> Optional[str]:
    t = title.replace("API", "").strip()
    if "목록" in t and "조회" in t:
        return "목록조회"
    if "본문" in t and "조회" in t:
        return "본문조회"
    return None


def _parse_request_params(soup: BeautifulSoup) -> List[Parameter]:
    # '요청변수/값/설명' 헤더를 가진 테이블 찾기
    for tbl in soup.find_all("table"):
        header_text = _norm(tbl.get_text(" ", strip=True))
        if "요청변수" in header_text and "값" in header_text and "설명" in header_text:
            rows = tbl.find_all("tr")
            if len(rows) < 2:
                continue

            out: List[Parameter] = []
            for tr in rows[1:]:
                cols = tr.find_all(["td", "th"])
                if len(cols) < 3:
                    continue
                out.append(
                    Parameter(
                        name=_norm(cols[0].get_text(" ", strip=True)),
                        type=_norm(cols[1].get_text(" ", strip=True)),
                        description=_norm(cols[2].get_text(" ", strip=True)),
                    )
                )
            # 빈 name 제거
            return [p for p in out if p.name]
    return []


def _parse_sample_urls(soup: BeautifulSoup) -> List[SampleUrl]:
    out: List[SampleUrl] = []

    # a[href] 기반으로 HTML/XML/JSON 추출
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not (href.startswith("http://") or href.startswith("https://")):
            continue

        label = _norm(a.get_text(" ", strip=True)).upper()
        fmt = None
        if "HTML" in label:
            fmt = "HTML"
        elif "XML" in label:
            fmt = "XML"
        elif "JSON" in label:
            fmt = "JSON"
        else:
            q = parse_qs(urlparse(href).query)
            t = (q.get("type", [""])[0] or "").upper()
            if t:
                fmt = t

        if fmt:
            out.append(SampleUrl(format=fmt, url=href))

    # 텍스트만 있는 경우 대비
    if not out:
        text = soup.get_text("\n", strip=True)
        for m in re.finditer(r"(https?://[^\s]+)", text):
            url = m.group(1)
            q = parse_qs(urlparse(url).query)
            t = (q.get("type", [""])[0] or "").upper()
            if t:
                out.append(SampleUrl(format=t, url=url))

    uniq = {(s.format, s.url): s for s in out}
    return list(uniq.values())


def parse_guide_result(html: str) -> Tuple[Optional[str], Optional[str], List[Parameter], List[SampleUrl]]:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)
    request_url = _extract_request_url(text)
    target = _extract_target_from_url(request_url)
    params = _parse_request_params(soup)
    samples = _parse_sample_urls(soup)
    return request_url, target, params, samples


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_category_file(category_ko: str, category_en: str, filename: str, items: List[ApiItem]) -> Path:
    ensure_output_dir()
    payload = {
        "category": category_ko.replace("\n", " "),
        "category_en": category_en,
        "updated_at": _today(),
        "api_count": len(items),
        "apis": [asdict(x) for x in items],
    }
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run(headless: bool = True) -> None:
    """
    guideList 표를 순회하며:
    - 구분(category) / 분류(sub_category) / 제공API(title)
    - 제공API 셀 클릭 -> guideResult 방문 -> request_url/params/samples/target 추출
    - 구분별 JSON(18개) 생성
    - 모바일 구분은 전체 제외
    - rowspan 처리: 논리적 테이블로 변환 후 처리
    """
    ensure_output_dir()

    # category_en -> ApiItem list
    buckets: Dict[str, List[ApiItem]] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(GUIDE_LIST_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        # 1단계: HTML에서 논리적 테이블 구조 파싱 (rowspan 처리)
        html_content = page.content()
        logical_table = parse_table_with_rowspan(html_content)
        
        if len(logical_table) < 2:
            raise RuntimeError("guideList.do에서 API 목록 행을 찾지 못했습니다.")

        print(f"[DEBUG] 논리적 테이블: {len(logical_table)}행 x {len(logical_table[0]) if logical_table else 0}열")
        
        # 디버그 추적
        failed_clicks = []
        total_cells_found = 0
        skipped_mobile = 0

        # 2단계: 논리적 테이블 순회 (헤더 제외, row 1부터)
        for row_idx in range(1, len(logical_table)):
            row = logical_table[row_idx]
            if len(row) < 3:
                continue
            
            # 컬럼 구조: [구분, 분류, 제공API1, 제공API2, ...]
            category_text = row[0]["text"]
            sub_category_text = row[1]["text"] or None
            
            # 구분 확인
            cfg = CATEGORY_CONFIG.get(category_text)
            if not cfg:
                # 줄바꿈 변형 체크
                for k, v in CATEGORY_CONFIG.items():
                    if _norm(k) == _norm(category_text):
                        cfg = v
                        break
            
            if not cfg:
                continue
            
            category_en = cfg["en"]
            filename = cfg["file"]
            
            # 모바일 스킵
            if category_en in SKIP_CATEGORY_EN:
                skipped_mobile += 1
                continue
            
            buckets.setdefault(category_en, [])
            
            # 제공API 셀들 (col 2부터)
            for col_idx in range(2, len(row)):
                cell_info = row[col_idx]
                title = cell_info["text"]
                
                if not title or title in {"-", "—", ""}:
                    continue
                
                # 중복 클릭 방지: is_origin이 True인 셀만 클릭 (rowspan 원본)
                if not cell_info["is_origin"]:
                    continue
                
                total_cells_found += 1
                
                # Playwright로 해당 셀 찾아서 클릭
                # 물리적 행/열 인덱스로 셀 찾기
                html = None
                try:
                    # CSS selector로 정확한 셀 위치 찾기
                    cell_selector = f"table tr:nth-child({row_idx + 1}) td:has-text('{title[:20]}')"
                    cell = page.locator(cell_selector).first
                    
                    if not cell.is_visible():
                        # 대안: 텍스트로 찾기
                        cell = page.locator(f"td:has-text('{title}')").first
                    
                    # popup 우선
                    try:
                        with page.expect_popup(timeout=800) as pop:
                            cell.click(timeout=2500)
                        pop_page = pop.value
                        pop_page.wait_for_load_state("domcontentloaded", timeout=7000)
                        html = pop_page.content()
                        pop_page.close()
                    except PwTimeoutError:
                        pass
                    except Exception:
                        pass

                    # navigation fallback
                    if html is None:
                        try:
                            with page.expect_navigation(wait_until="domcontentloaded", timeout=7000):
                                cell.click(timeout=2500)
                            html = page.content()
                        except PwTimeoutError:
                            page.wait_for_timeout(800)
                            if "guideResult.do" in page.url:
                                html = page.content()
                        except Exception:
                            pass
                    
                except Exception as e:
                    print(f"[WARN] 셀 찾기 실패: row={row_idx}, col={col_idx}, title='{title}', error={e}")
                    continue

                if html is None:
                    failed_clicks.append(f"row={row_idx}, col={col_idx}, title='{title}', category='{category_text}'")
                    print(f"[WARN] HTML 확보 실패: row={row_idx}, col={col_idx}, title={title}")
                    if "guideResult.do" in page.url:
                        try:
                            page.go_back(wait_until="domcontentloaded")
                            page.wait_for_timeout(300)
                        except Exception:
                            pass
                    continue

                request_url, target, params, samples = parse_guide_result(html)

                api_item = ApiItem(
                    id="__TEMP__",
                    title=title if title.endswith("API") else f"{title} API",
                    request_url=request_url,
                    target=target,
                    api_type=_parse_api_type(title),
                    sub_category=sub_category_text,
                    parameters=params,
                    sample_urls=samples,
                )
                buckets[category_en].append(api_item)
                print(f"[OK] {category_text}/{sub_category_text}: {title}")

                # 목록으로 복귀
                if "guideResult.do" in page.url:
                    page.go_back(wait_until="domcontentloaded")
                    page.wait_for_timeout(400)

        browser.close()

    # 실패한 API 자동 보완
    supplemented_count = 0
    for category_en, supplement_list in SUPPLEMENT_APIS.items():
        if category_en not in buckets:
            buckets[category_en] = []
        
        # 이미 추출된 title 목록
        existing_titles = {api.title for api in buckets[category_en]}
        
        for sup in supplement_list:
            if sup["title"] not in existing_titles:
                api_item = ApiItem(
                    id="__TEMP__",
                    title=sup["title"],
                    request_url=sup["request_url"],
                    target=sup["target"],
                    api_type=sup["api_type"],
                    sub_category=sup["sub_category"],
                    parameters=[],
                    sample_urls=[],
                )
                buckets[category_en].append(api_item)
                supplemented_count += 1
                print(f"[SUPPLEMENT] {category_en}: {sup['title']}")

    # 디버그 요약 출력
    total_extracted = sum(len(v) for v in buckets.values())
    crawled_count = total_extracted - supplemented_count
    print("\n" + "="*70)
    print("[CRAWL SUMMARY]")
    print("="*70)
    print(f"  논리적 테이블 행 수: {len(logical_table)}")
    print(f"  발견된 API 셀 수  : {total_cells_found}")
    print(f"  크롤링 성공       : {crawled_count}")
    print(f"  자동 보완         : {supplemented_count}")
    print(f"  총 추출           : {total_extracted}")
    print(f"  추출 실패         : {len(failed_clicks) - supplemented_count}")
    print(f"  모바일 스킵       : {skipped_mobile}행")
    
    if failed_clicks:
        print(f"\n[FAILED APIS] 클릭/HTML 확보 실패 ({len(failed_clicks)}개):")
        print("-"*70)
        for fail in failed_clicks:
            print(f"  - {fail}")
        
        # 실패 목록 파일 저장
        failed_log_path = OUTPUT_DIR / "_failed_apis.log"
        with open(failed_log_path, "w", encoding="utf-8") as f:
            f.write(f"# 크롤링 실패 API 목록\n")
            f.write(f"# 생성일: {_today()}\n")
            f.write(f"# 총 {len(failed_clicks)}개\n\n")
            for fail in failed_clicks:
                f.write(f"{fail}\n")
        print(f"\n  -> 실패 목록 저장: {failed_log_path}")
    
    if supplemented_count > 0:
        print(f"\n[AUTO SUPPLEMENT] 자동 보완된 API ({supplemented_count}개):")
        print("-"*70)
        for cat, apis in SUPPLEMENT_APIS.items():
            titles = [a["title"] for a in apis]
            if titles:
                print(f"  {cat}: {', '.join(t.replace(' API', '') for t in titles)}")
    
    print("\n[NOTES]")
    print("-"*70)
    print("  - rowspan 처리: HTML 테이블의 rowspan을 논리적 2D 테이블로 변환")
    print("  - 자동 보완: SUPPLEMENT_APIS에 정의된 API는 크롤링 실패 시 자동 추가")
    print("  - target 패턴: 중앙부처={약어}CgmExpc, 특별행정심판={약어}SpecialDecc")
    print("="*70 + "\n")

    # 크롤링 요약 JSON 저장
    summary = {
        "crawl_date": _today(),
        "source_url": GUIDE_LIST_URL,
        "table_rows": len(logical_table),
        "api_cells_found": total_cells_found,
        "crawled_success": crawled_count,
        "auto_supplemented": supplemented_count,
        "total_extracted": total_extracted,
        "failed_count": len(failed_clicks) - supplemented_count,
        "mobile_skipped": skipped_mobile,
        "failed_apis": [f for f in failed_clicks if not any(
            sup["title"] in f for sups in SUPPLEMENT_APIS.values() for sup in sups
        )],
        "supplemented_apis": {k: [s["title"] for s in v] for k, v in SUPPLEMENT_APIS.items()},
        "category_counts": {k: len(v) for k, v in buckets.items()},
    }
    summary_path = OUTPUT_DIR / "_crawl_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 크롤링 요약 저장: {summary_path}\n")

    # 파일 저장(18개) + id 재부여
    # 중복 없이 각 category_en별로 한 번만 저장
    saved_categories = set()
    for category_ko, cfg in CATEGORY_CONFIG.items():
        category_en = cfg["en"]
        filename = cfg["file"]

        if category_en in SKIP_CATEGORY_EN:
            continue

        if category_en in saved_categories:
            continue

        items = buckets.get(category_en, [])
        
        # 빈 파일 생성하지 않음
        if not items:
            print(f"[SKIP] {category_ko.replace(chr(10), ' ')}({category_en}): 0개 - 빈 파일 생성 안함")
            saved_categories.add(category_en)
            continue
        
        for idx, it in enumerate(items, 1):
            it.id = str(idx)

        out = write_category_file(category_ko.replace("\n", " "), category_en, filename, items)
        saved_categories.add(category_en)
        print(f"[OK] {category_ko.replace(chr(10), ' ')}({category_en}): {len(items)} -> {out}")


if __name__ == "__main__":
    headless = os.environ.get("HEADLESS", "1") != "0"
    run(headless=headless)
