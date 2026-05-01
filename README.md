# Lawgic MVP (RAG/LLM Ready)

FastAPI + Streamlit 기반 MVP이며, 현재는 키워드 기반 분석을 수행합니다.
동시에 ChromaDB(RAG)와 LLM API를 붙이기 쉽도록 서비스 경계를 분리해 두었습니다.

## 구조

- `app/services/rag_service.py`: RAG 검색 스텁 (향후 ChromaDB 연결)
- `app/services/llm_service.py`: LLM 요약 스텁 (향후 provider API 연결)
- `app/core/config.py`: `.env` 기반 설정 로딩

## 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload --port 8000
# new terminal
streamlit run frontend/streamlit_app.py
```

## 현재 임시 탐지 키워드

- 수당
- 퇴사
- 손해배상
- 연장근로
- 최저임금

## 다음 구현 포인트

1. `rag_service.py`에 ChromaDB 검색 로직 구현
2. `llm_service.py`에 실제 provider(OpenAI 등) 호출 구현
3. `prompt.py` 프롬프트 버저닝 및 JSON 출력 강제
