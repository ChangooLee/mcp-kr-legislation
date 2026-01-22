#!/usr/bin/env python3
"""
MCP 도구 품질 검증 - 실제 API 호출 테스트

이 스크립트는 모든 주요 API target에 대해 실제 HTTP 요청을 보내 검증합니다.

기능:
1. Referer 헤더 포함 확인
2. JSON 응답 파싱 검증
3. 데이터 존재 여부 (totalCnt > 0 또는 items 존재)
4. 검색/상세조회 모두 테스트
5. 실패한 API 목록 및 원인 분류
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import requests

# 기본 설정
OC = "lchangoo"
SEARCH_BASE_URL = "http://www.law.go.kr/DRF/lawSearch.do"
SERVICE_BASE_URL = "http://www.law.go.kr/DRF/lawService.do"
HEADERS = {"Referer": "https://open.law.go.kr/"}
TIMEOUT = 15

# 테스트 케이스 정의
# 형식: (target, test_type, params, description)
# test_type: "search" or "detail"
LIVE_TEST_CASES: List[Tuple[str, str, Dict[str, Any], str]] = [
    # === 핵심 법령 검색 ===
    ("law", "search", {"query": "개인정보"}, "현행법령 검색"),
    ("law", "detail", {"MST": "248613"}, "현행법령 상세"),
    ("elaw", "search", {"query": "act"}, "영문법령 검색"),
    ("eflaw", "search", {"query": "민법"}, "시행일법령 검색"),
    
    # === 판례/해석례 ===
    ("prec", "search", {"query": "계약"}, "판례 검색"),
    ("detc", "search", {"query": "위헌"}, "헌재결정례 검색"),
    ("expc", "search", {"query": "병역법"}, "법령해석례 검색"),
    ("decc", "search", {"query": "행정"}, "행정심판례 검색"),
    
    # === 위원회 결정문 ===
    ("ppc", "search", {"query": "개인정보"}, "개인정보보호위원회"),
    ("fsc", "search", {"query": "금융"}, "금융위원회"),
    ("ftc", "search", {"query": "공정"}, "공정거래위원회"),
    ("acr", "search", {}, "국민권익위원회"),
    ("nlrc", "search", {"query": "노동"}, "노동위원회"),
    ("ecc", "search", {"query": "환경"}, "환경분쟁조정위원회"),
    ("sfc", "search", {"query": "증권"}, "증권선물위원회"),
    ("nhrck", "search", {"query": "인권"}, "국가인권위원회"),
    ("kcc", "search", {"query": "방송"}, "방송통신위원회"),
    ("iaciac", "search", {"query": "산재"}, "산재심사위원회"),
    ("oclt", "search", {"query": "토지"}, "중앙토지수용위원회"),
    ("eiac", "search", {"query": "고용"}, "고용보험심사위원회"),
    
    # === 행정규칙/자치법규 ===
    ("admrul", "search", {"query": "지침"}, "행정규칙 검색"),
    ("ordin", "search", {"query": "조례"}, "자치법규 검색"),
    
    # === 조약/기타 ===
    ("trty", "search", {"query": "무역"}, "조약 검색"),
    ("lstrm", "search", {"query": "계약"}, "법령용어 검색"),
    
    # === 중앙부처해석 (주요 부처) ===
    ("moefCgmExpc", "search", {"query": "세금"}, "기획재정부 해석"),
    ("molitCgmExpc", "search", {"query": "건설"}, "국토교통부 해석"),
    ("moelCgmExpc", "search", {"query": "근로"}, "고용노동부 해석"),
    ("ntsCgmExpc", "search", {"query": "소득"}, "국세청 해석"),
    ("moisCgmExpc", "search", {"query": "지방"}, "행정안전부 해석"),
    ("mndCgmExpc", "search", {"query": "병역"}, "국방부 해석"),  # 이전에 404 발생
    
    # === 특별행정심판 ===
    ("ttSpecialDecc", "search", {"query": "조세"}, "조세심판원"),
    ("kmstSpecialDecc", "search", {"query": "해양"}, "해양안전심판원"),
    
    # === 맞춤형 ===
    ("couseLs", "search", {"vcode": "01"}, "맞춤법령"),
    ("couseAdmrul", "search", {"vcode": "01"}, "맞춤행정규칙"),
]


def test_api(
    target: str,
    test_type: str,
    params: Dict[str, Any],
    description: str
) -> Dict[str, Any]:
    """단일 API 테스트 실행"""
    result = {
        "target": target,
        "type": test_type,
        "description": description,
        "success": False,
        "http_status": None,
        "is_json": False,
        "total_count": 0,
        "has_data": False,
        "error": None,
        "response_time_ms": 0,
    }
    
    # URL 및 파라미터 구성
    base_url = SERVICE_BASE_URL if test_type == "detail" else SEARCH_BASE_URL
    full_params = {"OC": OC, "target": target, "type": "JSON"}
    full_params.update(params)
    
    try:
        start_time = time.time()
        response = requests.get(base_url, params=full_params, headers=HEADERS, timeout=TIMEOUT)
        result["response_time_ms"] = int((time.time() - start_time) * 1000)
        result["http_status"] = response.status_code
        
        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            return result
        
        # JSON 파싱 시도
        try:
            data = response.json()
            result["is_json"] = True
        except json.JSONDecodeError:
            result["error"] = "JSON 파싱 실패 (HTML 응답?)"
            return result
        
        # 데이터 존재 여부 확인
        # 다양한 응답 구조 처리
        total_count = 0
        has_data = False
        
        for key in data:
            if isinstance(data[key], dict):
                # totalCnt 필드 확인
                if "totalCnt" in data[key]:
                    total_count = int(data[key]["totalCnt"])
                
                # 데이터 리스트 확인
                for list_key in data[key]:
                    if isinstance(data[key][list_key], list) and len(data[key][list_key]) > 0:
                        has_data = True
                        break
                    elif isinstance(data[key][list_key], dict) and data[key][list_key]:
                        has_data = True
                        break
        
        result["total_count"] = total_count
        result["has_data"] = has_data or total_count > 0
        result["success"] = result["has_data"] or result["is_json"]  # JSON 응답이면 기본 성공
        
        if not result["has_data"] and total_count == 0:
            result["error"] = "0건 반환 (검색어/파라미터 확인 필요)"
        
    except requests.exceptions.Timeout:
        result["error"] = "타임아웃"
    except requests.exceptions.ConnectionError:
        result["error"] = "연결 실패"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def run_all_tests() -> Dict[str, Any]:
    """모든 테스트 실행"""
    print("=" * 60)
    print("MCP 도구 품질 검증 - 실제 API 호출 테스트")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    results = []
    success_count = 0
    warning_count = 0
    fail_count = 0
    
    for idx, (target, test_type, params, description) in enumerate(LIVE_TEST_CASES, 1):
        print(f"[{idx}/{len(LIVE_TEST_CASES)}] {description} ({target})...", end=" ")
        
        result = test_api(target, test_type, params, description)
        results.append(result)
        
        if result["success"] and result["has_data"]:
            print(f"✅ 성공 (HTTP {result['http_status']}, {result['total_count']}건, {result['response_time_ms']}ms)")
            success_count += 1
        elif result["success"] and not result["has_data"]:
            print(f"⚠️ 경고 (HTTP {result['http_status']}, 0건, {result['response_time_ms']}ms)")
            warning_count += 1
        else:
            print(f"❌ 실패: {result['error']}")
            fail_count += 1
        
        # API 호출 간격
        time.sleep(0.3)
    
    # 결과 요약
    print()
    print("=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"총 테스트: {len(LIVE_TEST_CASES)}개")
    print(f"✅ 성공: {success_count}개")
    print(f"⚠️ 경고 (0건): {warning_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"성공률: {success_count / len(LIVE_TEST_CASES) * 100:.1f}%")
    print()
    
    # 실패한 API 목록
    failed = [r for r in results if not r["success"]]
    if failed:
        print("❌ 실패한 API 목록:")
        for r in failed:
            print(f"  - {r['target']} ({r['description']}): {r['error']}")
        print()
    
    # 경고 API 목록
    warned = [r for r in results if r["success"] and not r["has_data"]]
    if warned:
        print("⚠️ 0건 반환 API 목록 (파라미터 조정 필요):")
        for r in warned:
            print(f"  - {r['target']} ({r['description']})")
        print()
    
    # 결과 저장
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total": len(LIVE_TEST_CASES),
        "success": success_count,
        "warning": warning_count,
        "fail": fail_count,
        "success_rate": f"{success_count / len(LIVE_TEST_CASES) * 100:.1f}%",
        "results": results,
    }
    
    return summary


def test_referer_header():
    """Referer 헤더 유무에 따른 응답 차이 테스트"""
    print()
    print("=" * 60)
    print("Referer 헤더 영향 테스트")
    print("=" * 60)
    
    test_targets = [
        ("mndCgmExpc", "국방부 해석 (이전 404 발생)"),
        ("moefCgmExpc", "기획재정부 해석"),
        ("law", "현행법령"),
    ]
    
    for target, desc in test_targets:
        url = f"{SEARCH_BASE_URL}?OC={OC}&target={target}&type=JSON&query=테스트"
        
        # Referer 없이 요청
        try:
            resp_no_referer = requests.get(url, timeout=10)
            status_no_referer = resp_no_referer.status_code
        except:
            status_no_referer = "오류"
        
        # Referer 있이 요청
        try:
            resp_with_referer = requests.get(url, headers=HEADERS, timeout=10)
            status_with_referer = resp_with_referer.status_code
        except:
            status_with_referer = "오류"
        
        print(f"{desc} ({target}):")
        print(f"  - Referer 없음: HTTP {status_no_referer}")
        print(f"  - Referer 있음: HTTP {status_with_referer}")
        print()


def test_detail_api():
    """상세조회 API 테스트 (lawService.do)"""
    print()
    print("=" * 60)
    print("상세조회 API 테스트 (lawService.do)")
    print("=" * 60)
    
    # 먼저 검색으로 실제 ID 획득
    print("1. 법령해석례 검색으로 실제 ID 획득...")
    search_url = f"{SEARCH_BASE_URL}?OC={OC}&target=expc&type=JSON&query=병역법"
    resp = requests.get(search_url, headers=HEADERS, timeout=10)
    
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("Expc", {}).get("expc", [])
        if isinstance(items, dict):
            items = [items]
        
        if items:
            first_item = items[0]
            real_id = first_item.get("법령해석례일련번호", first_item.get("해석례일련번호", ""))
            case_no = first_item.get("안건번호", "")
            
            print(f"   첫 번째 결과:")
            print(f"   - 안건번호: {case_no}")
            print(f"   - 법령해석례일련번호 (실제 ID): {real_id}")
            print()
            
            # 실제 ID로 상세조회 테스트
            if real_id:
                print(f"2. 실제 ID ({real_id})로 상세조회 테스트...")
                detail_url = f"{SERVICE_BASE_URL}?OC={OC}&target=expc&ID={real_id}&type=JSON"
                resp = requests.get(detail_url, headers=HEADERS, timeout=10)
                print(f"   HTTP 상태: {resp.status_code}")
                if resp.status_code == 200:
                    try:
                        detail_data = resp.json()
                        print(f"   JSON 파싱: 성공")
                        print(f"   응답 키: {list(detail_data.keys())}")
                    except:
                        print(f"   JSON 파싱: 실패 (HTML 응답?)")
                print()
            
            # 잘못된 ID (안건번호)로 상세조회 테스트
            if case_no:
                print(f"3. 잘못된 ID (안건번호: {case_no})로 상세조회 테스트...")
                wrong_url = f"{SERVICE_BASE_URL}?OC={OC}&target=expc&ID={case_no}&type=JSON"
                resp = requests.get(wrong_url, headers=HEADERS, timeout=10)
                print(f"   HTTP 상태: {resp.status_code}")
                print(f"   ※ 안건번호를 ID로 사용하면 오류 발생!")
                print()


if __name__ == "__main__":
    # Referer 헤더 영향 테스트
    test_referer_header()
    
    # 상세조회 API 테스트
    test_detail_api()
    
    # 전체 테스트 실행
    summary = run_all_tests()
    
    # 결과 파일 저장
    output_file = "test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"결과가 {output_file}에 저장되었습니다.")
