"""
한국 법제처 OPEN API 도구들

카테고리별로 분리된 모듈들:
- law_tools: 모든 법령 관련 통합 도구들 (23개)
- administrative_rule_tools: 행정규칙 및 자치법규 도구들 (8개)
- precedent_tools: 판례 관련 도구들 (8개)
- committee_tools: 위원회 결정문 도구들 (24개)
- specialized_tools: 전문화된 도구들 (조약, 별표서식, 학칙공단, 심판원)
- additional_service_tools: 부가서비스 도구들 (지식베이스, FAQ, 상담 등)
- custom_tools: 맞춤형 도구들 (자치법규, 판례)
- legal_term_tools: 법령용어 도구들 (10개)
- ministry_interpretation_tools: 중앙부처해석 도구들 (30개+)
- linkage_tools: 연계정보 도구들
- misc_tools: 기타 도구들 (자치법규, 조약)
- legislation_tools: 나머지 도구들
- search_enhance_tools: BM25 재랭킹 + 캐시 관리 도구들 (5개)
"""

import logging

_logger = logging.getLogger(__name__)

try:
    from .law_tools import *
except ImportError as e:
    _logger.error(f"law_tools import 실패: {e}")

try:
    from .administrative_rule_tools import *
except ImportError as e:
    _logger.error(f"administrative_rule_tools import 실패: {e}")

try:
    from .precedent_tools import *
except ImportError as e:
    _logger.error(f"precedent_tools import 실패: {e}")

try:
    from .committee_tools import *
except ImportError as e:
    _logger.error(f"committee_tools import 실패: {e}")

try:
    from .specialized_tools import *
except ImportError as e:
    _logger.error(f"specialized_tools import 실패: {e}")

try:
    from .additional_service_tools import *
except ImportError as e:
    _logger.error(f"additional_service_tools import 실패: {e}")

try:
    from .custom_tools import *
except ImportError as e:
    _logger.error(f"custom_tools import 실패: {e}")

try:
    from .legal_term_tools import *
except ImportError as e:
    _logger.error(f"legal_term_tools import 실패: {e}")

try:
    from .ministry_interpretation_tools import *
except ImportError as e:
    _logger.error(f"ministry_interpretation_tools import 실패: {e}")

try:
    from .linkage_tools import *
except ImportError as e:
    _logger.error(f"linkage_tools import 실패: {e}")

try:
    from .misc_tools import *
except ImportError as e:
    _logger.error(f"misc_tools import 실패: {e}")

try:
    from .legislation_tools import *
except ImportError as e:
    _logger.error(f"legislation_tools import 실패: {e}")
