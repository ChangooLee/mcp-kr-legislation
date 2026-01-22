"""
MCP 컨텍스트 헬퍼 유틸리티
"""

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("mcp-kr-legislation")

def _normalize_lifespan_context(lifespan_context: Any) -> Any:
    """
    lifespan_context를 정규화합니다.
    dict 형태로 래핑된 경우 실제 컨텍스트를 추출합니다.
    
    Args:
        lifespan_context: 원본 lifespan_context
        
    Returns:
        정규화된 LegislationContext
    """
    # dict 형태로 래핑된 경우 처리
    if isinstance(lifespan_context, dict):
        # 일반적인 키 이름들 확인
        for key in ['app_lifespan_context', 'lifespan_context', 'context', 'ctx']:
            if key in lifespan_context:
                return lifespan_context[key]
        # dict 자체가 컨텍스트인 경우 (dict에 필요한 속성이 있는지 확인)
        if hasattr(lifespan_context, 'client') or 'client' in lifespan_context:
            return lifespan_context
    
    return lifespan_context

def _get_context_from_ctx(ctx: Any) -> Optional[Any]:
    """
    MCPContext에서 LegislationContext를 추출합니다.
    
    Args:
        ctx: MCPContext or None
        
    Returns:
        LegislationContext or None
    """
    if ctx is None:
        return None
    
    try:
        # ctx.request_context.lifespan_context 접근 시도
        if hasattr(ctx, 'request_context'):
            request_ctx = ctx.request_context
            if hasattr(request_ctx, 'lifespan_context'):
                lifespan_ctx = request_ctx.lifespan_context
                return _normalize_lifespan_context(lifespan_ctx)
    except Exception as e:
        logger.debug(f"Context 추출 실패: {e}")
        return None
    
    return None

def with_context(
    ctx: Optional[Any],
    tool_name: str,
    fallback_func: Callable[[Any], Any]
) -> Any:
    """
    MCP context를 안전하게 처리합니다.
    ctx 주입이 있으면 사용하고, 없으면 전역 컨텍스트로 fallback합니다.

    Args:
        ctx: MCPContext or None
        tool_name: 도구명 (로깅용)
        fallback_func: context.client.search 등 context 의존 로직

    Returns:
        fallback_func 실행 결과
        
    Raises:
        ValueError: 전역 컨텍스트도 없을 때
    """
    logger.info(f"📌 Tool: {tool_name} 호출됨")

    # 1. ctx에서 컨텍스트 추출 시도
    legislation_ctx = _get_context_from_ctx(ctx)
    
    if legislation_ctx is not None:
        try:
            result = fallback_func(legislation_ctx)
            logger.info("✅ MCP 내부 컨텍스트 사용")
            return result
        except Exception as e:
            logger.warning(f"⚠️ MCPContext 접근 실패, 전역 컨텍스트로 fallback: {e}")
            # fallback으로 계속 진행
    
    # 2. 전역 컨텍스트로 fallback
    try:
        from mcp_kr_legislation.server import get_global_context
        global_ctx = get_global_context()
        
        if global_ctx is not None:
            result = fallback_func(global_ctx)
            logger.info("✅ 전역 컨텍스트 사용 (fallback)")
            return result
    except Exception as e:
        logger.error(f"⚠️ 전역 컨텍스트 접근 실패: {e}")
    
    # 3. 기존 전역 변수로 fallback (하위 호환성)
    try:
        from mcp_kr_legislation.server import legislation_context
        if legislation_context is not None:
            result = fallback_func(legislation_context)
            logger.info("✅ 기존 전역 변수 사용 (legacy fallback)")
            return result
    except Exception as e:
        logger.error(f"⚠️ 기존 전역 변수 접근 실패: {e}")
    
    # 4. 모두 실패
    raise ValueError("Legislation context is required but not provided. Lifespan context not initialized.")
