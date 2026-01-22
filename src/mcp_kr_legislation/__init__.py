# src/mcp_kr_legislation/__init__.py
"""
한국 법제처 OPEN API MCP 서버 패키지

도구 모듈은 server.py에서 자동으로 로드됩니다.
"""
import click
from mcp_kr_legislation.server import mcp

__all__: list[str] = ["mcp"]


@click.command()
def main():
    """법령 종합 정보 MCP 서버를 실행합니다."""
    mcp.run()


if __name__ == "__main__":
    main()
