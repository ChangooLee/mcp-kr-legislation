"""
한국 법제처 OPEN API MCP 서버 설정
"""

import os
import logging
from dataclasses import dataclass
from typing import Literal, cast
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class LegislationConfig:
    """법제처 OPEN API 통합 설정"""
    
    oc: str  # 사용자 이메일 ID (필수)
    
    # API 기본 URL들
    search_base_url: str = "http://www.law.go.kr/DRF/lawSearch.do"
    service_base_url: str = "http://www.law.go.kr/DRF/lawService.do" 
    
    # 로그 설정
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "legislation.log"
    
    # 기본 요청 설정
    default_display: int = 20
    max_display: int = 100
    default_timeout: int = 30

    @classmethod
    def from_env(cls) -> "LegislationConfig":
        oc = os.getenv("LEGISLATION_API_KEY", "lchangoo")  # 작동하는 기본값 설정
        # 이메일 형태면 @앞 부분만 사용
        if "@" in oc:
            oc = oc.split("@")[0]
        
        return cls(
            oc=oc,
            search_base_url=os.getenv("LEGISLATION_SEARCH_URL", "http://www.law.go.kr/DRF/lawSearch.do"),
            service_base_url=os.getenv("LEGISLATION_SERVICE_URL", "http://www.law.go.kr/DRF/lawService.do"),
            log_format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            log_file=os.getenv("LOG_FILE", "legislation.log"),
            default_display=int(os.getenv("DEFAULT_DISPLAY", "20")),
            max_display=int(os.getenv("MAX_DISPLAY", "100")),
            default_timeout=int(os.getenv("REQUEST_TIMEOUT", "30"))
        )

@dataclass
class MCPConfig:
    """MCP 서버 설정"""
    
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "INFO"
    server_name: str = "kr-legislation-mcp"
    transport: Literal["stdio", "http"] = "stdio"

    @classmethod
    def from_env(cls) -> "MCPConfig":
        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8001")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            server_name=os.getenv("MCP_SERVER_NAME", "kr-legislation-mcp"),
            transport=cast(Literal["stdio", "http"], os.getenv("TRANSPORT", "stdio"))
        )

# 설정 인스턴스 생성
def _try_make_config():
    try:
        return LegislationConfig.from_env()
    except Exception:
        return None

legislation_config = _try_make_config()
mcp_config = MCPConfig.from_env() 