#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""질문 하나를 에이전트 그래프에 넣고 무슨 일이 있었는지 본다.

    python scripts/ask.py "카카오뱅크 정기예금을 120일 만에 해지하면 중도해지이율은?"
    python scripts/ask.py "2013년 판 기준 하나은행 여신거래기본약관 제7조 기한의 이익 상실 사유는?"
    python scripts/ask.py "ABL 암보험을 5년 뒤 해지하면 해약환급금은 얼마인가요?"      # 거절이 맞다
    MAX_RETRIES=0 python scripts/ask.py "..."                                      # 상한을 바꿔 본다

찍는 것: 지나간 노드(trace), 뽑힌 필터, 판정, 재검색 횟수, 근거 상위 3개, 계산 결과, 고지, 답변, 시간.
키가 없으면 가짜 모델로 돌아 판정·답변은 의미가 없고 검색과 경로만 본다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--json", action="store_true", help="상태 전체를 JSON 으로")
    args = ap.parse_args()

    from finrag.agent.graph import ask
    from finrag.llm import get_llm, is_fake

    if is_fake(get_llm("grade", size="small")):
        print("[주의] LLM 키가 없어 가짜 모델로 돕니다. 판정·필터·답변은 의미가 없습니다. 경로만 보세요.\n")

    out = ask(args.question)
    if args.json:
        print(json.dumps({k: v for k, v in out.items() if k != "hits"}, ensure_ascii=False, indent=1))
        return 0

    print(f"질문      {args.question}")
    if out.get("masked_question") != args.question:
        print(f"마스킹 뒤 {out.get('masked_question')}")
    print(f"재작성    {out.get('query')}")
    flt = {k: v for k, v in (out.get("filters") or {}).items() if v not in (None, "", True)}
    print(f"필터      {flt or '(없음)'}")
    print(f"경로      {' → '.join(out.get('trace', []))}")
    print(f"판정      {out.get('grade')}   재검색 {out.get('retry_count', 0)}회   {out.get('latency_ms', 0):,.0f}ms")
    print("근거 상위 3")
    for i, h in enumerate(out.get("hits", [])[:3], start=1):
        print(f"  [{i}] {h.get('doc_id')} {h.get('article') or '-'} p{h.get('page_start')} "
              f"{h.get('effective_from') or ''}  {' '.join(h.get('text', '').split())[:50]}")
    c = out.get("calc") or {}
    if c:
        if c.get("value") is not None:
            print(f"계산      {c.get('tool')} → {c['value']}{c.get('unit', '')}")
            for s in c.get("steps", []):
                print(f"            {s}")
        else:
            print(f"계산      (안 함) {c.get('abstain_reason', '')}")
    for n in out.get("notices", []):
        print(f"고지      {n}")
    if out.get("escalation_reason"):
        print(f"에스컬레이션  {out['escalation_reason']}")
    print(f"\n{'거절' if out.get('abstained') else '답변'}\n{out.get('answer', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
