# AGENTS.md - MCP 한국 법령 프로젝트 가이드

이 문서는 코드 AI가 MCP 한국 법령 프로젝트를 효과적으로 이해하고 유지보수할 수 있도록 작성되었습니다.

## 프로젝트 개요

MCP 한국 법령은 국가법령정보센터 OPEN API를 통합한 Model Context Protocol(MCP) 서버입니다. FastMCP 프레임워크를 사용하여 법제처 API를 MCP 도구로 제공합니다.

### 주요 기능
- **원본 구분 기준 18개 JSON 파일** (모바일 제외)
- **법령 검색**: 현행법령, 시행일법령, 영문법령, 법령연혁
- **판례 검색**: 대법원 판례, 헌법재판소 결정례, 법령해석례, 행정심판례
- **위원회결정문**: 12개 위원회 결정문 검색
- **자치법규/행정규칙**: 지방자치법규 및 행정규칙 검색
- **중앙부처해석**: 법령해석 검색
- **특별행정심판**: 심판례 검색
- **지식베이스**: FAQ, Q&A, 상담, 민원사례 검색

### API 카테고리 (원본 18개 구분, 모바일 제외)
- 법령 - `api_layout/law.json`
- 행정규칙 - `api_layout/admin_rule.json`
- 자치법규 - `api_layout/local_ordinance.json`
- 판례 - `api_layout/precedent.json`
- 헌재결정례 - `api_layout/constitutional_court.json`
- 법령해석례 - `api_layout/legal_interpretation.json`
- 행정심판례 - `api_layout/administrative_appeal.json`
- 위원회 결정문 - `api_layout/committee.json`
- 조약 - `api_layout/treaty.json`
- 별표·서식 - `api_layout/appendix.json`
- 학칙·공단·공공기관 - `api_layout/school_corp.json`
- 법령용어 - `api_layout/legal_term.json`
- 맞춤형 - `api_layout/custom.json`
- 법령정보 지식베이스 - `api_layout/knowledge_base.json`
- 법령 간 관계 - `api_layout/law_relation.json`
- 지능형 법령검색 시스템 - `api_layout/intelligent_search.json`
- 중앙부처 1차 해석 - `api_layout/ministry_interpretation.json`
- 특별행정심판 - `api_layout/special_tribunal.json`

> **제외됨**: 모바일 API (별도 모바일 앱 전용)

### API Layout JSON 재생성

```bash
source .crawler_venv/bin/activate
python src/mcp_kr_legislation/utils/api_crawler.py
```

## 개발 환경 설정

### 필수 요구사항
- Python 3.10 이상 (필수)
- uv 패키지 매니저 (권장) 또는 pip
- 법제처 API 키 (LEGISLATION_API_KEY)

### 환경 설정

```bash
# Python 버전 확인
python3 --version  # 3.10 이상이어야 함

# 가상환경 생성 (uv 사용 - 권장)
uv venv
uv pip install -e .

# 또는 pip 사용
python3.10 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate  # Windows

# 패키지 설치
pip install -e .
```

### 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성:

```bash
# 법제처 API 키 (사용자 이메일 ID) - 필수
LEGISLATION_API_KEY=lchangoo  # 또는 이메일 주소

# API 기본 URL (기본값 사용 권장)
LEGISLATION_SEARCH_URL=http://www.law.go.kr/DRF/lawSearch.do
LEGISLATION_SERVICE_URL=http://www.law.go.kr/DRF/lawService.do

# MCP 서버 설정
HOST=0.0.0.0
PORT=8002
TRANSPORT=stdio  # 또는 http
LOG_LEVEL=INFO
MCP_SERVER_NAME=mcp-kr-legislation
```

> **참고**: 법제처 API는 무료이며, 이메일 주소만으로 사용 가능합니다. `LEGISLATION_API_KEY`에는 이메일 주소를 입력하거나, `@` 앞 부분만 입력해도 됩니다.

## 프로젝트 구조

```
src/mcp_kr_legislation/
├── __init__.py              # 패키지 초기화
├── server.py                # FastMCP 서버 메인 로직
├── config.py                # 설정 관리 (LegislationConfig, MCPConfig)
├── apis/                    # 법제처 API 클라이언트
│   ├── client.py           # LegislationClient (기본 클라이언트)
│   ├── law_api.py          # 법령 API
│   └── legislation_api.py  # 자치법규 API
├── tools/                   # MCP 도구 정의 (14개 모듈)
│   ├── law_tools.py        # 법령 관련 도구
│   ├── precedent_tools.py  # 판례 관련 도구
│   ├── committee_tools.py  # 위원회결정문 도구
│   ├── administrative_rule_tools.py  # 행정규칙 도구
│   ├── custom_tools.py     # 맞춤형 도구
│   ├── legal_term_tools.py # 법령용어 도구
│   ├── linkage_tools.py    # 연계 도구
│   ├── ministry_interpretation_tools.py  # 중앙부처해석 도구
│   ├── optimized_law_tools.py  # 최적화 도구 (캐싱)
│   ├── ai_tools.py         # AI 기반 도구
│   └── ...
├── utils/                   # 유틸리티 함수
│   ├── ctx_helper.py       # 컨텍스트 처리 및 데이터 변환
│   ├── law_tools_utils.py  # 법령 도구 유틸리티
│   ├── data_processor.py   # 데이터 처리
│   ├── api_crawler.py      # API 정보 크롤러 (Playwright)
│   ├── api_md_to_json.py   # Markdown → JSON 변환
│   ├── api_layout/         # 구분별 API JSON 파일
│   │   ├── law.json        # 법령 API
│   │   ├── precedent.json  # 판례 API
│   │   ├── committee.json  # 위원회결정문 API
│   │   └── ...             # 기타 카테고리
│   └── korean_law_api_complete_guide.md  # 전체 API 가이드 (참고용)
├── registry/               # 도구 레지스트리
│   ├── tool_registry.py
│   └── initialize_registry.py
```

## 주요 아키텍처

### FastMCP 구조

```mermaid
graph TD
    A[FastMCP Server] --> B[legislation_lifespan]
    B --> C[LegislationContext 생성]
    C --> D[전역 컨텍스트 저장]
    C --> E[API 모듈 초기화]
    E --> F[law_api, legislation_api]
    A --> G[Tool 등록]
    G --> H[tools/*.py 모듈]
    H --> I[@mcp.tool 데코레이터]
    I --> J[with_context 호출]
    J --> K[전역 컨텍스트 fallback]
```

### 전역 컨텍스트 Fallback 메커니즘

- **목적**: streamable-http에서 ctx 주입이 없어도 동작하도록
- **구현**: `server.py`의 전역 `legislation_context` 변수
- **사용**: `ctx_helper.py`의 `with_context()` 함수에서 자동 fallback
- **참고**: [skills/context-handling.md](skills/context-handling.md)

### API 패턴

**법제처 API 구조**:
- **목록 조회**: `lawSearch.do?target={value}`
- **본문 조회**: `lawService.do?target={value}`
- **target 파라미터**: 50개 이상의 고유한 값으로 기능 구분

**예시**:
- `target=law`: 현행법령 목록/본문
- `target=prec`: 판례 목록/본문
- `target=ppc`: 개인정보보호위원회 결정문

**참고**: [docs/api-master-guide.md](docs/api-master-guide.md)

### 캐시 시스템 (계획)

- **legislation_cache/**: 법령/판례/위원회결정문 캐시 (런타임 생성)
- **knowledge_graph/**: 지식 그래프 데이터 (계획)
- **경로**: `src/mcp_kr_legislation/utils/data/`
- **참고**: [skills/cache-management.md](skills/cache-management.md)

## 테스트 지침

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/test_specific.py

# 커버리지 포함
pytest --cov=src/mcp_kr_legislation

# 특정 테스트만 실행
pytest -k "test_function_name"
```

### API 직접 테스트

```bash
# 실제 API 호출 테스트
python -c "
from mcp_kr_legislation.apis.client import LegislationClient
from mcp_kr_legislation.config import legislation_config
client = LegislationClient(config=legislation_config)
result = client.search('law', {'query': '개인정보보호법'})
print(result)
"
```

### Linting 및 타입 체크

```bash
# Ruff로 linting
ruff check src/

# 자동 수정
ruff check --fix src/

# Black으로 포맷팅
black src/

# MyPy 타입 체크
mypy src/
```

### 커밋 전 체크리스트

- [ ] `ruff check src/` 통과
- [ ] `mypy src/` 통과 (타입 에러 없음)
- [ ] `pytest` 통과
- [ ] 새로운 tool 추가 시 `tool_modules` 리스트에 추가 확인
- [ ] 실제 API 호출 테스트 완료

## PR 및 커밋 가이드

### 커밋 메시지 형식

```
<type>: <간단한 설명>

<상세 설명 (선택)>

예시:
fix: Add global context fallback for streamable-http support
docs: Improve API documentation structure
feat: Add new tool for precedent search
```

### PR 제목 형식

```
[<카테고리>] <제목>

예시:
[Fix] streamable-http에서 tools/call 실패 문제 해결
[Docs] API 가이드 문서 구조 개선
[Feature] 판례 캐싱 기능 추가
```

### PR 전 체크리스트

- [ ] 모든 테스트 통과
- [ ] Linting 통과
- [ ] 타입 체크 통과
- [ ] README.md 업데이트 (필요시)
- [ ] 변경사항 설명 명확히 작성
- [ ] 실제 API 호출 테스트 완료

## 주요 개발 워크플로우

### 새로운 Tool 추가

1. `src/mcp_kr_legislation/tools/` 디렉토리에 새 파일 생성 또는 기존 파일 수정
2. `@mcp.tool` 데코레이터 사용
3. `with_context(None, ...)` 패턴 사용 (ctx 파라미터 제거)
4. `server.py`의 `tool_modules` 리스트에 모듈명 추가
5. 실제 API 호출 테스트

**참고**: [skills/tool-development.md](skills/tool-development.md)

### 새로운 API 통합

1. `src/mcp_kr_legislation/apis/` 디렉토리에 새 API 클래스 생성
2. `LegislationClient` 사용
3. `server.py`의 `LegislationContext`에 추가
4. Tool에서 사용

**참고**: [skills/api-integration.md](skills/api-integration.md)

### 캐시 데이터 관리

1. `utils/data/` 디렉토리 구조 이해
2. 캐시 저장/로드 함수 구현
3. 캐시 무효화 전략 수립

**참고**: [skills/cache-management.md](skills/cache-management.md)

## 문제 해결

### 일반적인 문제

#### 1. "MCP context is required but not provided" 에러
- **원인**: streamable-http에서 ctx 주입 실패
- **해결**: 전역 컨텍스트 fallback이 자동으로 작동하므로, 서버 재시작 확인
- **참고**: [skills/context-handling.md](skills/context-handling.md)

#### 2. Tool이 0개로 표시됨
- **원인**: Tool 모듈 import 실패
- **해결**: `server.py`에서 tool 모듈 import 확인, 로그에서 ImportError 확인
- **체크**: `tool_modules` 리스트에 모듈명이 포함되어 있는지 확인

#### 3. API 호출 실패
- **원인**: OC 값 오류 또는 API 엔드포인트 오류
- **해결**: `.env` 파일의 `LEGISLATION_API_KEY` 확인, API URL 확인
- **참고**: OC 값은 이메일 주소 또는 `@` 앞 부분만 사용 가능

#### 4. 검색 결과가 없음
- **원인**: 검색어가 너무 구체적이거나 API 파라미터 오류
- **해결**: 검색어를 더 일반적으로 변경, API 파라미터 확인
- **참고**: [docs/api-master-guide.md](docs/api-master-guide.md)

### 디버깅 팁

```bash
# 서버 로그 확인
# Claude Desktop 로그: ~/Library/Logs/Claude/mcp-server-mcp-kr-legislation.log

# Python 모듈 확인
python -c "import mcp_kr_legislation; print(mcp_kr_legislation.__file__)"

# Tool 모듈 import 테스트
python -c "from mcp_kr_legislation.tools import law_tools; print('OK')"

# API 클라이언트 테스트
python -c "
from mcp_kr_legislation.apis.client import LegislationClient
from mcp_kr_legislation.config import legislation_config
client = LegislationClient(config=legislation_config)
print('Client OK')
"
```

## Skills 문서

프로젝트의 특정 기능에 대한 상세 가이드는 `skills/` 디렉토리를 참고하세요:

- [tool-development.md](skills/tool-development.md) - 새로운 MCP tool 추가 가이드
- [api-integration.md](skills/api-integration.md) - 법제처 API 통합 가이드
- [cache-management.md](skills/cache-management.md) - 캐시 데이터 관리 가이드
- [context-handling.md](skills/context-handling.md) - 컨텍스트 처리 가이드
- [graph-search.md](skills/graph-search.md) - 지식 그래프 검색 가이드
- [self-improvement.md](skills/self-improvement.md) - 자가 개선 패턴 가이드

## API 가이드 문서

법제처 API의 상세 가이드는 `docs/` 디렉토리를 참고하세요:

- [api-master-guide.md](docs/api-master-guide.md) - API 구조 패턴 및 카테고리별 구분표
- [api-law.md](docs/api-law.md) - 법령 관련 API
- [api-precedent.md](docs/api-precedent.md) - 판례 관련 API
- [api-committee.md](docs/api-committee.md) - 위원회결정문 API
- [api-ordinance.md](docs/api-ordinance.md) - 자치법규, 행정규칙 API
- [api-others.md](docs/api-others.md) - 조약, 학칙공단, 법령용어 등 기타 API

## 참고 자료

- [FastMCP 문서](https://gofastmcp.com)
- [MCP 스펙](https://modelcontextprotocol.io)
- [국가법령정보센터 OPEN API](http://www.law.go.kr/LSW/openapi/openapi.do)
- [법제처 OPEN API 가이드](src/mcp_kr_legislation/utils/korean_law_api_complete_guide.md)
