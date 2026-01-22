#!/usr/bin/env python3
"""
178개 MCP 도구 전체 자동화 테스트 스크립트

사용법:
    python test_all_tools.py                    # 전체 테스트
    python test_all_tools.py --category 법령    # 카테고리별 테스트
    python test_all_tools.py --verbose          # 상세 출력
    python test_all_tools.py --fix              # 문제 발견 시 수정 제안
"""

import sys
import json
import time
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from mcp_kr_legislation.apis.client import LegislationClient
from mcp_kr_legislation.config import legislation_config


@dataclass
class TestResult:
    """테스트 결과"""
    tool_name: str
    status: str  # "success", "warning", "error"
    api_called: bool
    response_time: float
    has_data: bool
    data_count: int
    html_detected: bool
    error_message: Optional[str] = None
    sample_data: Optional[Dict] = None


# 도구별 테스트 파라미터 정의
TOOL_TEST_PARAMS: Dict[str, Dict[str, Any]] = {
    # ===== 법령 검색 =====
    "search_law": {"query": "개인정보보호법", "display": 3},
    "search_english_law": {"query": "Civil", "display": 3},
    "search_effective_law": {"query": "민법", "display": 3},
    "search_law_nickname": {"query": "개인정보", "display": 3},
    "search_deleted_law_data": {"query": "법령", "display": 3},
    "search_law_articles": {"query": "개인정보", "display": 3},
    "search_old_and_new_law": {"query": "개인정보보호법", "display": 3},
    "search_three_way_comparison": {"query": "개인정보보호법", "display": 3},
    "search_deleted_history": {"query": "법령", "display": 3},
    "search_one_view": {"query": "개인정보보호법", "display": 3},
    "search_law_system_diagram": {"query": "개인정보보호법", "display": 3},
    "search_law_change_history": {"query": "개인정보보호법", "display": 3},
    "search_daily_article_revision": {"query": "개인정보", "display": 3},
    "search_article_change_history": {"query": "개인정보", "display": 3},
    "search_law_ordinance_link": {"query": "개인정보보호법", "display": 3},
    "search_ordinance_law_link": {"query": "조례", "display": 3},
    "search_related_law": {"query": "개인정보보호법", "display": 3},
    "search_law_appendix": {"query": "개인정보보호법", "display": 3},
    "search_law_unified": {"query": "개인정보보호법", "display": 3},
    "search_law_with_cache": {"query": "은행법"},
    
    # ===== 법령 상세 =====
    "get_law_detail": {"law_id": "270351"},
    "get_law_summary": {"law_name": "개인정보보호법"},
    "get_english_law_detail": {"mst": "246569"},
    "get_english_law_summary": {"law_name": "Civil Act"},
    "get_law_article_by_key": {"mst": "270351", "article_key": "제15조"},
    "get_law_articles_range": {"mst": "270351", "start_article": 1, "end_article": 5},
    "get_law_articles_summary": {"law_id": "270351"},
    "get_law_article_detail": {"law_id": "270351", "article_no": "제15조"},
    "get_delegated_law": {"law_id": "270351"},
    "get_effective_law_articles": {"law_id": "270351"},
    "get_current_law_articles": {"law_id": "270351"},
    "get_effective_law_detail": {"law_id": "270351"},
    "get_law_appendix_detail": {"law_id": "270351"},
    "get_law_system_diagram_detail": {"law_id": "270351"},
    "get_law_system_diagram_full": {"law_id": "270351"},
    "compare_law_versions": {"law_id": "270351"},
    "compare_article_before_after": {"law_id": "270351", "article_no": "15"},
    
    # ===== 판례 =====
    "search_precedent": {"query": "계약", "display": 3},
    "search_constitutional_court": {"query": "위헌", "display": 3},
    "search_legal_interpretation": {"query": "법제처", "display": 3},
    "search_administrative_trial": {"query": "행정처분", "display": 3},
    "get_precedent_detail": {"precedent_id": "612389"},
    "get_constitutional_court_detail": {"case_id": "177507"},
    "get_legal_interpretation_detail": {"case_id": "313393"},
    "get_administrative_trial_detail": {"case_id": "1"},
    
    # ===== 위원회결정문 =====
    "search_privacy_committee": {"query": "개인정보", "display": 3},
    "search_financial_committee": {"query": "금융", "display": 3},
    "search_monopoly_committee": {"query": "공정거래", "display": 3},
    "search_anticorruption_committee": {"query": "국민권익", "display": 3},
    "search_labor_committee": {"query": "노동", "display": 3},
    "search_environment_committee": {"query": "환경", "display": 3},
    "search_securities_committee": {"query": "증권", "display": 3},
    "search_human_rights_committee": {"query": "인권", "display": 3},
    "search_broadcasting_committee": {"query": "방송", "display": 3},
    "search_industrial_accident_committee": {"query": "산업재해", "display": 3},
    "search_land_tribunal": {"query": "토지", "display": 3},
    "search_employment_insurance_committee": {"query": "고용보험", "display": 3},
    "get_privacy_committee_detail": {"case_id": "9459"},
    "get_financial_committee_detail": {"case_id": "1"},
    "get_monopoly_committee_detail": {"case_id": "1"},
    "get_anticorruption_committee_detail": {"case_id": "1"},
    "get_labor_committee_detail": {"case_id": "1"},
    "get_environment_committee_detail": {"case_id": "1"},
    "get_securities_committee_detail": {"case_id": "1"},
    "get_human_rights_committee_detail": {"case_id": "1"},
    "get_broadcasting_committee_detail": {"case_id": "1"},
    "get_industrial_accident_committee_detail": {"case_id": "1"},
    "get_land_tribunal_detail": {"case_id": "1"},
    "get_employment_insurance_committee_detail": {"case_id": "1"},
    
    # ===== 행정규칙 =====
    "search_administrative_rule": {"query": "훈령", "display": 3},
    "search_administrative_rule_comparison": {"query": "훈령", "display": 3},
    "get_administrative_rule_detail": {"rule_id": "26943"},
    "get_administrative_rule_comparison_detail": {"rule_id": "26943"},
    
    # ===== 자치법규 =====
    "search_local_ordinance": {"query": "서울", "display": 3},
    "search_ordinance_appendix": {"query": "서울", "display": 3},
    "search_linked_ordinance": {"query": "서울", "display": 3},
    "get_local_ordinance_detail": {"ordinance_id": "1526175"},
    "get_ordinance_detail": {"ordinance_id": "1526175"},
    "get_ordinance_appendix_detail": {"ordinance_id": "1526175"},
    
    # ===== 조약 =====
    "search_treaty": {"query": "조약", "display": 3},
    "get_treaty_detail": {"treaty_id": "1"},
    
    # ===== 학칙/공단 =====
    "search_university_regulation": {"query": "학칙", "display": 3},
    "search_public_corporation_regulation": {"query": "공단", "display": 3},
    "search_public_institution_regulation": {"query": "공공기관", "display": 3},
    
    # ===== 특별행정심판 =====
    "search_tax_tribunal": {"query": "조세", "display": 3},
    "search_maritime_safety_tribunal": {"query": "해양", "display": 3},
    "get_tax_tribunal_detail": {"case_id": "1"},
    "get_maritime_safety_tribunal_detail": {"case_id": "1"},
    "search_anticorruption_committee_tribunal": {"query": "권익위", "display": 3},
    "search_mpm_appeal_committee": {"query": "인사", "display": 3},
    "get_anticorruption_committee_tribunal_detail": {"case_id": "1"},
    "get_mpm_appeal_committee_detail": {"case_id": "1"},
    
    # ===== 지식베이스 =====
    "search_knowledge_base": {"query": "법률", "display": 3},
    "search_faq": {"query": "법률", "display": 3},
    "search_qna": {"query": "법률", "display": 3},
    "search_counsel": {"query": "법률", "display": 3},
    "search_precedent_counsel": {"query": "판례", "display": 3},
    "search_civil_petition": {"query": "민원", "display": 3},
    
    # ===== 맞춤형 =====
    "search_custom_ordinance": {"query": "개인정보", "display": 3},
    "search_custom_ordinance_articles": {"query": "개인정보", "display": 3},
    "search_custom_precedent": {"query": "개인정보", "display": 3},
    "search_custom_law": {"query": "개인정보", "display": 3},
    "search_custom_law_articles": {"query": "개인정보", "display": 3},
    
    # ===== 법령용어 =====
    "search_legal_term": {"query": "법률", "display": 3},
    "search_legal_term_ai": {"query": "법률", "display": 3},
    "search_daily_legal_term_link": {"query": "일상", "display": 3},
    "search_daily_term": {"query": "일상", "display": 3},
    "search_legal_daily_term_link": {"query": "법률", "display": 3},
    "search_legal_term_article_link": {"query": "법률", "display": 3},
    "search_article_legal_term_link": {"query": "조문", "display": 3},
    "get_legal_term_detail": {"term_id": "1"},
    
    # ===== AI/통합 =====
    "search_legal_ai": {"query": "개인정보"},
    "search_all_legal_documents": {"query": "개인정보", "display": 3},
    "get_practical_law_guide": {"topic": "개인정보"},
    "search_law_articles_semantic": {"mst": "270351", "query": "동의"},
    "search_english_law_articles_semantic": {"mst": "246569", "query": "contract"},
    
    # ===== 금융/세무 특화 =====
    "search_financial_laws": {"query": "금융", "display": 3},
    "search_tax_laws": {"query": "세금", "display": 3},
    "search_privacy_laws": {"query": "개인정보", "display": 3},
    
    # ===== 중앙부처해석 (기존 8개) =====
    "search_moef_interpretation": {"query": "세금", "display": 3},
    "search_molit_interpretation": {"query": "국토", "display": 3},
    "search_moel_interpretation": {"query": "고용", "display": 3},
    "search_mof_interpretation": {"query": "해양", "display": 3},
    "search_mohw_interpretation": {"query": "보건", "display": 3},
    "search_moe_interpretation": {"query": "교육", "display": 3},
    "search_korea_interpretation": {"query": "한국", "display": 3},
    "search_mssp_interpretation": {"query": "중소", "display": 3},
    "get_moef_interpretation_detail": {"case_id": "140278"},
    "get_nts_interpretation_detail": {"case_id": "1"},
    "get_kcs_interpretation_detail": {"case_id": "1"},
    
    # ===== 중앙부처해석 (확장 22개) =====
    "search_mois_interpretation": {"query": "행정", "display": 3},
    "search_me_interpretation": {"query": "환경", "display": 3},
    "search_mcst_interpretation": {"query": "문화", "display": 3},
    "search_moj_interpretation": {"query": "법무", "display": 3},
    "search_mogef_interpretation": {"query": "여성", "display": 3},
    "search_mofa_interpretation": {"query": "외교", "display": 3},
    "search_unikorea_interpretation": {"query": "통일", "display": 3},
    "search_moleg_interpretation": {"query": "법제", "display": 3},
    "search_mfds_interpretation": {"query": "식품", "display": 3},
    "search_mpm_interpretation": {"query": "인사", "display": 3},
    "search_kma_interpretation": {"query": "기상", "display": 3},
    "search_cha_interpretation": {"query": "문화재", "display": 3},
    "search_rda_interpretation": {"query": "농촌", "display": 3},
    "search_police_interpretation": {"query": "경찰", "display": 3},
    "search_dapa_interpretation": {"query": "방위", "display": 3},
    "search_mma_interpretation": {"query": "병무", "display": 3},
    "search_fire_agency_interpretation": {"query": "소방", "display": 3},
    "search_oka_interpretation": {"query": "해외", "display": 3},
    "search_pps_interpretation": {"query": "조달", "display": 3},
    "search_kdca_interpretation": {"query": "질병", "display": 3},
    "search_kcg_interpretation": {"query": "해경", "display": 3},
    "search_naacc_interpretation": {"query": "감사", "display": 3},
    "search_mote_interpretation": {"query": "산업", "display": 3},
    "search_maf_interpretation": {"query": "농림", "display": 3},
    "search_moms_interpretation": {"query": "해양", "display": 3},
    "search_sme_interpretation": {"query": "중기", "display": 3},
    "search_nfa_interpretation": {"query": "소방", "display": 3},
    "search_korail_interpretation": {"query": "철도", "display": 3},
    "search_nts_interpretation": {"query": "국세", "display": 3},
    "search_kcs_interpretation": {"query": "관세", "display": 3},
    "get_mois_interpretation_detail": {"case_id": "1"},
    "get_me_interpretation_detail": {"case_id": "1"},
    "get_mcst_interpretation_detail": {"case_id": "1"},
    "get_moj_interpretation_detail": {"case_id": "1"},
    "get_mogef_interpretation_detail": {"case_id": "1"},
    "get_mofa_interpretation_detail": {"case_id": "1"},
    "get_unikorea_interpretation_detail": {"case_id": "1"},
    "get_moleg_interpretation_detail": {"case_id": "1"},
    "get_mfds_interpretation_detail": {"case_id": "1"},
    "get_mpm_interpretation_detail": {"case_id": "1"},
    "get_kma_interpretation_detail": {"case_id": "1"},
    "get_cha_interpretation_detail": {"case_id": "1"},
    "get_rda_interpretation_detail": {"case_id": "1"},
    "get_police_interpretation_detail": {"case_id": "1"},
    "get_dapa_interpretation_detail": {"case_id": "1"},
    "get_mma_interpretation_detail": {"case_id": "1"},
    "get_fire_agency_interpretation_detail": {"case_id": "1"},
    "get_oka_interpretation_detail": {"case_id": "1"},
    "get_pps_interpretation_detail": {"case_id": "1"},
    "get_kdca_interpretation_detail": {"case_id": "1"},
    "get_kcg_interpretation_detail": {"case_id": "1"},
    "get_naacc_interpretation_detail": {"case_id": "1"},
}

# 도구 카테고리 매핑
TOOL_CATEGORIES = {
    "법령검색": ["search_law", "search_english_law", "search_effective_law", "search_law_nickname", 
                "search_deleted_law_data", "search_law_articles", "search_old_and_new_law",
                "search_three_way_comparison", "search_deleted_history", "search_one_view",
                "search_law_system_diagram", "search_law_change_history", "search_daily_article_revision",
                "search_article_change_history", "search_law_ordinance_link", "search_ordinance_law_link",
                "search_related_law", "search_law_appendix", "search_law_unified", "search_law_with_cache"],
    "법령상세": ["get_law_detail", "get_law_summary", "get_english_law_detail", "get_english_law_summary",
               "get_law_article_by_key", "get_law_articles_range", "get_law_articles_summary",
               "get_law_article_detail", "get_delegated_law", "get_effective_law_articles",
               "get_current_law_articles", "get_effective_law_detail", "get_law_appendix_detail",
               "get_law_system_diagram_detail", "get_law_system_diagram_full",
               "compare_law_versions", "compare_article_before_after"],
    "판례": ["search_precedent", "search_constitutional_court", "search_legal_interpretation",
            "search_administrative_trial", "get_precedent_detail", "get_constitutional_court_detail",
            "get_legal_interpretation_detail", "get_administrative_trial_detail"],
    "위원회": ["search_privacy_committee", "search_financial_committee", "search_monopoly_committee",
              "search_anticorruption_committee", "search_labor_committee", "search_environment_committee",
              "search_securities_committee", "search_human_rights_committee", "search_broadcasting_committee",
              "search_industrial_accident_committee", "search_land_tribunal", "search_employment_insurance_committee"],
    "행정규칙": ["search_administrative_rule", "search_administrative_rule_comparison",
                "get_administrative_rule_detail", "get_administrative_rule_comparison_detail"],
    "자치법규": ["search_local_ordinance", "search_ordinance_appendix", "search_linked_ordinance",
               "get_local_ordinance_detail", "get_ordinance_detail", "get_ordinance_appendix_detail"],
    "중앙부처해석": [t for t in TOOL_TEST_PARAMS.keys() if "interpretation" in t],
}


def detect_html_tags(text: str) -> bool:
    """HTML 태그 감지"""
    if not text:
        return False
    html_pattern = re.compile(r'<[^>]+>')
    return bool(html_pattern.search(str(text)))


def check_response_for_html(data: Any, path: str = "") -> List[str]:
    """응답 데이터에서 HTML 태그가 있는 필드 찾기"""
    html_fields = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, str) and detect_html_tags(value):
                html_fields.append(current_path)
            elif isinstance(value, (dict, list)):
                html_fields.extend(check_response_for_html(value, current_path))
    elif isinstance(data, list):
        for i, item in enumerate(data[:3]):  # 처음 3개만 확인
            current_path = f"{path}[{i}]"
            html_fields.extend(check_response_for_html(item, current_path))
    
    return html_fields


def extract_items_from_response(result: Dict[str, Any]) -> Tuple[List[Any], int]:
    """API 응답에서 실제 데이터 항목 추출"""
    if not result:
        return [], 0
    
    # 알려진 응답 구조 매핑
    response_mappings = [
        ("LawSearch", "law"),
        ("PrecSearch", "prec"),
        ("DetcSearch", "Detc"),
        ("ExpcSearch", "expc"),
        ("Expc", "expc"),
        ("Decc", "decc"),
        ("Ppc", "ppc"),
        ("AdmRulSearch", "admrul"),
        ("OrdinSearch", "law"),
        ("OrdinSearch", "ordinfd"),
        ("CgmExpc", "cgmExpc"),
        ("CgmExpcSearch", "CgmExpc"),
        ("DeccSearch", "Decc"),
    ]
    
    for outer_key, inner_key in response_mappings:
        if outer_key in result:
            inner = result[outer_key]
            if isinstance(inner, dict) and inner_key in inner:
                items = inner[inner_key]
                if isinstance(items, list):
                    return items, len(items)
                elif isinstance(items, dict):
                    return [items], 1
    
    # 직접 데이터가 있는 경우
    for key in ["법령", "Law", "items", "data"]:
        if key in result:
            value = result[key]
            if isinstance(value, list):
                return value, len(value)
            elif isinstance(value, dict):
                return [value], 1
    
    return [], 0


def test_tool_via_api(tool_name: str, params: Dict[str, Any], client: LegislationClient) -> TestResult:
    """도구를 API 클라이언트로 테스트"""
    start_time = time.time()
    
    try:
        # 도구 이름에서 API target 추론
        target_mapping = {
            "search_law": "law",
            "search_english_law": "elaw",
            "search_effective_law": "eflaw",
            "search_precedent": "prec",
            "search_constitutional_court": "detc",
            "search_legal_interpretation": "expc",
            "search_administrative_trial": "decc",
            "search_privacy_committee": "ppc",
            "search_financial_committee": "fsc",
            "search_monopoly_committee": "ftc",
            "search_administrative_rule": "admrul",
            "search_local_ordinance": "ordin",
            "search_treaty": "trty",
            "search_legal_term": "lstrm",
            "search_moef_interpretation": "moefCgmExpc",
            "search_molit_interpretation": "molitCgmExpc",
            "search_moel_interpretation": "moelCgmExpc",
            "search_mof_interpretation": "mofCgmExpc",
            "search_tax_tribunal": "ttSpecialDecc",
            "search_maritime_safety_tribunal": "kmstSpecialDecc",
        }
        
        # target 결정
        target = None
        for prefix, t in target_mapping.items():
            if tool_name.startswith(prefix):
                target = t
                break
        
        if not target:
            # 도구 이름에서 추론 시도
            if "interpretation" in tool_name:
                # 중앙부처 해석 도구
                ministry_map = {
                    "mois": "moisCgmExpc", "me": "meCgmExpc", "mcst": "mcstCgmExpc",
                    "moj": "mojCgmExpc", "mogef": "mogefCgmExpc", "mofa": "mofaCgmExpc",
                    "unikorea": "unikoreaCgmExpc", "moleg": "molegCgmExpc",
                    "mfds": "mfdsCgmExpc", "mpm": "mpmCgmExpc", "kma": "kmaCgmExpc",
                    "cha": "chaCgmExpc", "rda": "rdaCgmExpc", "police": "policeCgmExpc",
                    "dapa": "dapaCgmExpc", "mma": "mmaCgmExpc", "fire": "nfaCgmExpc",
                    "oka": "okaCgmExpc", "pps": "ppsCgmExpc", "kdca": "kdcaCgmExpc",
                    "kcg": "kcgCgmExpc", "naacc": "naaccCgmExpc", "nts": "ntsCgmExpc",
                    "kcs": "kcsCgmExpc", "mote": "moteCgmExpc", "maf": "mafCgmExpc",
                    "moms": "momsCgmExpc", "sme": "smeCgmExpc", "nfa": "nfaCgmExpc",
                    "korail": "korailCgmExpc",
                }
                for key, val in ministry_map.items():
                    if key in tool_name:
                        target = val
                        break
        
        # API 호출
        if target:
            result = client.search(target=target, params=params)
        else:
            # API 호출 불가능한 경우 (상세 조회 등)
            result = None
        
        response_time = time.time() - start_time
        
        if result is None:
            return TestResult(
                tool_name=tool_name,
                status="warning",
                api_called=False,
                response_time=response_time,
                has_data=False,
                data_count=0,
                html_detected=False,
                error_message="API target 매핑 없음 (상세 조회 도구일 수 있음)"
            )
        
        # 데이터 추출
        items, count = extract_items_from_response(result)
        
        # HTML 태그 감지
        html_fields = check_response_for_html(result)
        
        # 샘플 데이터
        sample = items[0] if items else None
        
        status = "success"
        if count == 0:
            status = "warning"
        if html_fields:
            status = "warning"
        
        return TestResult(
            tool_name=tool_name,
            status=status,
            api_called=True,
            response_time=response_time,
            has_data=count > 0,
            data_count=count,
            html_detected=len(html_fields) > 0,
            error_message=f"HTML in: {html_fields[:3]}" if html_fields else None,
            sample_data=sample
        )
        
    except Exception as e:
        return TestResult(
            tool_name=tool_name,
            status="error",
            api_called=False,
            response_time=time.time() - start_time,
            has_data=False,
            data_count=0,
            html_detected=False,
            error_message=str(e)
        )


def run_all_tests(category: Optional[str] = None, verbose: bool = False) -> List[TestResult]:
    """전체 테스트 실행"""
    client = LegislationClient(config=legislation_config)
    results = []
    
    # 테스트할 도구 목록
    tools_to_test = TOOL_TEST_PARAMS
    
    if category:
        category_tools = TOOL_CATEGORIES.get(category, [])
        tools_to_test = {k: v for k, v in TOOL_TEST_PARAMS.items() if k in category_tools}
    
    total = len(tools_to_test)
    
    print(f"\n{'='*60}")
    print(f"MCP 도구 전체 테스트 시작")
    print(f"테스트 대상: {total}개 도구")
    print(f"{'='*60}\n")
    
    for i, (tool_name, params) in enumerate(tools_to_test.items(), 1):
        print(f"[{i}/{total}] {tool_name}...", end=" ", flush=True)
        
        result = test_tool_via_api(tool_name, params, client)
        results.append(result)
        
        # 상태 표시
        status_icon = {"success": "✅", "warning": "⚠️", "error": "❌"}[result.status]
        print(f"{status_icon} ({result.response_time:.2f}s, {result.data_count}건)")
        
        if verbose and result.error_message:
            print(f"    → {result.error_message}")
        
        # API 부하 방지
        time.sleep(0.3)
    
    return results


def print_summary(results: List[TestResult]):
    """테스트 결과 요약 출력"""
    success = sum(1 for r in results if r.status == "success")
    warning = sum(1 for r in results if r.status == "warning")
    error = sum(1 for r in results if r.status == "error")
    html_detected = sum(1 for r in results if r.html_detected)
    
    print(f"\n{'='*60}")
    print("테스트 결과 요약")
    print(f"{'='*60}")
    print(f"✅ 성공: {success}개")
    print(f"⚠️ 경고: {warning}개")
    print(f"❌ 실패: {error}개")
    print(f"🏷️ HTML 감지: {html_detected}개")
    
    if warning > 0 or error > 0:
        print(f"\n{'─'*60}")
        print("문제 있는 도구:")
        for r in results:
            if r.status in ["warning", "error"]:
                print(f"  {r.tool_name}: {r.error_message or '데이터 없음'}")
    
    if html_detected > 0:
        print(f"\n{'─'*60}")
        print("HTML 태그 정제 필요:")
        for r in results:
            if r.html_detected:
                print(f"  {r.tool_name}")


def save_results(results: List[TestResult], output_path: Path):
    """결과를 JSON 파일로 저장"""
    output_data = {
        "test_time": datetime.now().isoformat(),
        "total_tools": len(results),
        "summary": {
            "success": sum(1 for r in results if r.status == "success"),
            "warning": sum(1 for r in results if r.status == "warning"),
            "error": sum(1 for r in results if r.status == "error"),
            "html_detected": sum(1 for r in results if r.html_detected),
        },
        "results": [asdict(r) for r in results]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n결과 저장: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="MCP 도구 전체 테스트")
    parser.add_argument("--category", help="특정 카테고리만 테스트")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 출력")
    parser.add_argument("--output", "-o", help="결과 저장 경로")
    args = parser.parse_args()
    
    results = run_all_tests(category=args.category, verbose=args.verbose)
    print_summary(results)
    
    if args.output:
        save_results(results, Path(args.output))
    else:
        # 기본 저장 경로
        output_path = Path(__file__).parent / "test_results.json"
        save_results(results, output_path)


if __name__ == "__main__":
    main()
