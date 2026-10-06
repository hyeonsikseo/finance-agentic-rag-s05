# -*- coding: utf-8 -*-
"""법령 상수 로더.

여기 있는 값은 문서에서 검색해 오는 값이 아니라 법령이 정한 상수다. 답변에는
"세율·한도는 법령 상수(as_of 기준)이며 검색된 문서의 근거가 아닙니다"를 함께 적는다.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from ..settings import get_settings


@lru_cache
def constants() -> dict[str, Any]:
    path = get_settings().data / "constants.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def get(path: str, default: Any = None) -> Any:
    """'tax.interest_income.total_rate' 처럼 점으로 찾는다."""
    node: Any = constants()
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def disclaimer() -> str:
    c = constants()["meta"]
    return f"세율·한도 등은 법령 상수({c['as_of']} 기준)이며 검색된 문서의 근거가 아닙니다."


def as_of() -> str:
    return constants()["meta"]["as_of"]
