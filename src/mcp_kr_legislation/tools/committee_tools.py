"""
한국 법제처 OPEN API - 위원회 결정문 도구들

개인정보보호위원회, 금융위원회, 공정거래위원회, 국민권익위원회, 노동위원회 등
다양한 위원회의 결정문 검색 및 조회 기능을 제공합니다.
"""

import logging
import json
import os
import requests  # type: ignore
from urllib.parse import urlencode
from typing import Optional, Union, Annotated
from mcp.types import TextContent

from ..server import mcp
from ..config import legislation_config

logger = logging.getLogger(__name__)

# 유틸리티 함수들 import
from .law_tools import (
    _make_legislation_request,
    _generate_api_url,
)
from ..utils.law_tools_utils import extract_total_count, format_result_guidance

def _format_committee_search_results(data: dict, target: str, search_query: str, max_results: int = 50) -> str:
    """위원회 검색 전용 결과 포맷팅 함수"""
    try:
        # 타겟별 루트 키 매핑 (실제 API 응답 구조 기준)
        target_root_map = {
            "ppc": "Ppc",
            "fsc": "Fsc", 
            "ftc": "Ftc",
            "acr": "Acr",
            "nlrc": "Nlrc",
            "ecc": "Ecc",
            "sfc": "Sfc",
            "nhrck": "Nhrck",
            "kcc": "Kcc",
            "iaciac": "Iaciac",
            "oclt": "Oclt",
            "eiac": "Eiac"
        }
        
        # 올바른 루트 키에서 데이터 추출
        root_key = target_root_map.get(target)
        if not root_key or root_key not in data:
            return f"'{search_query}'에 대한 검색 결과가 없습니다."
        
        search_data = data[root_key]
        
        # 위원회 데이터는 단수형 dict로 반환되는 경우가 많음
        committee_item = search_data.get(target, {})
        if isinstance(committee_item, dict) and committee_item:
            target_data = [committee_item]  # 배열로 통일
        elif isinstance(committee_item, list):
            target_data = committee_item  # 이미 배열인 경우
        else:
            return f"'{search_query}'에 대한 검색 결과가 없습니다."
        
        # 제한된 결과만 처리
        if isinstance(target_data, list):
            target_data = target_data[:max_results]
        
        # 타겟별 제목 키 설정
        if target == "ppc":
            # 개인정보보호위원회: 안건명이 비어있는 경우가 많으므로 대체 필드 사용
            title_keys = ['안건명', '의안명', '결정구분', '회의종류', '결정문제목']
        else:
            title_keys = ['안건명', '사건명', '제목', '의안명', '결정문제목', '위원회결정문명']
        
        # 상세 정보 필드
        detail_fields = {
            '결정문일련번호': ['결정문일련번호', '결정문ID', 'decision_id'],
            '의결일자': ['의결일', '의결일자', '회의일자', '처리일자', '결정일자'],
            '의안번호': ['의안번호', '안건번호', '사건번호'],
            '회의종류': ['회의종류', '회의구분', '결정구분']
        }
        
        results = []
        
        for idx, item in enumerate(target_data, 1):
            if not isinstance(item, dict):
                continue
                
            # 제목 찾기 - 안건명/의안명 우선, 없으면 결정문ID 기반 복합 제목
            title = None
            primary_keys = ['안건명', '의안명', '결정문제목', '사건명', '제목']
            for key in primary_keys:
                val = item.get(key, '')
                if val and str(val).strip():
                    title = str(val).strip()
                    break
            if not title:
                dec_id = item.get('결정문일련번호', '') or item.get('ID', '')
                구분 = item.get('결정구분', '')
                의결일 = item.get('의결일', '') or item.get('의결일자', '')
                if dec_id:
                    parts = [f"결정문 #{dec_id}"]
                    if 구분:
                        parts.append(구분)
                    if 의결일:
                        parts.append(의결일)
                    title = " | ".join(parts)
                else:
                    구분 = item.get('결정구분', '') or item.get('회의종류', '')
                    title = 구분 or "제목 없음"
            
            result_lines = [f"**{idx}. {title}**"]
            
            # 상세 정보 추가
            for field_name, possible_keys in detail_fields.items():
                for key in possible_keys:
                    if key in item and item[key] and str(item[key]).strip():
                        result_lines.append(f"   {field_name}: {item[key]}")
                        break
            
            # ID 정보 추가 (상세조회용)
            _target_to_committee_code = {
                "ppc": "privacy", "fsc": "financial", "ftc": "monopoly",
                "acr": "anticorruption", "nlrc": "labor", "ecc": "environment",
                "sfc": "securities", "nhrck": "human_rights", "kcc": "broadcasting",
                "iaciac": "industrial_accident", "oclt": "land", "eiac": "employment_insurance",
            }
            committee_code = _target_to_committee_code.get(target, target)
            for id_key in ['결정문일련번호', 'ID', 'id']:
                if id_key in item and item[id_key]:
                    result_lines.append(f"   상세조회: get_committee_decision_detail(committee=\"{committee_code}\", decision_id=\"{item[id_key]}\")")
                    break
                    
            results.append("\\n".join(result_lines))
        
        total_count = search_data.get('totalCnt', len(target_data))
        
        return f"**'{search_query}' 검색 결과** (총 {total_count}건)\\n\\n" + "\\n\\n".join(results)
        
    except Exception as e:
        logger.error(f"위원회 검색 결과 포맷팅 오류: {e}")
        return f"검색 결과 처리 중 오류가 발생했습니다: {str(e)}"

def _format_committee_detail(data: dict, target: str, decision_id: str, url: str) -> str:
    """위원회 결정문 상세조회 결과 포맷팅"""
    if not data:
        return f"결정문 상세 정보를 찾을 수 없습니다.\\n\\nAPI URL: {url}"
    
    # 위원회별 상세조회 응답 구조 매핑
    service_key_map = {
        "ppc": "PpcService",
        "fsc": "FscService", 
        "ftc": "FtcService",
        "acr": "AcrService",
        "nlrc": "NlrcService",
        "ecc": "EccService",
        "sfc": "SfcService",
        "nhrck": "NhrckService",
        "kcc": "KccService",
        "iaciac": "IaciacService",
        "oclt": "OcltService",
        "eiac": "EiacService"
    }
    
    service_key = service_key_map.get(target, "Law")
    
    if service_key in data:
        service_data = data[service_key]
        result = f"**위원회 결정문 상세정보** (ID: {decision_id})\\n"
        result += "=" * 50 + "\\n\\n"
        
        if isinstance(service_data, dict):
            # 구조화된 데이터인 경우
            for key, value in service_data.items():
                if isinstance(value, str) and value.strip():
                    result += f"**{key}:**\\n{value}\\n\\n"
                elif isinstance(value, dict):
                    result += f"**{key}:**\\n"
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str) and sub_value.strip():
                            result += f"  - {sub_key}: {sub_value}\\n"
                    result += "\\n"
        else:
            result += f"**결정문 내용:**\\n{str(service_data)}\\n\\n"
            
        result += f"\\n**API URL:** {url}"
        return result
        
    elif "Law" in data:
        # Law 키로 반환된 경우 (오류 메시지 등)
        law_content = data["Law"]
        if isinstance(law_content, str):
            if "없습니다" in law_content or "확인" in law_content:
                return f"결정문을 찾을 수 없습니다: {law_content}\\n\\n**해결방법:**\\n- 올바른 결정문 ID를 확인하세요\\n- 검색 결과에서 'id' 또는 '결정문일련번호' 필드값을 사용하세요\\n\\nAPI URL: {url}"
            else:
                return f"**위원회 결정문 상세정보** (ID: {decision_id})\\n{'=' * 50}\\n\\n{law_content}\\n\\nAPI URL: {url}"
    
    # 알 수 없는 구조
    available_keys = list(data.keys())
    return f"상세조회 응답 구조를 인식할 수 없습니다.\\n\\n**사용 가능한 키들:** {available_keys}\\n\\nAPI URL: {url}"

# ===========================================
# 위원회 결정문 도구들 (통합 2개)
# ===========================================

# 위원회 코드 → (API 타겟, 한글명) 매핑
COMMITTEE_TARGETS: dict[str, tuple[str, str]] = {
    "privacy":             ("ppc",    "개인정보보호위원회"),
    "financial":           ("fsc",    "금융위원회"),
    "monopoly":            ("ftc",    "공정거래위원회"),
    "anticorruption":      ("acr",    "국민권익위원회"),
    "labor":               ("nlrc",   "노동위원회"),
    "environment":         ("ecc",    "중앙환경분쟁조정위원회"),
    "securities":          ("sfc",    "증권선물위원회"),
    "human_rights":        ("nhrck",  "국가인권위원회"),
    "broadcasting":        ("kcc",    "방송통신위원회"),
    "industrial_accident": ("iaciac", "산업재해보상보험재심사위원회"),
    "land":                ("oclt",   "중앙토지수용위원회"),
    "employment_insurance":("eiac",   "고용보험심사위원회"),
}

_COMMITTEE_NAME_TO_CODE: dict[str, str] = {v[1]: k for k, v in COMMITTEE_TARGETS.items()}

_COMMITTEE_LIST = "\n".join(
    f"  {code}: {name}" for code, (_, name) in COMMITTEE_TARGETS.items()
)


def _resolve_committee(committee: str) -> tuple[str, str] | None:
    key = committee.strip().lower()
    if key in COMMITTEE_TARGETS:
        return COMMITTEE_TARGETS[key]
    code = _COMMITTEE_NAME_TO_CODE.get(committee.strip())
    if code:
        return COMMITTEE_TARGETS[code]
    return None


@mcp.tool(name="search_committee_decision", description=f"""위원회 결정문을 검색합니다. 12개 위원회를 단일 도구로 지원합니다.

매개변수:
- committee: 위원회 코드 (필수). 아래 목록 참조.
- query: 검색어
- display: 결과 개수 (기본 20, 최대 100)
- page: 페이지 번호
- sort: 정렬 (lasc=명오름차순, ldes=명내림차순, dasc=날짜오름차순, ddes=날짜내림차순)

위원회 코드 목록:
{_COMMITTEE_LIST}

사용 예시:
  search_committee_decision(committee="privacy", query="개인정보 수집")
  search_committee_decision(committee="labor", query="부당해고", display=50)
  search_committee_decision(committee="financial", query="금융규제")

상세조회: 결과의 결정문일련번호(ID)로 get_committee_decision_detail 호출""")
def search_committee_decision(
    committee: Annotated[str, "위원회 코드 (예: privacy, labor, financial)"],
    query: Annotated[Optional[str], "검색어"] = None,
    display: Annotated[int, "결과 개수 (최대 100)"] = 20,
    page: Annotated[int, "페이지 번호"] = 1,
    sort: Annotated[Optional[str], "정렬 (lasc/ldes/dasc/ddes)"] = None,
) -> TextContent:
    resolved = _resolve_committee(committee)
    if not resolved:
        valid = ", ".join(COMMITTEE_TARGETS.keys())
        return TextContent(type="text", text=f"알 수 없는 위원회 코드: '{committee}'\n유효한 코드: {valid}")

    target, committee_name = resolved
    search_query = (query or "").strip()
    if not search_query:
        return TextContent(type="text", text="검색어를 입력해주세요.")

    params: dict = {"query": search_query, "search": 2, "display": min(display, 100), "page": page}
    if sort:
        params["sort"] = sort

    try:
        data = _make_legislation_request(target, params, use_cache=True)
        result = _format_committee_search_results(data, target, search_query, display)
        result += format_result_guidance(extract_total_count(data), search_query)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"{committee_name} 결정문 검색 중 오류: {str(e)}")


@mcp.tool(name="get_committee_decision_detail", description=f"""위원회 결정문 상세내용을 조회합니다.

매개변수:
- committee: 위원회 코드 (search_committee_decision의 committee 파라미터와 동일)
- decision_id: 결정문일련번호 (search_committee_decision 결과의 결정문일련번호 또는 ID 필드값)

위원회 코드 목록:
{_COMMITTEE_LIST}

⚠️ 주의: 'id' 필드(1,2,3...)가 아닌 '결정문일련번호' 필드값을 사용하세요.

사용 예시:
  get_committee_decision_detail(committee="privacy", decision_id="6173")
  get_committee_decision_detail(committee="labor", decision_id="123456")""")
def get_committee_decision_detail(
    committee: Annotated[str, "위원회 코드 (예: privacy, labor, financial)"],
    decision_id: Annotated[Union[str, int], "결정문일련번호 (search_committee_decision 결과의 ID)"],
) -> TextContent:
    resolved = _resolve_committee(committee)
    if not resolved:
        valid = ", ".join(COMMITTEE_TARGETS.keys())
        return TextContent(type="text", text=f"알 수 없는 위원회 코드: '{committee}'\n유효한 코드: {valid}")

    target, committee_name = resolved
    params = {"ID": str(decision_id)}
    try:
        data = _make_legislation_request(target, params, is_detail=True, use_cache=True)
        url = _generate_api_url(target, params, is_detail=True)
        result = _format_committee_detail(data, target, str(decision_id), url)
        return TextContent(type="text", text=result)
    except Exception as e:
        return TextContent(type="text", text=f"{committee_name} 결정문 상세조회 중 오류: {str(e)}")


