#!/usr/bin/env python3
"""
MCP 도구 완성도 점수 평가 스크립트.

progress.json 기반으로 프로젝트 완성도를 정량적으로 계산합니다.
openclaw 또는 수동으로 실행하여 현재 상태를 평가할 수 있습니다.

사용법:
    python automation/completeness_score.py          # 점수 출력
    python automation/completeness_score.py --json   # JSON 형태로 출력
    python automation/completeness_score.py --update # progress.json에 점수 기록
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

PROGRESS_FILE = Path(__file__).parent / "progress.json"

WEIGHTS = {
    "api_coverage": 30,
    "test_health": 25,
    "quality_gate": 20,
    "task_completion": 15,
    "warning_resolution": 10,
}


def load_progress():
    if not PROGRESS_FILE.exists():
        print(f"ERROR: {PROGRESS_FILE} not found")
        sys.exit(1)
    with open(PROGRESS_FILE) as f:
        return json.load(f)


def score_api_coverage(progress):
    """API 구현 커버리지 (30점).

    coverage_check 결과가 있으면 api_layout 기준 실시간 검증 결과를 사용하고,
    없으면 summary의 수동 기록 기준으로 평가합니다.
    """
    cc = progress.get("coverage_check", {})
    if cc:
        live = cc.get("live_targets", 0)
        covered = cc.get("covered", 0)
        coverage_pct = cc.get("coverage_percent", 0)
        detail = f"[자동검증] {covered}/{live} target 커버 ({coverage_pct}%)"
        return round(coverage_pct, 1), detail

    summary = progress.get("summary", {})
    total_targets = summary.get("total_unique_targets", 0)
    covered_targets = summary.get("tool_covered_targets", 0)

    if total_targets == 0:
        return 0.0, "데이터 없음"

    coverage = covered_targets / total_targets
    score = coverage * 100

    official = progress.get("official_api_stats", {})
    non_mobile = official.get("non_mobile_apis", 175)
    detail = f"{covered_targets}/{total_targets} target 커버 ({coverage:.0%}), 공식 비모바일 {non_mobile}건"
    return round(score, 1), detail


def score_test_health(progress):
    """테스트 건강도 (25점).

    full_coverage_results가 있으면 전수 테스트 기준으로 평가하고,
    없으면 기존 test_results(대표 13건) 기준으로 평가합니다.
    """
    full_results = progress.get("full_coverage_results", {})
    test_results = full_results if full_results else progress.get("test_results", {})
    source = "전수" if full_results else "대표"

    if not test_results:
        return 0.0, "테스트 결과 없음"

    total = len(test_results)
    passed = sum(1 for r in test_results.values() if r.get("status") == "pass")
    failed = sum(1 for r in test_results.values() if r.get("status") == "fail")
    skipped = sum(1 for r in test_results.values() if r.get("status") == "skip")

    testable = total - skipped
    pass_ratio = passed / testable if testable > 0 else 0

    freshness_score = 0
    now = datetime.now()
    for result in test_results.values():
        tested_at = result.get("tested_at", "")
        if tested_at:
            try:
                test_date = datetime.strptime(tested_at, "%Y-%m-%d")
                days_old = (now - test_date).days
                if days_old <= 1:
                    freshness_score += 1.0
                elif days_old <= 7:
                    freshness_score += 0.7
                elif days_old <= 30:
                    freshness_score += 0.3
            except ValueError:
                pass
    freshness_ratio = freshness_score / total if total > 0 else 0

    score = (pass_ratio * 0.7 + freshness_ratio * 0.3) * 100

    detail = f"[{source}] {passed}/{testable} 통과, {failed} 실패, {skipped} skip, 신선도 {freshness_ratio:.0%}"
    return round(score, 1), detail


def score_quality_gate(progress):
    """품질 게이트 점수 (20점)."""
    qg = progress.get("quality_gate_results", {})

    if not qg:
        return 0.0, "품질 게이트 결과 없음"

    total = len(qg)
    passed = sum(1 for r in qg.values() if r.get("status") == "pass")
    warnings = sum(1 for r in qg.values() if r.get("status") == "warning")
    failures = sum(1 for r in qg.values() if r.get("status") == "fail")

    score = ((passed * 1.0 + warnings * 0.5 + failures * 0.0) / total) * 100 if total > 0 else 0

    detail = f"{passed} pass, {warnings} warning, {failures} fail (총 {total})"
    return round(score, 1), detail


def score_task_completion(progress):
    """작업 완료율 (15점)."""
    tasks = progress.get("tasks", [])

    if not tasks:
        return 100.0, "pending 작업 없음"

    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("status") == "completed")
    pending = sum(1 for t in tasks if t.get("status") == "pending")
    failed = sum(1 for t in tasks if t.get("status") == "failed")

    if total == 0:
        return 100.0, "작업 없음"

    score = (completed / total) * 100

    detail = f"{completed}/{total} 완료, {pending} 대기, {failed} 실패"
    return round(score, 1), detail


def score_warning_resolution(progress):
    """경고 해결률 (10점)."""
    warnings = progress.get("warning_tools", [])
    tasks = progress.get("tasks", [])

    if not warnings:
        return 100.0, "경고 항목 없음"

    total_warnings = len(warnings)

    resolved = 0
    for w in warnings:
        tool_name = w.get("tool", "")
        matching_tasks = [
            t for t in tasks
            if tool_name in t.get("tool_name", "")
            and t.get("status") == "completed"
        ]
        if matching_tasks:
            resolved += 1

    score = (resolved / total_warnings) * 100 if total_warnings > 0 else 0

    detail = f"{resolved}/{total_warnings} 해결"
    return round(score, 1), detail


SCORE_FUNCTIONS = {
    "api_coverage": score_api_coverage,
    "test_health": score_test_health,
    "quality_gate": score_quality_gate,
    "task_completion": score_task_completion,
    "warning_resolution": score_warning_resolution,
}


def calculate_completeness(progress):
    """전체 완성도 점수 계산."""
    scores = {}
    total_weighted = 0

    for category, func in SCORE_FUNCTIONS.items():
        raw_score, detail = func(progress)
        weight = WEIGHTS[category]
        weighted = raw_score * weight / 100

        scores[category] = {
            "raw_score": raw_score,
            "weight": weight,
            "weighted_score": round(weighted, 1),
            "detail": detail,
        }
        total_weighted += weighted

    return {
        "total_score": round(total_weighted, 1),
        "max_score": 100,
        "grade": _grade(total_weighted),
        "evaluated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "breakdown": scores,
    }


def _grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    return "F"


def print_report(result):
    print(f"\n{'='*55}")
    print(f"  MCP 한국 법령 - 완성도 평가 ({result['evaluated_at']})")
    print(f"{'='*55}")
    print(f"\n  총점: {result['total_score']}/{result['max_score']} (등급: {result['grade']})\n")

    for cat, data in result["breakdown"].items():
        bar_len = int(data["raw_score"] / 5)
        bar = "#" * bar_len + "." * (20 - bar_len)
        print(f"  [{bar}] {data['raw_score']:5.1f}/100 x{data['weight']:2d}% = {data['weighted_score']:5.1f}  {cat}")
        print(f"       {data['detail']}")

    print(f"\n{'='*55}")

    if result["total_score"] < 70:
        print("  개선 필요 영역:")
        for cat, data in result["breakdown"].items():
            if data["raw_score"] < 70:
                print(f"  - {cat}: {data['detail']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="MCP 완성도 평가")
    parser.add_argument("--json", action="store_true", help="JSON 형태로 출력")
    parser.add_argument("--update", action="store_true", help="progress.json에 점수 기록")
    args = parser.parse_args()

    progress = load_progress()
    result = calculate_completeness(progress)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report(result)

    if args.update:
        progress["completeness_score"] = {
            "total_score": result["total_score"],
            "grade": result["grade"],
            "evaluated_at": result["evaluated_at"],
            "breakdown": {
                k: {"score": v["raw_score"], "weighted": v["weighted_score"]}
                for k, v in result["breakdown"].items()
            },
        }
        progress["last_updated"] = datetime.now().strftime("%Y-%m-%d")

        with open(PROGRESS_FILE, "w") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        print(f"progress.json 업데이트 완료")

    return result


if __name__ == "__main__":
    main()
