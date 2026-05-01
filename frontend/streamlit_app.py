import requests
import streamlit as st

API_URL = "http://localhost:8000/api/analyze"

st.set_page_config(page_title="Lawgic MVP", page_icon="⚖️", layout="centered")
st.title("⚖️ Lawgic MVP")
st.caption("계약서 텍스트를 입력하면 임시 위험 조항을 분석합니다.")

sample_text = """\
근로자는 연장근로를 요청받을 수 있다.
퇴사 시 회사는 별도 위약금을 청구할 수 있다.
기본급은 최저임금 이상으로 한다.
"""

text = st.text_area("계약서 텍스트 입력", value=sample_text, height=220)

if st.button("분석 실행", type="primary"):
    if not text.strip():
        st.warning("계약서 텍스트를 입력해 주세요.")
    else:
        with st.spinner("분석 중..."):
            try:
                response = requests.post(API_URL, json={"text": text}, timeout=10)
                response.raise_for_status()
                result = response.json()
            except requests.RequestException as exc:
                st.error(f"API 호출 실패: {exc}")
            else:
                st.success("분석 완료")
                st.write(f"- 총 문장 수: **{result['total_sentences']}**")
                st.write(f"- 위험 조항 수: **{result['risk_count']}**")
                st.info(result["summary"])

                if result["risk_clauses"]:
                    st.subheader("탐지된 위험 조항")
                    for idx, clause in enumerate(result["risk_clauses"], start=1):
                        st.markdown(
                            f"""
**{idx}. 키워드:** `{clause['keyword']}`  
**문장:** {clause['sentence']}  
**사유:** {clause['reason']}
"""
                        )
                else:
                    st.write("탐지된 위험 조항이 없습니다.")
