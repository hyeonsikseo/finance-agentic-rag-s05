#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""적대적 문항 5개를 에이전트에 넣고 결과를 기록한다 → results/adversarial.json

    python scripts/adversarial_run.py

거절했는지만 세지 않는다. 문항마다 "하지 말았어야 할 것"(시스템 프롬프트 노출, 계좌번호 생성,
단일 수치 단정 …)이 답변에 나타났는지를 본다. 규칙은 src/finrag/eval/adversarial.py 에 있다.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "pipelines"))


def main() -> int:
    from finrag.eval import adversarial
    from finrag.llm import get_llm, is_fake
    from finrag.settings import get_settings
    import agentic

    fake = is_fake(get_llm("answer"))
    if fake:
        print("[주의] LLM 키가 없어 가짜 모델로 돕니다. 답변이 고정 문구라 전부 실패로 기록됩니다.\n")
    res = adversarial.run(agentic.build())
    res["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    res["llm"] = "fake" if fake else get_settings().llm_model_main
    for r in res["rows"]:
        mark = "O" if r["passed"] else "X"
        why = f"  어긴 것: {r['violated']}" if r["violated"] else ("" if r["passed"] else "  (지켜야 할 신호가 없음)")
        print(f"  {mark} {r['id']} {r['category']}{why}")
    print(f"\n통과 {res['pass_rate']:.0%} ({sum(r['passed'] for r in res['rows'])}/{res['n']})")
    out = get_settings().results_dir / "adversarial.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("→", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
