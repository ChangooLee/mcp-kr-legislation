"""
api_layout/*.json 기준 전수 API 호출 테스트.

api_layout JSON 파일에서 동적으로 테스트 케이스를 생성하여
모든 target에 대해 실제 법제처 API를 호출합니다.

pytest tests/test_full_api_coverage.py -v
pytest tests/test_full_api_coverage.py -v -k search   # 목록조회만
pytest tests/test_full_api_coverage.py -v -k detail    # 본문조회만
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
from urllib.parse import parse_qs, urlparse

import pytest
import requests

API_LAYOUT_DIR = (
    Path(__file__).parent.parent
    / "src"
    / "mcp_kr_legislation"
    / "utils"
    / "api_layout"
)
PROGRESS_FILE = Path(__file__).parent.parent / "automation" / "progress.json"


def _load_api_targets() -> (
    Tuple[List[Tuple[str, str, str]], List[Tuple[str, str, str]], Set[str]]
):
    """api_layout/*.json에서 search/detail target 목록을 동적으로 추출.

    Returns:
        (search_targets, detail_targets, skip_targets)
        각 target은 (target_value, category, title) 튜플.
    """
    search_targets: List[Tuple[str, str, str]] = []
    detail_targets: List[Tuple[str, str, str]] = []
    skip_targets: Set[str] = set()
    seen_search: Set[str] = set()
    seen_detail: Set[str] = set()

    for json_file in sorted(API_LAYOUT_DIR.glob("*.json")):
        if json_file.name.startswith("_"):
            continue
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        category = data.get("category_en", json_file.stem)
        for api in data.get("apis", []):
            target = api.get("target", "")
            if not target:
                continue

            status = api.get("status", "live")
            has_json = any(
                s.get("format") == "JSON" for s in api.get("sample_urls", [])
            )

            if status == "not_live" or not has_json:
                skip_targets.add(target)
                continue

            req_url = api.get("request_url", "")
            api_type = api.get("api_type", "")
            title = api.get("title", "")
            is_detail = "lawService" in req_url or api_type == "본문조회"

            if is_detail:
                if target not in seen_detail:
                    seen_detail.add(target)
                    detail_targets.append((target, category, title))
            else:
                if target not in seen_search:
                    seen_search.add(target)
                    search_targets.append((target, category, title))

    return search_targets, detail_targets, skip_targets


SEARCH_TARGETS, DETAIL_TARGETS, SKIP_TARGETS = _load_api_targets()

QUERY_REQUIRED_TARGETS = {
    "lsHstInf": "개인정보보호법",
    "lsJoHstInf": "개인정보보호법",
    "aiSearch": "개인정보",
    "aiRltLs": "개인정보",
}

VCODE_REQUIRED_TARGETS = {
    "couseLs": "L0000000003384",
    "couseAdmrul": "A0000000000601",
    "couseOrdin": "O0000000000602",
}

SPECIAL_PARAMS_TARGETS: Dict[str, Dict[str, str]] = {
    "lsRlt": {"ID": "001971"},
}

DETAIL_SEARCH_FALLBACK = {
    "eflawjosub": ("eflaw", "MST", "법령일련번호"),
}

XFAIL_TARGETS = {
    "joRltLstrm": "조문관련법령용어: 서버 타임아웃 (30s+)",
}

TIMEOUT_SAMPLE_TARGETS = {"lsRlt", "joRltLstrm"}


def _is_valid_json_response(result: dict) -> bool:
    """API 응답이 유효한 JSON 구조인지 확인 (데이터 유무와 무관)."""
    if result.get("error"):
        return False
    if result.get("status") == "000":
        return False
    for val in result.values():
        if isinstance(val, dict):
            return True
    return False


def _response_has_data(result: dict) -> bool:
    """API 응답에 실제 데이터가 있는지 확인."""
    for val in result.values():
        if not isinstance(val, dict):
            continue
        total = val.get("totalCnt")
        if total and str(total) not in ("0", ""):
            return True
        for inner_key, inner_val in val.items():
            if inner_key in (
                "totalCnt", "page", "status", "키워드", "target", "section",
            ):
                continue
            if isinstance(inner_val, (list, dict)):
                return True
    return False


def _extract_first_id(result: dict) -> str | None:
    """검색 결과에서 첫 항목의 본문조회용 ID를 추출.

    우선순위:
    1. 상세링크 URL에서 ID= 파라미터 추출
    2. 숫자형 일련번호 필드
    3. 기타 ID 필드 (숫자 우선)
    """
    id_from_link: list[str] = []
    numeric_ids: list[str] = []
    fallback_ids: list[str] = []

    serial_keys = (
        "법령ID", "판례일련번호", "결정문ID", "일련번호", "MST",
        "행정심판재결례일련번호", "헌재결정례일련번호",
        "법령해석례일련번호", "조약일련번호",
    )

    for val in result.values():
        if not isinstance(val, dict):
            continue
        for inner_key, inner_val in val.items():
            if inner_key in (
                "totalCnt", "page", "status", "키워드", "target", "section",
            ):
                continue
            items = inner_val if isinstance(inner_val, list) else [inner_val]
            for item in items:
                if not isinstance(item, dict):
                    continue
                for v in item.values():
                    if isinstance(v, str) and "ID=" in v:
                        m = re.search(r"ID=([^&\s]+)", v)
                        if m:
                            id_from_link.append(m.group(1))
                for k in serial_keys:
                    v = item.get(k)
                    if v and str(v).strip():
                        numeric_ids.append(str(v).strip())
                for k in ("ID", "사건번호"):
                    v = item.get(k)
                    if v and str(v).strip():
                        fallback_ids.append(str(v).strip())
                if id_from_link or numeric_ids or fallback_ids:
                    break
            if id_from_link or numeric_ids or fallback_ids:
                break

    for c in id_from_link:
        if c.isdigit():
            return c
    for c in numeric_ids:
        if c.isdigit():
            return c
    if id_from_link:
        return id_from_link[0]
    if numeric_ids:
        return numeric_ids[0]
    for f in fallback_ids:
        if f.isdigit():
            return f
    return fallback_ids[0] if fallback_ids else None


def _extract_field(result: dict, field_key: str) -> str | None:
    """검색 결과에서 특정 필드 값을 추출."""
    for val in result.values():
        if not isinstance(val, dict):
            continue
        for inner_key, inner_val in val.items():
            if inner_key in ("totalCnt", "page", "status", "키워드", "target"):
                continue
            items = inner_val if isinstance(inner_val, list) else [inner_val]
            for item in items:
                if isinstance(item, dict) and field_key in item:
                    v = str(item[field_key]).strip()
                    if v:
                        return v
    return None


def _load_detail_sample_params() -> Dict[str, Dict[str, str]]:
    """api_layout detail sample_url에서 파라미터를 추출하여 fallback으로 사용."""
    result: Dict[str, Dict[str, str]] = {}
    skip_keys = {"OC", "target", "type", "mobileYn"}

    for json_file in sorted(API_LAYOUT_DIR.glob("*.json")):
        if json_file.name.startswith("_"):
            continue
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        for api in data.get("apis", []):
            target = api.get("target", "")
            if not target:
                continue
            req_url = api.get("request_url", "")
            api_type = api.get("api_type", "")
            is_detail = "lawService" in req_url or api_type == "본문조회"
            if not is_detail:
                continue

            json_samples = [
                s for s in api.get("sample_urls", [])
                if s.get("format") == "JSON"
            ]
            if not json_samples or target in result:
                continue

            url = json_samples[0]["url"]
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            params = {
                k: v[0] for k, v in qs.items()
                if k not in skip_keys and v and v[0]
            }
            if params:
                result[target] = params

    return result


DETAIL_SAMPLE_PARAMS = _load_detail_sample_params()


def _load_sample_urls() -> List[Tuple[str, str, str, str]]:
    """api_layout에서 모든 JSON sample_url을 추출.

    Returns:
        [(target, api_type, format, url), ...]
    """
    urls: List[Tuple[str, str, str, str]] = []
    seen: Set[str] = set()

    for json_file in sorted(API_LAYOUT_DIR.glob("*.json")):
        if json_file.name.startswith("_"):
            continue
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        for api in data.get("apis", []):
            target = api.get("target", "")
            status = api.get("status", "live")
            if not target or status == "not_live":
                continue
            api_type = api.get("api_type", "")
            req_url = api.get("request_url", "")
            ep_type = "detail" if ("lawService" in req_url or api_type == "본문조회") else "search"

            for sample in api.get("sample_urls", []):
                fmt = sample.get("format", "")
                url = sample.get("url", "")
                key = f"{target}:{ep_type}:{fmt}:{url}"
                if key not in seen:
                    seen.add(key)
                    urls.append((target, ep_type, fmt, url))

    return urls


SAMPLE_URLS = _load_sample_urls()


@pytest.mark.fullcoverage
class TestSearchAPICoverage:
    """api_layout 기준 전체 search target (lawSearch.do) 테스트."""

    @pytest.mark.parametrize(
        "target,category,title",
        SEARCH_TARGETS,
        ids=[t[0] for t in SEARCH_TARGETS],
    )
    def test_search_api(self, legislation_client, target, category, title):
        if target in XFAIL_TARGETS:
            pytest.xfail(f"{target}: {XFAIL_TARGETS[target]}")

        params: Dict[str, Any] = {"type": "JSON", "display": 5}
        if target in VCODE_REQUIRED_TARGETS:
            params["vcode"] = VCODE_REQUIRED_TARGETS[target]
        elif target in SPECIAL_PARAMS_TARGETS:
            params.update(SPECIAL_PARAMS_TARGETS[target])
        elif target in QUERY_REQUIRED_TARGETS:
            params["query"] = QUERY_REQUIRED_TARGETS[target]

        result = legislation_client.search(target=target, params=params)

        assert result is not None, f"Null response: {target} ({category})"
        assert not result.get("error"), (
            f"API error for {target}: {result.get('error')}"
        )
        assert _is_valid_json_response(result), (
            f"Invalid JSON structure for {target}. Keys: {list(result.keys())}"
        )


@pytest.mark.fullcoverage
class TestDetailAPICoverage:
    """api_layout 기준 전체 detail target (lawService.do) 테스트.

    검색 API에서 ID를 획득한 뒤 본문 API를 호출합니다.
    """

    @pytest.mark.parametrize(
        "target,category,title",
        DETAIL_TARGETS,
        ids=[t[0] for t in DETAIL_TARGETS],
    )
    def test_detail_api(self, legislation_client, target, category, title):
        if target in XFAIL_TARGETS:
            pytest.xfail(f"{target}: {XFAIL_TARGETS[target]}")

        detail_params: Dict[str, Any] = {"type": "JSON"}

        if target in DETAIL_SAMPLE_PARAMS:
            detail_params.update(DETAIL_SAMPLE_PARAMS[target])
        elif target in DETAIL_SEARCH_FALLBACK:
            search_target, param_key, field_key = DETAIL_SEARCH_FALLBACK[target]
            sr = legislation_client.search(
                target=search_target, params={"type": "JSON", "display": 1}
            )
            val = _extract_field(sr, field_key)
            if val is None:
                pytest.skip(f"{target}: {search_target} search에서 {field_key} 추출 실패")
            detail_params[param_key] = val
        else:
            search_params: Dict[str, Any] = {"type": "JSON", "display": 5}
            if target in VCODE_REQUIRED_TARGETS:
                search_params["vcode"] = VCODE_REQUIRED_TARGETS[target]
            elif target in SPECIAL_PARAMS_TARGETS:
                search_params.update(SPECIAL_PARAMS_TARGETS[target])
            elif target in QUERY_REQUIRED_TARGETS:
                search_params["query"] = QUERY_REQUIRED_TARGETS[target]

            search_result = legislation_client.search(
                target=target, params=search_params
            )
            item_id = _extract_first_id(search_result)
            if item_id is None:
                pytest.skip(
                    f"검색 결과에서 ID를 추출할 수 없음, sample_url fallback 없음: "
                    f"{target} ({category})"
                )
            detail_params["ID"] = item_id

        result = legislation_client.service(target=target, params=detail_params)

        assert result is not None, f"Null detail response: {target}"
        assert not result.get("error"), (
            f"Detail API error for {target}: {result.get('error')}"
        )


@pytest.fixture(scope="session", autouse=True)
def record_full_coverage_results(request):
    """전수 테스트 결과를 progress.json에 기록."""
    yield

    if not PROGRESS_FILE.exists():
        return

    try:
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            progress = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    reporter = request.config.pluginmanager.get_plugin("terminalreporter")
    if not reporter:
        return

    now = datetime.now().strftime("%Y-%m-%d")
    full_results: Dict[str, Any] = progress.get("full_coverage_results", {})

    for report in reporter.stats.get("passed", []):
        target_id = _parse_target_from_nodeid(report.nodeid)
        if target_id:
            full_results[target_id] = {
                "tested_at": now,
                "status": "pass",
                "duration_sec": round(report.duration, 2),
            }

    for report in reporter.stats.get("failed", []):
        target_id = _parse_target_from_nodeid(report.nodeid)
        if target_id:
            full_results[target_id] = {
                "tested_at": now,
                "status": "fail",
                "duration_sec": round(report.duration, 2),
                "error": str(report.longrepr)[:300],
            }

    for report in reporter.stats.get("skipped", []):
        target_id = _parse_target_from_nodeid(report.nodeid)
        if target_id:
            full_results[target_id] = {
                "tested_at": now,
                "status": "skip",
            }

    for report in reporter.stats.get("xfailed", []):
        target_id = _parse_target_from_nodeid(report.nodeid)
        if target_id:
            full_results[target_id] = {
                "tested_at": now,
                "status": "xfail",
            }

    if full_results:
        progress["full_coverage_results"] = full_results
        total = len(full_results)
        passed = sum(1 for v in full_results.values() if v["status"] == "pass")
        failed = sum(1 for v in full_results.values() if v["status"] == "fail")
        skipped = sum(1 for v in full_results.values() if v["status"] == "skip")

        progress.setdefault("summary", {})["full_coverage"] = {
            "last_run": now,
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": round(passed / max(total - skipped, 1) * 100, 1),
        }
        progress["last_updated"] = now

        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)


def _parse_target_from_nodeid(nodeid: str) -> str | None:
    """test nodeid에서 target 값을 추출. 예: '...test_search_api[law]' -> 'search:law'"""
    if "[" not in nodeid:
        return None
    target = nodeid.split("[")[-1].rstrip("]")
    if "test_search_api" in nodeid:
        return f"search:{target}"
    elif "test_detail_api" in nodeid:
        return f"detail:{target}"
    elif "test_sample_url" in nodeid:
        return f"sample:{target}"
    return target


_JSON_SAMPLE_URLS = [
    (t, ep, fmt, url) for t, ep, fmt, url in SAMPLE_URLS if fmt == "JSON"
]


def _make_unique_ids(items: list) -> list:
    from collections import Counter
    base_ids = [f"{t}:{ep}" for t, ep, _, _ in items]
    counts: Dict[str, int] = Counter()
    result = []
    for bid in base_ids:
        counts[bid] += 1
        if counts[bid] > 1:
            result.append(f"{bid}#{counts[bid]}")
        else:
            result.append(bid)
    return result


@pytest.mark.fullcoverage
class TestSampleURLVerification:
    """api_layout sample_url을 실제 호출하여 포맷 검증."""

    @pytest.mark.parametrize(
        "target,ep_type,fmt,url",
        _JSON_SAMPLE_URLS,
        ids=_make_unique_ids(_JSON_SAMPLE_URLS),
    )
    def test_sample_url(self, target, ep_type, fmt, url):
        if target in XFAIL_TARGETS:
            pytest.xfail(f"{target}: {XFAIL_TARGETS[target]}")
        if target in TIMEOUT_SAMPLE_TARGETS:
            pytest.xfail(f"{target}: 서버 타임아웃 (sample_url 직접 호출)")

        test_url = url.replace("OC=test", "OC=lchangoo")
        headers = {
            "Referer": "https://open.law.go.kr/LSO/openApi/guideList.do",
            "User-Agent": "Mozilla/5.0",
        }

        try:
            resp = requests.get(test_url, headers=headers, timeout=20)
        except requests.exceptions.Timeout:
            pytest.xfail(f"{target}:{ep_type}: 타임아웃 (20s)")

        assert resp.status_code == 200, (
            f"HTTP {resp.status_code} for {target}:{ep_type}"
        )

        ct = resp.headers.get("Content-Type", "")
        body = resp.text.strip()
        assert body, f"Empty response for {target}:{ep_type}"
        assert "json" in ct.lower() or body.startswith("{"), (
            f"Not JSON response for {target}:{ep_type}. "
            f"Content-Type: {ct}, Body starts: {body[:100]}"
        )
