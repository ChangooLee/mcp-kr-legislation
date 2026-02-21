"""
한국 법제처 OPEN API 도구들

카테고리별로 분리된 모듈들:
- law_tools: 모든 법령 관련 통합 도구들 (29개)
- administrative_rule_tools: 행정규칙 및 자치법규 도구들 (8개)
- precedent_tools: 판례 관련 도구들 (8개)
- committee_tools: 위원회 결정문 도구들 (24개)
- specialized_tools: 전문화된 도구들 (조약, 별표서식, 학칙공단, 심판원)
- additional_service_tools: 부가서비스 도구들 (지식베이스, FAQ, 상담 등)
- custom_tools: 맞춤형 도구들 (자치법규, 판례)
- legal_term_tools: 법령용어 도구들 (6개)
- ministry_interpretation_tools: 중앙부처해석 도구들 (30개+)
- linkage_tools: 연계정보 도구들 (용어 관련)
- misc_tools: 기타 도구들 (자치법규, 조약)
- legislation_tools: 나머지 도구들 (1개)
"""

# 분리된 모듈들에서 도구들을 가져옵니다
try:
    from .law_tools import *
    print("law_tools 모듈 import 성공 (29개 법령 관련 도구)")
except ImportError as e:
    print(f"law_tools import 실패: {e}")

try:
    from .administrative_rule_tools import *
    print("administrative_rule_tools 모듈 import 성공")
except ImportError as e:
    print(f"administrative_rule_tools import 실패: {e}")

try:
    from .precedent_tools import *
    print("precedent_tools 모듈 import 성공")
except ImportError as e:
    print(f"precedent_tools import 실패: {e}")

try:
    from .committee_tools import *
    print("committee_tools 모듈 import 성공")
except ImportError as e:
    print(f"committee_tools import 실패: {e}")

try:
    from .specialized_tools import *
    print("specialized_tools 모듈 import 성공")
except ImportError as e:
    print(f"specialized_tools import 실패: {e}")

try:
    from .additional_service_tools import *
    print("additional_service_tools 모듈 import 성공")
except ImportError as e:
    print(f"additional_service_tools import 실패: {e}")

try:
    from .custom_tools import *
    print("custom_tools 모듈 import 성공")
except ImportError as e:
    print(f"custom_tools import 실패: {e}")

try:
    from .legal_term_tools import *
    print("legal_term_tools 모듈 import 성공")
except ImportError as e:
    print(f"legal_term_tools import 실패: {e}")

try:
    from .ministry_interpretation_tools import *
    print("ministry_interpretation_tools 모듈 import 성공")
except ImportError as e:
    print(f"ministry_interpretation_tools import 실패: {e}")

try:
    from .linkage_tools import *
    print("linkage_tools 모듈 import 성공")
except ImportError as e:
    print(f"linkage_tools import 실패: {e}")

try:
    from .misc_tools import *
    print("misc_tools 모듈 import 성공")
except ImportError as e:
    print(f"misc_tools import 실패: {e}")

try:
    from .legislation_tools import *
    print("legislation_tools 모듈 import 성공")
except ImportError as e:
    print(f"legislation_tools import 실패: {e}")

print("\n모든 도구 모듈 로드 완료!")
print("주요 변경사항:")
print("   • 법령 관련 29개 도구 → law_tools.py로 통합")
print("   • basic_law_tools.py → 삭제됨")
print("   • 각 파일에서 법령 도구들 제거 완료")
print("   • 모든 유틸리티 함수 law_tools로 통합") 