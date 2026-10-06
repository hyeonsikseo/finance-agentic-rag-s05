# -*- coding: utf-8 -*-
"""5회차 자기 확인.

    make test        (Windows: .venv\\Scripts\\python -m pytest -q)

세 묶음입니다. grade · route(실습 1)와 selfquery(실습 2)는 Qdrant 도 API 키도 없이 돕니다
(LLM 을 가짜로 바꿔 넣습니다). 계산 Tool(실습 3)은 tests/test_calc_golden.py 가 봅니다.
채우기 전에는 실습 1·2 묶음이 NotImplementedError 로 실패합니다. 그게 정상입니다.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableLambda

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ── 가짜 LLM. 구조화 출력(with_structured_output)이 우리가 정한 값을 돌려준다 ──────
class _FakeLLM:
    def __init__(self, output=None, error: Exception | None = None):
        self.output, self.error, self.calls = output, error, []

    def with_structured_output(self, schema, **kwargs):
        def run(prompt_value):
            self.calls.append(prompt_value)
            if self.error:
                raise self.error
            return self.output
        return RunnableLambda(run)


def _hits(*texts: str) -> list[dict]:
    return [{"chunk_id": f"c{i}", "doc_id": "kakao_deposit_terms_2024", "article": f"제{i}조",
             "page_start": i, "text": t} for i, t in enumerate(texts, start=1)]


def _use(monkeypatch, module, llm, fake: bool = False):
    monkeypatch.setattr(module, "get_llm", lambda *a, **k: llm)
    monkeypatch.setattr(module, "is_fake", lambda m: fake)


# ── 실습 1 · nodes.grade ──────────────────────────────────────────────
def test_grade_without_hits_is_none_and_skips_the_llm(monkeypatch):
    from finrag.agent import nodes
    def boom(*a, **k):
        raise AssertionError("근거가 없으면 LLM 을 부르지 않습니다")
    monkeypatch.setattr(nodes, "get_llm", boom)
    out = nodes.grade({"masked_question": "질문", "hits": [], "trace": ["retrieve"]})
    assert out["grade"] == "none", "근거가 하나도 없으면 none 입니다"
    assert out["trace"][-1] == "grade", "trace 에 grade 를 이어 붙입니다"


def test_grade_returns_the_llm_verdict(monkeypatch):
    from finrag.agent import nodes
    for verdict in ("sufficient", "insufficient", "none"):
        llm = _FakeLLM(nodes.Grade(verdict=verdict, reason="테스트"))
        _use(monkeypatch, nodes, llm)
        out = nodes.grade({"masked_question": "중도해지이율은?", "hits": _hits("중도해지이율은 기본이율의 50%")})
        assert out["grade"] == verdict, "LLM 의 verdict 를 그대로 씁니다"
    text = llm.calls[-1].to_string()
    assert "중도해지이율은?" in text and "기본이율의 50%" in text, \
        "프롬프트에 질문(masked_question)과 근거(_context)가 들어가야 합니다"


def test_grade_without_a_key_uses_the_context_length_rule(monkeypatch):
    from finrag.agent import nodes
    _use(monkeypatch, nodes, _FakeLLM(), fake=True)
    short = nodes.grade({"masked_question": "q", "hits": _hits("짧은 근거")})
    long = nodes.grade({"masked_question": "q", "hits": _hits("가" * 400)})
    assert short["grade"] == "insufficient" and long["grade"] == "sufficient", \
        "키가 없으면(is_fake) policy 의 min_context_chars 로 분량만 봅니다. 판단이 아니라 자리 채우기입니다"


def test_grade_llm_failure_leans_to_insufficient_not_none(monkeypatch):
    from finrag.agent import nodes
    _use(monkeypatch, nodes, _FakeLLM(error=RuntimeError("timeout")))
    out = nodes.grade({"masked_question": "q", "hits": _hits("근거가 있다")})
    assert out["grade"] == "insufficient", \
        "근거가 있는데 호출이 실패했다고 none(거절)으로 보내면 오거절입니다. insufficient 로 기울입니다"


# ── 실습 1 · nodes.route_after_grade ──────────────────────────────────
@pytest.fixture
def cap2(monkeypatch):
    from finrag.agent import nodes
    monkeypatch.setattr(nodes, "get_settings", lambda: SimpleNamespace(max_retries=2))
    return nodes


def test_route_sufficient_goes_to_answer(cap2):
    assert cap2.route_after_grade({"grade": "sufficient", "retry_count": 0}) == "answer"


def test_route_insufficient_retries_under_the_cap(cap2):
    assert cap2.route_after_grade({"grade": "insufficient", "retry_count": 0}) == "retry"
    assert cap2.route_after_grade({"grade": "insufficient", "retry_count": 1}) == "retry", \
        "상한 2 면 두 번째 재검색까지 허용합니다"


def test_route_insufficient_at_the_cap_answers_with_limits(cap2):
    assert cap2.route_after_grade({"grade": "insufficient", "retry_count": 2}) == "answer", \
        "상한에 닿으면 거절이 아니라 '한계를 밝힌 답변'으로 갑니다 (ADR-004)"


def test_route_none_abstains_without_retry(cap2):
    assert cap2.route_after_grade({"grade": "none", "retry_count": 0}) == "abstain", \
        "근거가 없으면 재검색해도 없습니다. 바로 거절합니다"


def test_route_missing_grade_abstains(cap2):
    assert cap2.route_after_grade({}) == "abstain", "grade 가 아예 없어도 abstain 입니다 (3회차와 같은 규칙)"


# ── 실습 2 · selfquery.extract_filters ────────────────────────────────
def test_extract_filters_returns_what_the_llm_filled(monkeypatch):
    from finrag.agent import selfquery
    from finrag.retrieval.filters import QueryFilters
    llm = _FakeLLM(QueryFilters(issuer="카카오뱅크", doc_type="특약", effective_on="latest"))
    _use(monkeypatch, selfquery, llm)
    f = selfquery.extract_filters("카카오뱅크 정기예금 특약의 현행 계약기간은?")
    assert isinstance(f, QueryFilters)
    assert (f.issuer, f.doc_type, f.effective_on) == ("카카오뱅크", "특약", "latest")
    assert "카카오뱅크 정기예금 특약" in llm.calls[-1].to_string(), "질문이 프롬프트에 들어가야 합니다"


def test_extract_filters_accepts_a_dict_from_the_llm(monkeypatch):
    from finrag.agent import selfquery
    from finrag.retrieval.filters import QueryFilters
    _use(monkeypatch, selfquery, _FakeLLM({"issuer": "하나은행", "effective_on": "2013-07-01"}))
    f = selfquery.extract_filters("2013년 7월 1일 시행 하나은행 여신거래기본약관 제7조")
    assert isinstance(f, QueryFilters) and f.issuer == "하나은행" and f.effective_on == "2013-07-01"


def test_extract_filters_without_a_key_is_empty(monkeypatch):
    from finrag.agent import selfquery
    from finrag.retrieval.filters import QueryFilters
    _use(monkeypatch, selfquery, _FakeLLM(), fake=True)
    f = selfquery.extract_filters("아무 질문")
    assert f == QueryFilters(), "키가 없으면 빈 필터. 필터 없이 검색하는 것이 조용히 0건보다 낫습니다"


def test_extract_filters_llm_error_is_empty_not_an_exception(monkeypatch):
    from finrag.agent import selfquery
    from finrag.retrieval.filters import QueryFilters
    _use(monkeypatch, selfquery, _FakeLLM(error=RuntimeError("rate limit")))
    assert selfquery.extract_filters("아무 질문") == QueryFilters(), \
        "호출이 실패해도 그래프가 죽으면 안 됩니다. 빈 필터로 계속 갑니다"


# ── 완성본으로 도는 것 (채우기 전에도 통과) ─────────────────────────────
def test_agent_graph_compiles_with_a_bounded_loop():
    from finrag.agent.graph import build_agent_graph
    g = build_agent_graph().get_graph()
    names = {n for n in g.nodes}
    assert {"preprocess", "rewrite", "selfquery", "retrieve", "grade", "bump_retry",
            "calc", "answer", "abstain"} <= names
    edges = {(e.source, e.target) for e in g.edges}
    assert ("bump_retry", "rewrite") in edges, "재검색은 rewrite 로 돌아갑니다. 상한은 라우터가 지킵니다"


def test_preprocess_masks_resident_and_account_numbers():
    from finrag.agent import nodes
    out = nodes.preprocess({"question": "홍길동(850101-1234567) 계좌 110-123-456789 잔액 알려줘"})
    assert "850101" not in out["masked_question"] and "456789" not in out["masked_question"]
    assert out["notices"], "무엇을 가렸는지 고지에 남깁니다"
