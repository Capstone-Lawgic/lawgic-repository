# Lawgic MVP

계약서 텍스트 또는 파일을 입력하면 계약서 유형별 RAG 근거를 검색하고, LLM이 위험 조항과 수정 방향을 구조화해서 보여주는 FastAPI + Streamlit 기반 MVP입니다.

이 결과는 법률 자문이 아니라 계약서 검토를 보조하기 위한 참고 결과입니다. 최종 판단은 전문가 검토가 필요합니다.

## 동작 흐름

1. 사용자가 계약서 텍스트를 입력하거나 PDF/이미지 파일을 업로드합니다.
2. FastAPI가 계약서 유형을 자동 감지하거나 사용자가 선택한 유형을 사용합니다.
3. 계약서 유형에 맞는 RAG 데이터를 ChromaDB에서 검색합니다.
4. OpenAI LLM이 위험 조항, 판단 이유, RAG 근거, 수정 권고를 구조화합니다.
5. Streamlit UI가 분석 결과와 검색된 근거를 표시합니다.
6. OpenAI API 키가 없거나 호출이 실패하면 `local-fallback` 규칙으로 같은 응답 형식을 유지합니다.

지원 계약서 유형:

- 근로계약서: `employment`
- 주택임대차계약서: `lease`

## 프로젝트 구조

```text
app/
  main.py
  api/
    analyze.py              # /api/analyze, /api/analyze-file
  core/
    contract_domain.py      # 계약서 유형 정의 및 자동 감지
    env.py                  # .env 로딩
    prompt.py
  data/
    labor_law_contexts.json # 근로계약서 RAG 데이터
    lease_law_contexts.json # 임대차계약서 RAG 데이터
    eval/                   # RAG 평가 케이스
    generated/              # 자동 생성 RAG 후보
    raw/                    # law.go.kr 원문 수집 결과
  schemas/
    contract.py             # 요청/응답 스키마
  services/
    contract_service.py     # 분석 오케스트레이션
    rag_service.py          # ChromaDB 검색 및 임베딩
    llm_service.py          # LLM 분석 및 fallback
    file_text_service.py    # PDF/이미지 텍스트 추출
frontend/
  streamlit_app.py
scripts/
  collect_law_sources.py
  generate_rag_contexts.py
  validate_rag_contexts.py
  evaluate_rag.py
requirements.txt
```

## 설치

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

`uv`를 사용하는 경우:

```powershell
uv pip install -r requirements.txt
```

## 환경 변수

`.env` 예시:

```env
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4o-mini"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
MAX_RISK_CLAUSES="8"
LAW_API_OC="law.go.kr_API_OC"
```

- `OPENAI_API_KEY`: LLM 분석, OpenAI embedding, 이미지 OCR에 사용합니다.
- `OPENAI_MODEL`: 계약서 위험 분석 모델입니다. 기본값은 `gpt-4o-mini`입니다.
- `OPENAI_EMBEDDING_MODEL`: ChromaDB RAG 검색용 embedding 모델입니다. 기본값은 `text-embedding-3-small`입니다.
- `MAX_RISK_CLAUSES`: LLM이 반환할 위험 조항 최대 개수입니다. 기본값은 `8`입니다.
- `LAW_API_OC`: 공식 법령 원문 수집 스크립트에서 사용하는 law.go.kr 인증값입니다.

`OPENAI_API_KEY`가 없으면 텍스트 분석은 `local-fallback` 모드로 실행됩니다. 단, 이미지 파일 텍스트 추출은 OpenAI API 키가 필요합니다.

## 실행

FastAPI 서버:

```powershell
uv run uvicorn app.main:app --reload --port 8000
```

API 확인:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

Streamlit UI:

```powershell
uv run streamlit run frontend/streamlit_app.py
```

화면:

```text
http://localhost:8501
```

## API

텍스트 분석:

```http
POST /api/analyze
Content-Type: application/json
```

```json
{
  "text": "계약서 원문",
  "contract_type": "lease"
}
```

`contract_type`은 생략할 수 있습니다. 생략하면 계약서 본문 키워드로 `employment` 또는 `lease`를 자동 감지합니다.

파일 분석:

```http
POST /api/analyze-file
Content-Type: multipart/form-data
```

필드:

- `file`: `pdf`, `jpg`, `jpeg`, `png`, `webp`
- `contract_type`: 선택값. `employment` 또는 `lease`

응답 주요 필드:

```json
{
  "contract_type": "lease",
  "total_sentences": 15,
  "risk_count": 6,
  "risk_clauses": [
    {
      "sentence": "위험 조항 원문",
      "category": "위험 유형",
      "severity": "high",
      "reason": "판단 이유",
      "evidence": "[근거 제목] / 출처: 법령명",
      "recommendation": "수정 또는 확인 권고",
      "related_contexts": []
    }
  ],
  "summary": "요약",
  "model_used": "gpt-5.4-mini",
  "contexts": []
}
```

## 현재 구현 범위

- FastAPI 분석 API
- Streamlit 데모 UI
- 계약서 유형 자동 감지 및 명시 선택
- 텍스트, PDF, 이미지 업로드 분석
- 계약서 유형별 RAG 검색
- ChromaDB persistent collection 사용
- OpenAI embedding 우선 사용, 실패 시 local hash embedding fallback
- OpenAI LLM 기반 구조화 분석
- 결과 형식 안정화를 위한 출력 예시 프롬프트
- OpenAI API 키 없음 또는 LLM 오류 시 `local-fallback` 분석
- 공식 법령 원문 수집 및 RAG 데이터 생성 스크립트
- RAG 검색 품질 평가 스크립트

## RAG 데이터

앱에서 실제 사용하는 RAG 데이터:

- 근로계약서: `app/data/labor_law_contexts.json`
- 주택임대차계약서: `app/data/lease_law_contexts.json`

각 항목 구조:

```json
{
  "source": "주택임대차보호법 제3조의2",
  "title": "확정일자와 우선변제권",
  "content": "확정일자 취득을 제한하거나 보증금 회수 절차를 약화하는 조항은 주의해야 한다.",
  "keywords": ["확정일자", "우선변제", "보증금 회수"],
  "category": "대항력/우선변제",
  "risk_level": "high",
  "source_url": "https://www.law.go.kr/법령/주택임대차보호법"
}
```

## RAG 평가

근로계약서 평가:

```powershell
uv run python scripts/evaluate_rag.py --domain employment --cases app\data\eval\rag_eval_cases.json --top-k 3 --show
```

주택임대차계약서 평가:

```powershell
uv run python scripts/evaluate_rag.py --domain lease --cases app\data\eval\lease_rag_eval_cases.json --top-k 3 --show
```

현재 기준 평가 결과:

```text
근로 RAG:   Top-1 95.0%, Top-3 100.0% (20 cases)
임대차 RAG: Top-1 85.7%, Top-3 100.0% (21 cases)
```

평가셋은 검색 로직과 RAG 데이터 품질을 점검하기 위한 내부 기준입니다. 실제 법률 검토 정확도를 완전히 보장하지는 않습니다.

## RAG 데이터 생성

공식 법령 원문 수집:

```powershell
uv run python scripts/collect_law_sources.py --domain employment
uv run python scripts/collect_law_sources.py --domain lease --output app\data\raw\lease_law_sources.json
```

RAG 후보 생성:

```powershell
uv run python scripts/generate_rag_contexts.py --domain employment
uv run python scripts/generate_rag_contexts.py --domain lease --input app\data\raw\lease_law_sources.json
```

검증:

```powershell
uv run python scripts/validate_rag_contexts.py --input app\data\generated\labor_law_contexts.generated.json
uv run python scripts/validate_rag_contexts.py --input app\data\generated\lease_law_contexts.generated.json
```

검수한 생성 결과를 실제 앱 데이터로 반영:

```powershell
uv run python scripts/generate_rag_contexts.py --domain employment --apply
uv run python scripts/generate_rag_contexts.py --domain lease --apply
```

자동 생성 결과는 반드시 검수 후 반영하는 것을 권장합니다.

## 파일 업로드 처리

- PDF: `pypdf`로 텍스트를 추출합니다.
- 이미지: OpenAI vision 모델로 텍스트를 추출합니다.
- 이미지 분석에는 `OPENAI_API_KEY`가 필요합니다.
- 추출된 텍스트가 비어 있으면 API가 오류를 반환합니다.

## 현재 한계

- RAG는 계약서 전체를 기준으로 검색하므로, 긴 계약서에서는 일부 조항의 최적 근거가 상위 검색 결과에서 밀릴 수 있습니다.
- LLM 응답은 프롬프트와 예시로 형식을 고정하려 하지만, 문체와 세부 표현은 모델 출력에 따라 조금씩 달라질 수 있습니다.
- `local-fallback`은 키워드 기반 보조 결과이므로 OpenAI LLM 분석보다 품질이 낮습니다.
- RAG 데이터와 평가셋은 MVP 검증용으로 구성되어 있어, 실제 법률 검토 범위를 모두 포괄하지 않습니다.
- 자동 생성된 RAG 데이터는 환각이나 부적절한 요약이 섞일 수 있어 수동 검수가 필요합니다.

## 향후 개선 방향

- 조항별 RAG 검색을 안정적으로 재설계
- fallback 규칙을 최신 RAG 데이터와 더 정교하게 연결
- 파일 업로드 오류 메시지와 OCR 품질 개선
- 실제 계약서 샘플 기반 평가셋 확장
- LLM evidence가 제공된 RAG 근거만 사용하는지 검증 강화
- Streamlit 결과 화면의 근거 표시 방식 개선
