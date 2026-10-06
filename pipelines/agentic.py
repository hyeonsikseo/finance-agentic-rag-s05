#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agentic: 자기교정 루프 + Self-Query + 계산 Tool. 5회차 결과."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from finrag.agent.graph import build_agent_graph   # noqa: E402


def build():
    from langchain_core.callbacks import UsageMetadataCallbackHandler
    graph = build_agent_graph()

    def run(question: str) -> dict:
        # 문항마다 콜백을 새로 만든다. 노드 안의 LLM 호출이 전부 이 콜백에 모델별 토큰을 더한다.
        # 6회차 ROI 가 이 숫자(usage)로 문항당 비용을 계산한다.
        usage = UsageMetadataCallbackHandler()
        out = graph.invoke({"question": question}, {"callbacks": [usage]})
        return {"chunk_ids": out.get("chunk_ids", []), "hits": out.get("hits", []),
                "answer": out.get("answer"), "abstained": bool(out.get("abstained")),
                "grade": out.get("grade"), "retry_count": out.get("retry_count", 0),
                "notices": out.get("notices", []), "trace": out.get("trace", []),
                "filters": out.get("filters"), "calc": out.get("calc"),
                "usage": usage.usage_metadata}
    return run


if __name__ == "__main__":
    import argparse

    from finrag.eval import harness

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="앞에서 N 문항만. 결과는 results/agentic_sample.json 에 따로 저장한다")
    ap.add_argument("--verbose", action="store_true", help="문항마다 한 줄씩 찍는다")
    args = ap.parse_args()

    name = "agentic_sample" if args.limit else "agentic"
    res = harness.run(build(), name, limit=args.limit or None, verbose=args.verbose)
    harness.print_summary(res)
    print("→", harness.save(res))
