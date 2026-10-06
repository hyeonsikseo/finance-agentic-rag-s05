#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""회차 확인.

    python scripts/check_session.py 5        →  results/check_s05.json

회차 끝에 이걸 돌려서 나온 JSON 을 커밋합니다. 그 파일이 제출물입니다.
강사는 그 파일들을 모아 표로 보고 빨간 칸만 확인합니다.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def ok(cond: bool, detail: str = "") -> dict:
    return {"ok": bool(cond), "detail": detail}


def _json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for l in path.open(encoding="utf-8") if l.strip())


CHUNK_ID = re.compile(r"^[^#]+#[^#]*#\d+$")
GATE_VERDICTS = {"pass", "reparse", "ocr"}


def check_s02() -> dict:
    from finrag.settings import get_settings
    s = get_settings()
    path = s.chunks_dir / "chunks.jsonl"
    chunks = [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()] if path.exists() else []
    sample = chunks[:500]

    required = {"chunk_id", "doc_id", "text", "article", "page_start"}
    missing_fields = [c.get("chunk_id", "?") for c in sample if not required <= set(c)]
    meta_required = {"doc_type", "issuer", "effective_from", "parser", "validation"}
    missing_meta = [c.get("chunk_id", "?") for c in sample
                    if not meta_required <= set(c.get("meta", {}))]
    bad_verdict = [c.get("chunk_id", "?") for c in sample
                   if c.get("meta", {}).get("validation") not in GATE_VERDICTS]

    ids = [c["chunk_id"] for c in chunks if "chunk_id" in c]
    dup = len(ids) - len(set(ids))
    bad_id = [i for i in ids if not CHUNK_ID.match(i)]

    # 1회차 질문에 근거 청크를 붙였는가. 붙였다면 그 ID 가 실제로 존재해야 한다.
    q = s.golden_dir / "student_q.jsonl"
    qs = []
    if q.exists():
        for line in q.open(encoding="utf-8"):
            if line.strip():
                try:
                    qs.append(json.loads(line))
                except json.JSONDecodeError:
                    qs.append({})
    id_set = set(ids)
    with_gold = [r for r in qs if r.get("gold_chunk_ids")]
    dangling = [g for r in with_gold for g in r["gold_chunk_ids"] if g not in id_set]

    return {
        "청크 생성": ok(len(chunks) >= 1000, f"{len(chunks):,}개"),
        "청크 필수 필드": ok(not missing_fields,
                      f"누락 {len(missing_fields)}건: {', '.join(missing_fields[:2])}"
                      if missing_fields else f"{sorted(required)}"),
        "메타데이터 부착": ok(not missing_meta,
                       f"누락 {len(missing_meta)}건: {', '.join(missing_meta[:2])}"
                       if missing_meta else f"{sorted(meta_required)}"),
        "게이트 판정 기록": ok(bool(sample) and not bad_verdict,
                        f"판정 없는 청크 {len(bad_verdict)}건" if bad_verdict else
                        # 분포는 표본이 아니라 전체로 센다. 앞 500개는 대개 한 문서에서
                        # 나와 "reparse 500" 처럼 한쪽으로 쏠려 보인다.
                        ", ".join(f"{k} {v:,}" for k, v in sorted(
                            Counter(c.get("meta", {}).get("validation") for c in chunks).items()
                            if chunks else []))),
        "청크 ID 유일·형식": ok(dup == 0 and not bad_id,
                          f"중복 {dup}건 · 형식 위반 {len(bad_id)}건"),
        "질문에 근거 청크": ok(len(with_gold) >= 3 and not dangling,
                        f"{len(with_gold)}/{len(qs)}문항에 gold_chunk_ids"
                        + (f" · 없는 ID {len(dangling)}건" if dangling else "")),
    }


def _qdrant_points() -> tuple[int, str]:
    """포인트 수를 센다.

    임베디드 Qdrant 는 한 프로세스만 붙을 수 있다. API 서버가 떠 있으면 여기서
    잠금 오류가 난다. 그럴 때는 /health 로 물어본다. "API 를 끄고 다시 하세요"는
    답이 아니다 — 확인 스크립트는 서버가 떠 있든 아니든 돌아야 한다.
    """
    from finrag.index import qdrant
    try:
        return qdrant.count(), "직접 조회"
    except Exception as e:
        if "already accessed" not in str(e):
            return 0, f"오류: {type(e).__name__}"
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:8000/health", timeout=5) as r:
            return json.loads(r.read()).get("points", 0), "API /health 경유"
    except Exception:
        return 0, "임베디드 잠금 + API 미기동 (API 를 끄거나 켜고 다시 실행)"


def check_s03() -> dict:
    from finrag.settings import get_settings
    s = get_settings()
    rep = _json(s.data / "ingest_report.json") or {}
    res = _json(s.results_dir / "baseline.json") or {}
    points, how = _qdrant_points()

    routes = rep.get("routes", {})
    routed = sum(routes.values())
    verdicts = rep.get("verdicts", {})
    overall = res.get("overall", {})

    # ADR-002 는 3회차 과제다. 템플릿을 복사만 하고 빈칸(______)을 남겨 두면 안 낸 것이다.
    adr = s.root / "docs" / "adr" / "ADR-002-ingestion-graph.md"
    if not adr.exists():
        adr_ok = ok(False, "docs/adr/ADR-002-ingestion-graph.md 가 없다 (docs/templates/adr.md 를 복사해 채운다)")
    else:
        blanks = adr.read_text(encoding="utf-8").count("______")
        adr_ok = ok(blanks == 0, f"빈칸 {blanks}곳 남음" if blanks else f"{len(adr.read_text(encoding='utf-8')):,}자")

    # 코퍼스 전체를 돌렸는지 본다. 경로 합 = 문서 수만 보면 --only 로 1건만 돌려도
    # 통과한다(실제로 그렇게 통과했다).
    corpus = max(_lines(s.data / "documents.csv") - 1, 0)
    n_doc = rep.get("documents") or 0

    return {
        "인제스천 전체 처리": ok(routed == n_doc and corpus and n_doc >= corpus * 0.9,
                          f"문서 {n_doc}/{corpus}건 · 경로 합 {routed}"
                          + (f" · {routes}" if routes else "")
                          + ("  → --only 없이 전체를 돌리세요" if 0 < n_doc < corpus * 0.9 else "")),
        "게이트 3분기 동작": ok(len({v for v in verdicts if verdicts.get(v)}) >= 3,
                         f"{verdicts}" if verdicts else "판정 기록 없음"),
        "Qdrant 포인트": ok(points > 0, f"{points:,}개 ({how})"),
        "baseline Recall@5": ok(overall.get("recall@5") is not None,
                                f"{overall.get('recall@5')} (MRR {overall.get('mrr')})"),
        "유형별 분해": ok(len(res.get("by_type", {})) >= 5,
                     f"{len(res.get('by_type', {}))}개 유형"),
        "ADR-002": adr_ok,
    }


def check_s04() -> dict:
    from finrag.settings import get_settings
    s = get_settings()
    base = _json(s.results_dir / "baseline.json") or {}
    hyb = _json(s.results_dir / "hybrid.json") or {}
    # 리랭커가 실제로 사 주는 것은 "순서"다. Recall@5 는 이미 baseline 이 높아
    # 더 오를 자리가 없는 유형이 있다(조항번호형 baseline 100%). 그래서 순위 품질
    # 지표(MRR·Recall@1)로 판정한다. 통과시키려고 기준을 낮추는 게 아니라,
    # 애초에 그 지표가 이 단계가 개선하는 지표다.
    def m(res: dict, t: str, k: str):
        return res.get("by_type", {}).get(t, {}).get(k) if t else res.get("overall", {}).get(k)

    b_mrr, h_mrr = m(base, "조항번호형", "mrr"), m(hyb, "조항번호형", "mrr")
    b_all, h_all = m(base, "", "mrr"), m(hyb, "", "mrr")
    b_r1, h_r1 = m(base, "", "recall@1"), m(hyb, "", "recall@1")
    # ADR-003 은 4회차 과제다. 템플릿을 복사만 하고 빈칸(______)을 남겨 두면 안 낸 것이다.
    adr = s.root / "docs" / "adr" / "ADR-003-hybrid-retrieval.md"
    if not adr.exists():
        adr_ok = ok(False, "docs/adr/ADR-003-hybrid-retrieval.md 가 없다 (docs/templates/adr.md 를 복사해 채운다)")
    else:
        blanks = adr.read_text(encoding="utf-8").count("______")
        adr_ok = ok(blanks == 0, f"빈칸 {blanks}곳 남음" if blanks else f"{len(adr.read_text(encoding='utf-8')):,}자")
    return {
        "hybrid.json 존재": ok(bool(hyb), f"{hyb.get('n', 0)}문항"),
        "조항번호형 MRR ≥ baseline": ok(b_mrr is not None and h_mrr is not None and h_mrr >= b_mrr,
                                    f"baseline {b_mrr} → hybrid {h_mrr}"),
        "전체 MRR ≥ baseline": ok(b_all is not None and h_all is not None and h_all >= b_all,
                                f"{b_all} → {h_all}"),
        "전체 Recall@1 ≥ baseline": ok(b_r1 is not None and h_r1 is not None and h_r1 >= b_r1,
                                     f"{b_r1} → {h_r1}"),
        "리랭커 지연 기록": ok(any(r.get("latency_ms") for r in hyb.get("rows", [])),
                        f"평균 {hyb.get('overall', {}).get('latency_ms_avg')}ms"),
        "ADR-003": adr_ok,
    }


def check_s05() -> dict:
    from finrag.settings import get_settings
    s = get_settings()
    ag = _json(s.results_dir / "agentic.json") or {}
    adv = _json(s.results_dir / "adversarial.json") or {}
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_calc_golden.py", "-q"],
                           cwd=ROOT, capture_output=True, timeout=300, text=True)
        tests_ok, detail = r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout else ""
    except Exception as e:
        tests_ok, detail = False, str(e)
    o = ag.get("overall", {})
    abst = o.get("abstain_accuracy")
    # 정책 1쪽은 5회차 과제다. 템플릿을 복사만 하고 빈칸(____)을 남겨 두면 안 낸 것이다.
    pol = ROOT / "docs" / "agent_policy.md"
    if not pol.exists():
        pol_ok = ok(False, "docs/agent_policy.md 가 없다 (docs/templates/agent_policy.md 를 복사해 채운다)")
    else:
        blanks = pol.read_text(encoding="utf-8").count("____")
        pol_ok = ok(blanks == 0, f"빈칸 {blanks}곳 남음" if blanks else f"{len(pol.read_text(encoding='utf-8')):,}자")
    return {
        "계산 골든 테스트": ok(tests_ok, detail),
        "agentic.json 존재": ok(ag.get("n", 0) >= 40, f"{ag.get('n', 0)}문항" + (" (가짜 모델)" if ag.get("llm") == "fake" else "")),
        "미답변형 거절 기록": ok(abst is not None,
                          f"미답변 정확도 {abst}, 오거절률 {o.get('false_refusal_rate')}, 답변률 {o.get('answer_rate')}"),
        "적대적 5문항 기록": ok(adv.get("n", 0) >= 5, f"통과 {adv.get('pass_rate')}" if adv else "results/adversarial.json 없음 (make adversarial)"),
        "에이전트 정책 문서": pol_ok,
    }


CHECKS = {2: check_s02, 3: check_s03, 4: check_s04, 5: check_s05}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=int, choices=sorted(CHECKS))
    args = ap.parse_args()

    try:
        checks = CHECKS[args.session]()
    except Exception as e:
        checks = {"실행 실패": ok(False, f"{type(e).__name__}: {e}")}

    passed = sum(1 for v in checks.values() if v["ok"])
    print(f"\ncheck-s{args.session:02d}   {passed}/{len(checks)} 통과")
    for k, v in checks.items():
        print(f"  {'O' if v['ok'] else 'X'}  {k:28} {v['detail']}")

    out = ROOT / "results" / f"check_s{args.session:02d}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "session": args.session,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "passed": passed, "total": len(checks), "checks": checks},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {out.relative_to(ROOT)}  (이 파일을 커밋하세요)")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
