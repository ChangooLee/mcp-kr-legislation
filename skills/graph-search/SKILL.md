---
name: graph-search
description: 법령, 판례, 위원회결정문 간 관계를 지식 그래프로 모델링하고 검색할 때 사용. 노드/엣지 구조 설계, 자연어 쿼리, 관계 탐색 구현 시 참조.
---

# 지식 그래프 검색 가이드

법령, 판례, 위원회결정문 간의 관계를 지식 그래프로 모델링하고 검색하는 방법입니다.

## 엔티티 타입

### 법령 관련
- `Law` (법령)
- `Article` (조문)
- `Section` (장/절)
- `Subsection` (항/호)

### 판례 관련
- `Precedent` (판례)
- `ConstitutionalCourt` (헌법재판소 결정례)
- `LegalInterpretation` (법령해석례)
- `AdministrativeTrial` (행정심판례)

### 위원회 관련
- `CommitteeDecision` (위원회결정문)
- `PrivacyCommittee` (개인정보보호위원회)
- `FinancialCommittee` (금융위원회)
- 기타 위원회

### 자치법규 관련
- `Ordinance` (자치법규)
- `AdministrativeRule` (행정규칙)

## 관계 타입

### 법령 간 관계
- `references`: Law → Law (법령이 다른 법령을 참조)
- `amends`: Law → Law (법령이 다른 법령을 개정)
- `delegates`: Law → Ordinance (법령이 자치법규에 위임)

### 판례와 법령 관계
- `interprets`: Precedent → Law (판례가 법령을 해석)
- `applies`: Precedent → Article (판례가 조문을 적용)

### 위원회와 법령 관계
- `decides`: CommitteeDecision → Law (위원회가 법령에 대해 결정)
- `enforces`: CommitteeDecision → Article (위원회가 조문을 집행)

### 자치법규와 법령 관계
- `implements`: Ordinance → Law (자치법규가 법령을 시행)

## 자연어 쿼리 예시

```
"개인정보보호법을 참조하는 법령"
→ relation: references, from: law_개인정보보호법

"개인정보보호법을 해석한 판례"
→ relation: interprets, to: law_개인정보보호법

"개인정보보호위원회 결정문"
→ node_type: CommitteeDecision, committee: PrivacyCommittee
```

## 유틸리티 스크립트

지식 그래프 빌드:
```bash
python scripts/build_graph.py
```

## 상세 구현

구현 코드는 [implementation.md](implementation.md) 참조.

## 주의사항

1. **그래프 크기 관리**: 노드/엣지 수가 많아지면 성능 저하
2. **관계 추출 정확도**: 법령 본문에서 관계 자동 추출은 어려움
3. **동기화**: 법령 개정 시 그래프 업데이트 필요

## 관련 파일

- [src/mcp_kr_legislation/utils/data/knowledge_graph/](../../src/mcp_kr_legislation/utils/data/knowledge_graph/) - 지식 그래프 데이터
- [skills/cache-management/](../cache-management/) - 캐시 관리
