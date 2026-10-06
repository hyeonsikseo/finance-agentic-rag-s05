# -*- coding: utf-8 -*-
"""에이전트 그래프. 상태도는 get_graph().draw_mermaid() 로 뽑아 슬라이드에 쓴다."""
from __future__ import annotations

import time

from langgraph.graph import END, StateGraph

from . import nodes as N
from .calc_node import calculate
from ..observability import callbacks


def build_agent_graph(checkpointer=None):
    g = StateGraph(N.AgentState)
    for name in ("preprocess", "rewrite", "selfquery", "retrieve", "grade",
                 "bump_retry", "answer", "abstain"):
        g.add_node(name, getattr(N, name))
    g.add_node("calc", calculate)

    g.set_entry_point("preprocess")
    g.add_edge("preprocess", "rewrite")
    g.add_edge("rewrite", "selfquery")
    g.add_edge("selfquery", "retrieve")
    g.add_edge("retrieve", "grade")
    # 계산은 grade 통과 후, 답변 전에 한다. 근거가 부실한 채로 계산하면 틀린 값을
    # 그럴듯하게 설명하게 된다.
    g.add_conditional_edges("grade", N.route_after_grade,
                            {"answer": "calc", "retry": "bump_retry", "abstain": "abstain"})
    g.add_edge("calc", "answer")
    g.add_edge("bump_retry", "rewrite")     # 상한은 route_after_grade 가 지킨다
    g.add_edge("answer", END)
    g.add_edge("abstain", END)
    return g.compile(checkpointer=checkpointer)


def ask(question: str, graph=None) -> dict:
    graph = graph or build_agent_graph()
    t0 = time.perf_counter()
    # 키가 없으면 빈 목록이라 아무 일도 일어나지 않는다.
    cfg = {"callbacks": cbs} if (cbs := callbacks()) else {}
    out = graph.invoke({"question": question}, cfg)
    out["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return out
