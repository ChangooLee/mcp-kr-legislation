"""
한국 법제처 OPEN API MCP 서버

지원하는 API 카테고리:
- 법령 (16개)
- 부가서비스 (10개)
- 행정규칙 (5개)  
- 자치법규 (4개)
- 판례관련 (8개)
- 위원회결정문 (30개)
- 조약 (2개)
- 별표서식 (4개)
- 학칙공단 (2개)
- 법령용어 (2개)
- 맞춤형 (6개)
- 지식베이스 (6개)
- 기타 (1개)
- 중앙부처해석 (14개)
"""

import logging
import sys
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Optional
from typing import AsyncIterator

from fastmcp import FastMCP
from mcp.types import TextContent

from .config import MCPConfig, LegislationConfig, mcp_config, legislation_config
from .apis.client import LegislationClient
from .apis import law_api, legislation_api
from .registry.initialize_registry import initialize_registry

# 로거 설정
level_name = mcp_config.log_level.upper()
level = getattr(logging, level_name, logging.INFO)
logger = logging.getLogger("mcp-kr-legislation")
logging.basicConfig(
    level=level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)

# 전역 LegislationContext 저장소 (fallback용)
_global_context: Optional['LegislationContext'] = None
_context_lock = threading.Lock()

def set_global_context(ctx: 'LegislationContext') -> None:
    """전역 LegislationContext를 설정합니다."""
    global _global_context
    with _context_lock:
        _global_context = ctx
        logger.info("✅ Global LegislationContext 저장됨")

def get_global_context() -> Optional['LegislationContext']:
    """전역 LegislationContext를 가져옵니다."""
    global _global_context
    with _context_lock:
        return _global_context


@dataclass
class LegislationContext:
    """법제처 API 통합 컨텍스트"""
    client: Optional[LegislationClient] = None
    law_api: Any = None
    legislation_api: Any = None

    def __post_init__(self):
        # client가 None이면 기본 클라이언트 생성
        if self.client is None:
            if legislation_config is None:
                raise ValueError("법제처 설정이 올바르게 로드되지 않았습니다.")
            self.client = LegislationClient(config=legislation_config)
            
        # API 모듈이 None이면 초기화
        if self.law_api is None:
            self.law_api = law_api.LawAPI(self.client)
        if self.legislation_api is None:
            self.legislation_api = legislation_api.LegislationAPI(self.client)

# 전역 컨텍스트 생성 (fallback용)
legislation_client = None
legislation_context = None
ctx = None

if legislation_config is not None:
    try:
        legislation_client = LegislationClient(config=legislation_config)
        legislation_context = LegislationContext(
            client=legislation_client,
            law_api=law_api.LawAPI(legislation_client),
            legislation_api=legislation_api.LegislationAPI(legislation_client)
        )
        ctx = legislation_context
        # 전역 컨텍스트로 저장
        set_global_context(legislation_context)
    except Exception as e:
        logger.warning(f"fallback 컨텍스트 생성 실패: {e}")
        ctx = None
else:
    logger.warning("법제처 설정이 없어 fallback 컨텍스트를 생성하지 않습니다.")

@asynccontextmanager
async def legislation_lifespan(app: FastMCP) -> AsyncIterator[LegislationContext]:
    """법제처 MCP 서버 라이프사이클 관리"""
    logger.info("Initializing Legislation FastMCP server...")
    
    try:
        logger.info(f"Server Name: {mcp_config.server_name}")
        logger.info(f"Host: {mcp_config.host}")
        logger.info(f"Port: {mcp_config.port}")
        logger.info(f"Log Level: {mcp_config.log_level}")
        
        if legislation_config is None:
            raise ValueError("법제처 설정이 올바르게 로드되지 않았습니다.")
        
        # 법제처 API 클라이언트 초기화
        client = LegislationClient(config=legislation_config)
        
        # API 모듈 초기화
        ctx = LegislationContext(
            client=client,
            law_api=law_api.LawAPI(client),
            legislation_api=legislation_api.LegislationAPI(client)
        )
        
        logger.info("Legislation client and API modules initialized successfully.")
        logger.info("🚀 176개 법제처 OPEN API 지원 완료!")
        
        # 전역 컨텍스트로 저장 (fallback용)
        set_global_context(ctx)
        
        yield ctx
        
    except Exception as e:
        logger.error(f"Failed to initialize Legislation client: {e}", exc_info=True)
        raise
    finally:
        # 전역 컨텍스트 정리
        global _global_context
        with _context_lock:
            _global_context = None
        logger.info("Shutting down Legislation FastMCP server...")

# 도구 레지스트리 초기화
tool_registry = initialize_registry()

# FastMCP 인스턴스 생성
mcp = FastMCP(
    "KR Legislation MCP",
    instructions="Korean legislation information MCP server with comprehensive tools covering all categories",
    lifespan=legislation_lifespan,
)

# 도구 모듈 동적 로딩
import importlib
tool_modules = [
    "law_tools",
    "law_comparison_tools",  # 비교/이력/연계 도구들
    "law_specialized_tools",  # 금융/세무/개인정보 특수 검색 도구들
    "optimized_law_tools",  # 캐싱 최적화된 도구들
    "legislation_tools",
    "additional_service_tools",
    "administrative_rule_tools",
    "ai_tools",
    "committee_tools",
    "custom_tools",
    "legal_term_tools",
    "linkage_tools",
    "ministry_interpretation_tools",
    "ministry_interpretation_tools_extended",
    "misc_tools",
    "precedent_tools",
    "specialized_tools",
]

logger.info(f"🔧 도구 모듈 로딩 시작... (총 {len(tool_modules)}개)")
_loaded_count = 0
for module_name in tool_modules:
    try:
        importlib.import_module(f"mcp_kr_legislation.tools.{module_name}")
        _loaded_count += 1
        logger.info(f"✅ Loaded tool module: {module_name}")
    except Exception as e:
        logger.error(f"❌ Failed to load tool module {module_name}: {type(e).__name__}: {e}")

# 도구 등록 상태 확인
try:
    _tools = list(mcp._tool_manager._tools.keys()) if hasattr(mcp, '_tool_manager') else []
    logger.info(f"🔧 도구 모듈 로딩 완료: {_loaded_count}/{len(tool_modules)}개 모듈, {len(_tools)}개 도구 등록됨")
except Exception as e:
    logger.warning(f"도구 등록 상태 확인 실패: {e}")

def main():
    """메인 서버 실행 함수"""
    logger.info("✅ Initializing Legislation FastMCP server...")
    
    if legislation_config is None:
        logger.error("법제처 설정이 올바르게 로드되지 않았습니다. .env 파일을 확인하세요.")
        return
    
    # 도구 등록 상태 확인
    try:
        _tools = list(mcp._tool_manager._tools.keys()) if hasattr(mcp, '_tool_manager') else []
        logger.info(f"🔧 main() 시작 시 등록된 도구: {len(_tools)}개")
        if len(_tools) == 0:
            logger.error("❌ 도구가 등록되지 않았습니다! mcp 인스턴스 확인 필요")
            logger.info(f"   mcp 인스턴스 id: {id(mcp)}")
    except Exception as e:
        logger.warning(f"도구 등록 상태 확인 실패: {e}")
    
    mcp_config = MCPConfig.from_env()
    
    if mcp_config.transport == "http":
        logger.info(f"Starting server with HTTP transport on http://{mcp_config.host}:{mcp_config.port}")
        mcp.run(transport="streamable-http", host=mcp_config.host, port=mcp_config.port)
    else:
        mcp.run()

if __name__ == "__main__":
    main() 