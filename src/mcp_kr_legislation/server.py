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
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Literal, Optional
from typing import AsyncIterator

from fastmcp import FastMCP
from mcp.types import TextContent
from mcp.server.session import ServerSession

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

@dataclass
class LegislationContext(ServerSession):
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

    async def __aenter__(self):
        logger.info("🔁 LegislationContext entered (Claude requested tool execution)")
        return self

    async def __aexit__(self, *args):
        logger.info("🔁 LegislationContext exited")

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
        logger.info("🚀 157개 법제처 OPEN API 지원 완료!")
        
        yield ctx
        
    except Exception as e:
        logger.error(f"Failed to initialize Legislation client: {e}", exc_info=True)
        raise
    finally:
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
    "misc_tools",
    "precedent_tools",
    "specialized_tools"
]

for module_name in tool_modules:
    try:
        importlib.import_module(f"mcp_kr_legislation.tools.{module_name}")
        logger.info(f"Loaded tool module: {module_name}")
    except ImportError as e:
        logger.warning(f"Failed to load tool module {module_name}: {e}")

def main():
    """메인 서버 실행 함수"""
    logger.info("✅ Initializing Legislation FastMCP server...")
    
    if legislation_config is None:
        logger.error("법제처 설정이 올바르게 로드되지 않았습니다. .env 파일을 확인하세요.")
        return
    
    transport = mcp_config.transport
    port = mcp_config.port
    
    if transport == "sse":
        asyncio.run(run_server(transport="sse", port=port))
    else:
        mcp.run()

async def run_server(
    transport: Literal["stdio", "sse"] = "stdio",
    port: int = 8001,
) -> None:
    """MCP 법제처 서버 실행
    
    Args:
        transport: 전송 방식. "stdio" 또는 "sse" 중 하나
        port: SSE 전송용 포트
    """
    if transport == "stdio":
        await mcp.run_stdio_async()
    elif transport == "sse":
        logger.info(f"Starting server with SSE transport on http://0.0.0.0:{port}")
        await mcp.run_sse_async(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main() 