"""
한국 법제처 OPEN API - 연계정보 도구들

법령용어-일상용어 연계 등 용어 관련 연계정보 조회 기능을 제공합니다.

주의: search_daily_term, search_legal_daily_term_link 도구는
      legal_term_tools.py에 정의되어 있습니다. (중복 방지)
"""

import logging
from typing import Optional
from mcp.types import TextContent

from ..server import mcp

logger = logging.getLogger(__name__)

logger.info("연계정보 도구가 로드되었습니다. (search_daily_term, search_legal_daily_term_link는 legal_term_tools.py에 등록됨)")
