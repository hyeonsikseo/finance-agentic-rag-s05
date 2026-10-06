# 약관부터 답변까지 — 5회차

금융 문서 특화 Agentic RAG 수업의 5회차 레포지토리입니다. 4회차 레포지토리(finance-agentic-rag-s04)와는 별개이고 새로 받습니다. 1~4회차 내용은 그대로 들어 있고, 4회차에 채운 자리 셋(`tokenize`, `rrf`, `search` 의 합치기)은 **강사가 작성한 코드로 채워져** 있습니다. 자기 코드로 바꿔 써도 되지만, 그러면 검색 성능이 강사 값과 조금 달라질 수 있습니다.

## 5회차에 할 일

1. 설치합니다. 4회차 폴더에서 문서·청크·모델·결과를 복사하고, 메타코드에서 받은 OpenAI 키를 `.env` 에 넣습니다. 새로 받는 것은 없습니다. → [docs/install.md](docs/install.md)
2. 수업 앞부분은 노트북으로 에이전트 그래프의 상태도와 노드 셋(개인정보 마스킹 · 재작성 · 판정)을 봅니다. → `make notebook`
3. 수업 중반은 채울 자리 넷(`grade` · `route_after_grade`, `extract_filters`, `savings_early_termination_rate`)을 채우고, 10문항으로 재검색 경로를 읽습니다. → [docs/session5/lab.md](docs/session5/lab.md)
4. 수업 뒷부분은 40문항을 에이전트로 다시 풀어(`results/agentic.json`) 답변률·오거절률·미답변 정확도를 읽고, 적대적 문항 5개를 넣어 봅니다.
5. 과제는 필수 둘(전체 실행, 에이전트 정책 1쪽)에 선택 하나이고, `make check-s05` 가 5/5 이면 끝입니다. → [docs/session5/homework.md](docs/session5/homework.md)

## 폴더

| 폴더 | 무엇 |
|---|---|
| `docs/install.md` | 설치. 4회차 폴더에서 복사하는 단계와 `.env` 에 키를 넣는 단계 |
| `docs/session5/` | 실습 순서(lab.md)와 과제(homework.md) |
| `docs/templates/agent_policy.md` | 과제 "에이전트 정책 1쪽"의 템플릿. `docs/agent_policy.md` 로 복사해 채웁니다 |
| `docs/adr/ADR-004-agent-policy.md` | 재검색 상한과 미답변 정책을 왜 그렇게 정했는지. 강사가 쓴 완성본 |
| `notebooks/s05_agent.ipynb` | 에이전트 루프 20분. 수업 1~2부. Qdrant 를 열지 않습니다 |
| `src/finrag/agent/nodes.py` | 그래프의 노드들. 채울 것 `grade` 와 `route_after_grade`(실습 1)가 여기 있습니다 |
| `src/finrag/agent/selfquery.py` | Self-Query. 채울 것 `extract_filters`(실습 2) |
| `src/finrag/tools/calc.py` | 계산 함수들. 채울 것 `savings_early_termination_rate`(실습 3). 중도상환수수료 등 나머지는 완성본 |
| `src/finrag/agent/graph.py`, `calc_node.py`, `policy.yaml` | 그래프 조립, 계산 노드(파라미터 추출), 정책(거절 문구·상한·PII 정규식). 읽기만 합니다 |
| `src/finrag/tools/calc_specs.yaml` | 계산 Tool 명세. 모델이 어떤 파라미터를 문서에서 뽑아야 하는지 |
| `pipelines/agentic.py` | 골든셋 40문항을 에이전트로 풀어 `results/agentic.json` 을 만듭니다 |
| `scripts/ask.py`, `agent_graph.py`, `adversarial_run.py` | 질문 하나 넣어 보기, 상태도 찍기, 적대적 5문항 |
| `tests/test_agent.py`, `tests/test_calc_golden.py` | 채운 것이 맞는지 보는 테스트. 2~4회차 테스트도 그대로 돕니다 |
| `scripts/check_session.py` | 5회차 확인. 결과 파일이 제출물입니다 |

## 명령

```bash
make setup           # 패키지 설치. 4회차 폴더가 있으면 1분
make index           # 4회차 청크를 Qdrant 에 넣는다 (스냅샷 재사용). 10초
make notebook        # 에이전트 노트북 열기
make test            # 자동 채점. 2~4회차 51개 + 5회차 51개. 채우기 전에는 16개 실패가 정상입니다
make ask Q="질문"     # 질문 하나를 에이전트에 넣고 경로·판정·근거·답변을 본다
make graph           # 상태도를 mermaid 텍스트로
make agentic-sample  # 골든셋 앞 10문항 → results/agentic_sample.json. 약 3분
make agentic         # 40문항 전부 → results/agentic.json (오늘 결과물). 약 12분. 휴식에 돌립니다
make adversarial     # 적대적 5문항 → results/adversarial.json. 1분
make check-s05       # 결과물이 조건 5개를 만족하는지 확인 → results/check_s05.json
```

Windows 에서는 `make` 가 없으니 [docs/install.md](docs/install.md) 의 PowerShell 명령을 씁니다.

## 원본 문서가 레포지토리에 없는 이유

약관과 상품설명서는 각 금융회사의 저작물이라 다시 나눠 줄 수 없습니다. 레포지토리에는 "무엇을 어디서 받는지"만 있고, 각자 원 출처에서 받거나 4회차 폴더에서 복사합니다. 자세한 것은 [data/README.md](data/README.md) 에 있습니다. 같은 이유로 문서 본문이 들어 있는 `data/chunks/`, `data/ocr_cache/`, `data/bm25_cache/` 도 레포지토리에 올리지 않습니다.
