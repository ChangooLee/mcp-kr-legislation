# MCP 도구 테스트 프롬프트 (LLM 통합 평가용)

> Claude Desktop / Cursor에서 반복 실행 가능한 테스트 프롬프트
> 기존 `law-tools-test-prompts.md`의 44개 기본 도구 + 전체 카테고리 확장

---

## A. 카테고리별 기본 검색 프롬프트

### A-1. 법령 (law)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 1 | 개인정보보호법을 검색해줘 | search_law → 결과 건수, 법령ID, MST, 상세조회 안내 |
| 2 | 개인정보보호법의 상세 내용을 보여줘 | get_law_detail → 기본정보, 조문 인덱스, 소관부처 |
| 3 | 개인정보보호법 제15조의 전체 내용을 알려줘 | get_law_article_detail → 조문 본문 |
| 4 | 은행법의 조문 목차를 보여줘 | get_law_articles_summary → 조문 번호+제목 목록 |

### A-2. 판례 (precedent)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 5 | 손해배상 관련 판례를 검색해줘 | search_precedent → 사건번호, 선고일자, 상세조회용 ID |
| 6 | 위 검색 결과 중 첫 번째 판례의 상세 내용을 보여줘 | get_precedent_detail → 판시사항, 판결요지, 전문 |

### A-3. 헌법재판소 (constitutional_court)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 7 | 위헌 관련 헌법재판소 결정례를 검색해줘 | search_constitutional_court → 사건번호, 종국일자, ID |
| 8 | 위 결정례 중 첫 번째의 전문을 보여줘 | get_constitutional_court_detail → 결정 전문 |

### A-4. 법령해석례 (legal_interpretation)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 9 | 행정절차 관련 법령해석례를 검색해줘 | search_legal_interpretation → 안건번호, 회신일자, ID |
| 10 | 위 해석례 중 첫 번째의 상세 내용을 보여줘 | get_legal_interpretation_detail → 질의요지, 회답 |

### A-5. 행정규칙 (administrative_rule)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 11 | 훈령 관련 행정규칙을 검색해줘 | search_administrative_rule → 규칙명, 소관부처, ID |
| 12 | 위 결과 중 첫 번째의 상세 내용을 보여줘 | get_administrative_rule_detail → 종류, 발령일, 부칙 |

### A-6. 자치법규 (local_ordinance)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 13 | 서울시 주차 관련 조례를 검색해줘 | search_local_ordinance → 법규명, 공포일, ID |
| 14 | 위 결과 중 첫 번째의 상세 내용을 보여줘 | get_local_ordinance_detail → 조례 본문 |

### A-7. 행정심판례 (administrative_appeal)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 15 | 취소 관련 행정심판례를 검색해줘 | search_administrative_trial → 사건번호 |
| 16 | 위 결과의 상세 내용을 보여줘 | get_administrative_trial_detail → 재결 내용 |

### A-8. 위원회결정문 (committee)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 17 | 공정거래위원회 과징금 결정문을 검색해줘 | search_monopoly_committee → 의결번호, ID |
| 18 | 위 결과 중 첫 번째의 상세 내용을 보여줘 | get_monopoly_committee_detail → 의결 내용 |

### A-9. 조약 (treaty)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 19 | 무역 관련 조약을 검색해줘 | search_treaty → 조약명, ID |
| 20 | 위 조약의 상세 내용을 보여줘 | get_treaty_detail → 조약 본문 |

### A-10. 법령용어 (legal_term)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 21 | 주민등록 관련 법령용어를 검색해줘 | search_legal_term → 용어명, 정의, ID |
| 22 | 위 용어의 상세 정의를 보여줘 | get_legal_term_detail → 용어 정의, 관련 조문 |

### A-11. 중앙부처 해석 (ministry_interpretation)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 23 | 법제처의 행정 관련 해석을 검색해줘 | search_moleg_interpretation → 안건명, ID |
| 24 | 위 해석의 상세 내용을 보여줘 | get_moleg_interpretation_detail → 질의/회답 |

### A-12. 특별행정심판 (special_tribunal)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 25 | 토지수용 보상 관련 심판례를 검색해줘 | search_land_tribunal → 결정문번호, ID |
| 26 | 위 심판례의 상세 내용을 보여줘 | get_land_tribunal_detail → 재결 내용 |

### A-13. 지식베이스 (knowledge_base)

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| 27 | 법률 관련 FAQ를 검색해줘 | search_faq → FAQ 목록 |
| 28 | 법률 관련 QnA를 검색해줘 | search_qna → QnA 목록 |

---

## B. 멀티도구 워크플로우 프롬프트

### B-1. 법령 조회 플로우

**프롬프트**: "개인정보보호법을 검색하고, 상세 내용을 조회한 다음, 조문 목차를 보여줘"

**기대 흐름**:
1. search_law("개인정보보호법") → MST 추출
2. get_law_detail(mst=MST) → 법령 상세
3. get_law_articles_summary(law_id=LAW_ID) → 조문 목차

**검증 포인트**:
- Step 1 → 2: MST가 정확히 전달되는가
- Step 2 → 3: law_id vs mst 파라미터 구분이 맞는가
- 최종 결과가 동일 법령에 대한 것인가

### B-2. 판례 + 법령해석 교차 참조

**프롬프트**: "손해배상과 관련된 대법원 판례를 찾고, 첫 번째 판례의 상세를 보여준 뒤, 같은 주제의 법령해석례도 검색해줘"

**기대 흐름**:
1. search_precedent("손해배상") → case_id 추출
2. get_precedent_detail(case_id=ID) → 판례 전문
3. search_legal_interpretation("손해배상") → 해석례 목록

**검증 포인트**:
- Step 2에서 판시사항, 판결요지가 출력되는가
- Step 3에서 안건번호, 상세조회용 ID가 포함되는가

### B-3. 법령 비교

**프롬프트**: "소득세법의 신구법 비교 자료와 3단 비교 자료를 모두 조회해줘"

**기대 흐름**:
1. search_old_and_new_law("소득세법") → MST 추출
2. get_old_and_new_law_detail(mst=MST) → 신구 대조표
3. search_three_way_comparison("소득세법") → 3단 비교

**검증 포인트**:
- 동일 법령에 대한 두 종류 비교 자료가 일관되는가

### B-4. 행정규칙 + 자치법규 연계

**프롬프트**: "공무원 복무와 관련된 행정규칙을 찾고, 서울시의 관련 조례도 검색해줘"

**기대 흐름**:
1. search_administrative_rule("공무원 복무") → 행정규칙 목록
2. get_administrative_rule_detail(rule_id=ID) → 규칙 상세
3. search_local_ordinance("공무원 복무") → 자치법규 목록

**검증 포인트**:
- 행정규칙과 자치법규의 관계가 자연스러운가

### B-5. 에러 복구

**프롬프트**: "법령일련번호 999999999의 법령 상세를 조회해줘"

**기대 결과**:
- 명확한 에러 메시지 (빈 구조체가 아닌)
- 올바른 조회 방법 안내
- 검색부터 시작하라는 가이드

---

## C. 에러 케이스 프롬프트

| # | 프롬프트 | 기대 결과 |
|---|---------|----------|
| C-1 | 빈 문자열로 법령 검색해줘 | 검색어 필요 안내 + 예시 |
| C-2 | 존재하지 않는 판례 ID로 상세조회해줘 | 에러 + 올바른 검색 방법 안내 |
| C-3 | 아주 긴 무의미 문자열로 법령 검색해줘 | 결과 없음 + 검색어 조정 가이드 |
| C-4 | 잘못된 파라미터 타입으로 도구 호출 | 파라미터 사용법 안내 |

---

## D. 품질 평가 체크리스트

각 프롬프트 실행 후 확인:

- [ ] 응답 시간 3초 이내 (search) / 5초 이내 (detail)
- [ ] 핵심 정보 포함 (ID, 이름, 날짜)
- [ ] 후속 호출 안내가 정확한 도구명/파라미터를 포함
- [ ] 에러 시 대안 안내 포함
- [ ] 불필요한 장식(이모지) 없음
