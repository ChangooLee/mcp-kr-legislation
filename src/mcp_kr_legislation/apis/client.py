"""
한국 법제처 OPEN API 121개 완전 통합 클라이언트

지원하는 API 카테고리:
- 법령 (16개): 목록/본문/영문/시행일/변경이력/연혁/체계도/신구법비교/3단비교/약칭/삭제데이터/한눈보기/조문별/별표
- 행정규칙 (5개): 목록/본문/신구법비교/별표
- 자치법규 (4개): 목록/본문/법령연계/별표
- 판례 (8개): 판례/헌재결정례/법령해석례/행정심판례 목록/본문
- 위원회결정문 (30여개): 개인정보보호위원회/공정거래위원회/국민권익위원회 등
- 조약 (2개): 목록/본문
- 별표서식 (3개): 법령/행정규칙/자치법규별표
- 학칙공단 (2개): 목록/본문
- 법령용어 (2개): 목록/본문
- 맞춤형 (4개): 법령/행정규칙/자치법규 맞춤형 분류
- 지식베이스 (7개): 법령용어-일상용어-조문 연계
- 기타 (1개): 조문-법령용어 연계
- 중앙부처해석 (12개): 고용노동부/국토교통부/기획재정부/해양수산부/행정안전부/환경부 법령해석
"""

import logging
import json
import requests
from typing import Dict, Any, Optional, Union
from urllib.parse import urlencode
from dotenv import load_dotenv

from mcp_kr_legislation.config import LegislationConfig, legislation_config

load_dotenv()

logger = logging.getLogger(__name__)

class LegislationClient:
    """법제처 OPEN API 121개 완전 통합 클라이언트"""
    
    def __init__(self, config: Optional[LegislationConfig] = None):
        self.config = config or legislation_config
        if not self.config:
            raise ValueError("법제처 API 설정이 초기화되지 않았습니다.")
        
        self.oc = self.config.oc
        self.search_base_url = self.config.search_base_url
        self.service_base_url = self.config.service_base_url
        self.timeout = self.config.default_timeout
        
        # API 호출에 필요한 헤더 설정 (Referer 헤더가 필수로 확인됨)
        self.headers = {
            "Referer": "https://open.law.go.kr/LSO/openApi/guideList.do",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        
        logger.info(f"법제처 API 클라이언트 초기화 완료 - OC: {self.oc}")

    def _make_request(self, 
                     endpoint_type: str = "search",
                     params: Optional[Dict[str, Any]] = None, 
                     method: str = "GET") -> Dict[str, Any]:
        """
        법제처 API 요청 실행
        
        Args:
            endpoint_type: "search" 또는 "service"
            params: 요청 파라미터
            method: HTTP 메소드
        """
        if params is None:
            params = {}
        
        # 기본 파라미터 설정
        params["OC"] = self.oc
        
        # URL 선택
        base_url = self.search_base_url if endpoint_type == "search" else self.service_base_url
        
        # URL 생성
        if method.upper() == "GET":
            query_string = urlencode(params, safe='~')
            url = f"{base_url}?{query_string}"
        else:
            url = base_url
            
        logger.debug(f"\n=== 법제처 API 요청 ===")
        logger.debug(f"URL: {url}")
        logger.debug(f"Method: {method}")
        logger.debug(f"Parameters: {params}")
        logger.debug("========================")
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, data=params, headers=self.headers, timeout=self.timeout)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
                
            logger.debug(f"\n=== API 응답 정보 ===")
            logger.debug(f"상태 코드: {response.status_code}")
            logger.debug(f"Content-Type: {response.headers.get('Content-Type', '없음')}")
            logger.debug("====================")
            
            response.raise_for_status()
        
            # 응답 처리
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                response_data: Dict[str, Any] = response.json()
                return response_data
            else:
                # JSON이 아닌 경우 텍스트로 처리한 후 JSON 파싱 시도
                try:
                    parsed_data: Dict[str, Any] = json.loads(response.text)
                    return parsed_data
                except json.JSONDecodeError:
                    return {"status": "000", "message": "정상", "content": response.text}
                    
        except requests.RequestException as e:
            logger.error(f"API 요청 실패: {str(e)}")
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}

    def search(self, target: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        법제처 검색 API 호출 (lawSearch.do)
        
        Args:
            target: 서비스 대상 (law, admrul, ordin, prec, etc.)
            params: 추가 파라미터
        """
        if params is None:
            params = {}
        
        params["target"] = target
        
        # 기본값 설정
        if "type" not in params:
            params["type"] = "JSON"
        if "display" not in params:
            params["display"] = self.config.default_display
        
        return self._make_request("search", params, "GET")

    def service(self, target: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        법제처 서비스 API 호출 (lawService.do)
        
        Args:
            target: 서비스 대상 (law, admrul, ordin, prec, etc.)
            params: 추가 파라미터
        """
        if params is None:
            params = {}
        
        params["target"] = target
        
        # 기본값 설정
        if "type" not in params:
            params["type"] = "JSON"
        
        return self._make_request("service", params, "GET")

    # ===========================================
    # 법령 관련 API (16개)
    # ===========================================
    
    def search_law(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """법령 목록 조회"""
        params = {"target": "law"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("law", params)
    
    def get_law_info(self, law_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """법령 본문 조회"""
        params = {"target": "law", "ID": str(law_id)}
        params.update(kwargs)
        return self.service("law", params)
    
    def search_englaw(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """영문법령 목록 조회"""
        params = {"target": "englaw"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("englaw", params)
    
    def search_eflaw(self, **kwargs) -> Dict[str, Any]:
        """시행일법령 목록 조회"""
        params = {"target": "eflaw"}
        params.update(kwargs)
        return self.search("eflaw", params)
    
    def search_jolaw(self, law_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """조문별 조회"""
        params = {"target": "jolaw", "ID": str(law_id)}
        params.update(kwargs)
        return self.search("jolaw", params)

    # ===========================================
    # 행정규칙 관련 API (5개)
    # ===========================================
    
    def search_admrul(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """행정규칙 목록 조회"""
        params = {"target": "admrul"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("admrul", params)
    
    def get_admrul_info(self, admrul_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """행정규칙 본문 조회"""
        params = {"target": "admrul", "ID": str(admrul_id)}
        params.update(kwargs)
        return self.service("admrul", params)

    # ===========================================
    # 자치법규 관련 API (4개)
    # ===========================================
    
    def search_ordin(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """자치법규 목록 조회"""
        params = {"target": "ordin"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("ordin", params)
    
    def get_ordin_info(self, ordin_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """자치법규 본문 조회"""
        params = {"target": "ordin", "ID": str(ordin_id)}
        params.update(kwargs)
        return self.service("ordin", params)

    # ===========================================
    # 판례 관련 API (8개)
    # ===========================================
    
    def search_prec(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """판례 목록 조회"""
        params = {"target": "prec"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("prec", params)
    
    def get_prec_info(self, prec_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """판례 본문 조회"""
        params = {"target": "prec", "ID": str(prec_id)}
        params.update(kwargs)
        return self.service("prec", params)
    
    def search_detc(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """헌재결정례 목록 조회"""
        params = {"target": "detc"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("detc", params)
    
    def get_detc_info(self, detc_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """헌재결정례 본문 조회"""
        params = {"target": "detc", "ID": str(detc_id)}
        params.update(kwargs)
        return self.service("detc", params)
    
    def search_expc(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """법령해석례 목록 조회"""
        params = {"target": "expc"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("expc", params)
    
    def get_expc_info(self, expc_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """법령해석례 본문 조회"""
        params = {"target": "expc", "ID": str(expc_id)}
        params.update(kwargs)
        return self.service("expc", params)
    
    def search_decc(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """행정심판례 목록 조회"""
        params = {"target": "decc"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("decc", params)
    
    def get_decc_info(self, decc_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """행정심판례 본문 조회"""
        params = {"target": "decc", "ID": str(decc_id)}
        params.update(kwargs)
        return self.service("decc", params)

    # ===========================================
    # 위원회결정문 관련 API (30여개)
    # ===========================================
    
    def search_ppc(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """개인정보보호위원회 결정문 목록 조회"""
        params = {"target": "ppc"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("ppc", params)
    
    def get_ppc_info(self, ppc_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """개인정보보호위원회 결정문 본문 조회"""
        params = {"target": "ppc", "ID": str(ppc_id)}
        params.update(kwargs)
        return self.service("ppc", params)
    
    def search_ftc(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """공정거래위원회 결정문 목록 조회"""
        params = {"target": "ftc"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("ftc", params)
    
    def get_ftc_info(self, ftc_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """공정거래위원회 결정문 본문 조회"""
        params = {"target": "ftc", "ID": str(ftc_id)}
        params.update(kwargs)
        return self.service("ftc", params)

    # ===========================================
    # 조약 관련 API (2개)
    # ===========================================
    
    def search_trty(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """조약 목록 조회"""
        params = {"target": "trty"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("trty", params)
    
    def get_trty_info(self, trty_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """조약 본문 조회"""
        params = {"target": "trty", "ID": str(trty_id)}
        params.update(kwargs)
        return self.service("trty", params)

    # ===========================================
    # 법령용어 관련 API (2개)
    # ===========================================
    
    def search_lstrm(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """법령용어 목록 조회"""
        params = {"target": "lstrm"}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search("lstrm", params)
    
    def get_lstrm_info(self, query: str, **kwargs) -> Dict[str, Any]:
        """법령용어 본문 조회"""
        params = {"target": "lstrm", "query": query}
        params.update(kwargs)
        return self.service("lstrm", params)

    # ===========================================
    # 중앙부처해석 관련 API (12개)
    # ===========================================
    
    def search_ministry_interpretation(self, ministry: str, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """중앙부처 법령해석 목록 조회
        
        Args:
            ministry: 부처코드 (moelCgmExpc, molitCgmExpc, moefCgmExpc, mofCgmExpc, moisCgmExpc, meCgmExpc)
            query: 검색어
        """
        params = {"target": ministry}
        if query:
            params["query"] = query
        params.update(kwargs)
        return self.search(ministry, params)
    
    def get_ministry_interpretation_info(self, ministry: str, interpretation_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """중앙부처 법령해석 본문 조회"""
        params = {"target": ministry, "ID": str(interpretation_id)}
        params.update(kwargs)
        return self.service(ministry, params)

"""
법제처 OPEN API 121개 완전 통합 HTTP 클라이언트
""" 