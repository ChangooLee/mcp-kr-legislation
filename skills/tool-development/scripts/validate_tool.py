#!/usr/bin/env python3
"""
Tool 시그니처 검증 스크립트

사용법:
    python validate_tool.py <tool_file_path>

검증 항목:
- ctx 파라미터 없음
- 모든 파라미터에 Annotated 사용
- @mcp.tool 데코레이터 존재
- with_context(None, ...) 패턴 사용
"""

import ast
import sys
import argparse
from pathlib import Path
from typing import List, Tuple


def check_tool_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Tool 파일 검증"""
    errors = []
    warnings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))
    except Exception as e:
        return False, [f"파일 파싱 실패: {e}"]
    
    # @mcp.tool 데코레이터 확인
    has_mcp_tool = False
    tool_functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # 데코레이터 확인
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Attribute):
                    if decorator.attr == 'tool':
                        if isinstance(decorator.value, ast.Attribute):
                            if decorator.value.attr == 'mcp':
                                has_mcp_tool = True
                                tool_functions.append(node)
    
    if not has_mcp_tool:
        warnings.append("⚠️  @mcp.tool 데코레이터를 사용하는 함수를 찾을 수 없습니다")
    
    # 각 tool 함수 검증
    for func in tool_functions:
        func_name = func.name
        
        # ctx 파라미터 확인
        for arg in func.args.args:
            if arg.arg == 'ctx':
                errors.append(f"❌ {func_name}: ctx 파라미터 사용 금지")
        
        # Annotated 사용 확인
        for arg in func.args.args:
            if arg.annotation:
                if not isinstance(arg.annotation, ast.Subscript):
                    warnings.append(f"⚠️  {func_name}.{arg.arg}: Annotated 사용 권장")
                elif not isinstance(arg.annotation.value, ast.Name) or arg.annotation.value.id != 'Annotated':
                    warnings.append(f"⚠️  {func_name}.{arg.arg}: Annotated 사용 권장")
        
        # with_context 사용 확인
        has_with_context = False
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'with_context':
                    has_with_context = True
                    # 첫 번째 인자가 None인지 확인
                    if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value is None:
                        pass  # 올바른 패턴
                    else:
                        warnings.append(f"⚠️  {func_name}: with_context(None, ...) 패턴 권장")
        
        if not has_with_context:
            warnings.append(f"⚠️  {func_name}: with_context() 사용 권장")
    
    return len(errors) == 0, errors + warnings


def main():
    parser = argparse.ArgumentParser(description='Tool 시그니처 검증')
    parser.add_argument('file', type=str, help='검증할 tool 파일 경로')
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        sys.exit(1)
    
    is_valid, messages = check_tool_file(file_path)
    
    print(f"\n📋 검증 결과: {file_path.name}\n")
    for msg in messages:
        print(msg)
    
    if is_valid and not any('❌' in m for m in messages):
        print("\n✅ 검증 통과")
        sys.exit(0)
    else:
        print("\n❌ 검증 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
