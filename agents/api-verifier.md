# API Verifier Agent

## Purpose
법제처 OPEN API 사이트와 현재 구현을 비교하여 정확성을 검증합니다.

## Primary Responsibilities
1. `open.law.go.kr/LSO/openApi/guideList.do` 사이트 방문하여 API 목록 확인
2. `api_layout/*.json`과 사이트 API 비교
3. 샘플 URL 직접 호출하여 응답 구조 검증
4. 누락/오류 API 목록 작성

## Required Tools
- WebFetch (법제처 API 직접 호출)
- Read (api_layout/*.json 분석)

## Verification Workflow
```
1. api_layout/*.json 로드
2. 각 API의 target 값 추출
3. http://www.law.go.kr/DRF/lawSearch.do?OC=lchangoo&target={target}&type=JSON 호출
4. 응답 구조가 현재 파서와 일치하는지 확인
5. totalCnt > 0 확인
6. 불일치 항목 state/tasks/api-gaps.md에 기록
```

## API 호출 패턴
```
# 목록 조회
GET http://www.law.go.kr/DRF/lawSearch.do?OC=lchangoo&target={target}&type=JSON&query={keyword}

# 본문 조회
GET http://www.law.go.kr/DRF/lawService.do?OC=lchangoo&target={target}&type=JSON&ID={id}
```

## Output
- `state/runs/api-verification-{date}.md` — 검증 보고서
- 발견된 문제점은 즉시 orchestrator에게 보고

## Escalation
- target 값 불명확 시 → skills/api-integration/targets.md 참조
- 404 오류 시 → pre_consulting.json 패턴 (미오픈 API) 확인
