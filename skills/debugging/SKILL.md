---
name: systematic-debugging
description: 도구 실패/API 오류 발생 시 4단계 근본 원인 분석 후 수정. 증상 수정이 아닌 원인 수정. superpowers의 systematic-debugging 기반.
---

# 체계적 디버깅 (Systematic Debugging)

> 원본: [superpowers/systematic-debugging](https://github.com/obra/superpowers)
> MCP 한국 법령 프로젝트에 맞게 커스터마이징

## 핵심 원칙

```
근본 원인을 찾기 전에 수정하지 않는다.
```

## 4단계 디버깅 프로세스

### Phase 1: 증상 수집

1. **에러 메시지 정확히 읽기**
   - API 응답의 error 필드
   - HTTP 상태 코드 (404, 500 등)
   - Python traceback 전체

2. **재현 확인**
   ```bash
   # 직접 API 호출로 재현
   .venv/bin/python -c "
   from mcp_kr_legislation.apis.client import LegislationClient
   from mcp_kr_legislation.config import legislation_config
   client = LegislationClient(config=legislation_config)
   result = client.search(target='TARGET', params={'query': 'QUERY', 'type': 'JSON'})
   print(result)
   "
   ```

3. **최근 변경 확인**
   ```bash
   git diff HEAD~3 -- src/mcp_kr_legislation/tools/TARGET_TOOL.py
   ```

### Phase 2: 가설 설정

MCP 도구 실패의 일반적 원인:

| 증상 | 가능한 원인 | 확인 방법 |
|------|-----------|----------|
| 404 Not Found | target 값 오류 | 공식 가이드 샘플 URL 직접 호출 |
| 빈 응답 (totalCnt: 0) | 검색어/파라미터 문제 | 다른 검색어 시도 |
| JSON 파싱 오류 | HTML 응답 반환됨 | type=JSON 파라미터 확인 |
| 타임아웃 | API 서버 과부하 | 시간 간격 후 재시도 |
| 필드 누락 | 응답 구조 변경 | 원본 JSON 출력 비교 |

### Phase 3: 공식 가이드 검증

**반드시 공식 가이드에서 직접 확인**:

1. https://open.law.go.kr/LSO/openApi/guideList.do 접속
2. 해당 API 카테고리 선택
3. 샘플 URL 직접 클릭하여 브라우저에서 응답 확인
4. 응답 구조를 코드의 파싱 로직과 비교

```
# 샘플 URL 직접 테스트
http://www.law.go.kr/DRF/lawSearch.do?OC=test&target=TARGET&type=JSON&query=TEST
```

### Phase 4: 수정 및 재테스트

1. **한 번에 하나만 수정** - 여러 수정 동시 적용 금지
2. **최소 변경** - 문제 해결에 필요한 최소한의 수정만
3. **재테스트** - 수정 후 반드시 동일 테스트 재실행
4. **회귀 확인** - 다른 도구에 영향이 없는지 확인

```bash
# 수정 후 회귀 테스트
.venv/bin/python -m pytest tests/ -v --tb=short
```

## 3회 이상 실패 시

같은 문제에 대해 3번 이상 수정을 시도했다면:
- **멈추고** 아키텍처를 의심할 것
- progress.json에 `needs_human` 이슈로 기록
- 사용자 판단 요청

## 자동화 세션에서의 적용

agent_entry_prompt.md에서 도구 테스트 실패 시 이 스킬이 적용됨:
- Phase 1~3을 순서대로 수행
- 3회 이상 실패 시 자동으로 이슈 기록 후 다음 작업으로 이동
