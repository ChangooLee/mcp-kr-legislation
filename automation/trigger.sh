#!/bin/bash
set -euo pipefail

# MCP 한국 법령 - Cursor Agent CLI 트리거 스크립트
# openclaw 에이전트가 주기적으로 호출하여 자동 개발 세션을 시작합니다.
#
# 사용법:
#   ./automation/trigger.sh              # 기본 실행 (10분 타임아웃)
#   ./automation/trigger.sh --timeout 900  # 15분 타임아웃
#   ./automation/trigger.sh --dry-run     # 실행하지 않고 상태만 확인

PROJECT_DIR="/home/lchangoo/Workspace/mcp-kr-legislation"
LOG_DIR="$PROJECT_DIR/automation/logs"
PROMPT_FILE="$PROJECT_DIR/automation/agent_entry_prompt.md"
LOCK_FILE="/tmp/mcp-kr-legislation-agent.lock"
TIMEOUT_SEC=600
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --timeout) TIMEOUT_SEC="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 1. Lock file 확인 - 이미 실행 중인 세션이 있는지
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        log "Agent already running (PID: $PID), skipping"
        exit 0
    fi
    log "Stale lock file found, removing"
    rm -f "$LOCK_FILE"
fi

# 2. 필수 파일 존재 확인
if [ ! -f "$PROMPT_FILE" ]; then
    log "ERROR: Prompt file not found: $PROMPT_FILE"
    exit 1
fi

if ! command -v agent &> /dev/null; then
    log "ERROR: Cursor Agent CLI not installed. Run: curl https://cursor.com/install -fsS | bash"
    exit 1
fi

# 3. 인증 상태 확인
AUTH_STATUS=$(agent status 2>&1)
if echo "$AUTH_STATUS" | grep -q "Not logged in"; then
    log "ERROR: Cursor CLI not authenticated. Run: agent login"
    exit 1
fi

# 4. progress.json 상태 요약
PROGRESS_FILE="$PROJECT_DIR/automation/progress.json"
if [ -f "$PROGRESS_FILE" ]; then
    PENDING_COUNT=$(python3 -c "
import json
with open('$PROGRESS_FILE') as f:
    data = json.load(f)
pending = [t for t in data.get('tasks', []) if t.get('status') == 'pending']
print(len(pending))
" 2>/dev/null || echo "?")
    log "Pending tasks: $PENDING_COUNT"
else
    log "WARNING: progress.json not found, agent will create initial state"
fi

# 5. Dry run 모드
if [ "$DRY_RUN" = true ]; then
    log "DRY RUN - would execute agent with timeout ${TIMEOUT_SEC}s"
    log "Auth: $AUTH_STATUS"
    exit 0
fi

# 6. 로그 디렉토리 생성
mkdir -p "$LOG_DIR"
SESSION_ID=$(date +%Y%m%d_%H%M%S)
SESSION_LOG="$LOG_DIR/session_${SESSION_ID}.log"

# 7. Lock 생성
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

log "Starting automation session: $SESSION_ID"
log "Timeout: ${TIMEOUT_SEC}s"
log "Log: $SESSION_LOG"

# 8. 사전 테스트 게이트 - 현재 main이 정상인지 확인
cd "$PROJECT_DIR"
log "Running pre-session smoke test..."
SNAPSHOT_HASH=$(git rev-parse HEAD)
if ! .venv/bin/python -m pytest tests/test_tools_smoke.py -v --tb=short > "$LOG_DIR/pre_test_${SESSION_ID}.log" 2>&1; then
    log "ERROR: Pre-session smoke test FAILED. main branch may be broken. Aborting."
    log "See: $LOG_DIR/pre_test_${SESSION_ID}.log"
    exit 2
fi
log "Pre-session smoke test PASSED (snapshot: $SNAPSHOT_HASH)"

# 9. Cursor Agent CLI 실행 (headless)
EXIT_CODE=0
timeout "$TIMEOUT_SEC" agent -p --force --trust --approve-mcps \
    --model auto \
    "$(cat "$PROMPT_FILE")" \
    < /dev/null \
    > "$SESSION_LOG" 2>&1 || EXIT_CODE=$?

# 10. 사후 테스트 게이트 - 에이전트 작업 후 main이 여전히 정상인지 확인
log "Running post-session smoke test..."
if ! .venv/bin/python -m pytest tests/test_tools_smoke.py -v --tb=short > "$LOG_DIR/post_test_${SESSION_ID}.log" 2>&1; then
    log "WARNING: Post-session smoke test FAILED. Rolling back to pre-session state."
    git reset --hard "$SNAPSHOT_HASH"
    log "Rolled back to $SNAPSHOT_HASH"
    EXIT_CODE=3
fi

# 11. 완성도 점수 기록
log "Evaluating completeness score..."
.venv/bin/python automation/completeness_score.py --update 2>&1 | tail -3

# 12. 결과 기록
{
    echo ""
    echo "---"
    echo "Session ID: $SESSION_ID"
    echo "Exit code: $EXIT_CODE"
    echo "Pre-session snapshot: $SNAPSHOT_HASH"
    echo "Post-session HEAD: $(git rev-parse HEAD)"
    echo "Duration: $(date '+%Y-%m-%d %H:%M:%S')"
    case $EXIT_CODE in
        0)   echo "Status: SUCCESS" ;;
        2)   echo "Status: PRE_TEST_FAILED (session aborted)" ;;
        3)   echo "Status: POST_TEST_FAILED (rolled back to $SNAPSHOT_HASH)" ;;
        124) echo "Status: TIMEOUT (${TIMEOUT_SEC}s exceeded)" ;;
        *)   echo "Status: ERROR" ;;
    esac
} >> "$SESSION_LOG"

log "Session completed: exit_code=$EXIT_CODE"

# 13. 오래된 로그 정리 (30일 이상)
find "$LOG_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE
