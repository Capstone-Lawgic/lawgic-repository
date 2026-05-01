import requests
import streamlit as st

API_URL = "http://localhost:8000/api/analyze"

st.set_page_config(page_title="Lawgic MVP", page_icon="⚖️", layout="centered")
st.title("⚖️ Lawgic MVP")
st.caption("RAG/LLM 연동 준비형 계약서 위험 조항 분석기")

text = st.text_area("계약서 텍스트 입력", height=240)

if st.button("분석 실행", type="primary"):
    if not text.strip():
        st.warning("계약서 텍스트를 입력해 주세요.")
    else:
        response = requests.post(API_URL, json={"text": text}, timeout=10)
        if response.ok:
            result = response.json()
            st.success("분석 완료")
            st.write(f"LLM Provider: `{result['llm_provider']}` / Model: `{result['llm_model']}`")
            st.info(result["summary"])
            for item in result["risk_clauses"]:
                st.markdown(f"- **{item['keyword']}** | {item['sentence']}\n  - 사유: {item['reason']}")
        else:
            st.error(f"분석 실패: {response.status_code} - {response.text}")
