"""
api_layout target <-> tools 소스 코드 매핑 자동 검증.

api_layout/*.json의 모든 target이 tools/*.py 소스에서 실제로 사용되는지 검증하고
결과를 progress.json에 기록합니다.

사용법:
    python automation/coverage_check.py          # 콘솔 출력
    python automation/coverage_check.py --update  # progress.json 업데이트
    python automation/coverage_check.py --json    # JSON 출력
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
API_LAYOUT_DIR = PROJECT_ROOT / "src" / "mcp_kr_legislation" / "utils" / "api_layout"
TOOLS_DIR = PROJECT_ROOT / "src" / "mcp_kr_legislation" / "tools"
PROGRESS_FILE = PROJECT_ROOT / "automation" / "progress.json"


def load_api_layout_targets() -> dict[str, dict]:
    """api_layout/*.json에서 target 정보를 추출."""
    targets: dict[str, dict] = {}
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

            has_json = any(
                s.get("format") == "JSON" for s in api.get("sample_urls", [])
            )
            status = api.get("status", "live")

            if target not in targets:
                targets[target] = {
                    "category": category,
                    "file": json_file.name,
                    "has_json": has_json,
                    "status": status,
                    "api_types": [],
                }
            api_type = api.get("api_type", "")
            req_url = api.get("request_url", "")
            if "lawService" in req_url or api_type == "본문조회":
                targets[target]["api_types"].append("detail")
            else:
                targets[target]["api_types"].append("search")

    return targets


def scan_tools_for_targets() -> dict[str, set[str]]:
    """tools/*.py 소스에서 사용되는 target 값을 추출.

    Returns:
        {target_value: {file1.py, file2.py, ...}}
    """
    target_usage: dict[str, set[str]] = {}

    patterns = [
        re.compile(r'''target\s*[=:]\s*["']([a-zA-Z]+)["']'''),
        re.compile(r'''["']target["']\s*:\s*["']([a-zA-Z]+)["']'''),
        re.compile(r'''\.search\(\s*["']([a-zA-Z]+)["']'''),
        re.compile(r'''\.service\(\s*["']([a-zA-Z]+)["']'''),
        re.compile(r'''_make_legislation_request\(\s*["']([a-zA-Z]+)["']'''),
        re.compile(r'''_make_request\([^)]*target\s*=\s*["']([a-zA-Z]+)["']'''),
        re.compile(r'''target=([a-zA-Z]{3,})&'''),
    ]

    for py_file in sorted(TOOLS_DIR.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        content = py_file.read_text(encoding="utf-8")
        for pattern in patterns:
            for match in pattern.finditer(content):
                target = match.group(1)
                if len(target) < 2:
                    continue
                if target in ("text", "type", "JSON", "HTML", "XML", "GET", "POST"):
                    continue
                target_usage.setdefault(target, set()).add(py_file.name)

    return target_usage


def check_coverage() -> dict:
    """api_layout과 tools 간의 매핑 검증."""
    api_targets = load_api_layout_targets()
    tool_targets = scan_tools_for_targets()

    covered = []
    missing = []
    extra = []

    for target, info in sorted(api_targets.items()):
        if info["status"] == "not_live":
            covered.append({
                "target": target,
                "category": info["category"],
                "status": "not_live",
                "tool_files": [],
            })
            continue

        if target in tool_targets:
            covered.append({
                "target": target,
                "category": info["category"],
                "status": "covered",
                "tool_files": sorted(tool_targets[target]),
            })
        else:
            missing.append({
                "target": target,
                "category": info["category"],
                "has_json": info["has_json"],
                "file": info["file"],
            })

    api_target_set = set(api_targets.keys())
    for target, files in sorted(tool_targets.items()):
        if target not in api_target_set:
            extra.append({
                "target": target,
                "tool_files": sorted(files),
            })

    total = len(api_targets)
    live_total = sum(1 for v in api_targets.values() if v["status"] != "not_live")
    covered_count = sum(1 for c in covered if c["status"] == "covered")

    return {
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "api_layout_targets": total,
        "live_targets": live_total,
        "covered": covered_count,
        "missing": len(missing),
        "extra_in_tools": len(extra),
        "coverage_percent": round(covered_count / max(live_total, 1) * 100, 1),
        "missing_targets": missing,
        "extra_targets": extra,
        "covered_targets": covered,
    }


def print_report(result: dict) -> None:
    """검증 결과를 콘솔에 출력."""
    print("=" * 60)
    print("api_layout <-> tools 커버리지 검증 결과")
    print("=" * 60)
    print(f"검증 시각: {result['checked_at']}")
    print(f"api_layout targets: {result['api_layout_targets']}")
    print(f"Live targets: {result['live_targets']}")
    print(f"도구에서 커버: {result['covered']}")
    print(f"누락 (api_layout O, tools X): {result['missing']}")
    print(f"잉여 (api_layout X, tools O): {result['extra_in_tools']}")
    print(f"커버리지: {result['coverage_percent']}%")
    print()

    if result["missing_targets"]:
        print("--- 누락 target ---")
        for m in result["missing_targets"]:
            json_flag = "JSON" if m["has_json"] else "HTML"
            print(f"  {m['target']:30s} {m['category']:25s} [{json_flag}] ({m['file']})")
        print()

    if result["extra_targets"]:
        print("--- 잉여 target (tools에만 존재) ---")
        for e in result["extra_targets"]:
            print(f"  {e['target']:30s} -> {', '.join(e['tool_files'])}")
        print()

    if result["coverage_percent"] == 100.0:
        print("ALL COVERED: api_layout의 모든 live target이 도구에서 사용됨")
    else:
        print(f"GAP FOUND: {result['missing']}개 target 누락")

    return result["coverage_percent"] == 100.0


def update_progress(result: dict) -> None:
    """progress.json에 커버리지 결과를 기록."""
    if not PROGRESS_FILE.exists():
        print("progress.json not found, skipping update")
        return

    with open(PROGRESS_FILE, encoding="utf-8") as f:
        progress = json.load(f)

    progress["coverage_check"] = {
        "checked_at": result["checked_at"],
        "api_layout_targets": result["api_layout_targets"],
        "live_targets": result["live_targets"],
        "covered": result["covered"],
        "missing": result["missing"],
        "extra_in_tools": result["extra_in_tools"],
        "coverage_percent": result["coverage_percent"],
        "missing_targets": [m["target"] for m in result["missing_targets"]],
        "extra_targets": [e["target"] for e in result["extra_targets"]],
    }
    progress["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    print(f"progress.json updated (coverage: {result['coverage_percent']}%)")


def main():
    parser = argparse.ArgumentParser(description="api_layout-tools 커버리지 검증")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    parser.add_argument("--update", action="store_true", help="progress.json 업데이트")
    args = parser.parse_args()

    result = check_coverage()

    if args.json:
        compact = {k: v for k, v in result.items() if k != "covered_targets"}
        print(json.dumps(compact, ensure_ascii=False, indent=2))
    else:
        print_report(result)

    if args.update:
        update_progress(result)

    sys.exit(0 if result["coverage_percent"] == 100.0 else 1)


if __name__ == "__main__":
    main()
