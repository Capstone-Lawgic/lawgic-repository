import requests
import streamlit as st

API_URL = "http://localhost:8000/api/analyze"

st.set_page_config(page_title="Lawgic MVP", page_icon="⚖️", layout="wide")
st.title("⚖️ Lawgic RAG/LLM")
st.caption("계약서 텍스트를 입력하면 관련 검토 기준을 검색하고 위험 조항과 수정 방향을 정리합니다.")
st.warning("본 결과는 법률 자문이 아닌 계약서 검토 보조 결과입니다. 최종 판단은 전문가 검토가 필요합니다.")

sample_text = """\
아르바이트 근로계약서

주식회사 테스트컴퍼니(이하 “회사”)와 근로자 김테스트(이하 “근로자”)는 다음과 같이 근로계약을 체결한다.

제1조 목적
본 계약은 회사가 운영하는 카페 매장에서 근로자가 음료 제조, 매장 정리, 고객 응대 및 기타 회사가 지시하는 업무를 수행하는 데 필요한 근로조건을 정하는 것을 목적으로 한다.

제2조 근로계약 기간
근로계약 기간은 2026년 6월 1일부터 2026년 8월 31일까지로 한다. 단, 회사의 사정에 따라 별도의 통보 없이 계약기간을 단축하거나 종료할 수 있다.

제3조 근무 장소 및 업무
근로자는 강원도 춘천시에 위치한 테스트컴퍼니 강원대점에서 근무한다. 다만 회사는 업무상 필요하다고 판단하는 경우 근로자의 동의 없이 다른 지점으로 근무 장소를 변경할 수 있다.

제4조 근로시간
근로자의 근로시간은 주 5일, 1일 8시간을 원칙으로 한다. 다만 매장 상황에 따라 회사는 근로자에게 사전 동의 없이 연장근로, 야간근로 또는 휴일근로를 지시할 수 있으며, 근로자는 이에 따라야 한다.

제5조 휴게시간
근로자는 1일 8시간 근무 시 30분의 휴게시간을 가진다. 단, 매장이 바쁜 경우 휴게시간은 제공되지 않을 수 있으며, 이 경우 별도의 보상은 하지 않는다.

제6조 임금
회사는 근로자에게 시간당 9,000원의 임금을 지급한다. 임금은 매월 말일에 지급하며, 회사의 자금 사정에 따라 지급일은 변경될 수 있다.

제7조 수습기간
근로자는 입사일로부터 3개월간 수습기간을 가진다. 수습기간 중에는 최저임금의 70%만 지급하며, 회사는 근로자의 업무능력이 부족하다고 판단하는 경우 즉시 계약을 해지할 수 있다.

제8조 연장·야간·휴일근로수당
근로자가 연장근로, 야간근로 또는 휴일근로를 하더라도 회사는 별도의 가산수당을 지급하지 않는다. 근로자는 본 계약 체결과 동시에 해당 수당 청구권을 포기한 것으로 본다.

제9조 지각 및 결근
근로자가 지각하는 경우 1회당 30,000원을 임금에서 공제한다. 무단결근 1회 발생 시 해당 월 임금의 30%를 공제하며, 회사는 별도의 절차 없이 근로자를 해고할 수 있다.

제10조 손해배상
근로자의 실수로 음료 제조 오류, 고객 불만, 매장 물품 파손 또는 금전 손실이 발생한 경우 회사는 손해액을 근로자의 임금에서 공제할 수 있다. 손해액 산정은 회사의 판단에 따른다.

제11조 비밀유지
근로자는 근무 중 알게 된 회사의 영업정보, 레시피, 고객정보 및 내부 운영 방식을 외부에 공개해서는 안 된다. 이를 위반할 경우 근로자는 회사에 손해배상금 5,000,000원을 지급한다.

제12조 퇴사
근로자가 퇴사하고자 하는 경우 최소 60일 전에 회사에 통보해야 한다. 이를 지키지 않고 퇴사하는 경우 근로자는 대체 인력 채용 비용 및 교육비로 1,000,000원을 회사에 지급한다.

제13조 임금 포기
근로자가 계약기간 만료 전 퇴사하거나 회사의 지시에 불응한 경우, 근로자는 이미 근무한 기간에 대한 임금 일부 또는 전부를 포기한 것으로 본다.

제14조 휴일 및 연차
근로자의 휴일은 회사가 정하는 날로 한다. 근로자는 단시간 근로자이므로 주휴수당 및 연차유급휴가는 발생하지 않는다.

제15조 계약 해지
회사는 근로자의 근무태도, 고객 응대 방식, 회사 분위기와의 적합성 등을 종합적으로 고려하여 필요하다고 판단하는 경우 언제든지 즉시 계약을 해지할 수 있다.

제16조 기타
본 계약서에 명시되지 않은 사항은 회사의 내부 규정에 따른다. 회사의 내부 규정은 근로자에게 별도로 공개하지 않을 수 있다.

2026년 6월 1일

회사
상호: 주식회사 테스트컴퍼니
대표자: 홍길동
주소: 강원도 춘천시 테스트로 123
서명: __________________

근로자
성명: 김테스트
주소: 강원도 춘천시 예시로 45
서명: __________________
"""

text = st.text_area("계약서 텍스트 입력", value=sample_text, height=240)

if st.button("분석 실행", type="primary", use_container_width=True):
    if not text.strip():
        st.warning("계약서 텍스트를 입력해 주세요.")
    else:
        with st.spinner("RAG 근거 검색 및 위험 조항 분석 중..."):
            try:
                response = requests.post(API_URL, json={"text": text}, timeout=60)
                response.raise_for_status()
                result = response.json()
            except requests.RequestException as exc:
                st.error(f"API 호출 실패: {exc}")
            else:
                st.success("분석 완료")

                col1, col2, col3 = st.columns(3)
                col1.metric("총 문장 수", result["total_sentences"])
                col2.metric("위험 조항 수", result["risk_count"])
                col3.metric("분석 모델", result["model_used"])

                if result["model_used"] == "local-fallback":
                    st.warning("OpenAI 분석을 사용할 수 없어 로컬 fallback 규칙으로 결과를 생성했습니다.")

                st.info(result["summary"])

                if result["risk_clauses"]:
                    st.subheader("탐지된 위험 조항")
                    for idx, clause in enumerate(result["risk_clauses"], start=1):
                        severity = clause["severity"].upper()
                        with st.expander(f"{idx}. [{severity}] {clause['category']}", expanded=True):
                            st.markdown(f"**원문**  \n{clause['sentence']}")
                            st.markdown(f"**판단 사유**  \n{clause['reason']}")
                            st.markdown(f"**RAG 근거**  \n{clause['evidence']}")
                            st.markdown(f"**권고 수정 방향**  \n{clause['recommendation']}")

                            if clause["related_contexts"]:
                                st.markdown("**관련 검색 근거**")
                                for context in clause["related_contexts"]:
                                    st.caption(
                                        f"{context['title']} · {context['source']} · score {context['score']}"
                                    )
                else:
                    st.write("탐지된 위험 조항이 없습니다.")

                if result["contexts"]:
                    st.subheader("검색된 검토 근거")
                    for context in result["contexts"]:
                        with st.expander(f"{context['title']} ({context['source']})"):
                            st.write(context["content"])
                            st.caption(f"검색 점수: {context['score']}")
