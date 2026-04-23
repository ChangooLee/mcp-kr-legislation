"""
고도화 검색 도구 모음 (kiwipiepy + BM25)

BM25 재랭킹 검색:
  search_law_bm25          - 법령 BM25 검색
  search_precedent_bm25    - 판례/헌재/행정심판 BM25 검색
  search_legal_term_bm25   - 법령용어 BM25 검색
  search_committee_bm25    - 위원회결정문 BM25 검색
  search_admin_rule_bm25   - 행정규칙 BM25 검색
  search_interpretation_bm25 - 법령해석례/중앙부처해석 BM25 검색
  search_all_bm25          - 전 카테고리 통합 BM25 검색

캐시 관리:
  get_cache_status         - 캐시 상태 조회
  cleanup_cache_tool       - 오래된 캐시 정리
  invalidate_law_cache     - 특정 법령 캐시 무효화

검색 진단:
  explain_bm25_tokenize    - 쿼리 형태소 분석 결과 확인
"""

import json
import logging
from typing import Annotated, Any, Optional

from mcp.types import TextContent

from ..server import mcp
from ..config import legislation_config
from ..utils.bm25_search import rank_search_results
from ..utils.legislation_utils import (
    cleanup_cache,
    get_cache_stats,
    invalidate_cache,
    get_cache_key,
    load_from_cache,
    save_to_cache,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _extract_api_keyword(query: str) -> str:
    """
    자연어 쿼리에서 API 검색에 최적인 핵심 키워드를 추출합니다.

    전략: 공백 기준 첫 번째 단어를 우선 사용.
    kiwipiepy 형태소 분석은 합성어를 분해하는 경우가 있어 법령명 검색에
    오히려 불리하므로, 첫 단어를 우선하고 형태소 분석은 BM25 재랭킹에만 사용.
    """
    words = query.strip().split()
    if not words:
        return query
    # 첫 단어가 2글자 이상이면 그대로 사용
    if len(words[0]) >= 2:
        return words[0]
    # 첫 단어가 너무 짧으면 두 단어 조합 시도
    if len(words) >= 2:
        return words[0] + words[1]
    return words[0]


def _raw_search(target: str, query: str, display: int = 50) -> dict:
    """법제처 API를 직접 호출하고 원시 dict를 반환합니다.

    전체 쿼리로 먼저 시도하고, 결과가 없으면 핵심 키워드로 재시도합니다.
    """
    import requests

    oc = legislation_config.oc
    url = legislation_config.search_base_url
    headers = {
        "Referer": "https://open.law.go.kr/",
        "User-Agent": "mcp-kr-legislation/0.2.0",
    }

    def _call(q: str) -> dict:
        params = {
            "OC": oc, "target": target, "type": "JSON",
            "query": q, "display": min(display, 100),
        }
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        if not resp.text.strip():
            return {}
        try:
            return resp.json()
        except Exception:
            return {}

    # 1차 시도: 전체 쿼리
    data = _call(query)
    if data:
        # 결과가 있는지 확인 (items가 존재하면 반환)
        items = _extract_list(data)
        if items:
            return data

    # 2차 시도: 핵심 키워드 추출
    keyword = _extract_api_keyword(query)
    if keyword != query:
        fallback = _call(keyword)
        if fallback:
            return fallback

    return data  # 원본 반환 (빈 결과라도)


def _extract_list(data: dict, *hint_root_keys: str) -> list[dict]:
    """
    중첩된 dict에서 검색 결과 목록을 자동으로 추출합니다.

    법제처 API 응답 구조:
      { "RootKey": { "target_name": [...], "totalCnt": "...", ... } }

    hint_root_keys가 일치하면 그것부터 시도하고,
    없으면 전체 구조를 탐색하여 가장 큰 list를 반환합니다.
    """
    if not data:
        return []

    def _find_list_in_dict(d: dict) -> list[dict]:
        """dict 내에서 dict 항목들로 이루어진 가장 큰 list를 찾습니다."""
        best: list = []
        for v in d.values():
            if isinstance(v, list) and len(v) > len(best):
                # dict 항목들로 이루어진 list인지 확인
                if all(isinstance(item, dict) for item in v[:3]):
                    best = v
        return best

    # 1단계: hint_root_keys 우선 탐색
    for rk in hint_root_keys:
        if rk in data and isinstance(data[rk], dict):
            result = _find_list_in_dict(data[rk])
            if result:
                return result

    # 2단계: 전체 루트 키 탐색 (API 응답 구조 변형 대응)
    for v in data.values():
        if isinstance(v, dict):
            result = _find_list_in_dict(v)
            if result:
                return result
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            return v

    return []


# ---------------------------------------------------------------------------
# BM25 법령 검색
# ---------------------------------------------------------------------------

@mcp.tool(
    name="search_law_bm25",
    description="""BM25 알고리즘으로 관련도 순 재랭킹된 법령을 검색합니다.

기본 search_law와 달리 클라이언트 측에서 BM25 Okapi 알고리즘으로
관련도 점수를 계산하여 정렬합니다. 동의어·부분 일치 검색에 더 강합니다.

매개변수:
- query: 자연어 검색어 (예: "개인정보 처리 동의", "환경오염 규제")
- display: API에서 가져올 최대 결과 수 (기본 50, BM25 재랭킹 후 top_k 적용)
- top_k: BM25 재랭킹 후 반환할 최대 결과 수 (기본 10)

반환정보: BM25 점수(_bm25_score), 법령명, MST, 소관부처""",
    tags={"법령검색", "BM25", "재랭킹", "고도화검색"},
)
def search_law_bm25(
    query: Annotated[str, "자연어 검색어"],
    display: Annotated[int, "API에서 가져올 결과 수 (최대 100)"] = 50,
    top_k: Annotated[int, "BM25 재랭킹 후 반환할 최대 결과 수"] = 10,
) -> TextContent:
    """BM25 재랭킹 법령 검색"""
    if not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")

    cache_key = get_cache_key(f"bm25_law_{query}_{display}", "bm25")
    cached = load_from_cache(cache_key)
    if cached and isinstance(cached, list):
        items = cached
        from_cache = True
    else:
        try:
            data = _raw_search("law", query, display)
            items = _extract_list(data, "LawSearch")
            save_to_cache(cache_key, items)
            from_cache = False
        except Exception as e:
            logger.error(f"법령 검색 API 오류: {e}")
            return TextContent(type="text", text=f"API 호출 오류: {e}")

    if not items:
        return TextContent(type="text", text=f"'{query}' 검색 결과가 없습니다.")

    ranked = rank_search_results(
        query=query,
        results=items,
        text_keys=["법령명한글", "소관부처명", "법령구분명"],
        top_k=top_k,
    )

    lines = [
        f"**'{query}' BM25 재랭킹 결과** (API {len(items)}건 → 상위 {len(ranked)}건)"
        + (" [캐시]" if from_cache else ""),
        "",
    ]
    for i, law in enumerate(ranked, 1):
        score = law.get("_bm25_score", 0)
        lines += [
            f"**{i}. {law.get('법령명한글', '')}** (BM25 점수: {score})",
            f"   MST: {law.get('법령일련번호', '')}",
            f"   공포일자: {law.get('공포일자', '')}  시행일자: {law.get('시행일자', '')}",
            f"   소관부처: {law.get('소관부처명', '')}",
            f"   상세조회: get_law_detail(mst=\"{law.get('법령일련번호', '')}\")",
            "",
        ]

    lines += [
        "---",
        "* BM25 점수가 높을수록 검색어와 관련성이 높습니다.",
        "* 더 많은 결과: display 값을 높이세요.",
    ]
    return TextContent(type="text", text="\n".join(lines))


# ---------------------------------------------------------------------------
# BM25 판례 검색
# ---------------------------------------------------------------------------

@mcp.tool(
    name="search_precedent_bm25",
    description="""BM25 알고리즘으로 관련도 순 재랭킹된 판례를 검색합니다.

대법원 판례, 헌법재판소 결정례를 BM25로 재랭킹하여 반환합니다.

매개변수:
- query: 자연어 검색어 (예: "손해배상 과실상계", "위헌 표현의 자유")
- target: 검색 대상 (prec=대법원판례, ccurt=헌법재판소)
- display: API에서 가져올 최대 결과 수
- top_k: BM25 재랭킹 후 반환할 결과 수""",
    tags={"판례검색", "BM25", "재랭킹", "고도화검색"},
)
def search_precedent_bm25(
    query: Annotated[str, "자연어 검색어"],
    target: Annotated[str, "검색 대상 (prec=대법원, ccurt=헌법재판소)"] = "prec",
    display: Annotated[int, "API에서 가져올 결과 수 (최대 100)"] = 50,
    top_k: Annotated[int, "BM25 재랭킹 후 반환할 최대 결과 수"] = 10,
) -> TextContent:
    """BM25 재랭킹 판례 검색"""
    if not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")

    allowed_targets = {"prec", "ccurt", "admrul", "admjd"}
    if target not in allowed_targets:
        return TextContent(type="text", text=f"허용된 target: {allowed_targets}")

    cache_key = get_cache_key(f"bm25_{target}_{query}_{display}", "bm25")
    cached = load_from_cache(cache_key)
    if cached and isinstance(cached, list):
        items = cached
        from_cache = True
    else:
        try:
            data = _raw_search(target, query, display)
            # 판례별 응답 구조가 다르므로 모든 루트 키 시도
            root_keys = {
                "prec": "PrecSearch",
                "ccurt": "CcurtSearch",
                "admrul": "AdmrulSearch",
                "admjd": "AdmjdSearch",
            }
            items = _extract_list(data, root_keys.get(target, ""))
            save_to_cache(cache_key, items)
            from_cache = False
        except Exception as e:
            logger.error(f"판례 검색 API 오류: {e}")
            return TextContent(type="text", text=f"API 호출 오류: {e}")

    if not items:
        return TextContent(type="text", text=f"'{query}' 검색 결과가 없습니다.")

    # 판례 필드 매핑
    text_key_map = {
        "prec": ["사건명", "법원명", "사건종류명"],
        "ccurt": ["사건명", "결정유형명"],
        "admrul": ["법령명", "소관부처명"],
        "admjd": ["심판청구명", "재결유형"],
    }

    ranked = rank_search_results(
        query=query,
        results=items,
        text_keys=text_key_map.get(target, None),
        top_k=top_k,
    )

    target_labels = {
        "prec": "대법원 판례", "ccurt": "헌법재판소 결정례",
        "admrul": "행정규칙", "admjd": "행정심판례",
    }
    label = target_labels.get(target, target)

    lines = [
        f"**'{query}' {label} BM25 결과** (API {len(items)}건 → 상위 {len(ranked)}건)"
        + (" [캐시]" if from_cache else ""),
        "",
    ]
    for i, item in enumerate(ranked, 1):
        score = item.get("_bm25_score", 0)
        case_name = (
            item.get("사건명") or item.get("법령명") or item.get("심판청구명", "")
        )
        # 제목 70자 제한
        if len(case_name) > 70:
            case_name = case_name[:70] + "..."
        case_no = item.get("사건번호") or item.get("사건ID", "")
        court = (
            item.get("법원명") or item.get("소관부처명") or item.get("재결기관", "")
        )
        # 숫자형 case_id (get_precedent_detail 등에서 필요)
        numeric_id = (
            item.get("판례일련번호") or item.get("결정례일련번호")
            or item.get("행정심판재결례일련번호") or item.get("ID") or item.get("id", "")
        )
        item_lines = [
            f"**{i}. {case_name}** (BM25: {score:.4f})",
            f"   사건번호: {case_no}  |  기관: {court}",
        ]
        if numeric_id and target == "prec":
            item_lines.append(f"   ★ 상세조회: get_precedent_detail(case_id=\"{numeric_id}\")")
        elif numeric_id and target == "ccurt":
            item_lines.append(f"   ★ 상세조회: get_constitutional_court_detail(case_id=\"{numeric_id}\")")
        item_lines.append("")
        lines += item_lines

    return TextContent(type="text", text="\n".join(lines))


# ---------------------------------------------------------------------------
# 캐시 관리 도구
# ---------------------------------------------------------------------------

@mcp.tool(
    name="get_cache_status",
    description="""현재 법령 캐시 상태를 조회합니다.

캐시 파일 수, 총 용량, 가장 오래된/최신 캐시 날짜 등을 반환합니다.
캐시 경로: ~/.cache/mcp-kr-legislation/""",
    tags={"캐시", "시스템"},
)
def get_cache_status() -> TextContent:
    """캐시 상태 조회"""
    stats = get_cache_stats()
    total_kb = stats["total_bytes"] // 1024
    total_mb = total_kb / 1024

    lines = [
        "## 캐시 상태",
        f"- 파일 수: {stats['files']}개",
        f"- 총 용량: {total_kb:,} KB ({total_mb:.1f} MB)",
        f"- 가장 오래된 캐시: {stats['oldest_days']}일 전",
        f"- 가장 최신 캐시: {stats['newest_days']}일 전",
        "",
        "캐시 정리: cleanup_cache_tool()",
        "특정 법령 캐시 삭제: invalidate_law_cache(law_id=...)",
    ]
    return TextContent(type="text", text="\n".join(lines))


@mcp.tool(
    name="cleanup_cache_tool",
    description="""오래된 캐시 파일을 정리합니다.

매개변수:
- max_age_days: 이 일수 이상 된 파일 삭제 (기본 30일)
- max_size_mb: 전체 크기 제한 MB (기본 100MB)

반환: 삭제 파일 수, 확보된 용량""",
    tags={"캐시", "시스템", "관리"},
)
def cleanup_cache_tool(
    max_age_days: Annotated[int, "삭제 기준 일수 (기본 30일)"] = 30,
    max_size_mb: Annotated[int, "최대 캐시 크기 MB (기본 100)"] = 100,
) -> TextContent:
    """캐시 정리"""
    result = cleanup_cache(max_age_days=max_age_days, max_size_mb=max_size_mb)
    freed_kb = result["freed_bytes"] // 1024
    lines = [
        "## 캐시 정리 결과",
        f"- 삭제된 파일: {result['deleted']}개",
        f"- 확보된 용량: {freed_kb:,} KB",
        f"- 남은 파일: {result['remaining']}개",
    ]
    return TextContent(type="text", text="\n".join(lines))


@mcp.tool(
    name="invalidate_law_cache",
    description="""특정 법령의 캐시를 즉시 무효화합니다.

법령이 개정되었을 때 캐시를 즉시 삭제하여 최신 데이터를 받도록 합니다.

매개변수:
- law_id: 법령ID 또는 MST 번호
- section: 섹션 (기본 "all")""",
    tags={"캐시", "시스템", "관리"},
)
def invalidate_law_cache(
    law_id: Annotated[str, "법령ID 또는 MST 번호"],
    section: Annotated[str, "캐시 섹션 (기본 all)"] = "all",
) -> TextContent:
    """특정 법령 캐시 무효화"""
    success = invalidate_cache(law_id=law_id, section=section)
    if success:
        return TextContent(type="text", text=f"✅ 캐시 무효화 완료: {law_id}/{section}")
    return TextContent(type="text", text=f"ℹ️ 캐시 없음 (이미 삭제됨 또는 미생성): {law_id}/{section}")


# ---------------------------------------------------------------------------
# 공통 BM25 결과 포맷터
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """전각공백/탭 등 이상 문자 정규화"""
    import re as _re
    text = text.replace('　', '').replace('\t', '')  # 전각공백, 탭 제거
    text = _re.sub(r'  +', ' ', text).strip()
    return text


def _format_bm25_results(
    label: str,
    query: str,
    ranked: list[dict],
    total_api: int,
    from_cache: bool,
    fields: list[tuple[str, str]],  # (dict_key, display_label)
) -> str:
    """BM25 재랭킹 결과를 일관된 형식으로 포맷합니다."""
    header = (
        f"**'{query}' {label} BM25 결과**"
        f" (API {total_api}건 → 상위 {len(ranked)}건)"
        + (" [캐시]" if from_cache else "")
    )
    lines = [header, ""]
    for i, item in enumerate(ranked, 1):
        score = item.get("_bm25_score", 0)
        title = next(
            (_normalize_text(str(item.get(k, ""))) for k, _ in fields if item.get(k)), "제목 없음"
        )
        lines.append(f"**{i}. {title}** (BM25: {score})")
        for key, lbl in fields[1:]:
            val = item.get(key, "")
            if val:
                lines.append(f"   {lbl}: {_normalize_text(str(val))}")
        lines.append("")
    lines += [
        "---",
        "* BM25 점수가 높을수록 검색어와 관련성이 높습니다.",
        "* display 값을 높이면 더 많은 후보에서 선택합니다.",
    ]
    return "\n".join(lines)


def _bm25_search(
    target: str,
    query: str,
    display: int,
    top_k: int,
    root_key: str,
    text_keys: list[str],
) -> tuple[list[dict], int, bool]:
    """공통 BM25 검색 파이프라인. (ranked_items, total_from_api, from_cache) 반환."""
    cache_key = get_cache_key(f"bm25_{target}_{query}_{display}", "bm25")
    cached = load_from_cache(cache_key)
    if cached and isinstance(cached, list):
        items = cached
        from_cache = True
    else:
        data = _raw_search(target, query, display)
        items = _extract_list(data, root_key)
        save_to_cache(cache_key, items)
        from_cache = False

    ranked = rank_search_results(query=query, results=items, text_keys=text_keys, top_k=top_k)
    return ranked, len(items), from_cache


# ---------------------------------------------------------------------------
# 법령용어 BM25 검색
# ---------------------------------------------------------------------------

@mcp.tool(
    name="search_legal_term_bm25",
    description="""BM25로 재랭킹된 법령용어를 검색합니다.

법령용어의 뜻풀이까지 포함하여 관련도를 계산하므로, 개념 설명이 포함된
자연어 쿼리에 유리합니다.

매개변수:
- query: 자연어 검색어 (예: "계약 해제 요건", "불법행위 손해배상")
- display: API 결과 수 (기본 50)
- top_k: 반환할 결과 수 (기본 10)""",
    tags={"법령용어", "BM25", "재랭킹", "고도화검색"},
)
def search_legal_term_bm25(
    query: Annotated[str, "자연어 검색어"],
    display: Annotated[int, "API에서 가져올 결과 수"] = 50,
    top_k: Annotated[int, "BM25 재랭킹 후 반환할 결과 수"] = 10,
) -> TextContent:
    """BM25 재랭킹 법령용어 검색"""
    if not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    try:
        ranked, total, from_cache = _bm25_search(
            target="lstrm",
            query=query,
            display=display,
            top_k=top_k,
            root_key="LstrmSearch",
            text_keys=["법령용어명", "뜻풀이", "법령명"],
        )
    except Exception as e:
        return TextContent(type="text", text=f"API 오류: {e}")

    if not ranked:
        return TextContent(type="text", text=f"'{query}' 검색 결과가 없습니다.")

    return TextContent(
        type="text",
        text=_format_bm25_results(
            label="법령용어",
            query=query,
            ranked=ranked,
            total_api=total,
            from_cache=from_cache,
            fields=[
                ("법령용어명", "용어"),
                ("뜻풀이", "뜻풀이"),
                ("법령명", "관련법령"),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 위원회결정문 BM25 검색
# ---------------------------------------------------------------------------

@mcp.tool(
    name="search_committee_bm25",
    description="""BM25로 재랭킹된 위원회결정문을 검색합니다.

개인정보보호위원회, 금융위원회, 공정거래위원회 등 12개 주요 위원회의
결정문을 자연어 쿼리로 검색합니다.

매개변수:
- query: 자연어 검색어 (예: "개인정보 유출 과징금", "불공정 약관")
- committee: 위원회 코드 (기본 ppc=개인정보보호위원회)
  ppc=개인정보보호위, fsc=금융위원회, ftc=공정거래위원회,
  acr=국민권익위, nlrc=노동위원회, ecc=환경부, sfc=증권선물위,
  nhrck=인권위, kcc=방통위, iaciac=산재, oclt=온라인분쟁조정
- display: API 결과 수 (기본 50)
- top_k: 반환할 결과 수 (기본 10)""",
    tags={"위원회결정문", "BM25", "재랭킹", "고도화검색"},
)
def search_committee_bm25(
    query: Annotated[str, "자연어 검색어"],
    committee: Annotated[str, "위원회 코드 (ppc, fsc, ftc, acr, nlrc, ecc, sfc, nhrck, kcc, iaciac, oclt)"] = "ppc",
    display: Annotated[int, "API에서 가져올 결과 수"] = 50,
    top_k: Annotated[int, "BM25 재랭킹 후 반환할 결과 수"] = 10,
) -> TextContent:
    """BM25 재랭킹 위원회결정문 검색"""
    if not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")

    allowed = {"ppc", "fsc", "ftc", "acr", "nlrc", "ecc", "sfc", "nhrck", "kcc", "iaciac", "oclt"}
    if committee not in allowed:
        return TextContent(type="text", text=f"허용된 위원회 코드: {sorted(allowed)}")

    committee_names = {
        "ppc": "개인정보보호위원회", "fsc": "금융위원회", "ftc": "공정거래위원회",
        "acr": "국민권익위원회", "nlrc": "노동위원회", "ecc": "환경부",
        "sfc": "증권선물위원회", "nhrck": "국가인권위원회", "kcc": "방송통신위원회",
        "iaciac": "산업재해보상보험", "oclt": "온라인분쟁조정위원회",
    }
    label = f"{committee_names.get(committee, committee)} 결정문"

    # 위원회별 루트 키 매핑 (실제 API 응답 루트키 기준)
    root_key_map = {
        "ppc": "Ppc", "fsc": "Fsc", "ftc": "Ftc",
        "acr": "Acr", "nlrc": "Nlrc", "ecc": "Ecc",
        "sfc": "Sfc", "nhrck": "Nhrck", "kcc": "Kcc",
        "iaciac": "Iaciac", "oclt": "Oclt",
    }

    # 위원회별 실제 필드명 매핑
    # nlrc: 제목/사건번호, ppc: 안건명, fsc/ftc/etc: 사건명 or 제목
    committee_fields: dict = {
        "ppc":   {"title": ["안건명", "의안명"], "text_keys": ["안건명", "결정구분", "회의종류"],
                  "display": [("안건명", "안건명"), ("결정구분", "결정구분"), ("의결일", "의결일")]},
        "nlrc":  {"title": ["제목", "사건번호"],  "text_keys": ["제목", "사건번호", "등록일"],
                  "display": [("제목", "사건명"), ("사건번호", "사건번호"), ("등록일", "등록일")]},
    }
    default_cf = {
        "title": ["사건명", "제목", "안건명"],
        "text_keys": ["사건명", "제목", "결정유형명", "결정일자"],
        "display": [("사건명", "사건명"), ("제목", "제목"), ("결정일자", "결정일")],
    }
    cf = committee_fields.get(committee, default_cf)

    try:
        ranked, total, from_cache = _bm25_search(
            target=committee,
            query=query,
            display=display,
            top_k=top_k,
            root_key=root_key_map.get(committee, committee.capitalize()),
            text_keys=cf["text_keys"],
        )
    except Exception as e:
        return TextContent(type="text", text=f"API 오류: {e}")

    if not ranked:
        return TextContent(type="text", text=f"'{query}' {label} 검색 결과가 없습니다.")

    # 제목이 없는 경우 여러 후보 필드 순서대로 시도
    title_fields = cf.get("title", ["사건명", "제목", "안건명"])
    for item in ranked:
        if not any(item.get(k) for k in [f[0] for f in cf["display"][:1]]):
            for tf in title_fields:
                if item.get(tf):
                    # 메인 표시 필드가 없으면 우선 필드로 보완
                    item.setdefault(cf["display"][0][0], item[tf])
                    break

    display_fields = cf["display"]

    return TextContent(
        type="text",
        text=_format_bm25_results(
            label=label,
            query=query,
            ranked=ranked,
            total_api=total,
            from_cache=from_cache,
            fields=display_fields,
        ),
    )


# ---------------------------------------------------------------------------
# 행정규칙 BM25 검색
# ---------------------------------------------------------------------------

@mcp.tool(
    name="search_admin_rule_bm25",
    description="""BM25로 재랭킹된 행정규칙을 검색합니다.

훈령, 예규, 고시, 지침 등 행정규칙을 자연어 쿼리로 검색합니다.

매개변수:
- query: 자연어 검색어 (예: "환경 기준 고시", "세금 납부 기한 안내")
- display: API 결과 수 (기본 50)
- top_k: 반환할 결과 수 (기본 10)""",
    tags={"행정규칙", "BM25", "재랭킹", "고도화검색"},
)
def search_admin_rule_bm25(
    query: Annotated[str, "자연어 검색어"],
    display: Annotated[int, "API에서 가져올 결과 수"] = 50,
    top_k: Annotated[int, "BM25 재랭킹 후 반환할 결과 수"] = 10,
) -> TextContent:
    """BM25 재랭킹 행정규칙 검색"""
    if not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")
    try:
        ranked, total, from_cache = _bm25_search(
            target="admrul",
            query=query,
            display=display,
            top_k=top_k,
            root_key="AdmRulSearch",
            text_keys=["행정규칙명", "소관부처명", "행정규칙종류"],
        )
    except Exception as e:
        return TextContent(type="text", text=f"API 오류: {e}")

    if not ranked:
        return TextContent(type="text", text=f"'{query}' 행정규칙 검색 결과가 없습니다.")

    return TextContent(
        type="text",
        text=_format_bm25_results(
            label="행정규칙",
            query=query,
            ranked=ranked,
            total_api=total,
            from_cache=from_cache,
            fields=[
                ("행정규칙명", "규칙명"),
                ("소관부처명", "소관부처"),
                ("행정규칙종류", "종류"),
                ("발령일자", "발령일"),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 법령해석례 / 중앙부처해석 BM25 검색
# ---------------------------------------------------------------------------

@mcp.tool(
    name="search_interpretation_bm25",
    description="""BM25로 재랭킹된 법령해석례를 검색합니다.

법제처 법령해석례와 행정심판례를 자연어 쿼리로 검색합니다.

매개변수:
- query: 자연어 검색어 (예: "계약 해제 이후 손해배상", "행정처분 취소 요건")
- target: 검색 대상
  lawInt=법령해석례, admjd=행정심판례
- display: API 결과 수 (기본 50)
- top_k: 반환할 결과 수 (기본 10)""",
    tags={"법령해석례", "BM25", "재랭킹", "고도화검색"},
)
def search_interpretation_bm25(
    query: Annotated[str, "자연어 검색어"],
    target: Annotated[str, "expc=법령해석례(기본), decc=행정심판례"] = "expc",
    display: Annotated[int, "API에서 가져올 결과 수"] = 50,
    top_k: Annotated[int, "BM25 재랭킹 후 반환할 결과 수"] = 10,
) -> TextContent:
    """BM25 재랭킹 법령해석례 검색"""
    if not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")

    # 실제 법제처 API target 값 (api_layout 검증 완료)
    # 목록 API는 상세 내용 없음 — 안건명/기관명으로 BM25 수행
    target_map = {
        "expc": ("Expc", "법령해석례", ["안건명", "회신기관명", "질의기관명"]),
        "decc": ("Decc", "행정심판례", ["사건명", "재결기관명", "관련법령명"]),
    }
    # 하위 호환 alias
    if target == "lawInt":
        target = "expc"
    elif target == "admjd":
        target = "decc"

    if target not in target_map:
        return TextContent(type="text", text=f"허용된 target: expc(법령해석례), decc(행정심판례)")

    root_key, label, text_keys = target_map[target]

    try:
        ranked, total, from_cache = _bm25_search(
            target=target,
            query=query,
            display=display,
            top_k=top_k,
            root_key=root_key,
            text_keys=text_keys,
        )
    except Exception as e:
        return TextContent(type="text", text=f"API 오류: {e}")

    if not ranked:
        return TextContent(type="text", text=f"'{query}' {label} 검색 결과가 없습니다.")

    field_labels = {
        "expc": [("안건명", "안건명"), ("회신기관명", "회신기관"), ("회신일자", "회신일")],
        "decc": [("사건명", "사건명"), ("재결기관명", "재결기관"), ("재결일자", "재결일")],
    }

    return TextContent(
        type="text",
        text=_format_bm25_results(
            label=label,
            query=query,
            ranked=ranked,
            total_api=total,
            from_cache=from_cache,
            fields=field_labels.get(target, [("사건명", "사건명")]),
        ),
    )


# ---------------------------------------------------------------------------
# 전 카테고리 통합 BM25 검색
# ---------------------------------------------------------------------------

@mcp.tool(
    name="search_all_bm25",
    description="""전 카테고리에 걸쳐 BM25 통합 검색을 수행합니다.

법령, 판례, 법령용어, 행정규칙을 동시에 검색하고 각 카테고리에서
상위 결과를 통합하여 반환합니다.

매개변수:
- query: 자연어 검색어 (예: "개인정보 침해 과징금")
- top_k_per_category: 카테고리별 반환 결과 수 (기본 5)

반환: 카테고리별 상위 결과 통합""",
    tags={"통합검색", "BM25", "재랭킹", "고도화검색"},
)
def search_all_bm25(
    query: Annotated[str, "자연어 검색어"],
    top_k_per_category: Annotated[int, "카테고리별 반환 결과 수 (기본 5)"] = 5,
) -> TextContent:
    """전 카테고리 통합 BM25 검색"""
    if not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")

    categories = [
        ("law",    "LawSearch",    ["법령명한글", "소관부처명"], "법령",     "법령명한글"),
        ("prec",   "PrecSearch",   ["사건명", "법원명"],        "대법원판례", "사건명"),
        ("admrul", "AdmRulSearch", ["행정규칙명", "소관부처명"],  "행정규칙",  "행정규칙명"),
        ("lstrm",  "LsTrmSearch",  ["법령용어명", "뜻풀이"],     "법령용어",  "법령용어명"),
    ]

    lines = [f"**'{query}' 통합 BM25 검색 결과** (카테고리별 상위 {top_k_per_category}건)", ""]
    total_found = 0

    for target, root_key, text_keys, label, title_key in categories:
        try:
            ranked, total, from_cache = _bm25_search(
                target=target,
                query=query,
                display=50,
                top_k=top_k_per_category,
                root_key=root_key,
                text_keys=text_keys,
            )
        except Exception as e:
            lines += [f"### {label}", f"  API 오류: {e}", ""]
            continue

        if not ranked:
            lines += [f"### {label} — 결과 없음", ""]
            continue

        total_found += len(ranked)
        cache_mark = " [캐시]" if from_cache else ""
        lines += [f"### {label} ({len(ranked)}/{total}건){cache_mark}", ""]
        for i, item in enumerate(ranked, 1):
            title = item.get(title_key, "")
            score = item.get("_bm25_score", 0)
            lines.append(f"  {i}. {title} (BM25: {score})")
        lines.append("")

    lines += [
        "---",
        f"총 {total_found}건 반환. 각 카테고리 전용 도구로 상세 검색 가능:",
        "  search_law_bm25 / search_precedent_bm25 / search_admin_rule_bm25 / search_legal_term_bm25",
    ]
    return TextContent(type="text", text="\n".join(lines))


# ---------------------------------------------------------------------------
# BM25 진단 도구
# ---------------------------------------------------------------------------

@mcp.tool(
    name="explain_bm25_tokenize",
    description="""쿼리의 형태소 분석 결과를 확인합니다.

BM25 검색에서 쿼리가 어떻게 토크나이징되는지 보여줍니다.
kiwipiepy 설치 시 형태소 분석, 미설치 시 단순 공백 분리.

매개변수:
- query: 분석할 쿼리""",
    tags={"BM25", "진단", "검색"},
)
def explain_bm25_tokenize(
    query: Annotated[str, "분석할 쿼리"],
) -> TextContent:
    """쿼리 토크나이징 진단"""
    from ..utils.bm25_search import tokenize_query, _get_kiwi

    tokens = tokenize_query(query)
    kiwi = _get_kiwi()
    method = "kiwipiepy 형태소 분석" if kiwi is not None else "공백 분리 (kiwipiepy 없음)"

    lines = [
        f"## BM25 토크나이징 결과",
        f"- 입력: `{query}`",
        f"- 방법: {method}",
        f"- 토큰 수: {len(tokens)}개",
        f"- 토큰: {tokens}",
    ]
    if kiwi is not None:
        lines += [
            "",
            "kiwipiepy가 활성화되어 있습니다.",
            "명사/동사/형용사 어간만 추출하여 법령 검색 정확도를 높입니다.",
        ]
    else:
        lines += [
            "",
            "kiwipiepy 미설치: `uv add kiwipiepy`로 설치하면 정확도가 향상됩니다.",
        ]
    return TextContent(type="text", text="\n".join(lines))
