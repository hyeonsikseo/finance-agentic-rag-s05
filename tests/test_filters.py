# -*- coding: utf-8 -*-
"""Self-Query 필터의 기준일 정규화.

LLM 은 "2021-03" 처럼 달까지만 주거나 "2013년 7월 1일" 처럼 한글로 주기도 한다.
그대로 Qdrant 의 날짜 범위에 넣으면 검색 노드가 죽는다(5회차 실측에서 S18 이 그랬다).
"""
from finrag.retrieval.filters import QueryFilters, normalize_date, to_qdrant


def test_year_month_becomes_month_end():
    assert normalize_date("2021-03") == "2021-03-31"
    assert normalize_date("2021.03") == "2021-03-31"
    assert normalize_date("2024-02") == "2024-02-29"


def test_year_only_and_full_dates():
    assert normalize_date("2021") == "2021-12-31"
    assert normalize_date("2013년 7월 1일") == "2013-07-01"
    assert normalize_date("2013-07-01") == "2013-07-01"


def test_latest_and_unreadable():
    assert normalize_date("latest") == "latest"
    assert normalize_date("현재") is None
    assert normalize_date("") is None
    assert normalize_date(None) is None


def test_query_filters_normalizes_so_to_qdrant_does_not_crash():
    f = QueryFilters(issuer="KB국민은행", effective_on="2021-03")
    assert f.effective_on == "2021-03-31"
    assert to_qdrant(f) is not None
    assert QueryFilters(effective_on="언제인지 모름").effective_on is None
