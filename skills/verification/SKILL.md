---
name: verification-before-completion
description: 도구 개발/개선 완료 선언 전 반드시 실제 API 호출 테스트를 수행하고 증거를 기록할 때 사용. superpowers의 verification-before-completion 기반.
---

# 완료 전 검증 (Verification Before Completion)

> 원본: [superpowers/verification-before-completion](https://github.com/obra/superpowers)
> MCP 한국 법령 프로젝트에 맞게 커스터마이징

## 핵심 원칙

```
검증 증거 없이 완료를 선언하지 않는다.
```

## 검증 절차

### 1. 도구 개발 완료 시

```bash
# 실제 API 호출 테스트
cd /home/lchangoo/Workspace/mcp-kr-legislation
.venv/bin/python -c "
from mcp_kr_legislation.apis.client import LegislationClient
from mcp_kr_legislation.config import legislation_config
client = LegislationClient(config=legislation_config)
result = client.search(target='TARGET_VALUE', params={'query': 'TEST_QUERY', 'type': 'JSON'})
print(result)
"
```

검증 체크리스트:
- [ ] API 호출이 에러 없이 반환되는가?
- [ ] 응답이 JSON 구조인가?
- [ ] 핵심 필드가 존재하는가?
- [ ] totalCnt > 0 인가? (0이면 검색어 조정 필요)
- [ ] 응답 크기가 적절한가?

### 2. 도구 개선 완료 시

```bash
# 기존 테스트 실행
.venv/bin/python -m pytest tests/ -v --tb=short

# 품질 게이트 실행
.venv/bin/python automation/quality_gate.py --tool TARGET_TOOL
```

검증 체크리스트:
- [ ] 기존 smoke test 전부 통과?
- [ ] 회귀 테스트 통과?
- [ ] 품질 게이트 통과?
- [ ] 기존 동작이 깨지지 않았는가?

### 3. 증거 기록

`automation/progress.json`에 반드시 기록:

```json
{
  "tool_name": {
    "tested_at": "2026-02-21",
    "status": "pass",
    "evidence": "API 호출 정상, 5건 반환, 응답 크기 2.3KB",
    "test_command": ".venv/bin/python -m pytest tests/ -v"
  }
}
```

## 금지 패턴

| 선언 | 필요한 증거 | 불충분한 것 |
|------|-----------|-----------|
| "도구 개발 완료" | 실제 API 호출 결과 | "코드 작성 완료" |
| "테스트 통과" | pytest 출력 (0 failures) | "통과할 것" |
| "버그 수정 완료" | 수정 전/후 비교 | "코드 수정함" |
| "품질 개선 완료" | quality_gate.py 결과 | "개선한 것 같음" |

## 자동화 세션에서의 적용

agent_entry_prompt.md의 Step 4에서 이 스킬이 자동 적용됨:
- 작업 후 반드시 테스트 실행
- 결과를 progress.json에 기록
- 증거 없이 status를 "completed"로 변경 금지
