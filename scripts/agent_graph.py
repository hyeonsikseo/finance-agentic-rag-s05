#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""에이전트 그래프의 상태도를 mermaid 로 찍는다. 그림을 손으로 그리지 않으므로 코드와 어긋나지 않는다.

    python scripts/agent_graph.py            # mermaid 텍스트 (https://mermaid.live 에 붙이면 그림)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

if __name__ == "__main__":
    from finrag.agent.graph import build_agent_graph
    print(build_agent_graph().get_graph().draw_mermaid())
