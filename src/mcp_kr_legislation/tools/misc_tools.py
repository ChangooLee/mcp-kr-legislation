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
        ordinance_id: 자치법규ID
    """
    if not ordinance_id:
        return TextContent(type="text", text="자치법규ID를 입력해주세요.")
    
    try:
        # API 요청 파라미터 - 올바른 target과 엔드포인트 사용
        params = {"target": "ordin", "ID": str(ordinance_id)}
        
        # 올바른 API 엔드포인트 사용 (lawService.do)
        oc = os.getenv("LEGISLATION_API_KEY", "lchangoo")
        url = f"http://www.law.go.kr/DRF/lawService.do?OC={oc}&target=ordin&ID={ordinance_id}&type=JSON"
        
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
        treaty_id: 조약ID
    """
    if not treaty_id:
        return TextContent(type="text", text="조약ID를 입력해주세요.")
    
    try:
        # API 요청 파라미터 - lawService.do에서 ID 파라미터 사용
        params = {"target": "trty", "ID": str(treaty_id)}
        
        # API 요청 (is_detail=True로 lawService.do 호출)
        data = _make_legislation_request("trty", params, is_detail=True)
        
        # 결과 포맷팅
        result = f"**조약 상세 정보** (ID: {treaty_id})\n"
        result += "=" * 50 + "\n\n"
        
        if 'BothTrtyService' in data:
            treaty_service = data['BothTrtyService']
            
            # 조약 기본정보
            if '조약기본정보' in treaty_service:
                basic_info = treaty_service['조약기본정보']
                result += "**📋 기본정보**\n"
                
                info_fields = {
                    '조약명(한글)': '조약명_한글',
                    '조약명(영문)': '조약명_영문', 
                    '조약번호': '조약번호',
                    '서명일자': '서명일자',
                    '발효일자': '발효일자',
                    '서명장소': '서명장소',
                    '관보게재일자': '관보게재일자',
                    '국회비준동의여부': '국회비준동의여부',
                    '국회비준동의일자': '국회비준동의일자'
                }
                
                for display_name, field_key in info_fields.items():
                    if field_key in basic_info and basic_info[field_key]:
                        result += f"- **{display_name}**: {basic_info[field_key]}\n"
            
            # 추가정보
            if '추가정보' in treaty_service:
                add_info = treaty_service['추가정보']
                result += "\n**🌏 체결 상대국**\n"
                
                if '체결대상국가한글' in add_info and add_info['체결대상국가한글']:
                    result += f"- **상대국**: {add_info['체결대상국가한글']}\n"
                if '양자조약분야명' in add_info and add_info['양자조약분야명']:
                    result += f"- **분야**: {add_info['양자조약분야명']}\n"
            
            # 조약 내용
            if '조약내용' in treaty_service and '조약내용' in treaty_service['조약내용']:
                content = treaty_service['조약내용']['조약내용']
                if content:
                    result += f"\n**📄 조약 전문**\n{content[:500]}{'...' if len(content) > 500 else ''}\n"
            
            # 첨부파일
            if '첨부파일' in treaty_service:
                file_info = treaty_service['첨부파일']
                if file_info.get('첨부파일명'):
                    result += f"\n**📎 첨부파일**: {file_info['첨부파일명']}\n"
                    
        else:
            result += "조약 정보를 찾을 수 없습니다.\n\n"
        
        result += "\n" + "=" * 50 + "\n"
        
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
        appendix_id: 별표서식ID
    """
    if not appendix_id:
        return TextContent(type="text", text="별표서식ID를 입력해주세요.")
    
    try:
        # API 요청 파라미터
        params = {"target": "ordinanceAppendix", "MST": str(appendix_id)}
        url = _generate_api_url("ordinbyl", params)
        
        # API 요청
        data = _make_legislation_request("ordinbyl", params)
        
        # 결과 포맷팅
        result = f"**자치법규 별표서식 상세 정보** (ID: {appendix_id})\n"
        result += "=" * 50 + "\n\n"
        
        if data:
            # 데이터 구조에 따라 처리
            appendix_info = None
            if 'ordinanceAppendix' in data:
                appendix_data = data['ordinanceAppendix']
                appendix_info = appendix_data[0] if isinstance(appendix_data, list) else appendix_data
            elif len(data) == 1:
                key = list(data.keys())[0]
                appendix_data = data[key]
                appendix_info = appendix_data[0] if isinstance(appendix_data, list) else appendix_data
            
            if appendix_info:
                # 기본 정보 출력
                basic_fields = {
                    '별표서식명': ['별표서식명', '명칭', 'title'],
                    '별표서식ID': ['별표서식ID', 'ID', 'id'],
                    '자치법규명': ['자치법규명', 'ordinance_name'],
                    '자치단체': ['자치단체명', 'local_gov'],
                    '별표종류': ['별표종류', 'appendix_type', 'type']
                }
                
                for field_name, field_keys in basic_fields.items():
                    value = None
                    for key in field_keys:
                        if key in appendix_info and appendix_info[key]:
                            value = appendix_info[key]
                            break
                    
                    if value:
                        result += f"**{field_name}**: {value}\n"
                
                result += "\n" + "=" * 50 + "\n\n"
                
                # 별표서식 내용 출력
                content_fields = ['내용', 'content', 'text', '별표내용', 'body']
                content = None
                
                for field in content_fields:
                    if field in appendix_info and appendix_info[field]:
                        content = appendix_info[field]
                        break
                
                if content:
                    result += "**별표서식 내용:**\n\n"
                    result += str(content)
                    result += "\n\n"
                else:
                    result += "별표서식 내용을 찾을 수 없습니다.\n\n"
            else:
                result += "별표서식 정보를 찾을 수 없습니다.\n\n"
        else:
            result += "별표서식 정보를 찾을 수 없습니다.\n\n"
        
        result += "=" * 50 + "\n"
        result += f"**API URL**: {url}\n"
        
        return TextContent(type="text", text=result)
        
    except Exception as e:
        logger.error(f"자치법규 별표서식 상세조회 중 오류: {e}")
        return TextContent(type="text", text=f"자치법규 별표서식 상세조회 중 오류가 발생했습니다: {str(e)}") 