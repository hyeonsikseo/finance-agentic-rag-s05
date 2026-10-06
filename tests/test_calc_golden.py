# -*- coding: utf-8 -*-
"""계산 골든 테스트.

data/golden/calc_golden.jsonl 의 기대값은 "문서에 인쇄된 예시값"이다. 모델이 아니라
문서가 정답을 갖고 있으므로, 이 테스트가 깨지면 코드가 틀렸거나 문서가 개정된 것이다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from finrag.tools import calc  # noqa: E402

GOLDEN = {r["id"]: r for r in
          (json.loads(l) for l in (ROOT / "data" / "golden" / "calc_golden.jsonl")
           .open(encoding="utf-8") if l.strip())}


def expected(cid: str):
    return GOLDEN[cid]["expected"]["value"]


def alt(cid: str, label_prefix: str):
    for a in GOLDEN[cid]["alternatives"]:
        if a["label"].startswith(label_prefix):
            return a["value"]
    raise KeyError(f"{cid}: '{label_prefix}' 대안이 없습니다")


# ── 적금 중도해지이율 (5회차 라이브 구현 대상) ────────────────────────
def test_c01_nh_band_ratio():
    """농협 형태 B: 기준이율 × 구간 적용률 × 경과월수/계약월수, 소수 셋째자리 절사."""
    r = calc.savings_early_termination_rate(base_rate_pct=5.0, months_elapsed=7,
                                            months_contract=24, ratio=0.60)
    assert r.value == expected("C01")


def test_c02_fixed_band_is_not_a_formula():
    """구간표 첫 행은 고정값이다. 산식을 적용하면 틀린다."""
    r = calc.savings_early_termination_rate(base_rate_pct=5.0, fixed_rate_pct=0.1)
    assert r.value == expected("C02")


def test_c03_min_guarantee_wins():
    """형태 C: 산출값이 최저보장보다 작으면 최저보장이 답이다."""
    r = calc.savings_early_termination_rate(base_rate_pct=2.0, days_elapsed=120,
                                            days_contract=365, ratio=0.5, min_rate_pct=0.5)
    assert r.value == expected("C03")
    assert r.warnings, "최저보장이 적용된 사실을 답변에 남겨야 한다"


def test_c04_rounding_rule_changes_the_answer():
    """총액 절사와 건별 절사가 다르다. 하나로 강요하지 않는다."""
    kw = dict(amount=300000, rate_pct=5.0, maturity="2027-01-15",
              deposit_dates=[f"2026-{m:02d}-15" for m in range(1, 13)])
    assert calc.savings_maturity_interest(**kw).value == expected("C04")
    assert calc.savings_maturity_interest(**kw, per_deposit_truncate=True).value == alt("C04", "건별")
    assert calc.savings_maturity_interest(**kw, tax="lump").value == alt("C04", "세후(15.4%")
    assert calc.savings_maturity_interest(**kw, tax="per_component").value == alt("C04", "세후(소득세")


def test_c05_compound_vs_simple():
    kw = dict(principal=10000000, rate_pct=3.0, months=12)
    assert calc.deposit_interest(**kw, mode="monthly_compound").value == expected("C05")
    assert calc.deposit_interest(**kw, mode="simple").value == alt("C05", "단리식 세전")
    assert calc.deposit_interest(**kw, mode="simple", tax="lump").value == alt("C05", "단리식 세후")


# ── 중도상환수수료 (5회차 과제 / 완성본 제공) ─────────────────────────
def test_c06_hana_printed_example():
    kw = dict(amount=100000000, fee_rate_pct=1.4, days_remaining=365, days_total=1095)
    assert calc.prepayment_fee(**kw).value == expected("C06")
    assert calc.prepayment_fee(**kw, leap_year=True).value == alt("C06", "윤년")


def test_c06_waiver_is_checked_before_the_formula():
    """만기까지 3개월 미만이면 0원이다. 산식부터 돌리면 숫자가 나와 틀린다."""
    r = calc.prepayment_fee(amount=100000000, fee_rate_pct=1.4, days_remaining=60,
                            days_total=1095, waiver_months=3, months_to_maturity=2)
    assert r.value == 0 and r.rules["waived"] is True


def test_c07_im_delinquency_printed_example():
    r = calc.delinquency_interest(principal=120000000, contract_rate_pct=5, penalty_add_pct=3,
                                  overdue_interest_amount=500000, months_overdue=2)
    assert r.value == expected("C07")


def test_c09_samsungfire_waiver_options():
    kw = dict(amount=100000000, fee_rate_pct=0.6, remaining_ratio=1 / 3)
    assert calc.prepayment_fee(**kw).value == expected("C09")
    assert calc.prepayment_fee(**kw, exempt_amount=20000000).value == alt("C09", "매년 10%")


# ── 카드 ──────────────────────────────────────────────────────────────
def test_c08_overseas_three_terms():
    r = calc.card_overseas_charge(usd=1000, tt_rate=1400, brand_fee_pct=1.0, service_fee_pct=0.25)
    assert r.value == expected("C08")


def test_c11_legal_cap_applies_and_is_disclosed():
    r = calc.delinquency_rate(normal_rate_pct=18.0)
    assert r.value == expected("C11")
    assert r.value != alt("C11", "캡 적용 전")
    assert any("법정최고" in w for w in r.warnings)


# ── 실손·암 ───────────────────────────────────────────────────────────
def test_c12_generation_changes_the_answer():
    """5세대는 공제 항목이 하나 더 있어 상급종합 답이 60,000 → 32,000 으로 바뀐다."""
    g5 = calc.silson_outpatient_payout(copay=80000, fixed_deductible=20000, health_copay_rate=0.60)
    g4 = calc.silson_outpatient_payout(copay=80000, fixed_deductible=20000)
    assert g5.value == expected("C12")
    assert g4.value == alt("C12", "상급종합 80,000원(4세대)")
    assert g5.value != g4.value


def test_c12_clinic_same_in_both_generations():
    kw = dict(copay=25000, fixed_deductible=10000)
    assert calc.silson_outpatient_payout(**kw, health_copay_rate=0.30).value == alt("C12", "의원 25,000원(5세대)")
    assert calc.silson_outpatient_payout(**kw).value == alt("C12", "의원 25,000원(4세대)")


def test_c13_severe_vs_nonsevere():
    assert calc.silson_noncovered_payout(amount=150000, kind="outpatient",
                                         fixed_deductible=30000, coinsurance_pct=30).value == expected("C13")
    assert calc.silson_noncovered_payout(amount=2000000, kind="inpatient",
                                         payout_pct=70).value == alt("C13", "중증 입원")
    assert calc.silson_noncovered_payout(amount=150000, kind="outpatient",
                                         fixed_deductible=50000, coinsurance_pct=50).value == alt("C13", "비중증 통원")
    assert calc.silson_noncovered_payout(amount=2000000, kind="inpatient",
                                         payout_pct=50).value == alt("C13", "비중증 입원")


def test_c14_waiting_period_before_reduction():
    assert calc.cancer_benefit(sum_insured=30000000, months_since_start=10).value == expected("C14")
    r = calc.cancer_benefit(sum_insured=30000000, months_since_start=2, days_since_start=60)
    assert r.value == alt("C14", "(2) 60일")
    assert r.rules["before_waiting"] is True


# ── 미답변 ────────────────────────────────────────────────────────────
def test_c15_surrender_value_is_not_calculable():
    """해약환급금은 산출방법서 영역이라 계산 함수가 없다. 숫자를 만들면 오답."""
    assert not hasattr(calc, "surrender_value")
    assert GOLDEN["C15"]["answerable"] is False


def test_blank_rate_leads_to_abstain():
    """하나은행 2014 설명서처럼 요율이 '( )%' 로 비어 있으면 거절해야 한다."""
    r = calc.prepayment_fee(amount=100000000, fee_rate_pct=None, days_remaining=365, days_total=1095)
    assert r.value is None and r.abstain_reason


@pytest.mark.parametrize("cid", sorted(GOLDEN))
def test_every_golden_item_has_basis(cid):
    """모든 계산 문항은 근거 문서와 기준일을 갖는다."""
    item = GOLDEN[cid]
    assert item["basis"], f"{cid}: 근거 없음"
    assert item["basis_date"], f"{cid}: 기준일 없음"
