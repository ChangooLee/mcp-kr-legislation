#!/usr/bin/env python3
"""
도구 구현 완성도 체크 스크립트

사용법:
    python test_tool_coverage.py

기능:
- korean_law_api_complete_guide.md의 API 목록 파싱
- src/mcp_kr_legislation/tools/ 디렉토리의 @mcp.tool 데코레이터 파싱
- API vs 도구 매핑 비교
- 미구현/불일치 항목 출력
"""

import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def parse_api_guide() -> Dict[str, Dict[str, str]]:
    """
    korean_law_api_complete_guide.md에서 API 목록 파싱
    
    Returns:
        {
            "api_name": {
                "target": "target_value",
                "search_tool": "search_law",
                "detail_tool": "get_law_detail",
                "category": "법령"
            }
        }
    """
    guide_path = project_root / "src" / "mcp_kr_legislation" / "utils" / "korean_law_api_complete_guide.md"
    
    if not guide_path.exists():
        print(f"❌ 가이드 파일을 찾을 수 없습니다: {guide_path}")
        return {}
    
    apis = {}
    
    with open(guide_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 표 형식에서 API 정보 추출
    # | **법령** | **본문** | 현행법령 목록 조회 | `law` | ... | `search_law` | `get_law_detail` |
    pattern = r'\|\s*\*\*([^*]+)\*\*\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+)\s*\|\s*`([^`]+)`\s*\|\s*([^|]*)\s*\|\s*`([^`]+)`\s*\|\s*([^|]*)\s*\|\s*([^|]+)\s*\|'
    
    for match in re.finditer(pattern, content):
        category = match.group(1).strip()
        subcategory = match.group(2).strip()
        search_api = match.group(3).strip()
        target = match.group(4).strip()
        detail_api = match.group(5).strip()
        detail_target = match.group(6).strip() if match.group(6) else ""
        search_tool = match.group(7).strip()
        detail_tool = match.group(8).strip()
        
        # 목록 조회 API
        if search_api and search_api != "-":
            api_key = f"{category}_{subcategory}_{search_api}"
            apis[api_key] = {
                "target": target,
                "search_tool": search_tool,
                "detail_tool": "",
                "category": category,
                "subcategory": subcategory,
                "api_name": search_api
            }
        
        # 본문 조회 API
        if detail_api and detail_api != "-" and detail_target:
            api_key = f"{category}_{subcategory}_{detail_api}"
            if api_key not in apis:
                apis[api_key] = {
                    "target": detail_target,
                    "search_tool": "",
                    "detail_tool": detail_tool,
                    "category": category,
                    "subcategory": subcategory,
                    "api_name": detail_api
                }
            else:
                apis[api_key]["detail_tool"] = detail_tool
    
    return apis


def parse_tool_files() -> Dict[str, List[str]]:
    """
    tools/ 디렉토리에서 @mcp.tool 데코레이터 파싱
    
    Returns:
        {
            "tool_name": ["file_path", ...]
        }
    """
    tools_dir = project_root / "src" / "mcp_kr_legislation" / "tools"
    
    if not tools_dir.exists():
        print(f"❌ tools 디렉토리를 찾을 수 없습니다: {tools_dir}")
        return {}
    
    tools = defaultdict(list)
    
    for tool_file in tools_dir.glob("*.py"):
        if tool_file.name == "__init__.py":
            continue
        
        try:
            with open(tool_file, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(tool_file))
            
            # @mcp.tool 데코레이터 찾기
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Attribute):
                            if decorator.attr == 'tool':
                                if isinstance(decorator.value, ast.Attribute):
                                    if decorator.value.attr == 'mcp':
                                        # tool 이름 찾기
                                        for kw in node.decorator_list:
                                            if isinstance(kw, ast.Call):
                                                for keyword in kw.keywords:
                                                    if keyword.arg == 'name':
                                                        if isinstance(keyword.value, ast.Constant):
                                                            tool_name = keyword.value.value
                                                            tools[tool_name].append(str(tool_file.relative_to(project_root)))
        except Exception as e:
            print(f"⚠️  파일 파싱 오류 ({tool_file.name}): {e}")
    
    return dict(tools)


def compare_api_tools(apis: Dict[str, Dict[str, str]], tools: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    API와 도구 매핑 비교
    
    Returns:
        {
            "implemented": [...],
            "missing": [...],
            "mismatched": [...]
        }
    """
    result = {
        "implemented": [],
        "missing": [],
        "mismatched": [],
        "extra_tools": []
    }
    
    # API에서 도구 이름 추출
    api_tools = set()
    for api_info in apis.values():
        if api_info.get("search_tool"):
            api_tools.add(api_info["search_tool"])
        if api_info.get("detail_tool"):
            api_tools.add(api_info["detail_tool"])
    
    # 구현된 도구 확인
    implemented_tools = set(tools.keys())
    
    # 매칭 확인
    for api_key, api_info in apis.items():
        search_tool = api_info.get("search_tool", "").strip()
        detail_tool = api_info.get("detail_tool", "").strip()
        
        if search_tool:
            if search_tool in implemented_tools:
                result["implemented"].append({
                    "api": api_key,
                    "tool": search_tool,
                    "type": "search"
                })
            else:
                result["missing"].append({
                    "api": api_key,
                    "tool": search_tool,
                    "type": "search",
                    "target": api_info.get("target")
                })
        
        if detail_tool:
            if detail_tool in implemented_tools:
                result["implemented"].append({
                    "api": api_key,
                    "tool": detail_tool,
                    "type": "detail"
                })
            else:
                result["missing"].append({
                    "api": api_key,
                    "tool": detail_tool,
                    "type": "detail",
                    "target": api_info.get("target")
                })
    
    # 추가 도구 (API에 없는 도구)
    for tool_name in implemented_tools:
        if tool_name not in api_tools:
            result["extra_tools"].append({
                "tool": tool_name,
                "files": tools[tool_name]
            })
    
    return result


def print_coverage_report(apis: Dict[str, Dict[str, str]], tools: Dict[str, List[str]], comparison: Dict[str, Any]):
    """커버리지 리포트 출력"""
    print(f"\n{'='*60}")
    print(f"📊 도구 구현 완성도 리포트")
    print(f"{'='*60}\n")
    
    print(f"📋 API 통계:")
    print(f"  - 총 API 수: {len(apis)}개")
    print(f"  - 구현된 도구: {len(comparison['implemented'])}개")
    print(f"  - 미구현 도구: {len(comparison['missing'])}개")
    print(f"  - 추가 도구: {len(comparison['extra_tools'])}개")
    print(f"  - 구현률: {len(comparison['implemented']) / (len(comparison['implemented']) + len(comparison['missing'])) * 100:.1f}%")
    
    if comparison['missing']:
        print(f"\n❌ 미구현 도구 ({len(comparison['missing'])}개):")
        for item in comparison['missing'][:20]:  # 최대 20개만 출력
            print(f"  - {item['tool']} (API: {item['api']}, target: {item.get('target', 'N/A')})")
        if len(comparison['missing']) > 20:
            print(f"  ... 외 {len(comparison['missing']) - 20}개")
    
    if comparison['extra_tools']:
        print(f"\n➕ 추가 도구 ({len(comparison['extra_tools'])}개):")
        for item in comparison['extra_tools'][:10]:  # 최대 10개만 출력
            print(f"  - {item['tool']} ({', '.join(item['files'])})")
        if len(comparison['extra_tools']) > 10:
            print(f"  ... 외 {len(comparison['extra_tools']) - 10}개")


def main():
    print("🔍 도구 구현 완성도 체크 시작...\n")
    
    # API 목록 파싱
    print("📖 API 가이드 파싱 중...")
    apis = parse_api_guide()
    print(f"  ✅ {len(apis)}개 API 발견")
    
    # 도구 목록 파싱
    print("\n🔧 도구 파일 파싱 중...")
    tools = parse_tool_files()
    print(f"  ✅ {len(tools)}개 도구 발견")
    
    # 비교
    print("\n🔍 API-도구 매핑 비교 중...")
    comparison = compare_api_tools(apis, tools)
    
    # 리포트 출력
    print_coverage_report(apis, tools, comparison)
    
    sys.exit(0 if len(comparison['missing']) == 0 else 1)


if __name__ == "__main__":
    main()
