#!/usr/bin/env python3
"""
MCP 도구 품질 게이트 스크립트.

각 도구의 실제 API 호출 결과를 검증하고 이슈를 자동 분류합니다.

사용법:
    python automation/quality_gate.py                    # 전체 검증
    python automation/quality_gate.py --category law     # 특정 카테고리만
    python automation/quality_gate.py --tool search_law  # 특정 도구만
"""

import json
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

PROGRESS_FILE = project_root / "automation" / "progress.json"

RESPONSE_SIZE_CACHE_THRESHOLD = 10240  # 10KB
TOTAL_COUNT_NARROWING_THRESHOLD = 1000

QUALITY_CHECKS = {
    "law": {"target": "law", "params": {"query": "개인정보보호법", "display": 5}},
    "precedent": {"target": "prec", "params": {"query": "손해배상", "display": 5}},
    "constitutional_court": {"target": "detc", "params": {"query": "위헌", "display": 5}},
    "legal_interpretation": {"target": "expc", "params": {"query": "해석", "display": 5}},
    "administrative_trial": {"target": "decc", "params": {"query": "행정", "display": 5}},
    "administrative_rule": {"target": "admrul", "params": {"query": "훈령", "display": 5}},
    "local_ordinance": {"target": "ordin", "params": {"query": "조례", "display": 5}},
    "legal_term": {"target": "lstrm", "params": {"query": "계약", "display": 5}},
    "treaty": {"target": "trty", "params": {"query": "투자", "display": 5}},
    "committee_ppc": {"target": "ppc", "params": {"query": "개인정보", "display": 5}},
    "english_law": {"target": "elaw", "params": {"query": "act", "display": 5}},
    "tax_tribunal": {"target": "ttSpecialDecc", "params": {"query": "조세", "display": 5}},
    "ministry_moef": {"target": "moefCgmExpc", "params": {"query": "조세", "display": 5}},
    "ministry_nts": {"target": "ntsCgmExpc", "params": {"query": "소득세", "display": 5}},
}


def check_response_quality(target, params, client):
    """Single API response quality check."""
    issues = []
    params_with_type = {**params, "type": "JSON"}

    start = time.time()
    try:
        result = client.search(target=target, params=params_with_type)
    except Exception as e:
        return {
            "status": "error",
            "issues": [{"category": "needs_human", "detail": f"Exception: {e}"}],
            "elapsed_sec": time.time() - start,
        }
    elapsed = time.time() - start

    response_str = json.dumps(result, ensure_ascii=False)
    response_size = len(response_str.encode("utf-8"))

    if result.get("error"):
        issues.append({"category": "needs_human", "detail": f"API error: {result['error']}"})

    total_count = 0
    for key, val in result.items():
        if isinstance(val, dict):
            tc = val.get("totalCnt")
            if tc:
                try:
                    total_count = int(tc)
                except (ValueError, TypeError):
                    pass

    if response_size > RESPONSE_SIZE_CACHE_THRESHOLD:
        issues.append({
            "category": "needs_cache",
            "detail": f"Response size {response_size} bytes > {RESPONSE_SIZE_CACHE_THRESHOLD} threshold",
        })

    if total_count > TOTAL_COUNT_NARROWING_THRESHOLD:
        issues.append({
            "category": "needs_narrowing",
            "detail": f"Total count {total_count} > {TOTAL_COUNT_NARROWING_THRESHOLD} threshold",
        })

    if total_count == 0 and not result.get("error"):
        issues.append({
            "category": "auto_fix",
            "detail": "Zero results - may need query adjustment or empty result message",
        })

    if elapsed > 10:
        issues.append({
            "category": "needs_cache",
            "detail": f"Slow response: {elapsed:.1f}s",
        })

    status = "pass" if not issues else "warning"
    if any(i["category"] == "needs_human" for i in issues):
        status = "fail"

    return {
        "status": status,
        "response_size_bytes": response_size,
        "total_count": total_count,
        "elapsed_sec": round(elapsed, 2),
        "issues": issues,
    }


def run_quality_gate(category=None, tool=None):
    from mcp_kr_legislation.apis.client import LegislationClient
    from mcp_kr_legislation.config import legislation_config

    client = LegislationClient(config=legislation_config)

    checks = QUALITY_CHECKS
    if category:
        checks = {k: v for k, v in checks.items() if k.startswith(category)}
    if tool:
        checks = {k: v for k, v in checks.items() if k == tool}

    if not checks:
        print(f"No checks found for category={category}, tool={tool}")
        return {}

    print(f"Quality gate: {len(checks)} checks\n")

    results = {}
    issue_summary = {"auto_fix": 0, "needs_cache": 0, "needs_narrowing": 0, "needs_parsing": 0, "needs_human": 0}

    for name, check in checks.items():
        print(f"  Checking {name}...", end=" ", flush=True)
        result = check_response_quality(check["target"], check["params"], client)
        results[name] = result

        if result["status"] == "pass":
            print(f"PASS ({result['response_size_bytes']}B, {result['elapsed_sec']}s)")
        elif result["status"] == "warning":
            cats = [i["category"] for i in result["issues"]]
            print(f"WARN [{', '.join(cats)}]")
            for i in result["issues"]:
                issue_summary[i["category"]] = issue_summary.get(i["category"], 0) + 1
        else:
            print(f"FAIL")
            for i in result["issues"]:
                print(f"    -> {i['detail']}")
                issue_summary[i["category"]] = issue_summary.get(i["category"], 0) + 1

    # Summary
    passed = sum(1 for r in results.values() if r["status"] == "pass")
    warned = sum(1 for r in results.values() if r["status"] == "warning")
    failed = sum(1 for r in results.values() if r["status"] == "fail")

    print(f"\n{'='*50}")
    print(f"Quality Gate Results: {passed} pass, {warned} warning, {failed} fail")
    if any(v > 0 for v in issue_summary.values()):
        print(f"Issues: {json.dumps(issue_summary)}")
    print(f"{'='*50}")

    # Update progress.json
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE) as f:
                progress = json.load(f)

            now = datetime.now().strftime("%Y-%m-%d")
            qg_results = progress.get("quality_gate_results", {})
            for name, result in results.items():
                qg_results[name] = {
                    "checked_at": now,
                    "status": result["status"],
                    "response_size_bytes": result["response_size_bytes"],
                    "total_count": result["total_count"],
                    "issues": result["issues"],
                }

            progress["quality_gate_results"] = qg_results
            progress["last_updated"] = now

            with open(PROGRESS_FILE, "w") as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)

            print(f"\nUpdated {PROGRESS_FILE}")
        except Exception as e:
            print(f"\nFailed to update progress.json: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(description="MCP Tool Quality Gate")
    parser.add_argument("--category", type=str, help="Filter by category prefix")
    parser.add_argument("--tool", type=str, help="Check specific tool")
    args = parser.parse_args()

    results = run_quality_gate(category=args.category, tool=args.tool)

    failed = sum(1 for r in results.values() if r["status"] == "fail")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
