"""
한국 법제처 OPEN API - 기타 도구들

자치법규, 조약 등 법령 외 기타 분류 도구들을 제공합니다.
"""

import logging
import json
import os
import requests
from urllib.parse import urlencode
from typing import Optional, Union, Annotated
from mcp.types import TextContent

from ..server import mcp
from ..config import legislation_config

logger = logging.getLogger(__name__)

# 유틸리티 함수들 import (law_tools로 변경)
from .law_tools import (
    _make_legislation_request,
    _generate_api_url,
    _format_search_results
)

# ===========================================
# 기타 도구들 (자치법규, 조약 등)
# ===========================================

@mcp.tool(name="get_ordinance_detail", description="""자치법규 상세내용을 조회합니다.

매개변수:
- ordinance_id: 자치법규ID - search_local_ordinance 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_ordinance_detail(ordinance_id="123456")""")
def get_ordinance_detail(ordinance_id: Union[str, int]) -> TextContent:
    """자치법규 상세내용 조회

    Args:
        ordinance_id: 자치법규일련번호(MST) - search_local_ordinance 결과의 '자치법규일련번호' 필드값 사용
    """
    if not ordinance_id:
        return TextContent(type="text", text="자치법규일련번호를 입력해주세요.")

    try:
        # MST 파라미터로 조회 (ID= 는 지원 안 됨, MST= 사용)
        oc = os.getenv("LEGISLATION_OC", os.getenv("LEGISLATION_API_KEY", "lchangoo"))
        url = f"http://www.law.go.kr/DRF/lawService.do?OC={oc}&target=ordin&MST={ordinance_id}&type=JSON"
        
        # API 요청 - 직접 requests 사용 (Referer 헤더 필수)
        headers = {"Referer": "https://open.law.go.kr/"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # 결과 포맷팅
        result = f"**자치법규 상세 정보** (ID: {ordinance_id})\n"
        result += "=" * 50 + "\n\n"
        
        if 'LawService' in data and data['LawService']:
            law_service = data['LawService']
            
            # 자치법규 기본정보 확인
            if '자치법규기본정보' in law_service:
                basic_info = law_service['자치법규기본정보']
                
                # 기본 정보 출력
                basic_fields = {
                    '자치법규명': '자치법규명',
                    '자치법규ID': '자치법규ID',
                    '공포일자': '공포일자',
                    '시행일자': '시행일자',
                    '자치단체': '지자체기관명',
                    '공포번호': '공포번호',
                    '담당부서': '담당부서명'
                }
                
                for field_name, field_key in basic_fields.items():
                    if field_key in basic_info and basic_info[field_key]:
                        result += f"**{field_name}**: {basic_info[field_key]}\n"
                
                result += "\n" + "=" * 50 + "\n\n"
                
                # 조문 내용 출력
                if '조문' in law_service and law_service['조문']:
                    조문_data = law_service['조문']
                    if '조' in 조문_data and 조문_data['조']:
                        result += "**조문 내용:**\n\n"
                        for 조 in 조문_data['조']:
                            if '조제목' in 조 and '조내용' in 조:
                                result += f"**{조['조제목']}**\n"
                                result += f"{조['조내용']}\n\n"
                    else:
                        result += "조문 내용을 찾을 수 없습니다.\n\n"
                else:
                    result += "조문 내용을 찾을 수 없습니다.\n\n"
                
                # 부칙 정보 출력
                if '부칙' in law_service and law_service['부칙']:
                    부칙_data = law_service['부칙']
                    if '부칙내용' in 부칙_data and 부칙_data['부칙내용']:
                        result += "**부칙:**\n"
                        result += f"{부칙_data['부칙내용']}\n\n"
            else:
                result += "자치법규 기본정보를 찾을 수 없습니다.\n\n"
        else:
            result += "자치법규 정보를 찾을 수 없습니다.\n\n"
        
        result += "=" * 50 + "\n"
        result += f"**API URL**: {url}\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"자치법규 상세조회 중 오류: {e}")
        return TextContent(type="text", text=f"자치법규 상세조회 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_treaty_detail", description="""조약의 상세내용을 조회합니다.

매개변수:
- treaty_id: 조약ID - search_treaty 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_treaty_detail(treaty_id="123456")""")
def get_treaty_detail(treaty_id: Union[str, int]) -> TextContent:
    """조약 상세내용 조회

    Args:
        treaty_id: 조약일련번호 - search_treaty 결과의 '조약일련번호' 필드값 사용
    """
    if not treaty_id:
        return TextContent(type="text", text="조약일련번호를 입력해주세요.")

    try:
        # 조약 상세 API(lawService.do)는 JSON 미지원 → 검색 API로 상세정보 취득
        params = {"조약일련번호": str(treaty_id), "display": 1}
        data = _make_legislation_request("trty", params, is_detail=False, use_cache=True)

        trty_list = []
        if "TrtySearch" in data:
            raw = data["TrtySearch"].get("Trty", [])
            trty_list = raw if isinstance(raw, list) else ([raw] if raw else [])

        if not trty_list:
            # 조약일련번호로 검색이 안 될 경우 조약번호 등으로 재시도
            params2 = {"query": str(treaty_id), "display": 5}
            data2 = _make_legislation_request("trty", params2, use_cache=True)
            if "TrtySearch" in data2:
                raw2 = data2["TrtySearch"].get("Trty", [])
                trty_list = raw2 if isinstance(raw2, list) else ([raw2] if raw2 else [])
            # ID 일치 항목 필터
            trty_list = [t for t in trty_list if str(t.get("조약일련번호", "")) == str(treaty_id)] or trty_list[:1]

        if not trty_list:
            return TextContent(type="text", text=f"조약일련번호 {treaty_id}에 해당하는 조약을 찾을 수 없습니다.")

        t = trty_list[0]
        result = f"**조약 상세 정보** (일련번호: {treaty_id})\n\n"
        field_map = [
            ("조약명", "조약명"),
            ("조약번호", "조약번호"),
            ("조약구분명", "조약 구분"),
            ("서명일자", "서명일자"),
            ("발효일자", "발효일자"),
            ("관보게제일자", "관보게재일자"),
            ("국가번호", "국가번호"),
        ]
        for api_key, label in field_map:
            val = t.get(api_key, "")
            if val:
                result += f"**{label}**: {val}\n"

        detail_link = t.get("조약상세링크", "")
        if detail_link:
            result += f"\n**전문 보기**: https://www.law.go.kr{detail_link.replace('type=HTML', 'type=HTML')}\n"
            result += "\n> 조약 전문은 법제처 상세 링크에서 확인할 수 있습니다.\n"

        return TextContent(type="text", text=result)

    except Exception as e:
        logger.error(f"조약 상세조회 중 오류: {e}")
        return TextContent(type="text", text=f"조약 상세조회 중 오류가 발생했습니다: {str(e)}")

@mcp.tool(name="get_ordinance_appendix_detail", description="""자치법규 별표서식 상세내용을 조회합니다.

매개변수:
- appendix_id: 별표서식ID - search_ordinance_appendix 도구의 결과에서 'ID' 필드값 사용

사용 예시: get_ordinance_appendix_detail(appendix_id="123456")""")
def get_ordinance_appendix_detail(appendix_id: Union[str, int]) -> TextContent:
    """자치법규 별표서식 상세내용 조회

    Args:
        appendix_id: 별표일련번호 - search_ordinance_appendix 결과의 '별표일련번호' 필드값 사용
    """
    if not appendix_id:
        return TextContent(type="text", text="별표일련번호를 입력해주세요.")

    try:
        # 검색 API로 해당 별표 정보 가져오기 (ID= 파라미터로 직접 조회)
        params = {"별표일련번호": str(appendix_id), "display": 1}
        data = _make_legislation_request("ordinbyl", params, use_cache=True)

        items = []
        if "licBylSearch" in data:
            raw = data["licBylSearch"].get("ordinbyl", [])
            items = raw if isinstance(raw, list) else ([raw] if raw else [])

        if not items:
            # 별표일련번호 직접 검색이 안 되면 ID로 재시도
            params2 = {"query": str(appendix_id), "display": 10}
            data2 = _make_legislation_request("ordinbyl", params2, use_cache=True)
            if "licBylSearch" in data2:
                raw2 = data2["licBylSearch"].get("ordinbyl", [])
                items = [i for i in (raw2 if isinstance(raw2, list) else [raw2]) if str(i.get("별표일련번호", "")) == str(appendix_id)]

        if not items:
            return TextContent(type="text", text=f"별표일련번호 {appendix_id}에 해당하는 별표서식을 찾을 수 없습니다.")

        item = items[0]
        result = f"**자치법규 별표서식 상세 정보** (별표일련번호: {appendix_id})\n\n"
        field_map = [
            ("별표명", "별표명"),
            ("별표종류", "별표종류"),
            ("관련자치법규명", "관련 자치법규"),
            ("지자체기관명", "지자체"),
            ("공포일자", "공포일자"),
            ("공포번호", "공포번호"),
            ("제개정구분명", "제개정 구분"),
        ]
        for api_key, label in field_map:
            val = item.get(api_key, "")
            if val:
                result += f"**{label}**: {val}\n"

        detail_link = item.get("별표자치법규상세링크", "")
        file_link = item.get("별표서식파일링크", "")
        if detail_link:
            result += f"\n**상세 보기**: https://www.law.go.kr{detail_link}\n"
        if file_link:
            result += f"**서식 파일**: https://www.law.go.kr{file_link}\n"

        result += "\n> 별표서식 본문은 상세 링크에서 확인할 수 있습니다.\n"
        return TextContent(type="text", text=result)

    except Exception as e:
        logger.error(f"자치법규 별표서식 상세조회 중 오류: {e}")
        return TextContent(type="text", text=f"자치법규 별표서식 상세조회 중 오류가 발생했습니다: {str(e)}")