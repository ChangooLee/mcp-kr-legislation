# 법령 구분 도구 테스트 프롬프트

> Claude Desktop 테스트용 (44개 도구)

## 1. 기본 법령 검색

1. `search_law` (현행법령 목록 검색) - 개인정보보호법을 검색해줘
2. `get_law_detail` (현행법령 본문 조회) - 개인정보보호법을 검색하고 그 상세 내용을 보여줘
3. `search_law_articles` (조항호목 검색) - 개인정보보호법의 제1조부터 제5조까지 조문을 보여줘
4. `get_law_article_detail` (특정 조문 상세) - 개인정보보호법 제15조의 전체 내용을 알려줘
5. `get_law_articles_range` (연속 조문 조회) - 은행법 제1조부터 제10조까지 연속으로 조회해줘
6. `get_law_summary` (법령 요약) - 개인정보보호법의 기본정보와 조문 요약을 보여줘
7. `get_law_articles_summary` (조문 목차) - 민법의 조문 목차와 인덱스만 간략히 보여줘
8. `search_law_unified` (통합 검색) - 부동산 관련 법령을 통합 검색해줘

## 2. 시행일 기준 법령

9. `search_effective_law` (시행일 기준 목록) - 현재 시행 중인 은행 관련 법령을 검색해줘
10. `get_effective_law_detail` (시행일 기준 본문) - 현재 시행 중인 개인정보보호법의 상세 내용을 조회해줘
11. `get_effective_law_articles` (시행일 기준 조항호목) - 현재 시행 중인 개인정보보호법 제1조의 조항, 호, 목 단위 내용을 보여줘

## 3. 영문 법령

12. `search_english_law` (영문 법령 검색) - Banking Act를 영문으로 검색해줘
13. `get_english_law_detail` (영문 법령 상세) - 영문 개인정보보호법의 전체 조문을 보여줘
14. `get_english_law_summary` (영문 법령 요약) - Show me the English version of the Personal Information Protection Act
15. `search_english_law_articles_semantic` (영문 조문 시맨틱 검색) - 영문 민법에서 contract provisions에 대한 조문을 찾아줘

## 4. 법령 이력/비교

16. `search_law_change_history` (법령 변경이력 검색) - 2024년 1월 1일에 변경된 법령을 검색해줘
17. `search_article_change_history` (조문별 변경이력) - 개인정보보호법 제15조의 변경 이력을 조회해줘
18. `compare_law_versions` (버전 비교) - 개인정보보호법의 현행 버전과 시행일 버전을 비교해줘
19. `search_old_and_new_law` (신구법 목록) - 은행법의 신구법 비교 자료를 검색해줘
20. `get_old_and_new_law_detail` (신구법 본문) - 은행법의 신조문과 구조문 대조표를 보여줘
21. `search_three_way_comparison` (3단 비교 목록) - 은행법의 3단 비교 자료를 검색해줘
22. `get_three_way_comparison_detail` (3단 비교 본문) - 은행법의 상위법령-하위법령-조문 3단 비교 내용을 보여줘

## 5. 법령 연계/체계

23. `search_ordinance_law_link` (자치법규 연계) - 개인정보보호법과 연계된 자치법규를 검색해줘
24. `get_delegated_law` (위임법령 조회) - 개인정보보호법의 위임법령을 조회해줘
25. `search_law_system_diagram` (법령 체계도 검색) - 은행법의 법령 체계도를 검색해줘
26. `get_law_system_diagram_detail` (법령 체계도 상세) - 은행법의 상하위법 체계와 관련법령을 보여줘
27. `search_related_law` (관련법령 검색) - 민법과 관련된 법령을 검색해줘

## 6. 부가서비스

28. `search_law_nickname` (법률명 약칭) - 최근 등록된 법령 약칭을 검색해줘
29. `search_deleted_law_data` (삭제 데이터) - 최근 삭제된 법령 데이터를 검색해줘
30. `search_one_view` (한눈보기 목록) - 은행법 한눈보기 자료를 검색해줘
31. `get_one_view_detail` (한눈보기 본문) - 은행법의 한눈보기 상세 내용을 보여줘
32. `search_law_appendix` (별표서식 검색) - 신청서 관련 법령 별표서식을 검색해줘
33. `get_law_appendix_detail` (별표서식 상세) - 신청서 별표서식의 상세 내용을 보여줘
34. `search_ordinance_appendix` (자치법규 별표서식) - 서울시 자치법규의 별표서식을 검색해줘

## 7. 분야별 전문 검색

35. `search_financial_laws` (금융 법령) - 금융소비자보호 관련 법령을 검색해줘
36. `search_tax_laws` (세무 법령) - 소득세 관련 법령을 검색해줘
37. `search_privacy_laws` (개인정보보호 법령) - 개인정보 수집 및 이용에 관한 법령을 검색해줘

## 8. 시맨틱/캐시 검색

38. `search_law_articles_semantic` (조문 시맨틱 검색) - 개인정보보호법에서 동의와 관련된 모든 조문을 의미 기반으로 찾아줘
39. `search_law_with_cache` (캐시 기반 검색) - 은행법을 검색하고 요약 정보를 함께 보여줘

## 9. 맞춤형 검색

40. `search_custom_law` (맞춤형 법령) - 분류코드 L0000000003384에 해당하는 맞춤형 법령을 검색해줘
41. `search_custom_law_articles` (맞춤형 법령 조문) - 분류코드 L0000000003384의 법령 조문을 검색해줘
42. `search_custom_ordinance_articles` (맞춤형 자치법규 조문) - 분류코드로 맞춤형 자치법규 조문을 검색해줘

## 10. 법령용어 연계

43. `search_article_legal_term_link` (조문-법령용어 연계) - 개인정보보호법 제2조에 사용된 법령용어 연계 정보를 알려줘
44. `search_legal_term_article_link` (법령용어-조문 연계) - '개인정보'라는 법령용어가 사용된 조문들을 찾아줘
