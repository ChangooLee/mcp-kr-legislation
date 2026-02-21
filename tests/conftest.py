import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


@pytest.fixture(scope="session")
def legislation_client():
    from mcp_kr_legislation.apis.client import LegislationClient
    from mcp_kr_legislation.config import legislation_config

    return LegislationClient(config=legislation_config)


@pytest.fixture(scope="session")
def mcp_server():
    from mcp_kr_legislation.server import mcp

    return mcp
