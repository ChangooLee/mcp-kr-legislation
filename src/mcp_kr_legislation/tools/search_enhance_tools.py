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
- max_size_mb: 전체 크기 제한 MB (기본 100MB)""",
    tags={"캐시", "시스템", "관리"},
)
def cleanup_cache_tool(
    max_age_days: Annotated[int, "삭제 기준 일수 (기본 30일)"] = 30,
    max_size_mb: Annotated[int, "최대 캐시 크기 MB (기본 100)"] = 100,
) -> TextContent:
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
    success = invalidate_cache(law_id=law_id, section=section)
    if success:
        return TextContent(type="text", text=f"✅ 캐시 무효화 완료: {law_id}/{section}")
    return TextContent(type="text", text=f"ℹ️ 캐시 없음 (이미 삭제됨 또는 미생성): {law_id}/{section}")


# ---------------------------------------------------------------------------
# BM25 공통 헬퍼
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    import re as _re
    text = text.replace('　', '').replace('\t', '')
    text = _re.sub(r'  +', ' ', text).strip()
    return text


def _format_bm25_results(
    label: str,
    query: str,
    ranked: list[dict],
    total_api: int,
    from_cache: bool,
    fields: list[tuple[str, str]],
) -> str:
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
    lines += ["---", "* BM25 점수가 높을수록 검색어와 관련성이 높습니다.",
              "* display 값을 높이면 더 많은 후보에서 선택합니다."]
    return "\n".join(lines)


def _bm25_search(
    target: str, query: str, display: int, top_k: int,
    root_key: str, text_keys: list[str],
) -> tuple[list[dict], int, bool]:
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
# BM25 통합 검색
# ---------------------------------------------------------------------------

_BM25_TARGET_CONFIG: dict[str, tuple] = {
    "law":    ("law",    "LawSearch",    ["법령명한글", "소관부처명", "법령구분명"], "법령",
               [("법령명한글", "법령명"), ("소관부처명", "소관부처"), ("공포일자", "공포일"), ("법령일련번호", "MST")]),
    "prec":   ("prec",  "PrecSearch",   ["사건명", "법원명"],                     "대법원판례",
               [("사건명", "사건명"), ("법원명", "법원"), ("선고일자", "선고일"), ("사건번호", "사건번호")]),
    "ccurt":  ("ccurt", "CcurtSearch",  ["사건명", "선고구분"],                    "헌법재판소",
               [("사건명", "사건명"), ("선고구분", "구분"), ("선고일자", "선고일")]),
    "admrul": ("admrul","AdmRulSearch", ["행정규칙명", "소관부처명"],              "행정규칙",
               [("행정규칙명", "규칙명"), ("소관부처명", "소관부처"), ("시행일자", "시행일")]),
    "lstrm":  ("lstrm", "LsTrmSearch",  ["법령용어명", "뜻풀이"],                "법령용어",
               [("법령용어명", "용어명"), ("뜻풀이", "뜻풀이")]),
    "expc":   ("expc",  "Expc",         ["안건명", "회신기관명", "질의기관명"],    "법령해석례",
               [("안건명", "안건명"), ("회신기관명", "회신기관"), ("회신일자", "회신일")]),
    "decc":   ("decc",  "Decc",         ["사건명", "재결기관명", "관련법령명"],    "행정심판례",
               [("사건명", "사건명"), ("재결기관명", "재결기관"), ("재결일자", "재결일")]),
}


@mcp.tool(
    name="search_bm25",
    description="""BM25 알고리즘으로 관련도 순 재랭킹 검색을 수행합니다.

단일 카테고리 또는 전체 카테고리에 걸친 BM25 검색을 지원합니다.
기본 API 검색과 달리 kiwipiepy 형태소 분석 기반 BM25 Okapi 알고리즘으로
관련도 점수를 계산하여 정렬합니다.

매개변수:
- query: 자연어 검색어 (예: "개인정보 처리 동의", "근로시간 단축")
- target: 검색 대상 (기본 "all")
    "all"   - 전체 카테고리 통합 (법령+판례+행정규칙+법령용어)
    "law"   - 법령
    "prec"  - 대법원 판례
    "ccurt" - 헌법재판소
    "admrul"- 행정규칙
    "lstrm" - 법령용어
    "expc"  - 법령해석례
    "decc"  - 행정심판례
- top_k: 반환할 결과 수 (기본 10, target=all이면 카테고리당)
- display: API에서 가져올 결과 수 (기본 50, 최대 100)

사용 예시:
  search_bm25(query="개인정보 침해", target="all")
  search_bm25(query="양도소득세 비과세", target="law", top_k=5)
  search_bm25(query="부당해고 구제", target="prec")""",
    tags={"BM25", "재랭킹", "고도화검색", "통합검색"},
)
def search_bm25(
    query: Annotated[str, "자연어 검색어"],
    target: Annotated[str, "검색 대상 (all/law/prec/ccurt/admrul/lstrm/expc/decc)"] = "all",
    top_k: Annotated[int, "반환할 결과 수 (target=all이면 카테고리당)"] = 10,
    display: Annotated[int, "API에서 가져올 결과 수 (최대 100)"] = 50,
) -> TextContent:
    if not query.strip():
        return TextContent(type="text", text="검색어를 입력해주세요.")

    if target == "all":
        all_targets = [
            ("law",    "LawSearch",    ["법령명한글", "소관부처명"], "법령",     "법령명한글"),
            ("prec",   "PrecSearch",   ["사건명", "법원명"],        "대법원판례", "사건명"),
            ("admrul", "AdmRulSearch", ["행정규칙명", "소관부처명"], "행정규칙",  "행정규칙명"),
            ("lstrm",  "LsTrmSearch",  ["법령용어명", "뜻풀이"],    "법령용어",  "법령용어명"),
        ]
        lines = [f"**'{query}' 통합 BM25 검색** (카테고리당 상위 {top_k}건)", ""]
        total_found = 0
        for t, root_key, text_keys, label, title_key in all_targets:
            try:
                ranked, total, from_cache = _bm25_search(t, query, display, top_k, root_key, text_keys)
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
        lines += ["---", f"총 {total_found}건 반환. 특정 카테고리: search_bm25(target=\"law\") 등 지정."]
        return TextContent(type="text", text="\n".join(lines))

    if target not in _BM25_TARGET_CONFIG:
        valid = ", ".join(_BM25_TARGET_CONFIG.keys())
        return TextContent(type="text", text=f"알 수 없는 target: '{target}'\n유효: all, {valid}")

    api_target, root_key, text_keys, label, fields = _BM25_TARGET_CONFIG[target]
    try:
        ranked, total, from_cache = _bm25_search(api_target, query, display, top_k, root_key, text_keys)
    except Exception as e:
        return TextContent(type="text", text=f"API 오류: {e}")

    if not ranked:
        return TextContent(type="text", text=f"'{query}' {label} 검색 결과가 없습니다.")

    return TextContent(
        type="text",
        text=_format_bm25_results(label=label, query=query, ranked=ranked,
                                   total_api=total, from_cache=from_cache, fields=fields),
    )


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
        lines += ["", "kiwipiepy가 활성화되어 있습니다.",
                  "명사/동사/형용사 어간만 추출하여 법령 검색 정확도를 높입니다."]
    else:
        lines += ["", "kiwipiepy 미설치: `uv add kiwipiepy`로 설치하면 정확도가 향상됩니다."]
    return TextContent(type="text", text="\n".join(lines))
