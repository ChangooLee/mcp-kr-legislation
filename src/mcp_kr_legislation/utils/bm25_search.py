"""
BM25 기반 로컬 검색 엔진 (kiwipiepy 형태소 분석기 통합)

법령/판례 검색 결과에 대해 BM25 Okapi 알고리즘으로 재랭킹(re-ranking)합니다.
API 결과를 수신한 후 클라이언트 측에서 관련도 순으로 정렬하는 데 사용합니다.

토크나이저 우선순위:
  1. kiwipiepy (한국어 형태소 분석 — 가장 정확)
  2. 공백 기반 단순 분리 (폴백)

사용 예:
    from mcp_kr_legislation.utils.bm25_search import rank_search_results

    ranked = rank_search_results(
        query="개인정보 처리 동의",
        results=api_results,
        text_keys=["법령명한글", "소관부처명"],
        top_k=10,
    )
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# 불용어 (조사, 어미, 접속사 등)
# -------------------------------------------------------------------
_STOPWORDS = {
    # 조사
    "이", "가", "을", "를", "은", "는", "의", "에", "에서", "로", "으로",
    "와", "과", "도", "만", "부터", "까지", "에게", "한테", "께서",
    # 어미/어간
    "하여", "하고", "하는", "하기", "하면", "하여서", "합니다", "합니까",
    "이다", "이며", "이고", "이나", "이면", "이어서",
    # 접속사
    "및", "또는", "또한", "그리고", "그러나", "따라서", "때문에",
    "그래서", "하지만", "그런데", "그러면", "즉", "다만",
    # 관계어
    "관한", "관하여", "대한", "대하여", "위한", "위하여",
    "에관한", "에대한", "을위한",
    # 일반 단음절
    "것", "수", "등", "중", "때", "각", "해", "년", "월", "일",
}

# -------------------------------------------------------------------
# 형태소 분석기 초기화
# -------------------------------------------------------------------
_kiwi = None
_kiwi_loaded = False


def _get_kiwi():
    """Kiwi 형태소 분석기 싱글톤. 첫 호출 시에만 로드."""
    global _kiwi, _kiwi_loaded
    if _kiwi_loaded:
        return _kiwi
    _kiwi_loaded = True
    try:
        from kiwipiepy import Kiwi  # type: ignore
        _kiwi = Kiwi()
        logger.info("kiwipiepy 형태소 분석기 로드 완료")
    except Exception as e:
        _kiwi = None
        logger.warning(f"kiwipiepy 로드 실패, 공백 분리 폴백 사용: {e}")
    return _kiwi


# BM25 관련 품사 태그 (명사류 + 동사/형용사 어간)
_CONTENT_POS = {
    "NNG",  # 일반명사
    "NNP",  # 고유명사
    "NNB",  # 의존명사
    "VV",   # 동사
    "VA",   # 형용사
    "XR",   # 어근
    "SL",   # 외래어
    "SH",   # 한자
}


def _tokenize_kiwi(text: str) -> list[str]:
    """kiwipiepy를 사용한 형태소 기반 토크나이저."""
    kiwi = _get_kiwi()
    if kiwi is None:
        return _tokenize_simple(text)
    try:
        result = kiwi.tokenize(text, normalize_coda=True)
        tokens = []
        for token in result:
            form = token.form
            pos = token.tag
            if pos in _CONTENT_POS and len(form) >= 2 and form not in _STOPWORDS:
                tokens.append(form.lower())
        return tokens if tokens else _tokenize_simple(text)
    except Exception:
        return _tokenize_simple(text)


def _tokenize_simple(text: str) -> list[str]:
    """공백/구두점 기반 단순 토크나이저 (폴백)."""
    if not text:
        return []
    text = re.sub(r"[^\w\s가-힣]", " ", text)
    tokens = text.lower().split()
    return [t for t in tokens if len(t) >= 2 and t not in _STOPWORDS]


def _tokenize(text: str) -> list[str]:
    """통합 토크나이저 (kiwipiepy 우선, 폴백으로 단순 분리)."""
    kiwi = _get_kiwi()
    if kiwi is not None:
        return _tokenize_kiwi(text)
    return _tokenize_simple(text)


# -------------------------------------------------------------------
# BM25Ranker
# -------------------------------------------------------------------

class BM25Ranker:
    """
    API 결과 목록을 BM25 Okapi 알고리즘으로 재랭킹합니다.

    - kiwipiepy 형태소 분석으로 토크나이징 (설치된 경우)
    - rank-bm25 패키지가 없으면 TF 기반 폴백
    """

    def __init__(self) -> None:
        self._has_bm25 = False
        try:
            from rank_bm25 import BM25Okapi  # type: ignore
            self._BM25Okapi = BM25Okapi
            self._has_bm25 = True
            logger.debug("BM25Okapi 로드 완료")
        except ImportError:
            logger.warning("rank-bm25 없음. TF 폴백 사용 (uv add rank-bm25)")
        # 형태소 분석기 미리 로드 (첫 검색 지연 방지)
        _get_kiwi()

    def rank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        text_keys: list[str] | None = None,
        top_k: int | None = None,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        문서 목록을 BM25 점수로 재랭킹합니다.

        Args:
            query: 검색 쿼리 (자연어)
            documents: 재랭킹할 문서 딕셔너리 목록
            text_keys: BM25 인덱싱에 사용할 필드명 목록. None이면 모든 str 값 사용
            top_k: 반환할 최대 결과 수. None이면 전체
            score_threshold: 이 점수 미만 문서 제외 (-1.0 = 전체 포함, 순서만 정렬)

        Returns:
            BM25 점수 내림차순 정렬된 목록. 각 항목에 _bm25_score 추가.
        """
        if not documents or not query.strip():
            return documents

        query_tokens = _tokenize(query)
        if not query_tokens:
            return documents

        corpus_texts = []
        for doc in documents:
            if text_keys:
                parts = [str(doc.get(k, "")) for k in text_keys if doc.get(k)]
            else:
                parts = [str(v) for v in doc.values() if isinstance(v, str) and v]
            corpus_texts.append(" ".join(parts))

        tokenized_corpus = [_tokenize(t) for t in corpus_texts]

        scores = (
            self._bm25_scores(query_tokens, tokenized_corpus)
            if self._has_bm25
            else self._tf_scores(query_tokens, tokenized_corpus)
        )

        scored = []
        for doc, score in zip(documents, scores):
            if score > score_threshold:
                doc_copy = dict(doc)
                doc_copy["_bm25_score"] = round(float(score), 4)
                scored.append(doc_copy)

        scored.sort(key=lambda x: x["_bm25_score"], reverse=True)
        return scored[:top_k] if top_k is not None else scored

    def _bm25_scores(
        self,
        query_tokens: list[str],
        tokenized_corpus: list[list[str]],
    ) -> list[float]:
        if not any(tokenized_corpus):
            return [0.0] * len(tokenized_corpus)
        bm25 = self._BM25Okapi(tokenized_corpus)
        return list(bm25.get_scores(query_tokens))

    def _tf_scores(
        self,
        query_tokens: list[str],
        tokenized_corpus: list[list[str]],
    ) -> list[float]:
        scores = []
        for tokens in tokenized_corpus:
            token_set = set(tokens)
            score = sum(1.0 for t in query_tokens if t in token_set)
            scores.append(score)
        return scores


# -------------------------------------------------------------------
# 전역 싱글톤 및 편의 함수
# -------------------------------------------------------------------

_ranker: BM25Ranker | None = None


def get_ranker() -> BM25Ranker:
    global _ranker
    if _ranker is None:
        _ranker = BM25Ranker()
    return _ranker


def rank_search_results(
    query: str,
    results: list[dict[str, Any]],
    text_keys: list[str] | None = None,
    top_k: int | None = None,
    score_threshold: float = -1.0,
) -> list[dict[str, Any]]:
    """
    편의 함수: API 검색 결과를 kiwipiepy+BM25로 재랭킹합니다.

    Args:
        query: 자연어 검색 쿼리
        results: API 반환 결과 목록 (list[dict])
        text_keys: 인덱싱 대상 필드 (예: ["법령명한글", "소관부처명"])
        top_k: 반환할 최대 결과 수
        score_threshold: 최소 BM25 점수 (0.0 = 모두 포함)

    Returns:
        재랭킹된 결과 목록 (각 항목에 _bm25_score 추가)
    """
    return get_ranker().rank(
        query=query,
        documents=results,
        text_keys=text_keys,
        top_k=top_k,
        score_threshold=score_threshold,
    )


def tokenize_query(query: str) -> list[str]:
    """쿼리 토크나이징 결과를 직접 확인할 때 사용합니다."""
    return _tokenize(query)
