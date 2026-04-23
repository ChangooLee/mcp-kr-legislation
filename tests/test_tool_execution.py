"""
MCP 도구 함수 직접 호출 테스트.

등록된 MCP 도구를 실제로 호출하여 응답이 TextContent이고
유효한 데이터를 포함하는지 검증합니다. 품질 메트릭(응답시간/크기)도 측정합니다.

pytest tests/test_tool_execution.py -v
"""

import time
import warnings
import pytest
from mcp.types import TextContent

TOOL_TESTS = {
    # ===================================================================
    # 법령 (law_tools.py)
    # ===================================================================
    "search_law": {"query": "민법", "display": 2},
    "get_law_detail": {"mst": "001597"},
    "search_effective_law": {"display": 2},
    "search_english_law": {"query": "act", "display": 2},
    "get_english_law_detail": {"mst": "001597", "max_articles": 5},
    "get_english_law_summary": {"law_name": "민법"},
    "search_law_nickname": {},
    "search_deleted_law_data": {"display": 2},
    "search_old_and_new_law": {"display": 2},
    "get_old_and_new_law_detail": {"mst": "001597"},
    "search_three_way_comparison": {"display": 2},
    "get_three_way_comparison_detail": {"mst": "001597", "knd": 1},
    "search_one_view": {"display": 2},
    "get_one_view_detail": {"mst": "001597", "display": 5},
    "search_law_system_diagram": {"display": 2},
    "get_law_system_diagram_detail": {"mst_id": "001597"},
    "get_delegated_law": {"law_id": "001597"},
    "get_effective_law_articles": {"mst": "001597", "display": 5},
    "search_effective_law_articles_raw": {"mst": "001597", "display": 5},
    "get_effective_law_detail": {"effective_law_id": "001597"},
    "search_law_unified": {"query": "부동산", "display": 2},
    "search_law_articles": {"mst": "001597", "display": 5},
    "get_law_article_by_key": {"mst": "001597", "target": "law", "article_key": "제1조"},
    "get_law_articles_range": {"mst": "001597", "target": "law", "start_article": 1, "count": 3},

    # ===================================================================
    # 법령 비교/이력 (law_comparison_tools.py)
    # ===================================================================
    "search_law_change_history": {"change_date": "20240101", "display": 2},
    "search_law_amendment_history": {"query": "민법", "display": 2},
    "get_law_amendment_history_detail": {"mst": "001597"},
    "search_article_change_history": {"mst": "001597", "article_no": "1"},
    "compare_law_versions": {"law_name": "민법"},
    "search_ordinance_law_link": {"display": 2},
    "search_law_ordinance_status": {"query": "민법", "display": 2},
    "search_related_law": {"query": "민법", "display": 2},
    "search_law_appendix": {"display": 2},
    "get_law_appendix_detail": {"appendix_id": "001597"},
    "search_admin_rule_appendix": {"query": "서식", "display": 2},

    # ===================================================================
    # 행정규칙 / 자치법규 (administrative_rule_tools.py)
    # ===================================================================
    "search_administrative_rule": {"query": "훈령", "display": 2},
    "get_administrative_rule_detail": {"rule_id": "2200000103699"},
    "search_administrative_rule_comparison": {"query": "훈령", "display": 2},
    "get_administrative_rule_comparison_detail": {"comparison_id": "2100000255350"},
    "search_local_ordinance": {"query": "조례", "display": 2},
    "get_local_ordinance_detail": {"ordinance_id": "1013533"},
    "search_ordinance_appendix": {"query": "서식", "display": 2},
    "search_linked_ordinance": {"display": 2},

    # ===================================================================
    # 판례 (precedent_tools.py)
    # ===================================================================
    "search_precedent": {"query": "손해배상", "display": 2},
    "get_precedent_detail": {"case_id": "614341"},
    "search_constitutional_court": {"query": "위헌", "display": 2},
    "get_constitutional_court_detail": {"decision_id": "137495"},
    "search_legal_interpretation": {"query": "해석", "display": 2},
    "get_legal_interpretation_detail": {"interpretation_id": "313895"},
    "search_administrative_trial": {"query": "행정", "display": 2},
    "get_administrative_trial_detail": {"trial_id": "1"},

    # ===================================================================
    # 위원회결정문 (committee_tools.py) - 12 search + 12 detail
    # ===================================================================
    "search_privacy_committee": {"query": "개인정보", "display": 2},
    "get_privacy_committee_detail": {"decision_id": "9459"},
    "search_financial_committee": {"query": "결정", "display": 2},
    "get_financial_committee_detail": {"decision_id": "7861"},
    "search_monopoly_committee": {"query": "공정", "display": 2},
    "get_monopoly_committee_detail": {"decision_id": "16413"},
    "search_anticorruption_committee": {"query": "민원", "display": 2},
    "get_anticorruption_committee_detail": {"decision_id": "2295"},
    "search_labor_committee": {"query": "노동", "display": 2},
    "get_labor_committee_detail": {"decision_id": "149"},
    "search_environment_committee": {"query": "환경", "display": 2},
    "get_environment_committee_detail": {"decision_id": "1"},
    "search_securities_committee": {"query": "증권", "display": 2},
    "get_securities_committee_detail": {"decision_id": "8259"},
    "search_human_rights_committee": {"query": "인권", "display": 2},
    "get_human_rights_committee_detail": {"decision_id": "147"},
    "search_broadcasting_committee": {"query": "방송", "display": 2},
    "get_broadcasting_committee_detail": {"decision_id": "11571"},
    "search_industrial_accident_committee": {"query": "산재", "display": 2},
    "get_industrial_accident_committee_detail": {"decision_id": "1"},
    "search_land_tribunal": {"query": "토지", "display": 2},
    "get_land_tribunal_detail": {"decision_id": "4971"},
    "search_employment_insurance_committee": {"query": "고용", "display": 2},
    "get_employment_insurance_committee_detail": {"decision_id": "1"},

    # ===================================================================
    # 맞춤형 (custom_tools.py)
    # ===================================================================
    "search_custom_law": {"query": "민법", "display": 2},
    "search_custom_law_articles": {"query": "민법", "display": 2},
    "search_custom_ordinance": {"query": "조례", "display": 2},
    "search_custom_ordinance_articles": {"query": "조례", "display": 2},
    "search_custom_administrative_rule": {"query": "훈령", "display": 2},
    "search_custom_administrative_rule_articles": {"query": "훈령", "display": 2},

    # ===================================================================
    # 법령용어 / 지식베이스 (legal_term_tools.py)
    # ===================================================================
    "search_legal_term": {"query": "계약", "display": 2},
    "get_legal_term_detail": {"term_id": "5407551"},
    "search_legal_term_ai": {"query": "계약", "display": 2},
    "search_daily_legal_term_link": {"query": "계약", "display": 2},
    "search_legal_term_article_link": {"term_id": "5407551", "display": 2},
    "search_article_legal_term_link": {"mst": "001597", "jo": "1", "display": 2},
    "search_intelligent_law": {"query": "개인정보"},
    "search_intelligent_related_law": {"query": "개인정보"},

    # ===================================================================
    # 연계 (linkage_tools.py)
    # ===================================================================
    "search_daily_term": {"query": "계약", "display": 2},
    "search_legal_daily_term_link": {"term_id": "5267621", "display": 2},

    # ===================================================================
    # 조약 / 학칙 / 특수 (specialized_tools.py)
    # ===================================================================
    "search_treaty": {"query": "투자", "display": 2},
    "search_university_regulation": {"query": "학칙", "display": 2},
    "search_public_corporation_regulation": {"query": "규정", "display": 2},
    "search_public_institution_regulation": {"query": "규정", "display": 2},
    "search_tax_tribunal": {"query": "조세", "display": 2},
    "get_tax_tribunal_detail": {"tribunal_id": "1"},
    "search_maritime_safety_tribunal": {"query": "해양", "display": 2},
    "get_maritime_safety_tribunal_detail": {"tribunal_id": "1"},
    "search_acrc_special_tribunal": {"query": "행정", "display": 2},
    "get_acrc_special_tribunal_detail": {"tribunal_id": "1"},
    "search_mpm_appeal_tribunal": {"query": "공무원", "display": 2},
    "get_mpm_appeal_tribunal_detail": {"tribunal_id": "1"},
    "search_bai_preconsulting": {"query": "법", "display": 2},
    "get_bai_preconsulting_detail": {"opinion_id": "1"},

    # ===================================================================
    # 기타 (misc_tools.py)
    # ===================================================================
    "get_treaty_detail": {"treaty_id": "20396"},
    "get_ordinance_detail": {"ordinance_id": "1013533"},
    "get_ordinance_appendix_detail": {"appendix_id": "1"},

    # ===================================================================
    # 최적화 (optimized_law_tools.py)
    # ===================================================================
    "get_law_summary": {"law_name": "민법"},
    "get_law_article_detail": {"law_id": "001597", "article_no": "1"},
    "get_law_articles_summary": {"law_name": "민법"},
    "search_law_with_cache": {"query": "민법"},

    # ===================================================================
    # 지식베이스 / 상담 (additional_service_tools.py 등)
    # ===================================================================
    "search_faq": {"query": "법률", "display": 2},
    "search_qna": {"query": "법률", "display": 2},
    "search_knowledge_base": {"query": "법률", "display": 2},
    "search_counsel": {"query": "법률", "display": 2},
    "search_precedent_counsel": {"query": "법률", "display": 2},
    "search_civil_petition": {"query": "법률", "display": 2},
    "search_all_legal_documents": {"query": "민법"},
    "search_financial_laws": {"query": "은행법", "display": 2},
    "search_privacy_laws": {"query": "개인정보", "display": 2},
    "search_tax_laws": {"query": "소득세", "display": 2},
    "search_law_articles_semantic": {"mst": "001597", "query": "목적"},
    "search_english_law_articles_semantic": {"mst": "001597", "query": "purpose"},

    # ===================================================================
    # 중앙부처해석 search (ministry_interpretation_tools.py)
    # ===================================================================
    "search_moef_interpretation": {"query": "조세", "display": 2},
    "search_molit_interpretation": {"query": "건축", "display": 2},
    "search_moel_interpretation": {"query": "근로", "display": 2},
    "search_mof_interpretation": {"query": "해양", "display": 2},
    "search_mohw_interpretation": {"query": "보건", "display": 2},
    "search_moe_interpretation": {"query": "교육", "display": 2},
    "search_mote_interpretation": {"query": "환경", "display": 2},
    "search_maf_interpretation": {"query": "농업", "display": 2},
    "search_moms_interpretation": {"query": "중소", "display": 2},
    "search_sme_interpretation": {"query": "중소", "display": 2},
    "search_nfa_interpretation": {"query": "산림", "display": 2},
    "search_nts_interpretation": {"query": "세금", "display": 2},
    "search_kcs_interpretation": {"query": "관세", "display": 2},

    # ===================================================================
    # 중앙부처해석 search (ministry_interpretation_tools_extended.py)
    # ===================================================================
    "search_mois_interpretation": {"query": "행정", "display": 2},
    "search_me_interpretation": {"query": "환경", "display": 2},
    "search_mcst_interpretation": {"query": "문화", "display": 2},
    "search_moj_interpretation": {"query": "형사", "display": 2},
    "search_mogef_interpretation": {"query": "여성", "display": 2},
    "search_mofa_interpretation": {"query": "외교", "display": 2},
    "search_unikorea_interpretation": {"query": "통일", "display": 2},
    "search_moleg_interpretation": {"query": "행정", "display": 2},
    "search_mfds_interpretation": {"query": "식품", "display": 2},
    "search_mpm_interpretation": {"query": "인사", "display": 2},
    "search_kma_interpretation": {"query": "기상", "display": 2},
    "search_cha_interpretation": {"query": "문화재", "display": 2},
    "search_rda_interpretation": {"query": "농업", "display": 2},
    "search_police_interpretation": {"query": "경찰", "display": 2},
    "search_dapa_interpretation": {"query": "방위", "display": 2},
    "search_mma_interpretation": {"query": "병역", "display": 2},
    "search_fire_agency_interpretation": {"query": "소방", "display": 2},
    "search_pps_interpretation": {"query": "조달", "display": 2},
    "search_kdca_interpretation": {"query": "질병", "display": 2},
    "search_kcg_interpretation": {"query": "해양", "display": 2},
    "search_mpva_interpretation": {"query": "보훈", "display": 2},
    "search_kostat_interpretation": {"query": "통계", "display": 2},
    "search_kipo_interpretation": {"query": "특허", "display": 2},
    "search_naacc_interpretation": {"query": "반부패", "display": 2},
    "search_msit_interpretation": {"query": "과학", "display": 2},
    "search_oka_interpretation": {"query": "해외", "display": 2},

    # ===================================================================
    # 중앙부처해석 detail (공통 패턴: interpretation_id)
    # ===================================================================
    "get_moef_interpretation_detail": {"interpretation_id": "650245"},
    "get_nts_interpretation_detail": {"interpretation_id": "1"},
    "get_kcs_interpretation_detail": {"interpretation_id": "1"},
    "get_mois_interpretation_detail": {"interpretation_id": "279212"},
    "get_me_interpretation_detail": {"interpretation_id": "1"},
    "get_mcst_interpretation_detail": {"interpretation_id": "1"},
    "get_moj_interpretation_detail": {"interpretation_id": "375468"},
    "get_mogef_interpretation_detail": {"interpretation_id": "1"},
    "get_mofa_interpretation_detail": {"interpretation_id": "1"},
    "get_unikorea_interpretation_detail": {"interpretation_id": "1"},
    "get_moleg_interpretation_detail": {"interpretation_id": "1"},
    "get_mfds_interpretation_detail": {"interpretation_id": "1"},
    "get_mpm_interpretation_detail": {"interpretation_id": "1"},
    "get_kma_interpretation_detail": {"interpretation_id": "1"},
    "get_cha_interpretation_detail": {"interpretation_id": "1"},
    "get_rda_interpretation_detail": {"interpretation_id": "1"},
    "get_police_interpretation_detail": {"interpretation_id": "1"},
    "get_dapa_interpretation_detail": {"interpretation_id": "1"},
    "get_mma_interpretation_detail": {"interpretation_id": "1"},
    "get_fire_agency_interpretation_detail": {"interpretation_id": "1"},
    "get_pps_interpretation_detail": {"interpretation_id": "1"},
    "get_kdca_interpretation_detail": {"interpretation_id": "1"},
    "get_kcg_interpretation_detail": {"interpretation_id": "1"},
    "get_mpva_interpretation_detail": {"interpretation_id": "1"},
    "get_kostat_interpretation_detail": {"interpretation_id": "1"},
    "get_kipo_interpretation_detail": {"interpretation_id": "1"},
    "get_naacc_interpretation_detail": {"interpretation_id": "1"},
    "get_msit_interpretation_detail": {"interpretation_id": "1"},
    "get_oka_interpretation_detail": {"interpretation_id": "1"},
}


def _get_tool_fn(mcp_server, tool_name):
    """MCP 서버에서 도구 함수를 가져옴."""
    tm = getattr(mcp_server, "_tool_manager", None)
    if not tm or not hasattr(tm, "_tools"):
        return None
    tool = tm._tools.get(tool_name)
    return tool.fn if tool else None


def _is_error_response(text: str) -> bool:
    """TextContent.text가 에러 응답인지 판별."""
    error_indicators = (
        "오류 발생", "API 요청 실패", "Error:", "error:",
        "검색어를 입력해주세요", "Traceback",
    )
    return any(indicator in text for indicator in error_indicators)


@pytest.mark.fullcoverage
class TestToolExecution:
    """MCP 도구 함수 직접 호출 테스트 (192개 전체 커버)."""

    @pytest.mark.parametrize(
        "tool_name,kwargs",
        list(TOOL_TESTS.items()),
        ids=list(TOOL_TESTS.keys()),
    )
    def test_tool_returns_valid_response(self, mcp_server, tool_name, kwargs):
        fn = _get_tool_fn(mcp_server, tool_name)
        if fn is None:
            pytest.skip(f"Tool '{tool_name}' not registered")

        start = time.time()
        result = fn(**kwargs)
        elapsed = round(time.time() - start, 2)

        assert isinstance(result, TextContent), (
            f"{tool_name}: expected TextContent, got {type(result)}"
        )
        assert result.text, f"{tool_name}: empty text response"

        size = len(result.text)

        assert not _is_error_response(result.text), (
            f"{tool_name}: error response ({elapsed}s, {size}chars): {result.text[:200]}"
        )

        if elapsed > 5.0:
            warnings.warn(
                f"{tool_name}: slow response ({elapsed}s, {size} chars)",
                stacklevel=1,
            )
        if size < 20:
            warnings.warn(
                f"{tool_name}: very small response ({size} chars): {result.text[:50]}",
                stacklevel=1,
            )
