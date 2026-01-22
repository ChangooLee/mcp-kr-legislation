# API 파라미터 가이드

> 최종 검증: 2026-01-20
> 참조: [국가법령정보 공동활용](https://open.law.go.kr/LSO/openApi/guideList.do#)

## 1. 공통 파라미터

| 파라미터 | 필수 | 설명 | 예시 |
|---------|------|------|------|
| OC | ✅ | API 키 (이메일 ID) | `lchangoo` |
| target | ✅ | API 대상 (아래 참조) | `law`, `prec` |
| type | ✅ | 응답 형식 | `JSON`, `XML`, `HTML` |
| display | | 결과 개수 (기본 20, 최대 100) | `20` |
| page | | 페이지 번호 (기본 1) | `1` |
| query | | 검색어 | `개인정보보호법` |

---

## 2. 법령 API (target=law)

### 검색 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 법령명/조문 검색어 | `개인정보` |
| sort | 정렬 (lasc/ldes/dasc/ddes) | `ddes` |
| efYd | 시행일 검색 (YYYYMMDD~YYYYMMDD) | `20240101~20241231` |
| prYd | 공포일 검색 | `20240101~20241231` |
| lawSel | 법종 (1:법률, 2:대통령령, 3:총리령, 4:부령) | `1` |

### 본문 조회 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| MST | 법령일련번호 (필수) | `248613` |
| JO | 조문번호 | `제15조` |
| orGan | 소관부처코드 | `1051000` |

### API URL 예시

```
# 현행법령 목록 검색
http://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=law&type=JSON&query=개인정보보호법

# 법령 본문 조회
http://www.law.go.kr/DRF/lawService.do?OC={OC}&target=law&type=JSON&MST=248613
```

---

## 3. 판례 API (target=prec)

### 검색 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 사건명/본문 검색어 | `계약해제` |
| search | 검색범위 (1:사건명, 2:본문) | `1` |
| sort | 정렬 (dasc/ddes/nasc/ndes) | `ddes` |
| precKnd | 판례종류 (대법원, 하급심 등) | |
| jdDt | 선고일 검색 | `20240101~20241231` |

### 본문 조회 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| ID | 판례일련번호 (필수) | `123456` |

**주의**: 판례 상세 조회는 **HTML만 지원**, JSON 미지원

---

## 4. 헌재결정례 API (target=detc)

### 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 사건명 검색어 | `위헌` |
| ID | 헌재결정례일련번호 | `123456` |
| search | 검색범위 (1:사건명, 2:본문) | `1` |
| dcsYd | 결정일 검색 | `20240101~20241231` |

---

## 5. 법령해석례 API (target=expc)

### 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 안건명 검색어 | `개인정보` |
| ID | 해석례일련번호 | `123456` |
| search | 검색범위 (1:안건명, 2:본문) | `1` |
| explYd | 해석일자 검색 | `20240101~20241231` |

---

## 6. 행정심판례 API (target=decc)

### 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 재결례명 검색어 | `취소` |
| ID | 행정심판례일련번호 | `123456` |
| search | 검색범위 (1:재결례명, 2:본문) | `1` |
| dcsYd | 재결일 검색 | `20240101~20241231` |

---

## 7. 위원회 결정문 API

### target 값 목록 (12개 위원회)

| target | 위원회명 | 상태 |
|--------|---------|------|
| ppc | 개인정보보호위원회 | ✅ |
| fsc | 금융위원회 | ✅ |
| ftc | 공정거래위원회 | ✅ |
| acr | 국민권익위원회 | ✅ |
| nlrc | 중앙노동위원회 | ✅ |
| ecc | 중앙환경분쟁조정위원회 | ✅ |
| sfc | 증권선물위원회 | ✅ |
| nhrck | 국가인권위원회 | ✅ |
| kcc | 방송통신위원회 | ✅ |
| iaciac | 산업재해보상보험재심사위원회 | ✅ |
| oclt | 중앙토지수용위원회 | ✅ |
| eiac | 고용보험심사위원회 | ✅ |

### 공통 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 결정문명 검색어 | `개인정보` |
| ID | 결정문일련번호 | `123456` |

---

## 8. 행정규칙 API (target=admrul)

### 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 행정규칙명 검색어 | `훈령` |
| MST | 행정규칙일련번호 | `123456` |
| admrulSe | 행정규칙종류 (훈령, 예규, 고시 등) | |

---

## 9. 자치법규 API (target=ordin)

### 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 자치법규명 검색어 | `조례` |
| MST | 자치법규일련번호 | `123456` |
| rgnCd | 지역코드 | `11` (서울) |

---

## 10. 중앙부처해석 API (CgmExpc) ✅ 전체 활성화

### 정상 동작 target 목록 (35개 부처)

| target | 부처명 | 데이터 건수 | 상태 |
|--------|--------|-----------|------|
| moefCgmExpc | 기획재정부 | 2,297 | ✅ |
| moelCgmExpc | 고용노동부 | 9,573 | ✅ |
| molitCgmExpc | 국토교통부 | 5,660 | ✅ |
| moisCgmExpc | 행정안전부 | 4,039 | ✅ |
| meCgmExpc | 환경부(기후에너지환경부) | 2,291 | ✅ |
| mofCgmExpc | 해양수산부 | 547 | ✅ |
| ntsCgmExpc | 국세청 | 135,765 | ✅ |
| kcsCgmExpc | 관세청 | 1,279 | ✅ |
| motieCgmExpc | 산업통상자원부 | 32 | ✅ |
| mssCgmExpc | 중소벤처기업부 | 4 | ✅ |
| moeCgmExpc | 교육부 | 40+ | ✅ |
| mohwCgmExpc | 보건복지부 | 142+ | ✅ |
| mcstCgmExpc | 문화체육관광부 | 44 | ✅ |
| mojCgmExpc | 법무부 | 1+ | ✅ |
| mogefCgmExpc | 성평등가족부 | 4+ | ✅ |
| mofaCgmExpc | 외교부 | 17 | ✅ |
| mouCgmExpc | 통일부 | 6 | ✅ |
| molegCgmExpc | 법제처 | 17 | ✅ |
| mfdsCgmExpc | 식품의약품안전처 | 1,216 | ✅ |
| mpmCgmExpc | 인사혁신처 | 10 | ✅ |
| kmaCgmExpc | 기상청 | 21 | ✅ |
| khaCgmExpc | 국가유산청 | 0 | ⚠️ |
| rdaCgmExpc | 농촌진흥청 | 6 | ✅ |
| knpaCgmExpc | 경찰청 | 0 | ⚠️ |
| dapaCgmExpc | 방위사업청 | 46 | ✅ |
| mmaCgmExpc | 병무청 | 1+ | ✅ |
| kfsCgmExpc | 산림청 | 623 | ✅ |
| nfaCgmExpc | 소방청 | 328 | ✅ |
| ppsCgmExpc | 조달청 | 23 | ✅ |
| kdcaCgmExpc | 질병관리청 | 0 | ⚠️ |
| kcgCgmExpc | 해양경찰청 | 0 | ⚠️ |
| mndCgmExpc | 국방부 | 40 | ✅ |
| mafraCgmExpc | 농림축산식품부 | 32 | ✅ |
| mpvaCgmExpc | 국가보훈부 | 116 | ✅ |
| **kostatCgmExpc** | **국가데이터처** | **4** | **✅** |
| **kipoCgmExpc** | **지식재산처** | **186** | **✅** |
| **naaccCgmExpc** | **행정중심복합도시건설청** | **37** | **✅** |

### 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 안건명 검색어 (선택) | `조세` |
| ID | 법령해석일련번호 | `215980` |
| search | 검색범위 (1:안건명, 2:본문) | `1` |
| explYd | 해석일자 검색 | `20240101~20241231` |
| inq | 질의기관코드 | |
| rpl | 해석기관코드 | |
| sort | 정렬 (lasc/ldes/dasc/ddes) | `ddes` |

**주의**: `query` 없이 호출하면 전체 목록 반환

### API URL 예시

```
# 기획재정부 법령해석 검색
http://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=moefCgmExpc&type=JSON&query=예산

# 기획재정부 법령해석 상세 조회
http://www.law.go.kr/DRF/lawService.do?OC={OC}&target=moefCgmExpc&type=JSON&ID=215980
```

---

## 11. 특별행정심판 API

### 정상 동작 target 목록 (4개)

| target | 기관명 | 데이터 건수 | 상태 |
|--------|--------|-----------|------|
| ttSpecialDecc | 조세심판원 | 다수 | ✅ |
| kmstSpecialDecc | 해양안전심판원 | 다수 | ✅ |
| **acrSpecialDecc** | **국민권익위원회** | **85** | **✅** |
| **adapSpecialDecc** | **인사혁신처 소청심사위원회** | **210** | **✅** |

### 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 사건명 검색어 (선택) | `자동차` |
| ID | 재결례일련번호 | `123456` |
| search | 검색범위 (1:사건명, 2:본문) | `1` |
| dpaYd | 처분일자 검색 | `20240101~20241231` |
| rslYd | 의결일자 검색 | `20240101~20241231` |

### API URL 예시

```
# 국민권익위원회 특별행정심판 검색
http://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=acrSpecialDecc&type=JSON

# 인사혁신처 소청심사위원회 검색
http://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=adapSpecialDecc&type=JSON&query=징계
```

---

## 12. 조약 API (target=trty)

### 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| query | 조약명 검색어 | `한미` |

---

## 참고: HTTP 헤더

### 필수 헤더

일부 API는 `Referer` 헤더 검증을 수행합니다:

```
Referer: https://open.law.go.kr/
```

이 헤더가 없으면 일부 중앙부처해석 API에서 에러가 발생할 수 있습니다.

---

## 버전 이력

- 2026-01-20: 전체 중앙부처해석 API (35개 부처) target 값 검증 완료
- 2026-01-20: Referer 헤더 필수 사항 추가
- 2026-01-20: 올바른 target 값으로 문서 업데이트
