# -*- coding: utf-8 -*-
"""계산 노드.

설계 원칙 한 줄: **LLM 은 파라미터만 뽑고, 계산은 순수 함수가 한다.**

모델에게 "계산해 줘"라고 하면 그럴듯하게 틀린다. 같은 '중도해지이율'이라도 산식이
세 가지이고, 절사 규칙과 월수 규칙이 은행마다 반대라서 그렇다. 그래서 모델의 역할을
"검색된 조항에서 요율·구간·최저이율·절사 규칙과 근거 조항 ID 를 뽑는 것"으로 좁힌다.

필수 파라미터가 문서에 없으면 계산하지 않는다. 하나은행 2014 설명서처럼 요율이
'( )%' 로 비어 있을 때 숫자를 만들어 내지 않는 유일한 방법이다.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..llm import get_llm, is_fake
from ..tools import calc

SPEC_PATH = Path(__file__).parent.parent / "tools" / "calc_specs.yaml"

# 계산 질문의 신호. 키워드만으로는 부족하지만, LLM 을 부르기 전 1차 거름망으로 쓴다.
CALC_HINTS = re.compile(
    r"얼마|계산|산출|이자|수수료|해약금|환급|공제|보험금|청구금액|연체이자|몇\s*%|몇\s*원")


@lru_cache
def specs() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def looks_like_calculation(question: str) -> bool:
    return bool(CALC_HINTS.search(question))


# 질문에 금액·기간 같은 값이 있는지 볼 때 값이 아닌 숫자: 연도·날짜(2014년 7월 1일, 2021.03), 조항 번호(제7조 제2항).
_NOT_A_VALUE = re.compile(
    r"\d{4}\s*년(\s*\d{1,2}\s*월(\s*\d{1,2}\s*일)?)?"          # 2014년, 2013년 7월 1일
    r"|\d{4}\s*[.\-/]\s*\d{1,2}(\s*[.\-/]\s*\d{1,2})?"        # 2021.03, 2024-10-17
    r"|\d{1,2}\s*월\s*\d{1,2}\s*일"                               # 7월 1일
    r"|제\s*\d+\s*(조|항|호)|\d+\s*(항|호|조)")
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def question_gives_values(question: str) -> bool:
    """질문이 계산에 쓸 값(금액·기간·요율)을 주는가. 연도·날짜·조항 번호는 값이 아니다.

    모델은 "예시값으로 대신하지 마라"는 규칙을 받고도 근거의 예시(1억 원, 2년 뒤)를 질문의 값으로
    뽑는 일이 있다(10/8 실측, "2014년 설명서 기준 중도상환수수료는?"). 그래서 코드에서 한 번 더 본다.
    """
    return bool(_NUMBER.search(_NOT_A_VALUE.sub(" ", question)))


class ExtractedParams(BaseModel):
    """검색된 조항에서 뽑아낸 계산 재료."""
    tool: str = Field(description="calc_specs.yaml 의 Tool 이름. 해당 없으면 빈 문자열")
    params: dict = Field(default_factory=dict, description="함수 인자. 문서에 없는 값은 넣지 않는다")
    basis_article: str = Field("", description="근거 조항 번호")
    basis_quote: str = Field("", description="근거가 된 원문 한 문장(요약 금지)")
    missing: list[str] = Field(default_factory=list, description="문서나 질문에서 찾지 못한 필수 항목")


TOOL_LIST = "\n".join(
    f"- {k}: {v['label']}  필수={v.get('required', [])}"
    + (f"  그 밖에={list(v['from_document'])}" if v.get("from_document") else "")
    for k, v in specs().items() if k != "not_calculable")

NOT_CALCULABLE = "\n".join(
    f"- {k}: {v['reason']}" for k, v in specs()["not_calculable"].items())

EXTRACT = ChatPromptTemplate.from_messages([
    ("system",
     "너는 한국 금융문서에서 계산 파라미터를 뽑는 추출기다. 계산은 하지 마라.\n\n"
     f"쓸 수 있는 Tool:\n{TOOL_LIST}\n\n"
     f"계산하면 안 되는 것(tool 을 비우고 missing 에 이유를 적어라):\n{NOT_CALCULABLE}\n\n"
     "규칙:\n"
     "1. params 에는 근거에서 실제로 읽은 값만 넣는다. 추측하거나 일반 상식으로 채우지 마라.\n"
     "2. 요율이 '( )%' 처럼 비어 있으면 그 이름을 missing 에 넣는다.\n"
     "3. 질문이 주는 값(금액·기간)은 params 에 넣어도 된다. 기간은 함수가 받는 단위로 환산한다"
     "(예: '3년 만기 중 2년 뒤 상환' → days_remaining 365, days_total 1095). 숫자는 숫자형으로 넣는다.\n"
     "4. basis_quote 는 근거 원문을 그대로 옮긴다. 요약하지 마라.\n"
     "5. 질문이 금액·기간을 주지 않으면 근거의 예시값으로 대신하지 마라. 그 이름을 missing 에 넣는다."),
    ("human", "질문: {question}\n\n--- 근거 시작 ---\n{context}\n--- 근거 끝 ---"),
])


def _call(tool: str, params: dict) -> calc.CalcResult:
    spec = specs().get(tool)
    if not spec:
        return calc.CalcResult(None, "", abstain_reason=f"알 수 없는 Tool: {tool}")
    fn = getattr(calc, spec["function"].split(".")[-1], None)
    if fn is None:
        return calc.CalcResult(None, "", abstain_reason=f"구현되지 않은 Tool: {tool}")
    missing = [k for k in spec.get("required", []) if params.get(k) is None]
    if missing:
        where = "질문" if _from_question(spec, missing) else "문서"
        return calc.CalcResult(
            None, "", abstain_reason=f"{where}에서 값을 찾지 못했습니다: {', '.join(missing)}")
    try:
        return fn(**_coerce(params))
    except TypeError as e:
        return calc.CalcResult(None, "", abstain_reason=f"파라미터가 맞지 않습니다: {e}")
    except Exception as e:
        # 모델이 넘긴 값으로 함수가 죽어도 그래프는 계속 간다. 계산만 포기하고 이유를 남긴다.
        return calc.CalcResult(None, "", abstain_reason=f"계산에 실패했습니다: {type(e).__name__}: {e}")


def _from_question(spec: dict, missing: list[str]) -> bool:
    """빠진 항목이 문서가 아니라 질문이 줘야 하는 값(금액·기간)인가. from_document 에 없는 필수 항목이 그것이다."""
    return any(m not in spec.get("from_document", {}) for m in missing)


def _known_missing(spec: dict, missing: list[str]) -> list[str]:
    """모델이 적은 missing 을 필수 파라미터 이름으로 좁힌다.

    required 에 있는 이름이 문장 안에 들어 있으면 그 이름으로 본다. required 가 아닌 것은 버린다.
    """
    required = list(spec.get("required", []))
    out = []
    for m in missing:
        for k in required:
            if k in m and k not in out:
                out.append(k)
    return out


def _coerce(params: dict) -> dict:
    """모델이 '10000' 이나 '1,095' 처럼 문자열로 준 숫자를 숫자로 바꾼다. 그대로 넘기면 서식 지정에서 죽는다."""
    out = {}
    for k, v in params.items():
        if isinstance(v, str):
            s = v.replace(",", "").strip()
            if re.fullmatch(r"-?\d+", s):
                v = int(s)
            elif re.fullmatch(r"-?\d+\.\d+", s):
                v = float(s)
            elif s.lower() in ("true", "false"):
                v = s.lower() == "true"
        out[k] = v
    return out


def calculate(state: dict) -> dict:
    """상태에 calc 결과를 붙인다. 계산 질문이 아니면 아무것도 하지 않는다."""
    question = state.get("masked_question", "")
    hits = state.get("hits", [])
    trace = state.get("trace", []) + ["calc"]
    if not looks_like_calculation(question) or not hits:
        return {"trace": trace}

    llm = get_llm("extract", size="main")
    if is_fake(llm):
        # 키가 없으면 추출을 못 한다. 계산을 건너뛰되 그 사실을 남긴다.
        return {"trace": trace,
                "notices": state.get("notices", []) + ["계산 파라미터 추출은 LLM 키가 필요합니다."]}

    from .nodes import _context, policy
    try:
        out = (EXTRACT | llm.with_structured_output(ExtractedParams, method="function_calling")).invoke(
            {"question": question, "context": _context(hits)})
        ext = out if isinstance(out, ExtractedParams) else ExtractedParams(**dict(out))
    except Exception as e:
        return {"trace": trace, "notices": state.get("notices", []) + [f"파라미터 추출 실패: {e}"]}

    if not ext.tool:
        reason = policy()["abstain"]["out_of_document"]
        return {"calc": {"abstain_reason": reason, "missing": ext.missing}, "trace": trace,
                "notices": state.get("notices", []) + [reason]}

    spec = specs().get(ext.tool, {})
    # 모델이 missing 에 적는 이름은 자유 문장이다("윤년이 끼는 경우 days_remaining", "입원 의료비 보험금 …").
    # 함수가 아는 이름으로 옮기고, 필수가 아닌 항목(from_document 의 선택 파라미터)은 빠져도 계산을 막지 않는다.
    # 선택 항목이 정말 필요하면 함수가 직접 "찾지 못했다"고 말한다(10/8 실측: C06 · C07 · C13 이 여기서 막혔었다).
    ext.missing = _known_missing(spec, ext.missing)
    from_question = [k for k in spec.get("required", []) if k not in spec.get("from_document", {})]
    if from_question and not question_gives_values(question):
        # 질문이 금액을 안 줬는데 params 에 금액이 있다면 근거의 예시값이다. 계산하지 않는다.
        ext.missing = sorted(set(ext.missing) | set(from_question))

    if ext.missing:
        # 질문이 줘야 할 값(금액·기간)이 없는 것과 문서의 요율이 비어 있는 것은 다른 안내다.
        key = "missing_in_question" if _from_question(spec, ext.missing) else "missing_parameter"
        msg = policy()["abstain"].get(key, policy()["abstain"]["missing_parameter"]).format(field=", ".join(ext.missing))
        return {"calc": {"abstain_reason": msg, "missing": ext.missing}, "trace": trace,
                "notices": state.get("notices", []) + [msg]}

    result = _call(ext.tool, ext.params)
    notices = list(state.get("notices", [])) + result.warnings
    if result.abstain_reason:
        notices.append(result.abstain_reason)
    return {"calc": {"tool": ext.tool, "params": ext.params,
                     "basis_article": ext.basis_article, "basis_quote": ext.basis_quote,
                     **result.to_dict()},
            "notices": notices, "trace": trace}
