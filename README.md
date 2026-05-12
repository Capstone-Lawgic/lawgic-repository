# Lawgic MVP

계약서 텍스트를 입력하면 관련 근로계약 검토 기준을 RAG로 검색하고, LLM이 위험 조항과 수정 방향을 구조화해서 보여주는 FastAPI + Streamlit 기반 MVP입니다.

본 결과는 법률 자문이 아닌 계약서 검토 보조 결과입니다. 최종 판단은 전문가 검토가 필요합니다.

## 데모 시나리오

1. 사용자가 계약서 문장을 입력합니다.
2. FastAPI의 `/api/analyze`가 계약서 문장을 분석합니다.
3. ChromaDB 기반 RAG가 `app/data/labor_law_contexts.json`에서 관련 근거를 검색합니다.
4. OpenAI LLM이 위험 조항, 위험도, 판단 사유, 근거, 권고 수정 방향을 생성합니다.
5. Streamlit UI가 분석 결과와 검색된 RAG 근거를 표시합니다.
6. OpenAI 호출이 실패하거나 API 키가 없으면 `local-fallback` 규칙으로 같은 응답 형식을 유지합니다.

데모용 입력 예시:

```text
근로자는 회사의 요청에 따라 연장근로와 야간근로를 수행할 수 있으며 별도 수당은 지급하지 않는다.
퇴사 시 회사에 위약금 500만원을 지급해야 한다.
회사는 근로자의 개인정보를 필요한 범위에서 수집하고 제3자에게 제공할 수 있다.
퇴직 후 2년간 동종업계에 취업할 수 없다.
회사는 업무상 필요에 따라 근무 장소와 직무를 변경할 수 있다.
```

## 프로젝트 구조

```text
app/
  main.py
  api/
    analyze.py
  core/
    env.py
  data/
    labor_law_contexts.json
    raw/
    generated/
    eval/
  schemas/
    contract.py
  services/
    contract_service.py
    rag_service.py
    llm_service.py
frontend/
  streamlit_app.py
scripts/
  collect_law_sources.py
  generate_rag_contexts.py
  validate_rag_contexts.py
  evaluate_rag.py
requirements.txt
README.md
```

## 설치

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`uv`를 사용하는 경우:

```bash
uv pip install -r requirements.txt
```

## 환경 변수

`.env` 예시:

```env
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-5.4-mini"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
LAW_API_OC="국가법령정보센터_API_OC"
```

- `OPENAI_API_KEY`: LLM 분석과 embedding 호출에 사용합니다.
- `OPENAI_MODEL`: 계약서 위험 분석 LLM 모델입니다.
- `OPENAI_EMBEDDING_MODEL`: ChromaDB RAG 검색용 embedding 모델입니다.
- `LAW_API_OC`: 공식 법령 원문 수집 스크립트에서 사용하는 국가법령정보센터 인증값입니다.

`OPENAI_API_KEY`가 없으면 앱은 `local-fallback` 모드로 실행됩니다.

## 실행

FastAPI 서버:

```bash
uvicorn app.main:app --reload --port 8000
```

API 확인:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

Streamlit UI:

```bash
streamlit run frontend/streamlit_app.py
```

화면:

```text
http://localhost:8501
```

## 현재 구현 범위

- FastAPI 분석 API
- Streamlit 데모 UI
- ChromaDB 기반 RAG 검색
- OpenAI embedding 우선 사용, 실패 시 로컬 fallback embedding 사용
- OpenAI LLM 기반 위험 조항 구조화
- API 키 없음 또는 LLM 오류 시 로컬 fallback 분석
- 공식 법령 원문 수집 및 LLM 기반 RAG 데이터 생성 스크립트
- RAG 검색 평가 스크립트

## RAG 데이터

현재 데모 앱은 검수된 RAG 데이터인 `app/data/labor_law_contexts.json`을 사용합니다.

RAG 검색 대상은 각 항목의 `title`, `content`, `keywords`입니다.

```json
{
  "source": "근로기준법 제20조",
  "title": "위약 예정의 금지",
  "content": "퇴사나 계약 불이행을 이유로 위약금 또는 손해배상액을 미리 정하는 조항은 위험할 수 있다.",
  "keywords": ["위약금", "손해배상", "퇴사"]
}
```

## RAG 근거 데이터 생성

공식 법령 원문을 수집한 뒤 LLM으로 계약서 검토용 RAG JSON을 생성할 수 있습니다.

```bash
python scripts/collect_law_sources.py
python scripts/generate_rag_contexts.py
python scripts/validate_rag_contexts.py
```

생성 결과는 기본적으로 아래 파일에 저장됩니다.

```text
app/data/generated/labor_law_contexts.generated.json
```

검수 후 실제 RAG 데이터로 반영하려면:

```bash
python scripts/generate_rag_contexts.py --apply
```

중간 데모에서는 자동 생성 결과를 바로 적용하지 않고, 검수된 JSON을 사용하는 방식을 권장합니다.

## RAG 평가

검색 품질 확인용 평가셋은 `app/data/eval/rag_eval_cases.json`에 있습니다.

```bash
python scripts/evaluate_rag.py --top-k 3 --show
```

이 평가는 RAG 데이터와 검색 로직을 개선하기 위한 내부 지표입니다.

## 현재 한계

- 계약서 전체에 대해 RAG를 한 번 수행하므로, 조항별 근거 매칭이 완벽하지 않을 수 있습니다.
- LLM이 생성한 RAG 데이터는 반드시 검수 후 반영해야 합니다.
- 현재 평가셋은 작고 데모 중심이라 실제 법률 검토 품질을 대표하지 않습니다.
- 경업금지, 전보, 개인정보 제3자 제공 등 일부 영역은 추가 근거 데이터 보강이 필요합니다.

## 향후 개선 방향

- 조항별 RAG 검색으로 전환
- 공식 법령 원문을 조문 단위로 추출하는 `extract_law_articles.py` 추가
- RAG 데이터 생성 후 자동 필터링과 사람 검수 흐름 강화
- 평가셋 확장 및 Top-1/Top-3 검색 정확도 개선
- LLM 답변의 근거 인용 검증 강화
