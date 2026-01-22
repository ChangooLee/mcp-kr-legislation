#!/usr/bin/env python3
"""
API 호출 테스트 스크립트

사용법:
    python test_api.py <target> <query> [--display N] [--page N]

예시:
    python test_api.py law "개인정보보호법"
    python test_api.py prec "계약" --display 10
"""

import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_api(target: str, query: str, display: int = 20, page: int = 1):
    """API 호출 테스트"""
    try:
        from mcp_kr_legislation.apis.client import LegislationClient
        from mcp_kr_legislation.config import legislation_config
        
        if legislation_config is None:
            print("❌ 설정을 불러올 수 없습니다. LEGISLATION_API_KEY 환경변수를 확인하세요.")
            return False
        
        client = LegislationClient(config=legislation_config)
        
        print(f"🔍 API 테스트: target={target}, query={query}\n")
        
        # 목록 조회 테스트
        result = client.search(
            target=target,
            params={
                "query": query,
                "display": display,
                "page": page
            }
        )
        
        # 결과 확인
        if result.get("error"):
            print(f"❌ API 오류: {result['error']}")
            return False
        
        # 결과 개수 확인
        total_count = result.get("totalCnt", 0)
        print(f"✅ 검색 성공: 총 {total_count}건")
        
        # 결과 타입별 확인
        result_keys = [k for k in result.keys() if k not in ["status", "totalCnt", "page"]]
        if result_keys:
            first_key = result_keys[0]
            items = result.get(first_key, [])
            if items:
                print(f"📋 첫 번째 결과:")
                first_item = items[0]
                for key, value in list(first_item.items())[:5]:  # 처음 5개 필드만
                    print(f"   - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='API 호출 테스트')
    parser.add_argument('target', type=str, help='API target 값 (예: law, prec)')
    parser.add_argument('query', type=str, help='검색어')
    parser.add_argument('--display', type=int, default=20, help='결과 개수 (기본값: 20)')
    parser.add_argument('--page', type=int, default=1, help='페이지 번호 (기본값: 1)')
    args = parser.parse_args()
    
    success = test_api(args.target, args.query, args.display, args.page)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
