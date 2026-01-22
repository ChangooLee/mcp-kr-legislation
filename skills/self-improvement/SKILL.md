---
name: self-improvement
description: API 호출 후 결과 검증 및 오류 자동 수정 패턴. 검색 결과 품질 개선, 파라미터 자동 조정, 자동 재시도 구현 시 참조.
---

# 자가 개선 가이드

API 호출 후 결과를 검증하고, 오류를 자동으로 수정하는 패턴입니다.

## 핵심 패턴

### 1. API 응답 검증

```python
def validate_api_response(response: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """API 응답 검증"""
    if response.get("error"):
        return False, f"API 오류: {response['error']}"
    
    if response.get("status") == "000":
        if not response.get("law") and not response.get("prec"):
            return False, "검색 결과가 없습니다"
    
    return True, None
```

### 2. 자동 재시도

```python
def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    backoff_seconds: float = 1.0
) -> Any:
    """백오프를 사용한 자동 재시도"""
    for attempt in range(max_retries):
        try:
            result = func()
            is_valid, error_msg = validate_api_response(result)
            if is_valid:
                return result
            # 재시도 로직
        except Exception as e:
            # 에러 처리
    raise ValueError("최대 재시도 횟수 초과")
```

### 3. 검색어 자동 개선

```python
def improve_search_query(original_query: str, results: Dict[str, Any]) -> str:
    """검색 결과를 분석하여 검색어 개선"""
    if not results.get("law") and not results.get("prec"):
        # 검색어 변형 시도
        if "법" not in original_query:
            return f"{original_query}법"
    return original_query
```

### 4. 파라미터 자동 조정

```python
def auto_adjust_params(
    target: str,
    params: Dict[str, Any],
    initial_results: Dict[str, Any]
) -> Dict[str, Any]:
    """초기 결과를 분석하여 파라미터 자동 조정"""
    adjusted = params.copy()
    
    # 결과가 너무 많으면 display 줄이기
    if initial_results.get("totalCount", 0) > 100:
        adjusted["display"] = min(adjusted.get("display", 20), 50)
    
    # 결과가 없으면 본문 검색으로 확장
    if initial_results.get("totalCount", 0) == 0:
        adjusted["search"] = 2  # 본문 검색
    
    return adjusted
```

## 유틸리티 스크립트

API 응답 검증:
```bash
python scripts/validate_response.py <response_file.json>
```

## 상세 패턴

상세 구현 코드는 [patterns.md](patterns.md) 참조.

## 주의사항

1. **API 호출 제한**: 과도한 요청 자제, 적절한 백오프 사용
2. **무한 루프 방지**: 최대 반복 횟수 제한, 조기 종료
3. **성능 고려**: 자가 개선은 필요시에만 실행, 캐시 우선 사용

## 관련 파일

- [src/mcp_kr_legislation/apis/client.py](../../src/mcp_kr_legislation/apis/client.py) - API 클라이언트
- [skills/cache-management/](../cache-management/) - 캐시 관리
