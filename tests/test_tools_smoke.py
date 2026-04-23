"""
MCP 도구 등록 및 기본 동작 smoke test.

모든 도구 모듈이 정상적으로 로드되고,
각 카테고리별 대표 도구가 등록되어 있는지 확인합니다.
"""

import pytest

EXPECTED_TOOL_MODULES = [
    "law_tools",
    "law_comparison_tools",
    "law_specialized_tools",
    "optimized_law_tools",
    "legislation_tools",
    "additional_service_tools",
    "administrative_rule_tools",
    "committee_tools",
    "custom_tools",
    "legal_term_tools",
    "linkage_tools",
    "ministry_interpretation_tools",
    "ministry_interpretation_tools_extended",
    "misc_tools",
    "precedent_tools",
    "specialized_tools",
    "search_enhance_tools",
]

REPRESENTATIVE_TOOLS = [
    "search_law",
    "get_law_detail",
    "search_precedent",
    "get_precedent_detail",
    "search_privacy_committee",
    "search_administrative_rule",
    "search_local_ordinance",
    "search_legal_term",
    "search_treaty",
    "search_tax_tribunal",
    "search_custom_law",
    "search_moef_interpretation",
    "search_mois_interpretation",
    "search_law_appendix",
    # BM25 enhanced search tools
    "search_law_bm25",
    "search_precedent_bm25",
    "search_legal_term_bm25",
    "search_committee_bm25",
    "search_admin_rule_bm25",
    "search_interpretation_bm25",
    "search_all_bm25",
    "explain_bm25_tokenize",
    # Cache management tools
    "get_cache_status",
    "cleanup_cache_tool",
    "invalidate_law_cache",
]


def _get_registered_tool_names(mcp_server):
    tool_manager = getattr(mcp_server, "_tool_manager", None)
    if tool_manager and hasattr(tool_manager, "_tools"):
        return list(tool_manager._tools.keys())
    return []


class TestToolRegistration:
    def test_minimum_tool_count(self, mcp_server):
        tools = _get_registered_tool_names(mcp_server)
        assert len(tools) >= 150, f"Expected 150+ tools, got {len(tools)}"

    @pytest.mark.parametrize("tool_name", REPRESENTATIVE_TOOLS)
    def test_representative_tool_exists(self, mcp_server, tool_name):
        tools = _get_registered_tool_names(mcp_server)
        assert tool_name in tools, f"Tool '{tool_name}' not registered"


class TestModuleImport:
    @pytest.mark.parametrize("module_name", EXPECTED_TOOL_MODULES)
    def test_tool_module_imports(self, module_name):
        import importlib

        mod = importlib.import_module(
            f"mcp_kr_legislation.tools.{module_name}"
        )
        assert mod is not None


class TestConfig:
    def test_legislation_config_loaded(self):
        from mcp_kr_legislation.config import legislation_config

        assert legislation_config is not None
        assert legislation_config.oc is not None
        assert len(legislation_config.oc) > 0

    def test_api_urls_configured(self):
        from mcp_kr_legislation.config import legislation_config

        assert "law.go.kr" in legislation_config.search_base_url
        assert "law.go.kr" in legislation_config.service_base_url
