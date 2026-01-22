#!/usr/bin/env python3
"""
컨텍스트 상태 확인 스크립트

사용법:
    python check_context.py
"""

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def check_context():
    """컨텍스트 상태 확인"""
    try:
        from mcp_kr_legislation.server import legislation_context
        from mcp_kr_legislation.config import legislation_config
        
        print("🔍 컨텍스트 상태 확인\n")
        
        # 설정 확인
        if legislation_config is None:
            print("❌ 설정을 불러올 수 없습니다.")
            print("   LEGISLATION_API_KEY 환경변수를 확인하세요.")
            return False
        
        print(f"✅ 설정 로드 성공")
        print(f"   - API Key: {legislation_config.oc[:3]}***")
        
        # 전역 컨텍스트 확인
        if legislation_context is None:
            print("❌ 전역 컨텍스트가 초기화되지 않았습니다.")
            return False
        
        print(f"✅ 전역 컨텍스트 초기화됨")
        
        # API 클라이언트 확인
        if legislation_context.client is None:
            print("❌ API 클라이언트가 없습니다.")
            return False
        
        print(f"✅ API 클라이언트 존재")
        
        # law_api 확인
        if legislation_context.law_api is None:
            print("⚠️  law_api가 없습니다.")
        else:
            print(f"✅ law_api 존재")
        
        # legislation_api 확인
        if legislation_context.legislation_api is None:
            print("⚠️  legislation_api가 없습니다.")
        else:
            print(f"✅ legislation_api 존재")
        
        print(f"\n✅ 모든 컨텍스트 정상")
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    success = check_context()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
