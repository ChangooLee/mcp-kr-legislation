"""
API 회귀 테스트 - 카테고리별 대표 API 실제 호출.

실제 법제처 API를 호출하므로 네트워크 필요.
pytest -m regression 으로 별도 실행 가능.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pytest

REGRESSION_CASES = {
    "law": {
        "target": "law",
        "params": {"query": "개인정보보호법"},
        "description": "현행법령 검색",
    },
    "precedent": {
        "target": "prec",
        "params": {"query": "손해배상"},
        "description": "판례 검색",
    },
    "constitutional_court": {
        "target": "detc",
        "params": {"query": "위헌"},
        "description": "헌재결정례 검색",
    },
    "legal_interpretation": {
        "target": "expc",
        "params": {"query": "해석"},
        "description": "법령해석례 검색",
    },
    "administrative_trial": {
        "target": "decc",
        "params": {"query": "행정"},
        "description": "행정심판례 검색",
    },
    "administrative_rule": {
        "target": "admrul",
        "params": {"query": "훈령"},
        "description": "행정규칙 검색",
    },
    "local_ordinance": {
        "target": "ordin",
        "params": {"query": "조례"},
        "description": "자치법규 검색",
    },
    "legal_term": {
        "target": "lstrm",
        "params": {"query": "계약"},
        "description": "법령용어 검색",
    },
    "treaty": {
        "target": "trty",
        "params": {"query": "투자"},
        "description": "조약 검색",
    },
    "committee_ppc": {
        "target": "ppc",
        "params": {"query": "개인정보"},
        "description": "개인정보보호위원회 결정문",
    },
    "english_law": {
        "target": "elaw",
        "params": {"query": "act"},
        "description": "영문법령 검색",
    },
    "tax_tribunal": {
        "target": "ttSpecialDecc",
        "params": {"query": "조세"},
        "description": "조세심판원 특별행정심판례",
    },
    "ministry_moef": {
        "target": "moefCgmExpc",
        "params": {"query": "조세"},
        "description": "기획재정부 중앙부처해석",
    },
}

PROGRESS_FILE = Path(__file__).parent.parent / "automation" / "progress.json"


@pytest.mark.regression
class TestAPIRegression:
    @pytest.mark.parametrize(
        "case_id,case",
        REGRESSION_CASES.items(),
        ids=list(REGRESSION_CASES.keys()),
    )
    def test_api_returns_results(self, legislation_client, case_id, case):
        params = case["params"].copy()
        params["type"] = "JSON"
        params["display"] = 5

        result = legislation_client.search(
            target=case["target"], params=params
        )

        assert result is not None, f"Null response for {case_id}"
        assert not result.get("error"), (
            f"API error for {case_id}: {result.get('error')}"
        )

        has_data = _check_response_has_data(result)
        assert has_data, f"No data returned for {case_id} (target={case['target']})"


def _check_response_has_data(result: dict) -> bool:
    for key, val in result.items():
        if not isinstance(val, dict):
            continue
        total = val.get("totalCnt")
        if total and str(total) not in ("0", ""):
            return True
        for inner_key, inner_val in val.items():
            if inner_key in ("totalCnt", "page", "status", "키워드", "target", "section"):
                continue
            if isinstance(inner_val, (list, dict)):
                return True
    return False


@pytest.fixture(scope="session", autouse=True)
def record_regression_results(request):
    """Record regression test results to progress.json after all tests."""
    yield

    if not PROGRESS_FILE.exists():
        return

    try:
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    terminalreporter = request.config.pluginmanager.get_plugin(
        "terminalreporter"
    )
    if not terminalreporter:
        return

    test_results = progress.get("test_results", {})
    now = datetime.now().strftime("%Y-%m-%d")

    passed = terminalreporter.stats.get("passed", [])
    failed = terminalreporter.stats.get("failed", [])

    for report in passed:
        if "test_api_returns_results" in report.nodeid:
            case_id = report.nodeid.split("[")[-1].rstrip("]")
            test_results[case_id] = {
                "tested_at": now,
                "status": "pass",
                "duration_sec": round(report.duration, 2),
            }

    for report in failed:
        if "test_api_returns_results" in report.nodeid:
            case_id = report.nodeid.split("[")[-1].rstrip("]")
            test_results[case_id] = {
                "tested_at": now,
                "status": "fail",
                "duration_sec": round(report.duration, 2),
                "error": str(report.longrepr)[:200],
            }

    progress["test_results"] = test_results
    progress["summary"]["last_test_run"] = now
    progress["last_updated"] = now

    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
