#!/usr/bin/env python3
"""
Tool 실행 테스트 스크립트

사용법:
    python test_tool.py <tool_name> [arguments...]

예시:
    python test_tool.py search_law "개인정보보호법"
    python test_tool.py get_law_detail "011357"
"""

import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_tool(tool_name: str, *args):
    """Tool 실행 테스트"""
    try:
        from mcp_kr_legislation.server import mcp
        from mcp_kr_legislation.config import legislation_config
        
        # Tool 찾기
        tool_func = None
        for tool in mcp.list_tools():
            if tool.name == tool_name:
                # Tool 함수 직접 호출은 어려우므로 안내만 출력
                print(f"✅ Tool '{tool_name}' 발견됨")
                print(f"📝 설명: {tool.description}")
                print(f"📋 파라미터:")
                for param_name, param_spec in tool.inputSchema.get('properties', {}).items():
                    param_type = param_spec.get('type', 'unknown')
                    param_desc = param_spec.get('description', '')
                    print(f"   - {param_name} ({param_type}): {param_desc}")
                print(f"\n💡 실제 실행은 MCP 서버를 통해 수행해야 합니다.")
                return True
        
        print(f"❌ Tool '{tool_name}'을 찾을 수 없습니다")
        print(f"\n사용 가능한 Tool 목록:")
        for tool in mcp.list_tools():
            print(f"  - {tool.name}")
        return False
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Tool 실행 테스트')
    parser.add_argument('tool_name', type=str, help='테스트할 tool 이름')
    parser.add_argument('args', nargs='*', help='Tool 인자')
    args = parser.parse_args()
    
    print(f"🔍 Tool 테스트: {args.tool_name}\n")
    
    success = test_tool(args.tool_name, *args.args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
