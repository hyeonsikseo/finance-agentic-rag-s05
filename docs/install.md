# 설치와 준비물 받기 (5회차)

4회차와 같은 컴퓨터에서, 4회차 폴더(`finance-agentic-rag-s04`) 옆에 새 레포지토리를 받습니다. **새로 받는 것은 없습니다.** 문서·청크·모델은 4회차 폴더에서 복사하고, 패키지 하나(pyyaml)가 더해지고, 메타코드에서 받은 OpenAI 키를 `.env` 에 넣습니다. 전부 10분 안쪽입니다. 수업 전날까지 끝내 두고, 마지막 7번의 확인 줄 둘을 디스코드에 남겨 주세요.

## 1. 준비물 두 가지, git 과 uv

1~4회차에 했으면 건너뜁니다. 확인은 `git --version`, `uv --version`.

## 2. 레포지토리 받기

지난 회차처럼 포크를 먼저 합니다.

1. 브라우저에서 https://github.com/hyeonsikseo/finance-agentic-rag-s05 를 열고 오른쪽 위 **Fork** 를 누릅니다.
2. 그 레포지토리를 받습니다. `<계정>` 자리에 자기 GitHub 계정을 넣습니다.

```bash
git clone https://github.com/<계정>/finance-agentic-rag-s05.git
cd finance-agentic-rag-s05
git remote add upstream https://github.com/hyeonsikseo/finance-agentic-rag-s05.git
```

포크가 막히면 원본을 그대로 받고 과제는 zip 으로 냅니다.

## 3. 4회차 폴더에서 가져오기

문서, OCR 캐시, 청크, 임베딩 스냅샷, BM25 토큰 캐시, 모델(임베딩 2.2GB + 리랭커 2.2GB), 그리고 4회차 결과 파일을 복사합니다. 폴더가 다른 곳에 있으면 경로만 바꿉니다.

**Mac**

```bash
cp -R ../finance-agentic-rag-s04/data/raw data/
cp -R ../finance-agentic-rag-s04/data/ocr_cache data/
cp -R ../finance-agentic-rag-s04/data/chunks data/
cp ../finance-agentic-rag-s04/data/ingest_report.json data/
cp -R ../finance-agentic-rag-s04/data/embeddings data/
cp -R ../finance-agentic-rag-s04/data/bm25_cache data/
cp -R ../finance-agentic-rag-s04/models .
mkdir -p results && cp ../finance-agentic-rag-s04/results/baseline.json ../finance-agentic-rag-s04/results/hybrid.json results/
```

**Windows (PowerShell)**

```powershell
Copy-Item -Recurse ..\finance-agentic-rag-s04\data\raw data\
Copy-Item -Recurse ..\finance-agentic-rag-s04\data\ocr_cache data\
Copy-Item -Recurse ..\finance-agentic-rag-s04\data\chunks data\
Copy-Item ..\finance-agentic-rag-s04\data\ingest_report.json data\
Copy-Item -Recurse ..\finance-agentic-rag-s04\data\embeddings data\
Copy-Item -Recurse ..\finance-agentic-rag-s04\data\bm25_cache data\
Copy-Item -Recurse ..\finance-agentic-rag-s04\models .
New-Item -ItemType Directory -Force results | Out-Null
Copy-Item ..\finance-agentic-rag-s04\results\baseline.json, ..\finance-agentic-rag-s04\results\hybrid.json results\
```

`models` 는 4GB 가 넘어서 1~2분 걸립니다. 디스크가 빠듯하면 복사 대신 옮겨도 됩니다(`mv`, `Move-Item`). 4회차 폴더는 이제 쓰지 않습니다. `results/` 의 두 파일은 오늘 결과(`agentic.json`)와 나란히 놓고 비교하는 데 씁니다. 4회차 과제를 아직 못 끝내서 `hybrid.json` 이 없으면 그 줄만 빼고 복사합니다.

4회차 폴더가 없으면, 문서는 `make download`, 모델은 `make models` 와 `make models-rerank`, 스냅샷은 `make embeddings` 로 받고, `make ingest`(약 6분)와 `make baseline` 을 먼저 합니다.

## 4. 파이썬과 패키지 설치

**Mac**

```bash
make setup
```

**Windows (PowerShell)**

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

4회차와 같은 패키지에 `pyyaml` 하나가 더해집니다(정책 파일과 계산 명세를 읽습니다). 1분이면 끝납니다.

## 5. OpenAI 키를 .env 에 넣기

오늘부터 LLM 을 실제로 부릅니다. 질문을 고쳐 쓰고, 근거가 충분한지 판정하고, 필터를 뽑고, 답변을 만듭니다. 키는 메타코드에서 받은 것을 씁니다.

```bash
cp .env.example .env        # Windows: Copy-Item .env.example .env
```

`.env` 를 열어 `OPENAI_API_KEY=` 뒤에 키를 붙이고 저장합니다. `.env` 는 커밋되지 않습니다. 키를 채팅이나 코드에 붙이지 마세요. 되는지 확인합니다.

**Mac**

```bash
.venv/bin/python -c "import sys; sys.path.insert(0,'src'); from finrag.llm import get_llm, is_fake; m=get_llm('answer'); print('키가 없어 가짜 모델입니다' if is_fake(m) else m.invoke('한 단어로 답하세요: 안녕하세요').content)"
```

**Windows (PowerShell)**

```powershell
.venv\Scripts\python -c "import sys; sys.path.insert(0,'src'); from finrag.llm import get_llm, is_fake; m=get_llm('answer'); print('키가 없어 가짜 모델입니다' if is_fake(m) else m.invoke('한 단어로 답하세요: 안녕하세요').content)"
```

한 단어 답(예: "안녕하세요")이 나오면 된 것입니다. "키가 없어 가짜 모델입니다"가 나오면 `.env` 의 줄을 다시 봅니다. 값 뒤에 공백이나 주석이 붙어 있으면 안 됩니다. **이 한 줄이 디스코드에 남길 확인 줄 하나입니다.**

키 없이도 수업은 됩니다. 그래프는 "가짜 모델"로 돌아서 경로와 검색은 볼 수 있지만, 판정·필터·답변은 고정 문구라 의미가 없습니다.

## 6. 인덱스 만들기

4회차 청크를 이 폴더의 Qdrant 에 넣습니다. 스냅샷을 재사용해서 10초입니다.

**Mac**

```bash
make index
```

**Windows (PowerShell)**

```powershell
$env:HF_HOME = ".\models"
.venv\Scripts\python scripts\build_index.py
```

## 7. 되는지 확인

**Mac**

```bash
make test
```

**Windows (PowerShell)**

```powershell
.venv\Scripts\python -m pytest -q
```

지금은 **실패가 정상**입니다. 채울 자리가 비어 있어서 5회차 테스트 16개가 `NotImplementedError` 로 실패합니다. 마지막 줄이 `16 failed, 82 passed` (3번에서 `hybrid.json` 을 복사하지 않았으면 `16 failed, 81 passed, 1 skipped`) 이고 `error` 가 없으면 설치는 된 것입니다. **이 마지막 줄과 5번의 한 단어 답, 둘을 디스코드에 적어 주세요.**

## 막힐 때

| 증상 | 이유 | 이렇게 합니다 |
|---|---|---|
| `uv: command not found` | 설치 뒤 터미널을 새로 안 열었습니다 | 터미널을 닫고 새로 엽니다 |
| 확인 명령이 "키가 없어 가짜 모델입니다" | `.env` 에 키가 안 들어갔거나 파일 이름이 `.env.example` 그대로입니다 | 레포지토리 폴더에 `.env` 가 있는지, `OPENAI_API_KEY=` 뒤에 키가 바로 붙어 있는지 봅니다 |
| 확인 명령이 `AuthenticationError` | 키가 틀렸거나 잘려서 들어갔습니다 | 키를 다시 붙입니다. 그래도 그러면 디스코드에 에러 **종류만** 적습니다(키는 적지 않습니다) |
| 확인 명령이 `RateLimitError` 나 `insufficient_quota` | 키의 사용량 한도입니다 | 강사에게 알립니다. 메타코드 쪽에서 봅니다 |
| `make test` 에 `ModuleNotFoundError: yaml` | 4번을 안 했습니다 | `make setup` |
| `make index` 가 25분째 돌고 있다 | 임베딩 스냅샷이 없거나 이름이 다릅니다 | 멈추고(Ctrl+C) `data/embeddings/BAAI_bge-m3.npz` 가 있는지 봅니다. 없으면 `make embeddings` |
| `make agentic` 이 "리랭커 모델이 없어 건너뜀" | 3번에서 `models` 를 복사하지 않았습니다 | `models` 를 복사하거나 `make models-rerank` |
| Qdrant `already accessed` 에러 | 다른 터미널이 Qdrant 를 잡고 있습니다 | 그쪽을 닫고 다시 돌립니다. 오늘 노트북은 Qdrant 를 열지 않습니다 |
| Windows 에서 `make` 가 없다 | 원래 없습니다 | 위의 PowerShell 명령을 씁니다 |

## 키가 안 되면

노트북(셀 3·6·8 은 "가짜 모델"로 표시되고 넘어갑니다), 실습 1·2·3, `make test` 는 키 없이 됩니다. `make agentic` 과 `make adversarial` 은 돌아가지만 판정·답변이 고정 문구라 숫자가 의미 없습니다. 수업 뒤 키를 넣고 다시 돌리면 됩니다.
