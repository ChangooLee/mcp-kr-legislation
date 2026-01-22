"""
법제처 OPEN API 테스트 케이스 정의

각 API별 target, 파라미터, 예상 필드를 정의합니다.
test_regression.py에서 import하여 사용합니다.
"""

from typing import Dict, Any, List

# 테스트 케이스 구조
# {
#     "api_name": {
#         "target": "target_value",
#         "endpoint": "search" | "service",
#         "params": {"query": "...", "display": 5},
#         "expected_fields": ["필드1", "필드2"],
#         "category": "법령" | "판례" | "위원회결정문" | ...
#     }
# }

TEST_CASES: Dict[str, Dict[str, Any]] = {
    # ===========================================
    # 법령 카테고리
    # ===========================================
    "law": {
        "target": "law",
        "endpoint": "search",
        "params": {"query": "개인정보보호법", "display": 5},
        "expected_fields": ["법령명", "법령ID"],
        "category": "법령"
    },
    "eflaw": {
        "target": "eflaw",
        "endpoint": "search",
        "params": {"query": "민법", "display": 5},
        "expected_fields": ["법령명", "법령ID"],
        "category": "법령"
    },
    "elaw": {
        "target": "elaw",
        "endpoint": "search",
        "params": {"query": "act", "display": 5},
        "expected_fields": ["법령명", "법령ID"],
        "category": "법령"
    },
    "lsHstInf": {
        "target": "lsHstInf",
        "endpoint": "search",
        "params": {"query": "개인정보보호법", "display": 5},
        "expected_fields": ["법령명"],
        "category": "법령"
    },
    "lsStmd": {
        "target": "lsStmd",
        "endpoint": "search",
        "params": {"query": "개인정보보호법", "display": 5},
        "expected_fields": ["법령명"],
        "category": "법령"
    },
    "oldAndNew": {
        "target": "oldAndNew",
        "endpoint": "search",
        "params": {"query": "개인정보보호법", "display": 5},
        "expected_fields": ["법령명"],
        "category": "법령"
    },
    "thdCmp": {
        "target": "thdCmp",
        "endpoint": "search",
        "params": {"query": "개인정보보호법", "display": 5},
        "expected_fields": ["법령명"],
        "category": "법령"
    },
    "lsAbrv": {
        "target": "lsAbrv",
        "endpoint": "search",
        "params": {"query": "개인정보보호법", "display": 5},
        "expected_fields": ["법령명"],
        "category": "법령"
    },
    "datDel": {
        "target": "datDel",
        "endpoint": "search",
        "params": {"query": "법령", "display": 5},
        "expected_fields": ["법령명"],
        "category": "법령"
    },
    "oneview": {
        "target": "oneview",
        "endpoint": "search",
        "params": {"query": "개인정보보호법", "display": 5},
        "expected_fields": ["법령명"],
        "category": "법령"
    },
    "licbyl": {
        "target": "licbyl",
        "endpoint": "search",
        "params": {"query": "개인정보보호법", "display": 5},
        "expected_fields": ["법령명"],
        "category": "법령"
    },
    "lnkLs": {
        "target": "lnkLs",
        "endpoint": "search",
        "params": {"query": "개인정보보호법", "display": 5},
        "expected_fields": ["법령명"],
        "category": "법령"
    },
    
    # ===========================================
    # 행정규칙 카테고리
    # ===========================================
    "admrul": {
        "target": "admrul",
        "endpoint": "search",
        "params": {"query": "규칙", "display": 5},
        "expected_fields": ["행정규칙명"],
        "category": "행정규칙"
    },
    "admrulOldAndNew": {
        "target": "admrulOldAndNew",
        "endpoint": "search",
        "params": {"query": "규칙", "display": 5},
        "expected_fields": ["행정규칙명"],
        "category": "행정규칙"
    },
    "admbyl": {
        "target": "admbyl",
        "endpoint": "search",
        "params": {"query": "규칙", "display": 5},
        "expected_fields": ["행정규칙명"],
        "category": "행정규칙"
    },
    
    # ===========================================
    # 자치법규 카테고리
    # ===========================================
    "ordinfd": {
        "target": "ordinfd",
        "endpoint": "search",
        "params": {"query": "조례", "display": 5},
        "expected_fields": ["자치법규명"],
        "category": "자치법규"
    },
    "lnkOrd": {
        "target": "lnkOrd",
        "endpoint": "search",
        "params": {"query": "조례", "display": 5},
        "expected_fields": ["자치법규명"],
        "category": "자치법규"
    },
    "ordinbyl": {
        "target": "ordinbyl",
        "endpoint": "search",
        "params": {"query": "조례", "display": 5},
        "expected_fields": ["자치법규명"],
        "category": "자치법규"
    },
    
    # ===========================================
    # 판례 카테고리
    # ===========================================
    "prec": {
        "target": "prec",
        "endpoint": "search",
        "params": {"query": "계약", "display": 5},
        "expected_fields": ["사건명", "판례일련번호"],
        "category": "판례"
    },
    "detc": {
        "target": "detc",
        "endpoint": "search",
        "params": {"query": "위헌", "display": 5},
        "expected_fields": ["사건명", "판례일련번호"],
        "category": "판례"
    },
    "expc": {
        "target": "expc",
        "endpoint": "search",
        "params": {"query": "법령해석", "display": 5},
        "expected_fields": ["사건명"],
        "category": "판례"
    },
    "decc": {
        "target": "decc",
        "endpoint": "search",
        "params": {"query": "행정심판", "display": 5},
        "expected_fields": ["사건명"],
        "category": "판례"
    },
    
    # ===========================================
    # 위원회결정문 카테고리
    # ===========================================
    "ppc": {
        "target": "ppc",
        "endpoint": "search",
        "params": {"query": "개인정보", "display": 5},
        "expected_fields": ["결정문명", "결정문일련번호"],
        "category": "위원회결정문"
    },
    "eiac": {
        "target": "eiac",
        "endpoint": "search",
        "params": {"query": "고용보험", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    "ftc": {
        "target": "ftc",
        "endpoint": "search",
        "params": {"query": "공정거래", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    "acr": {
        "target": "acr",
        "endpoint": "search",
        "params": {"query": "국민권익", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    "fsc": {
        "target": "fsc",
        "endpoint": "search",
        "params": {"query": "금융", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    "nlrc": {
        "target": "nlrc",
        "endpoint": "search",
        "params": {"query": "노동", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    "kcc": {
        "target": "kcc",
        "endpoint": "search",
        "params": {"query": "방송통신", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    "iaciac": {
        "target": "iaciac",
        "endpoint": "search",
        "params": {"query": "산업재해", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    "oclt": {
        "target": "oclt",
        "endpoint": "search",
        "params": {"query": "토지수용", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    "ecc": {
        "target": "ecc",
        "endpoint": "search",
        "params": {"query": "환경", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    "sfc": {
        "target": "sfc",
        "endpoint": "search",
        "params": {"query": "증권", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    "nhrck": {
        "target": "nhrck",
        "endpoint": "search",
        "params": {"query": "인권", "display": 5},
        "expected_fields": ["결정문명"],
        "category": "위원회결정문"
    },
    
    # ===========================================
    # 조약 카테고리
    # ===========================================
    "trty": {
        "target": "trty",
        "endpoint": "search",
        "params": {"query": "조약", "display": 5},
        "expected_fields": ["조약명"],
        "category": "조약"
    },
    
    # ===========================================
    # 학칙·공단·공공기관 카테고리
    # ===========================================
    "pi": {
        "target": "pi",
        "endpoint": "search",
        "params": {"query": "학칙", "display": 5},
        "expected_fields": ["기관명"],
        "category": "학칙·공단·공공기관"
    },
    
    # ===========================================
    # 법령용어 카테고리
    # ===========================================
    "lstrm": {
        "target": "lstrm",
        "endpoint": "search",
        "params": {"query": "법률", "display": 5},
        "expected_fields": ["용어명"],
        "category": "법령용어"
    },
    
    # ===========================================
    # 맞춤형 카테고리
    # ===========================================
    "couseLs": {
        "target": "couseLs",
        "endpoint": "search",
        "params": {"query": "개인정보", "display": 5},
        "expected_fields": ["법령명"],
        "category": "맞춤형"
    },
    "couseAdmrul": {
        "target": "couseAdmrul",
        "endpoint": "search",
        "params": {"query": "규칙", "display": 5},
        "expected_fields": ["행정규칙명"],
        "category": "맞춤형"
    },
    "couseOrdin": {
        "target": "couseOrdin",
        "endpoint": "search",
        "params": {"query": "조례", "display": 5},
        "expected_fields": ["자치법규명"],
        "category": "맞춤형"
    },
    
    # ===========================================
    # 법령정보 지식베이스 카테고리
    # ===========================================
    "lstrmAI": {
        "target": "lstrmAI",
        "endpoint": "search",
        "params": {"query": "법률", "display": 5},
        "expected_fields": ["용어명"],
        "category": "법령정보 지식베이스"
    },
    "dlytrm": {
        "target": "dlytrm",
        "endpoint": "search",
        "params": {"query": "일상", "display": 5},
        "expected_fields": ["용어명"],
        "category": "법령정보 지식베이스"
    },
    "lstrmRlt": {
        "target": "lstrmRlt",
        "endpoint": "search",
        "params": {"query": "법률", "display": 5},
        "expected_fields": ["용어명"],
        "category": "법령정보 지식베이스"
    },
    "dlytrmRlt": {
        "target": "dlytrmRlt",
        "endpoint": "search",
        "params": {"query": "일상", "display": 5},
        "expected_fields": ["용어명"],
        "category": "법령정보 지식베이스"
    },
    "lstrmRltJo": {
        "target": "lstrmRltJo",
        "endpoint": "search",
        "params": {"query": "법률", "display": 5},
        "expected_fields": ["용어명"],
        "category": "법령정보 지식베이스"
    },
    "joRltLstrm": {
        "target": "joRltLstrm",
        "endpoint": "search",
        "params": {"query": "조문", "display": 5},
        "expected_fields": ["조문"],
        "category": "법령정보 지식베이스"
    },
    "lsRlt": {
        "target": "lsRlt",
        "endpoint": "search",
        "params": {"query": "개인정보보호법", "display": 5},
        "expected_fields": ["법령명"],
        "category": "법령정보 지식베이스"
    },
    
    # ===========================================
    # 중앙부처 1차 해석 카테고리
    # ===========================================
    "moelCgmExpc": {
        "target": "moelCgmExpc",
        "endpoint": "search",
        "params": {"query": "고용", "display": 5},
        "expected_fields": ["해석명"],
        "category": "중앙부처 1차 해석"
    },
    "molitCgmExpc": {
        "target": "molitCgmExpc",
        "endpoint": "search",
        "params": {"query": "국토", "display": 5},
        "expected_fields": ["해석명"],
        "category": "중앙부처 1차 해석"
    },
    "moefCgmExpc": {
        "target": "moefCgmExpc",
        "endpoint": "search",
        "params": {"query": "재정", "display": 5},
        "expected_fields": ["해석명"],
        "category": "중앙부처 1차 해석"
    },
    "mofCgmExpc": {
        "target": "mofCgmExpc",
        "endpoint": "search",
        "params": {"query": "해양", "display": 5},
        "expected_fields": ["해석명"],
        "category": "중앙부처 1차 해석"
    },
    "moisCgmExpc": {
        "target": "moisCgmExpc",
        "endpoint": "search",
        "params": {"query": "행정", "display": 5},
        "expected_fields": ["해석명"],
        "category": "중앙부처 1차 해석"
    },
    "meCgmExpc": {
        "target": "meCgmExpc",
        "endpoint": "search",
        "params": {"query": "환경", "display": 5},
        "expected_fields": ["해석명"],
        "category": "중앙부처 1차 해석"
    },
    "kcsCgmExpc": {
        "target": "kcsCgmExpc",
        "endpoint": "search",
        "params": {"query": "관세", "display": 5},
        "expected_fields": ["해석명"],
        "category": "중앙부처 1차 해석"
    },
    "ntsCgmExpc": {
        "target": "ntsCgmExpc",
        "endpoint": "search",
        "params": {"query": "국세", "display": 5},
        "expected_fields": ["해석명"],
        "category": "중앙부처 1차 해석"
    },
    
    # ===========================================
    # 특별행정심판 카테고리
    # ===========================================
    "ttSpecialDecc": {
        "target": "ttSpecialDecc",
        "endpoint": "search",
        "params": {"query": "조세", "display": 5},
        "expected_fields": ["심판명"],
        "category": "특별행정심판"
    },
    "kmstSpecialDecc": {
        "target": "kmstSpecialDecc",
        "endpoint": "search",
        "params": {"query": "해양", "display": 5},
        "expected_fields": ["심판명"],
        "category": "특별행정심판"
    },
}

# 카테고리별 그룹핑
CATEGORIES = {
    "법령": ["law", "eflaw", "elaw", "lsHstInf", "lsStmd", "oldAndNew", "thdCmp", "lsAbrv", "datDel", "oneview", "licbyl", "lnkLs"],
    "행정규칙": ["admrul", "admrulOldAndNew", "admbyl"],
    "자치법규": ["ordinfd", "lnkOrd", "ordinbyl"],
    "판례": ["prec", "detc", "expc", "decc"],
    "위원회결정문": ["ppc", "eiac", "ftc", "acr", "fsc", "nlrc", "kcc", "iaciac", "oclt", "ecc", "sfc", "nhrck"],
    "조약": ["trty"],
    "학칙·공단·공공기관": ["pi"],
    "법령용어": ["lstrm"],
    "맞춤형": ["couseLs", "couseAdmrul", "couseOrdin"],
    "법령정보 지식베이스": ["lstrmAI", "dlytrm", "lstrmRlt", "dlytrmRlt", "lstrmRltJo", "joRltLstrm", "lsRlt"],
    "중앙부처 1차 해석": ["moelCgmExpc", "molitCgmExpc", "moefCgmExpc", "mofCgmExpc", "moisCgmExpc", "meCgmExpc", "kcsCgmExpc", "ntsCgmExpc"],
    "특별행정심판": ["ttSpecialDecc", "kmstSpecialDecc"],
}

def get_test_cases_by_category(category: str = None) -> Dict[str, Dict[str, Any]]:
    """카테고리별 테스트 케이스 반환"""
    if category is None:
        return TEST_CASES
    
    if category not in CATEGORIES:
        return {}
    
    return {name: TEST_CASES[name] for name in CATEGORIES[category] if name in TEST_CASES}
