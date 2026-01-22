# target 파라미터 전체 목록

법제처 API의 모든 target 값과 해당 기능입니다.

> **전체 API 정보**: `src/mcp_kr_legislation/utils/api_layout/*.json` 파일 참조
> **총 94개 고유 target 값** (모바일 제외)

## 주요 target 값

| target | 기능 | 목록 조회 | 본문 조회 |
|--------|------|-----------|-----------|
| `law` | 현행법령 | ✅ | ✅ |
| `eflaw` | 시행일법령 | ✅ | ✅ |
| `elaw` | 영문법령 | ✅ | ✅ |
| `prec` | 판례 | ✅ | ✅ |
| `detc` | 헌법재판소 결정례 | ✅ | ✅ |
| `expc` | 법령해석례 | ✅ | ✅ |
| `decc` | 행정심판례 | ✅ | ✅ |
| `ppc` | 개인정보보호위원회 결정문 | ✅ | ✅ |
| `ftc` | 공정거래위원회 결정문 | ✅ | ✅ |
| `fsc` | 금융위원회 결정문 | ✅ | ✅ |
| `admrul` | 행정규칙 | ✅ | ✅ |
| `ordin` | 자치법규 | ✅ | ✅ |
| `trty` | 조약 | ✅ | ✅ |
| `lstrm` | 법령용어 | ✅ | ✅ |

## 위원회 결정문 target

> 상세: `api_layout/committee.json`

| target | 위원회 |
|--------|--------|
| `ppc` | 개인정보보호위원회 |
| `eiac` | 고용보험심사위원회 |
| `ftc` | 공정거래위원회 |
| `acr` | 국민권익위원회 |
| `fsc` | 금융위원회 |
| `nlrc` | 노동위원회 |
| `kcc` | 방송통신위원회 |
| `iaciac` | 산업재해보상보험재심사위원회 |
| `oclt` | 중앙토지수용위원회 |
| `ecc` | 중앙환경분쟁조정위원회 |
| `sfc` | 증권선물위원회 |
| `nhrck` | 국가인권위원회 |

## 중앙부처 해석 target

> 상세: `api_layout/ministry_interpretation_1.json`, `api_layout/ministry_interpretation_2.json`

| target | 부처 |
|--------|------|
| `moelCgmExpc` | 고용노동부 |
| `molitCgmExpc` | 국토교통부 |
| `moefCgmExpc` | 기획재정부 |
| `mofCgmExpc` | 해양수산부 |
| `moisCgmExpc` | 행정안전부 |
| `meCgmExpc` | 환경부 |
| `kcsCgmExpc` | 관세청 |
| `ntsCgmExpc` | 국세청 |

## API 레이아웃 JSON 파일

전체 API 정보는 JSON 파일로 관리됩니다:

```
src/mcp_kr_legislation/utils/api_layout/
├── law.json                      # 법령 (26개)
├── admin_rule.json               # 행정규칙 (4개)
├── local_ordinance.json          # 자치법규 (3개)
├── precedent.json                # 판례 (8개)
├── committee.json                # 위원회결정문 (24개)
├── ministry_interpretation_1.json # 중앙부처 1차 해석 (65개)
├── ministry_interpretation_2.json # 중앙부처 2차 해석 (26개)
├── special_tribunal.json         # 특별행정심판 (8개)
└── ...                           # 기타
```

## 전체 목록

- [docs/api-master-guide.md](../../docs/api-master-guide.md) - API 마스터 가이드
- [api_layout/](../../src/mcp_kr_legislation/utils/api_layout/) - 구분별 JSON 파일
