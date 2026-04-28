"""
통폐합 도구 통합 테스트

각 통폐합 도구의 실제 API 호출 결과를 검증합니다.
- 기능 정확도 (올바른 결과 반환)
- 응답 시간
- 에러 처리 (잘못된 코드 입력)
- 필드 완전성 (필수 필드 포함 여부)

참고: @mcp.tool 데코레이터가 FunctionTool 객체를 반환하므로
      실제 함수는 tool.fn(...) 으로 직접 호출합니다.
"""

import sys
import time
import re
import traceback
from typing import Callable, Any

sys.path.insert(0, "/Users/changoo/Workspace/mcp-kr-legislation/src")
import os
os.environ.setdefault("LEGISLATION_API_KEY", "lchangoo")

# ── 모듈 임포트 ─────────────────────────────────────────────────────────────
from mcp_kr_legislation.tools.ministry_interpretation_tools import (
    search_ministry_interpretation as _smi_tool,
    get_ministry_interpretation_detail as _gmi_tool,
    MINISTRY_TARGETS,
)
from mcp_kr_legislation.tools.committee_tools import (
    search_committee_decision as _scd_tool,
    get_committee_decision_detail as _gcd_tool,
    COMMITTEE_TARGETS,
)
from mcp_kr_legislation.tools.specialized_tools import (
    search_tribunal_decision as _std_tool,
    get_tribunal_decision_detail as _gtd_tool,
    TRIBUNAL_TARGETS,
    search_treaty as _treaty_tool,
    search_university_regulation as _univ_tool,
    search_public_institution_regulation as _pi_tool,
)
from mcp_kr_legislation.tools.search_enhance_tools import (
    search_bm25 as _bm25_tool,
    explain_bm25_tokenize as _bm25_explain_tool,
)
from mcp_kr_legislation.tools.additional_service_tools import (
    search_legal_kb as _kb_tool,
    search_civil_petition as _civil_tool,
)

# FunctionTool 래퍼에서 실제 함수 추출
def unwrap(tool_or_fn):
    """@mcp.tool FunctionTool 객체에서 실제 함수를 꺼냅니다."""
    return tool_or_fn.fn if hasattr(tool_or_fn, 'fn') else tool_or_fn

smi   = unwrap(_smi_tool)    # search_ministry_interpretation
gmi   = unwrap(_gmi_tool)    # get_ministry_interpretation_detail
scd   = unwrap(_scd_tool)    # search_committee_decision
gcd   = unwrap(_gcd_tool)    # get_committee_decision_detail
std   = unwrap(_std_tool)    # search_tribunal_decision
gtd   = unwrap(_gtd_tool)    # get_tribunal_decision_detail
treaty = unwrap(_treaty_tool)
univ  = unwrap(_univ_tool)
pi    = unwrap(_pi_tool)
bm25  = unwrap(_bm25_tool)
bm25_explain = unwrap(_bm25_explain_tool)
kb    = unwrap(_kb_tool)
civil = unwrap(_civil_tool)

# ── 유틸리티 ─────────────────────────────────────────────────────────────────

PASS = "✅"; FAIL = "❌"; WARN = "⚠️"
results = []

def call(fn: Callable, *args, **kwargs) -> tuple[float, str, Exception | None]:
    start = time.time()
    try:
        result = fn(*args, **kwargs)
        elapsed = time.time() - start
        text = result.text if hasattr(result, "text") else str(result)
        return elapsed, text, None
    except Exception as e:
        elapsed = time.time() - start
        return elapsed, "", e

def check(name: str, ok: bool, detail: str = ""):
    icon = PASS if ok else FAIL
    results.append((name, ok, detail))
    print(f"  {icon} {name}" + (f"  [{detail}]" if detail else ""))

def section(title: str):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

def extract_id(text: str) -> list[str]:
    """응답 텍스트에서 ID 번호 추출"""
    # get_xxx_detail(xxx="...", decision_id="12345") 패턴
    ids = re.findall(r'(?:decision_id|interpretation_id|tribunal_id|opinion_id)="(\d+)"', text)
    if not ids:
        # ID: 12345 패턴
        ids = re.findall(r'ID[:\s]+"?(\d+)"?', text)
    return ids

# ════════════════════════════════════════════════════════════════════════════
# 1. 부처 법령해석 통합 도구
# ════════════════════════════════════════════════════════════════════════════

section("1. search_ministry_interpretation / get_ministry_interpretation_detail")

# 1-1. 기획재정부 검색 (실제 데이터가 있는 쿼리 사용)
elapsed, text, err = call(smi, ministry="moef", query="조세", display=5)
check("moef 검색 성공", err is None and len(text) > 100, f"{elapsed:.2f}s, {len(text)}chars")
check("moef 결과: 조세/해석 키워드 포함",
      err is None and any(k in text for k in ["조세", "세금", "해석", "기획재정부"]), text[:60])

# 1-2. 한글 부처명
elapsed, text2, err2 = call(smi, ministry="고용노동부", query="근로시간", display=3)
check("한글명 '고용노동부' → 코드 변환",
      err2 is None and any(k in text2 for k in ["근로", "노동", "해석"]), f"{elapsed:.2f}s")

# 1-3. 국세청 → 상세조회 체인
elapsed, text3, err3 = call(smi, ministry="nts", query="소득세", display=5)
check("nts 검색 성공", err3 is None and len(text3) > 100, f"{elapsed:.2f}s")
ids = extract_id(text3)
print(f"    nts 추출 ID: {ids[:3]}")
if ids:
    elapsed2, text4, err4 = call(gmi, ministry="nts", interpretation_id=ids[0])
    check("nts 상세조회 성공", err4 is None and len(text4) > 100, f"{elapsed2:.2f}s, {len(text4)}chars")
    check("상세조회 응답 반환 (본문 또는 원문 URL)",
          any(k in text4 for k in ["질의", "회답", "이유", "소득", "법인", "원문 보기", "상세"]), text4[:80])
    print(f"    상세 미리보기: {text4[:200]}\n")
else:
    check("nts 상세조회", False, "ID 추출 실패 — 검색 결과 없거나 포맷 불일치")

# 1-4. 잘못된 부처 코드 → 안내 메시지
_, text_err, _ = call(smi, ministry="bad_code", query="테스트")
check("잘못된 코드 → 유효 코드 목록 안내", "유효한 코드" in text_err, text_err[:80])

# 1-5. 39개 부처 매핑 확인
check("MINISTRY_TARGETS 39개", len(MINISTRY_TARGETS) == 39, f"실제: {len(MINISTRY_TARGETS)}개")

# ════════════════════════════════════════════════════════════════════════════
# 2. 위원회 결정문 통합 도구
# ════════════════════════════════════════════════════════════════════════════

section("2. search_committee_decision / get_committee_decision_detail")

# 2-1. 개인정보보호위원회
elapsed, text5, err5 = call(scd, committee="privacy", query="개인정보 수집", display=5)
check("privacy 검색 성공", err5 is None and len(text5) > 100, f"{elapsed:.2f}s, {len(text5)}chars")
check("privacy 결과: 개인정보/위원회/결정 키워드 포함",
      any(k in text5 for k in ["개인정보", "결정", "위원회", "수집"]), text5[:80])

# 2-2. 안내문이 통합 도구명을 참조하는지
check("안내문에 get_committee_decision_detail 포함",
      "get_committee_decision_detail" in text5, "")

# 2-3. 노동위원회 (필드명 '제목' 특수)
elapsed, text6, err6 = call(scd, committee="labor", query="부당해고", display=5)
check("labor 검색 성공", err6 is None and len(text6) > 50, f"{elapsed:.2f}s")

# 2-4. 한글 위원회명
elapsed, text7, err7 = call(scd, committee="금융위원회", query="금융규제", display=3)
check("한글명 '금융위원회' → 코드 변환",
      err7 is None and len(text7) > 50, f"{elapsed:.2f}s")

# 2-5. 상세조회 체인
elapsed, text8, err8 = call(scd, committee="privacy", query="처벌", display=5)
ids2 = extract_id(text8)
print(f"    privacy 추출 ID: {ids2[:3]}")
if ids2:
    elapsed2, text9, err9 = call(gcd, committee="privacy", decision_id=ids2[0])
    check("privacy 상세조회 성공", err9 is None and len(text9) > 100, f"{elapsed2:.2f}s, {len(text9)}chars")
    print(f"    상세 미리보기: {text9[:200]}\n")
else:
    check("privacy 상세조회", False, "ID 추출 실패")

# 2-6. 잘못된 위원회 코드
_, text_err2, _ = call(scd, committee="wrong", query="테스트")
check("잘못된 위원회 코드 → 유효 목록 안내", "유효한 코드" in text_err2, text_err2[:80])

# 2-7. 매핑 수 확인
check("COMMITTEE_TARGETS 12개", len(COMMITTEE_TARGETS) == 12, f"실제: {len(COMMITTEE_TARGETS)}개")

# ════════════════════════════════════════════════════════════════════════════
# 3. 특별행정심판 통합 도구
# ════════════════════════════════════════════════════════════════════════════

section("3. search_tribunal_decision / get_tribunal_decision_detail")

# 3-1. 조세심판원
elapsed, text10, err10 = call(std, tribunal="tax", query="양도소득세", display=5)
check("tax 검색 성공", err10 is None and len(text10) > 100, f"{elapsed:.2f}s, {len(text10)}chars")
check("tax 결과: 심판/사건 키워드 포함",
      any(k in text10 for k in ["양도", "소득세", "심판", "사건", "재결"]), text10[:80])

# 3-2. 해양안전심판원
elapsed, text11, err11 = call(std, tribunal="maritime", query="선박", display=5)
check("maritime 검색 성공", err11 is None and len(text11) > 100, f"{elapsed:.2f}s")

# 3-3. 상세조회 체인
elapsed, text12, err12 = call(std, tribunal="tax", query="부가가치세", display=5)
ids3 = extract_id(text12)
print(f"    tax 추출 ID: {ids3[:3]}")
if ids3:
    elapsed2, text13, err13 = call(gtd, tribunal="tax", decision_id=ids3[0])
    check("tax 상세조회 성공", err13 is None and len(text13) > 100, f"{elapsed2:.2f}s, {len(text13)}chars")
    check("심판례 본문 포함 (청구취지/주문/이유 중 하나)",
          any(k in text13 for k in ["청구취지", "주문", "이유", "재결", "사건"]), text13[:80])
    print(f"    상세 미리보기: {text13[:200]}\n")
else:
    check("tax 상세조회", False, "ID 추출 실패")

# 3-4. BAI (미오픈 API) → 정적 안내 반환
_, text_bai, _ = call(std, tribunal="bai", query="테스트")
check("bai 미오픈 정적 안내 반환", "미오픈" in text_bai, text_bai[:80])

# 3-5. 잘못된 코드
_, text_err3, _ = call(std, tribunal="xyz", query="테스트")
check("잘못된 tribunal 코드 → 유효 목록 안내", "유효한 코드" in text_err3, text_err3[:80])

# 3-6. 매핑 수 확인
check("TRIBUNAL_TARGETS 5개", len(TRIBUNAL_TARGETS) == 5, f"실제: {len(TRIBUNAL_TARGETS)}개")

# ════════════════════════════════════════════════════════════════════════════
# 4. BM25 통합 도구
# ════════════════════════════════════════════════════════════════════════════

section("4. search_bm25 (통합 BM25 검색)")

# 4-1. law
elapsed, text14, err14 = call(bm25, query="개인정보 보호", target="law", top_k=5, display=30)
check("BM25 law 성공", err14 is None and len(text14) > 50, f"{elapsed:.2f}s, {len(text14)}chars")
check("BM25 law 결과 포함", any(k in text14 for k in ["법령", "개인정보", "법", "Score"]), text14[:80])

# 4-2. prec
elapsed, text15, err15 = call(bm25, query="손해배상", target="prec", top_k=5, display=30)
check("BM25 prec 성공", err15 is None and len(text15) > 50, f"{elapsed:.2f}s")

# 4-3. admrul
elapsed, text16, err16 = call(bm25, query="행정처분", target="admrul", top_k=5, display=30)
check("BM25 admrul 성공", err16 is None and len(text16) > 50, f"{elapsed:.2f}s")

# 4-4. all (병렬 검색)
elapsed, text17, err17 = call(bm25, query="임대차", target="all", top_k=5, display=30)
check("BM25 all 성공", err17 is None and len(text17) > 50, f"{elapsed:.2f}s")
check("BM25 all 응답시간 < 15s", elapsed < 15, f"{elapsed:.2f}s")

# 4-5. 잘못된 target → 안내
_, text_err4, err_bm = call(bm25, query="테스트", target="invalid_xyz")
check("BM25 잘못된 target 처리", err_bm is None and len(text_err4) > 10, text_err4[:60])

# 4-6. explain_bm25_tokenize
elapsed, text18, err18 = call(bm25_explain, query="개인정보보호법")
check("explain_bm25_tokenize 성공", err18 is None and len(text18) > 10, f"{elapsed:.2f}s")

# ════════════════════════════════════════════════════════════════════════════
# 5. 지식베이스 통합 도구 (HTML 전용)
# ════════════════════════════════════════════════════════════════════════════

section("5. search_legal_kb / search_civil_petition (HTML 전용)")

# 5-1. source="all" → 4개 URL
elapsed, text19, err19 = call(kb, query="임대차 분쟁", source="all")
check("KB all 성공", err19 is None and len(text19) > 50, f"{elapsed:.2f}s")
url_count = text19.count("law.go.kr")
check("KB all → 4개 URL 포함", url_count >= 4, f"URL 수: {url_count}")
check("KB all: faq URL 포함", "faq" in text19.lower(), "")
check("KB all: qna URL 포함", "qna" in text19.lower(), "")
check("KB all: precCounsel URL 포함", "preccounsel" in text19.lower(), "")

# 5-2. source="faq" → 1개 URL
_, text20, err20 = call(kb, query="법률 용어", source="faq")
check("KB faq 성공", err20 is None and "faq" in text20.lower(), text20[:60])
check("KB faq → 단일 URL", text20.count("law.go.kr") == 1, f"URL 수: {text20.count('law.go.kr')}")

# 5-3. source="precedent_counsel"
_, text21, err21 = call(kb, query="계약 해제", source="precedent_counsel")
check("KB precedent_counsel 성공", err21 is None and "preccounsel" in text21.lower(), text21[:60])

# 5-4. 잘못된 source
_, text_err5, _ = call(kb, query="테스트", source="xyz")
check("KB 잘못된 source → 안내", "유효" in text_err5, text_err5[:60])

# 5-5. search_civil_petition
_, text22, err22 = call(civil, query="건축허가")
check("civil_petition 성공", err22 is None and "civil" in text22.lower(), text22[:60])

# ════════════════════════════════════════════════════════════════════════════
# 6. 기타 전문화 도구 (수정 없음 확인)
# ════════════════════════════════════════════════════════════════════════════

section("6. 기타 전문화 도구 (통폐합 미대상)")

elapsed, text23, err23 = call(treaty, query="무역협정", display=5)
check("search_treaty 성공", err23 is None and len(text23) > 50, f"{elapsed:.2f}s, {len(text23)}chars")

elapsed, text24, err24 = call(univ, query="서울대", display=5)
check("search_university_regulation 성공", err24 is None and len(text24) > 50, f"{elapsed:.2f}s")

elapsed, text25, err25 = call(pi, query="한국전력", display=5)
check("search_public_institution_regulation 성공", err25 is None and len(text25) > 50, f"{elapsed:.2f}s")

# ════════════════════════════════════════════════════════════════════════════
# 최종 리포트
# ════════════════════════════════════════════════════════════════════════════

section("최종 테스트 결과 요약")

total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print(f"\n  총 테스트: {total}개")
print(f"  통과: {PASS} {passed}개")
print(f"  실패: {FAIL} {failed}개")
print(f"  성공률: {passed/total*100:.1f}%")

if failed > 0:
    print("\n  실패한 테스트:")
    for name, ok, detail in results:
        if not ok:
            print(f"    {FAIL} {name}" + (f"  [{detail}]" if detail else ""))

print()
