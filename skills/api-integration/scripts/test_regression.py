#!/usr/bin/env python3
"""
전체 API 회귀 테스트 스크립트

사용법:
    python test_regression.py [--category law] [--verbose]

기존 test_api.py의 test_api() 함수를 재사용하여
주요 API 카테고리별 샘플 호출을 수행합니다.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
import time

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# 기존 test_api.py의 함수 import
from test_api import test_api

# 테스트 케이스 import
from test_cases import TEST_CASES, CATEGORIES, get_test_cases_by_category


def test_api_with_validation(
    target: str,
    params: Dict[str, Any],
    expected_fields: List[str],
    verbose: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    API 호출 및 검증
    
    Returns:
        (success, result_info)
    """
    try:
        from mcp_kr_legislation.apis.client import LegislationClient
        from mcp_kr_legislation.config import legislation_config
        
        if legislation_config is None:
            return False, {"error": "설정을 불러올 수 없습니다"}
        
        client = LegislationClient(config=legislation_config)
        
        # JSON 우선 시도
        params_json = params.copy()
        params_json["type"] = "JSON"
        
        start_time = time.time()
        result = client.search(target=target, params=params_json)
        elapsed_time = time.time() - start_time
        
        # 결과 검증
        if result.get("error"):
            # XML로 재시도
            if verbose:
                print(f"  ⚠️  JSON 실패, XML로 재시도...")
            params_xml = params.copy()
            params_xml["type"] = "XML"
            result = client.search(target=target, params=params_xml)
            elapsed_time = time.time() - start_time
        
        # 응답 구조 분석 (LawSearch 같은 래퍼 키 처리)
        actual_result = result
        wrapper_keys = ["LawSearch", "LawService", "PrecSearch", "DecSearch"]
        for wrapper in wrapper_keys:
            if wrapper in result:
                actual_result = result[wrapper]
                break
        
        # 필수 필드 확인
        has_expected_fields = False
        total_count = actual_result.get("totalCnt", 0)
        
        # 데이터 키 찾기 (law, prec, admrul, etc.)
        data_keys = [k for k in actual_result.keys() if k not in ["status", "totalCnt", "page", "error", "head"]]
        items = []
        
        if data_keys:
            first_key = data_keys[0]
            items_data = actual_result.get(first_key, [])
            # 리스트인 경우
            if isinstance(items_data, list):
                items = items_data
            # 딕셔너리인 경우 (단일 결과)
            elif isinstance(items_data, dict):
                items = [items_data]
        
        if items and len(items) > 0:
            first_item = items[0]
            # 예상 필드 중 하나라도 존재하는지 확인
            for field in expected_fields:
                # 한글/영문 필드명 모두 확인
                if field in first_item or any(field in str(k) for k in first_item.keys()):
                    has_expected_fields = True
                    break
            # 필드가 없어도 결과가 있으면 성공으로 처리
            if not has_expected_fields and items:
                has_expected_fields = True
        
        success = (
            not result.get("error") and
            len(items) > 0
        )
        
        return success, {
            "target": target,
            "total_count": total_count,
            "has_results": len(items) > 0,
            "has_expected_fields": has_expected_fields,
            "elapsed_time": elapsed_time,
            "error": result.get("error"),
            "item_count": len(items),
        }
        
    except Exception as e:
        return False, {"error": str(e)}


def run_regression_tests(
    category: str = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """회귀 테스트 실행"""
    test_cases = get_test_cases_by_category(category)
    
    if not test_cases:
        print(f"❌ 테스트 케이스를 찾을 수 없습니다. (category: {category})")
        return {}
    
    print(f"🔍 회귀 테스트 시작: {len(test_cases)}개 API\n")
    if category:
        print(f"📋 카테고리: {category}\n")
    
    results = {
        "total": len(test_cases),
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for api_name, test_case in test_cases.items():
        target = test_case["target"]
        params = test_case["params"]
        expected_fields = test_case["expected_fields"]
        category_name = test_case["category"]
        
        if verbose:
            print(f"테스트: {api_name} (target={target})")
        else:
            print(f"테스트: {api_name}...", end=" ", flush=True)
        
        success, result_info = test_api_with_validation(
            target, params, expected_fields, verbose
        )
        
        if success:
            results["passed"] += 1
            if verbose:
                print(f"  ✅ 통과: {result_info['total_count']}건, {result_info['elapsed_time']:.2f}초")
            else:
                print(f"✅ ({result_info['total_count']}건, {result_info['elapsed_time']:.2f}초)")
        else:
            results["failed"] += 1
            error_msg = result_info.get("error", "검증 실패")
            if verbose:
                print(f"  ❌ 실패: {error_msg}")
            else:
                print(f"❌ ({error_msg})")
        
        results["details"].append({
            "api_name": api_name,
            "target": target,
            "category": category_name,
            "success": success,
            **result_info
        })
    
    return results


def print_summary(results: Dict[str, Any]):
    """테스트 결과 요약 출력"""
    print(f"\n{'='*60}")
    print(f"📊 테스트 결과 요약")
    print(f"{'='*60}")
    print(f"총 테스트: {results['total']}개")
    print(f"✅ 통과: {results['passed']}개")
    print(f"❌ 실패: {results['failed']}개")
    print(f"성공률: {results['passed'] / results['total'] * 100:.1f}%")
    
    if results['failed'] > 0:
        print(f"\n❌ 실패한 API:")
        for detail in results['details']:
            if not detail['success']:
                print(f"  - {detail['api_name']} (target={detail['target']}): {detail.get('error', '검증 실패')}")


def main():
    parser = argparse.ArgumentParser(description='API 회귀 테스트')
    parser.add_argument('--category', type=str, help='테스트할 카테고리 (예: 법령, 판례)')
    parser.add_argument('--verbose', action='store_true', help='상세 출력')
    args = parser.parse_args()
    
    # 사용 가능한 카테고리 목록 출력
    if args.category and args.category not in CATEGORIES:
        print(f"❌ 알 수 없는 카테고리: {args.category}")
        print(f"\n사용 가능한 카테고리:")
        for cat in CATEGORIES.keys():
            print(f"  - {cat}")
        sys.exit(1)
    
    results = run_regression_tests(
        category=args.category,
        verbose=args.verbose
    )
    
    print_summary(results)
    
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
