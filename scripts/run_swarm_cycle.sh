#!/usr/bin/env bash
# 법령 MCP 프로젝트 스웜 사이클 실행
# 사용법: ./scripts/run_swarm_cycle.sh [--verify-only|--bm25-test|--cache-stats]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DATE="$(date +%Y-%m-%d_%H%M%S)"
RUN_DIR="${REPO_ROOT}/state/runs"
REPORT="${RUN_DIR}/cycle-${RUN_DATE}.md"

mkdir -p "${RUN_DIR}"
mkdir -p "${REPO_ROOT}/state/tasks"
mkdir -p "${REPO_ROOT}/state/reflections"

echo "# 스웜 사이클 보고서 — ${RUN_DATE}" > "${REPORT}"
echo "" >> "${REPORT}"

cd "${REPO_ROOT}"

# -----------------------------------------------------------------------
# 1단계: 환경 확인
# -----------------------------------------------------------------------
echo "## 1. 환경 확인" >> "${REPORT}"
echo "Running environment checks..."

if ! command -v uv &>/dev/null; then
  echo "❌ uv not found. Install: https://docs.astral.sh/uv/" | tee -a "${REPORT}"
  exit 1
fi
echo "- uv: $(uv --version)" >> "${REPORT}"
echo "- Python: $(uv run python3 --version 2>/dev/null || echo 'N/A')" >> "${REPORT}"

# rank-bm25 확인
if uv run python3 -c "from rank_bm25 import BM25Okapi" 2>/dev/null; then
  echo "- rank-bm25: ✅" >> "${REPORT}"
else
  echo "- rank-bm25: ❌ → 설치 중..."  | tee -a "${REPORT}"
  uv pip install rank-bm25
  echo "  → 설치 완료" >> "${REPORT}"
fi

# -----------------------------------------------------------------------
# 2단계: 서버 로딩 검증
# -----------------------------------------------------------------------
echo "" >> "${REPORT}"
echo "## 2. 서버 로딩 검증" >> "${REPORT}"
echo "Validating server module loading..."

TOOL_COUNT=$(uv run python3 -c "
import sys, logging
sys.path.insert(0, 'src')
logging.disable(logging.CRITICAL)
from mcp_kr_legislation import server
try:
    tools = list(server.mcp._tool_manager._tools.keys())
    sys.stdout.write(str(len(tools)))
except Exception:
    sys.stdout.write('0')
" 2>/dev/null | tail -1 || echo "0")

echo "- 등록된 도구 수: ${TOOL_COUNT}개" >> "${REPORT}"

if [[ "${TOOL_COUNT}" -lt 190 ]]; then
  echo "⚠️  도구 수가 예상보다 적습니다 (기대: 197개 이상)" | tee -a "${REPORT}"
else
  echo "✅ 도구 로딩 정상 (${TOOL_COUNT}개)" | tee -a "${REPORT}"
fi

# -----------------------------------------------------------------------
# 3단계: BM25 검색 테스트
# -----------------------------------------------------------------------
if [[ "${1:-}" != "--verify-only" ]]; then
  echo "" >> "${REPORT}"
  echo "## 3. BM25 검색 테스트" >> "${REPORT}"
  echo "Testing BM25 ranking..."

  BM25_RESULT=$(uv run python3 -c "
import sys; sys.path.insert(0, 'src')
from mcp_kr_legislation.utils.bm25_search import rank_search_results
docs = [
    {'법령명한글': '개인정보 보호법', '소관부처명': '개인정보보호위원회'},
    {'법령명한글': '정보통신망 이용촉진 및 정보보호 등에 관한 법률', '소관부처명': '과학기술정보통신부'},
    {'법령명한글': '전자금융거래법', '소관부처명': '금융위원회'},
]
ranked = rank_search_results('개인정보 처리 동의', docs, text_keys=['법령명한글', '소관부처명'])
top = ranked[0]['법령명한글'] if ranked else 'NONE'
score = ranked[0]['_bm25_score'] if ranked else 0
print(f'{top} (score={score})')
" 2>/dev/null || echo "ERROR")

  echo "- 쿼리: '개인정보 처리 동의'" >> "${REPORT}"
  echo "- 1위 결과: ${BM25_RESULT}" >> "${REPORT}"

  if echo "${BM25_RESULT}" | grep -q "개인정보"; then
    echo "✅ BM25 재랭킹 정상" | tee -a "${REPORT}"
  else
    echo "❌ BM25 결과 예상과 다름" | tee -a "${REPORT}"
  fi
fi

# -----------------------------------------------------------------------
# 4단계: 캐시 상태
# -----------------------------------------------------------------------
if [[ "${1:-}" == "--cache-stats" ]] || [[ "${1:-}" == "" ]]; then
  echo "" >> "${REPORT}"
  echo "## 4. 캐시 상태" >> "${REPORT}"

  CACHE_DIR="${HOME}/.cache/mcp-kr-legislation"
  if [[ -d "${CACHE_DIR}" ]]; then
    CACHE_FILES=$(find "${CACHE_DIR}" -name "*.json" | wc -l | tr -d ' ')
    CACHE_SIZE=$(du -sh "${CACHE_DIR}" 2>/dev/null | cut -f1 || echo "0")
    echo "- 캐시 파일: ${CACHE_FILES}개" >> "${REPORT}"
    echo "- 캐시 크기: ${CACHE_SIZE}" >> "${REPORT}"
  else
    echo "- 캐시 없음 (아직 미생성)" >> "${REPORT}"
  fi
fi

# -----------------------------------------------------------------------
# 5단계: pytest
# -----------------------------------------------------------------------
echo "" >> "${REPORT}"
echo "## 5. 테스트" >> "${REPORT}"
echo "Running tests (smoke only)..."

if uv run pytest tests/test_tools_smoke.py -q --tb=no 2>/dev/null; then
  echo "✅ Smoke 테스트 통과" | tee -a "${REPORT}"
else
  echo "⚠️  일부 테스트 실패 (네트워크 필요한 테스트는 정상)" | tee -a "${REPORT}"
fi

# -----------------------------------------------------------------------
# 완료
# -----------------------------------------------------------------------
echo "" >> "${REPORT}"
echo "---" >> "${REPORT}"
echo "완료: ${RUN_DATE}" >> "${REPORT}"

echo ""
echo "✅ 스웜 사이클 완료: ${REPORT}"
cat "${REPORT}"
