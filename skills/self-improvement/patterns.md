# 자가 개선 상세 패턴

## 자가 검증 패턴

### API 호출 결과 검증

```python
def validate_api_response(response: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    API 응답 검증
    
    Returns:
        (is_valid, error_message)
    """
    # 상태 코드 확인
    if response.get("error"):
        return False, f"API 오류: {response['error']}"
    
    # 필수 필드 확인
    if "status" not in response:
        return False, "응답에 status 필드가 없습니다"
    
    # 빈 결과 확인
    if response.get("status") == "000":
        # 결과 데이터 확인
        if not response.get("law") and not response.get("prec"):
            return False, "검색 결과가 없습니다"
    
    return True, None
```

## 자동 재시도 패턴

```python
from typing import Callable, Any
import time

def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    backoff_seconds: float = 1.0
) -> Any:
    """
    백오프를 사용한 자동 재시도
    """
    for attempt in range(max_retries):
        try:
            result = func()
            
            # 결과 검증
            is_valid, error_msg = validate_api_response(result)
            if is_valid:
                return result
            
            # 마지막 시도가 아니면 재시도
            if attempt < max_retries - 1:
                logger.warning(f"검증 실패 (시도 {attempt + 1}/{max_retries}): {error_msg}")
                time.sleep(backoff_seconds * (attempt + 1))
                continue
            
            # 모든 시도 실패
            raise ValueError(f"재시도 실패: {error_msg}")
            
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"오류 발생 (시도 {attempt + 1}/{max_retries}): {e}")
                time.sleep(backoff_seconds * (attempt + 1))
                continue
            raise
    
    raise ValueError("최대 재시도 횟수 초과")
```

## 검색어 자동 개선

```python
def improve_search_query(original_query: str, results: Dict[str, Any]) -> str:
    """
    검색 결과를 분석하여 검색어 개선
    """
    # 결과가 없으면 검색어 변형 시도
    if not results.get("law") and not results.get("prec"):
        # 법령명 패턴 확인
        if "법" not in original_query and "규칙" not in original_query:
            improved = f"{original_query}법"
            logger.info(f"검색어 개선: '{original_query}' -> '{improved}'")
            return improved
        
        # 약칭 확장 시도
        abbreviation_map = {
            "개보법": "개인정보보호법",
            "근기법": "근로기준법",
            "민법": "민법",
        }
        
        if original_query in abbreviation_map:
            improved = abbreviation_map[original_query]
            logger.info(f"약칭 확장: '{original_query}' -> '{improved}'")
            return improved
    
    return original_query
```

## 파라미터 자동 조정

```python
def auto_adjust_params(
    target: str,
    params: Dict[str, Any],
    initial_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    초기 결과를 분석하여 파라미터 자동 조정
    """
    adjusted = params.copy()
    
    # 결과가 너무 많으면 display 줄이기
    if initial_results.get("totalCount", 0) > 100:
        adjusted["display"] = min(adjusted.get("display", 20), 50)
        logger.info(f"결과가 많아 display 조정: {adjusted['display']}")
    
    # 결과가 없으면 검색 범위 확대
    if initial_results.get("totalCount", 0) == 0:
        # 본문 검색으로 확장
        if "search" not in adjusted:
            adjusted["search"] = 2  # 본문 검색
            logger.info("본문 검색으로 확장")
    
    return adjusted
```

## 자가 테스트 패턴

```python
def test_api_call_with_validation(
    target: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    실제 API 호출 후 결과 검증 및 개선
    """
    from mcp_kr_legislation.apis.client import LegislationClient
    from mcp_kr_legislation.config import legislation_config
    
    client = LegislationClient(config=legislation_config)
    
    # 초기 호출
    result = client.search(target, params)
    
    # 결과 검증
    is_valid, error_msg = validate_api_response(result)
    
    if not is_valid:
        logger.warning(f"초기 호출 실패: {error_msg}")
        
        # 검색어 개선 시도
        if "query" in params:
            improved_query = improve_search_query(params["query"], result)
            if improved_query != params["query"]:
                params["query"] = improved_query
                result = client.search(target, params)
                is_valid, error_msg = validate_api_response(result)
        
        # 파라미터 조정 시도
        if not is_valid:
            adjusted_params = auto_adjust_params(target, params, result)
            if adjusted_params != params:
                result = client.search(target, adjusted_params)
                is_valid, error_msg = validate_api_response(result)
    
    if not is_valid:
        logger.error(f"최종 검증 실패: {error_msg}")
        return {"error": error_msg, "result": result}
    
    return result
```

## 결과 점수 계산

```python
def calculate_result_score(result: Dict[str, Any]) -> float:
    """
    결과 점수 계산 (0.0 ~ 1.0)
    """
    score = 0.0
    
    # 결과 개수 점수
    total_count = result.get("totalCount", 0)
    if total_count > 0:
        if total_count <= 20:
            score += 0.5  # 적절한 개수
        elif total_count <= 100:
            score += 0.3  # 다소 많음
        else:
            score += 0.1  # 너무 많음
    
    # 에러 없음 점수
    if not result.get("error"):
        score += 0.3
    
    # 데이터 품질 점수
    if result.get("law") or result.get("prec"):
        score += 0.2
    
    return min(score, 1.0)
```
