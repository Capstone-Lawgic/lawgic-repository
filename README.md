# Lawgic MVP (FastAPI + Streamlit)

계약서 텍스트를 입력하면 `/api/analyze`에서 키워드 기반 임시 위험 조항 분석 결과를 반환하고,
Streamlit UI에 보여주는 MVP입니다.

## 1) 프로젝트 구조

```text
app/
  main.py
  api/
    analyze.py
  schemas/
    contract.py
  services/
    contract_service.py
    rag_service.py
    llm_service.py
  core/
    prompt.py
frontend/
  streamlit_app.py
requirements.txt
README.md
```

## 2) 설치

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3) 실행

### FastAPI 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

- Health check: `http://localhost:8000/health`
- Analyze API docs: `http://localhost:8000/docs`

### Streamlit 실행

새 터미널에서 아래 실행:

```bash
streamlit run frontend/streamlit_app.py
```

브라우저에서 Streamlit 화면을 열고 계약서 텍스트를 입력한 뒤 `분석 실행` 버튼을 누르면 결과를 확인할 수 있습니다.

## 4) 현재 분석 방식 (임시)

아래 키워드가 포함된 문장을 위험 조항으로 분류합니다.

- 수당
- 퇴사
- 손해배상
- 연장근로
- 최저임금

## 5) 확장 포인트

- `app/services/rag_service.py`: 향후 ChromaDB 기반 검색 로직 추가
- `app/services/llm_service.py`: 향후 LLM API 호출 및 고도화 요약 로직 추가
