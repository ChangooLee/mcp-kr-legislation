#!/usr/bin/env python3
"""
API 응답 검증 스크립트

사용법:
    python validate_response.py <response_file.json>
    또는
    echo '{"status": "000", "law": []}' | python validate_response.py

기능:
    API 응답 구조 검증, 필수 필드 확인, 개선 제안
"""

import sys
import argparse
import json
from typing import Dict, Any, Optional, Tuple


def validate_api_response(response: Dict[str, Any]) -> Tuple[bool, Optional[str], list]:
    """
    API 응답 검증
    
    Returns:
        (is_valid, error_message, suggestions)
    """
    errors = []
    suggestions = []
    
    # 상태 코드 확인
    if response.get("error"):
        errors.append(f"API 오류: {response['error']}")
        return False, errors[0], suggestions
    
    # 필수 필드 확인
    if "status" not in response:
        errors.append("응답에 status 필드가 없습니다")
        return False, errors[0], suggestions
    
    # 빈 결과 확인
    if response.get("status") == "000":
        # 결과 데이터 확인
        result_keys = [k for k in response.keys() if k not in ["status", "totalCnt", "page"]]
        has_results = False
        
        for key in result_keys:
            items = response.get(key, [])
            if items and len(items) > 0:
                has_results = True
                break
        
        if not has_results:
            total_count = response.get("totalCnt", 0)
            if total_count == 0:
                errors.append("검색 결과가 없습니다")
                suggestions.append("검색어를 변경하거나 본문 검색으로 확장해보세요")
            else:
                errors.append(f"totalCnt는 {total_count}이지만 실제 결과 데이터가 없습니다")
    
    # 결과가 너무 많음
    total_count = response.get("totalCnt", 0)
    if total_count > 100:
        suggestions.append(f"결과가 {total_count}개로 너무 많습니다. 검색어를 구체화하거나 display 파라미터를 줄이세요")
    
    # 응답 시간 확인 (있는 경우)
    response_time = response.get("_response_time", 0)
    if response_time > 5.0:
        suggestions.append(f"응답 시간이 {response_time:.2f}초로 느립니다. 캐싱을 고려하세요")
    
    is_valid = len(errors) == 0
    error_msg = errors[0] if errors else None
    
    return is_valid, error_msg, suggestions


def main():
    parser = argparse.ArgumentParser(description='API 응답 검증')
    parser.add_argument('file', nargs='?', type=str, help='응답 JSON 파일 경로 (없으면 stdin에서 읽음)')
    args = parser.parse_args()
    
    # JSON 읽기
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            response = json.load(f)
    else:
        # stdin에서 읽기
        response = json.load(sys.stdin)
    
    print("🔍 API 응답 검증\n")
    
    # 검증
    is_valid, error_msg, suggestions = validate_api_response(response)
    
    if is_valid:
        print("✅ 검증 통과")
        
        total_count = response.get("totalCnt", 0)
        print(f"📊 결과 개수: {total_count}개")
        
        if suggestions:
            print(f"\n💡 개선 제안:")
            for suggestion in suggestions:
                print(f"   - {suggestion}")
    else:
        print(f"❌ 검증 실패: {error_msg}")
        
        if suggestions:
            print(f"\n💡 개선 제안:")
            for suggestion in suggestions:
                print(f"   - {suggestion}")
        
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
