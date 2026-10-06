.PHONY: help setup download models models-rerank embeddings notebook test agentic-sample agentic adversarial graph ask ingest-sample ingest index baseline bm25-compare hybrid-norerank hybrid rerank-sweep chunk chunk-sample profile
PY := .venv/bin/python
export HF_HOME := ./models
EMB_URL := https://github.com/hyeonsikseo/finance-agentic-rag-s03/releases/download/s03/BAAI_bge-m3.npz
SAMPLE := --only hana_credit_terms_2009 --only fss_deposit_terms_2024_pdf --only knia_3500_scan --only kakao_deposit_terms_2024 --only hanacard_std_2017 --only law_silson_std_hwp

help:
	@echo "make setup           파이썬 3.12 와 패키지 설치 (3회차 폴더가 있으면 2~3분)"
	@echo "make download        문서 다운로드 (3회차 폴더에서 복사했으면 몇 초)"
	@echo "make models          임베딩 모델 BGE-M3 (3회차 폴더에서 models 를 복사했으면 건너뜁니다)"
	@echo "make models-rerank   리랭커 bge-reranker-v2-m3 다운로드 (2.2GB, 10~20분. 수업 전에)"
	@echo "make embeddings      강사가 만든 임베딩 스냅샷 다운로드 (13MB. 3회차 폴더에서 복사했으면 건너뜁니다)"
	@echo "make notebook        에이전트 노트북 열기 (수업 1~2부)"
	@echo "make test            자동 채점. 2~4회차 51개 + 5회차 검사 (채우기 전에는 실패가 정상)"
	@echo "make ask Q=\"질문\"    질문 하나를 에이전트에 넣고 경로·판정·근거·답변을 본다"
	@echo "make graph           에이전트 상태도를 mermaid 텍스트로 찍는다"
	@echo "make agentic-sample  골든셋 앞 10문항을 에이전트로 → results/agentic_sample.json (실측 1, 약 3분)"
	@echo "make agentic         40문항 전부 → results/agentic.json (오늘 결과물, 약 12~15분. 휴식에 돌립니다)"
	@echo "make adversarial     적대적 5문항 → results/adversarial.json (1분)"
	@echo "make check-s05       5회차 확인 → results/check_s05.json (이 파일을 제출)"
	@echo "--- 3·4회차 명령. 그대로 남겨 둡니다 ---"
	@echo "make hybrid          Hybrid + 리랭커로 40문항 → results/hybrid.json (약 8~10분)"
	@echo "make index           청크를 임베딩(스냅샷 재사용)해서 Qdrant 에 넣는다 (10초)"
	@echo "make baseline        골든셋 40문항 Dense 검색 → results/baseline.json (30초)"

setup:
	uv venv --python 3.12 .venv
	uv pip install --python $(PY) -r requirements.txt

download:
	$(PY) data/download_corpus.py

models:
	$(PY) scripts/pull_models.py --only embed

models-rerank:
	$(PY) scripts/pull_models.py --only rerank

embeddings:
	mkdir -p data/embeddings
	curl -L --fail -o data/embeddings/BAAI_bge-m3.npz $(EMB_URL)
	@ls -la data/embeddings/BAAI_bge-m3.npz

notebook:
	$(PY) -m jupyter lab notebooks/s05_agent.ipynb

test:
	$(PY) -m pytest -q

ask:
	$(PY) scripts/ask.py "$(Q)"

graph:
	$(PY) scripts/agent_graph.py

agentic-sample:
	$(PY) pipelines/agentic.py --limit 10 --verbose

agentic:
	$(PY) pipelines/agentic.py --verbose

adversarial:
	$(PY) scripts/adversarial_run.py

# ── 4회차 명령. 그대로 남겨 둡니다 ──

bm25-compare:
	$(PY) scripts/bm25_compare.py

hybrid-norerank:
	$(PY) pipelines/hybrid.py --no-rerank

hybrid:
	$(PY) pipelines/hybrid.py

rerank-sweep:
	$(PY) scripts/rerank_sweep.py

check-s%:
	$(PY) scripts/check_session.py $*

# ── 3회차 명령 ──
ingest-sample:
	$(PY) pipelines/ingest.py --no-checkpoint $(SAMPLE)

ingest:
	$(PY) pipelines/ingest.py

index:
	$(PY) scripts/build_index.py

baseline:
	$(PY) pipelines/baseline.py

# ── 2회차 명령 ──
chunk-sample:
	$(PY) pipelines/chunk_only.py --verbose $(SAMPLE)

chunk:
	$(PY) pipelines/chunk_only.py --verbose

profile:
	$(PY) scripts/profile_docs.py
