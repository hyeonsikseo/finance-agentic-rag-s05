# 5회차 과제

필수 둘, 선택 하나입니다. 다음 회차 전까지 냅니다. 끝났는지는 `make check-s05` 가 **5/5** 인지로 압니다. 다음 회차(평가 분석)가 오늘 결과 파일 위에서 돌아가므로 `results/agentic.json` 이 없으면 다음 수업이 안 됩니다.

## 필수 1. 전체 실행 — 수업에서 끝냈으면 0분, 아니면 15분

채울 자리 넷(`nodes.grade`, `nodes.route_after_grade`, `selfquery.extract_filters`, `calc.savings_early_termination_rate`)이 채워졌으면 이렇게 끝납니다.

```bash
make test          # 98개 전부 통과
make agentic       # 40문항 → results/agentic.json. 약 12분
make adversarial   # 적대적 5문항 → results/adversarial.json. 1분
make check-s05     # 4/5. 마지막 항목은 필수 2 입니다
```

Windows 는 [install.md](../install.md) 의 PowerShell 명령을 씁니다. 수업에서 못 채운 함수가 있으면 강사가 수업 뒤 올리는 **solution 브랜치**를 봅니다.

https://github.com/hyeonsikseo/finance-agentic-rag-s05/tree/solution/src/finrag

보고 베끼는 게 아니라 **읽고 닫은 다음 자기 손으로 다시 씁니다.**

`results/agentic.json` 의 `overall` 에서 넷을 적어 두세요. `mrr`, `answer_rate`, `false_refusal_rate`, `abstain_accuracy`. 키 없이 돌렸으면 파일에 `warning` 이 들어가고 뒤의 셋이 의미가 없으니, 키를 넣고 다시 돌립니다.

## 필수 2. 에이전트 정책 1쪽 — 25분

오늘 그래프가 따르는 정책을 **한 쪽**으로 씁니다. 값은 `src/finrag/agent/policy.yaml` 과 `.env` 에 이미 있습니다. 이 문서는 **왜 그 값인지**를 적는 곳입니다.

1. `docs/templates/agent_policy.md` 를 `docs/agent_policy.md` 로 복사합니다.
2. 빈칸(`____`)을 전부 채웁니다. `make check-s05` 가 빈칸이 남았는지 셉니다.

채울 때 볼 것:

- **재검색 상한.** 실측 1 에서 상한 0 과 2 로 잰 답변률·오거절률·평균 시간 두 줄이 근거입니다. 상한을 늘리면 오거절률은 내려가고 시간은 오릅니다. 여러분이 고른 값과 이유를 적습니다. 기본값 2 를 그대로 골라도 됩니다. 이유가 있으면 됩니다.
- **지연 예산.** `results/agentic.json` 의 `latency_ms_avg` 와 `latency_ms_p95`, 4회차 `hybrid.json` 의 같은 값을 넣습니다. 검색과 리랭킹이 얼마, LLM 이 얼마인지는 둘의 차이로 어림합니다.
- **미답변 문구.** `policy.yaml` 의 `abstain` 여섯 줄을 옮기고, 고객이 읽는 문장으로 괜찮은지 한 번 소리 내어 읽어 봅니다. 고칠 것이 있으면 yaml 도 같이 고칩니다.
- **에스컬레이션.** `policy.yaml` 의 `escalation.triggers` 일곱 낱말이 왜 자동 응답으로 끝내면 안 되는지 한 줄씩.
- **고지** 체크 다섯 개는 코드에서 어느 줄이 붙이는지 찾아보고 체크합니다(`nodes.answer`, `nodes.retrieve`, `calc_node`).
- **이번 판에서 바꾼 것.** 아무것도 안 바꿨으면 "없음. 처음 판"이라고 적고 `policy_version` 을 그대로 둡니다. 바꿨으면 `policy.yaml` 의 `policy_version` 도 올립니다.

길이는 한 쪽. 완성 예시는 과제 마감 뒤 `docs/session5/examples/` 에 올립니다.

## 선택. 자기 질문 5개를 에이전트에 — 15분

4회차 선택 과제로 적어 둔 Self-Query 대상 질문 5개(`docs/selfquery_questions.md`)가 있으면 그것을, 없으면 자기 코퍼스에서 질문 5개를 골라 `make ask` 에 넣습니다. 질문마다 네 칸을 표로 적습니다. 뽑힌 필터가 맞는가 / 판정과 재검색 횟수 / 거절했다면 거절이 맞는가 / 답변에 근거 번호가 붙었는가. 틀리게 뽑힌 필터가 있으면 `selfquery.SYSTEM` 프롬프트의 어느 줄을 고치면 될지 한 줄 적습니다. `docs/selfquery_questions.md` 에 이어서 씁니다.

## 제출

**마감: 10월 9일(금) 밤.** 6회차(10월 10일 토 10:00)에서 여러분의 `results/agentic.json` 을 한 표에 놓고 읽습니다. 하루뿐이라 필수 1(전체 실행)은 수업 당일 밤에 걸어 두는 것이 좋습니다.

1. `make check-s05` 가 5/5 인지 봅니다.
2. 커밋하고 자기 포크에 올립니다.

```bash
git add src/finrag/agent/nodes.py src/finrag/agent/selfquery.py src/finrag/tools/calc.py results/agentic.json results/adversarial.json results/check_s05.json docs/agent_policy.md
git commit -m "5회차 과제"
git push
```

3. 자기 포크 URL(`https://github.com/<계정>/finance-agentic-rag-s05`)를 디스코드에 올립니다. 포크 없이 받았으면 위 파일들을 zip 으로 묶어 올립니다. `.env` 는 올리지 않습니다(커밋되지 않게 되어 있습니다).

## check-s05 가 보는 것

| 항목 | 통과 기준 |
|---|---|
| 계산 골든 테스트 | `tests/test_calc_golden.py` 32개가 전부 통과한다 |
| agentic.json 존재 | `results/agentic.json` 에 40문항이 있다 |
| 미답변형 거절 기록 | 미답변 정확도 · 오거절률 · 답변률이 기록되어 있다 |
| 적대적 5문항 기록 | `results/adversarial.json` 에 5문항 결과가 있다 |
| 에이전트 정책 문서 | `docs/agent_policy.md` 가 있고 빈칸(`____`)이 없다 |

## 마감 뒤 강사가 올리는 것

`docs/session5/examples/` 에 에이전트 정책 1쪽 완성본을 올립니다. 받는 법은 같습니다.

```bash
git pull upstream main
```
