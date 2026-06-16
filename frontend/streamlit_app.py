import requests
import streamlit as st

API_URL = "http://localhost:8000/api/analyze"
API_FILE_URL = "http://localhost:8000/api/analyze-file"

st.set_page_config(page_title="Lawgic MVP", page_icon="⚖️", layout="wide")
st.title("⚖️ Lawgic RAG/LLM")
st.caption("계약서 텍스트, PDF, 이미지 파일을 분석해 위험 조항과 수정 방향을 정리합니다.")
st.warning("본 결과는 법률 자문이 아닌 계약서 검토 보조 결과입니다. 최종 판단은 전문가 검토가 필요합니다.")

SAMPLES = {
    "employment": """아르바이트 근로계약서

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
""",
    "lease": """주택 월세 임대차계약서

임대인 홍길동(이하 “임대인”)과 임차인 김테스트(이하 “임차인”)는 서울특별시 테스트구 예시로 100, 101호에 관하여 다음과 같이 임대차계약을 체결한다.

제1조 보증금 및 차임
보증금은 10,000,000원, 월 차임은 700,000원으로 한다. 임대인은 주변 시세나 개인 사정에 따라 계약기간 중에도 월세와 관리비를 조정할 수 있으며, 임차인은 이에 이의를 제기하지 않는다.

제2조 계약기간
계약기간은 2026년 7월 1일부터 2027년 6월 30일까지 1년으로 한다. 기간 만료 시 임대인이 별도로 통보하지 않아도 계약은 자동 종료되며 임차인은 즉시 퇴거해야 한다.

제3조 전입신고 및 확정일자
임차인은 임대인의 사전 서면 동의 없이 전입신고나 확정일자를 받을 수 없다. 이를 위반하는 경우 임대인은 계약을 즉시 해지할 수 있다.

제4조 수선 및 관리
누수, 보일러 고장, 배관 문제, 전기 설비 고장 등 주택 사용 중 발생하는 모든 수리비는 원인과 관계없이 임차인이 부담한다.

제5조 원상회복
임차인은 퇴거 시 통상적인 사용으로 생긴 마모나 노후화까지 포함하여 모든 시설을 신품 상태로 원상회복해야 하며, 임대인은 필요한 비용을 보증금에서 임의로 공제할 수 있다.

제6조 중도해지
임차인이 계약기간 중 중도해지를 원하는 경우 남은 계약기간의 월세 전액을 위약금으로 지급해야 하며, 보증금 반환은 새 임차인이 입주한 이후로 한다.

제7조 계약갱신
임차인은 본 계약 체결과 동시에 계약갱신 요구권을 행사하지 않기로 확약한다. 임대인은 필요하다고 판단하는 경우 갱신을 거절할 수 있다.

2026년 6월 16일

임대인: 홍길동
임차인: 김테스트
""",
}

CONTRACT_TYPE_OPTIONS = {
    "employment": "근로계약서",
    "lease": "주택임대차계약서",
}

uploaded_file = st.file_uploader(
    "PDF 또는 이미지 파일 업로드",
    type=["pdf", "jpg", "jpeg", "png", "webp"],
)
contract_type = st.selectbox(
    "계약서 유형",
    options=list(CONTRACT_TYPE_OPTIONS),
    format_func=lambda value: CONTRACT_TYPE_OPTIONS[value],
)
text = st.text_area(
    "계약서 텍스트 입력",
    value=SAMPLES[contract_type],
    height=240,
    key=f"contract_text_{contract_type}",
)

if st.button("분석 실행", type="primary", use_container_width=True):
    if uploaded_file is None and not text.strip():
        st.warning("계약서 텍스트를 입력하거나 파일을 업로드해 주세요.")
    else:
        with st.spinner("RAG 근거 검색 및 위험 조항 분석 중..."):
            try:
                if uploaded_file is not None:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    }
                    response = requests.post(
                        API_FILE_URL,
                        data={"contract_type": contract_type},
                        files=files,
                        timeout=120,
                    )
                else:
                    response = requests.post(
                        API_URL,
                        json={"text": text, "contract_type": contract_type},
                        timeout=60,
                    )

                if not response.ok:
                    try:
                        detail = response.json().get("detail", response.text)
                    except ValueError:
                        detail = response.text
                    raise requests.HTTPError(detail, response=response)

                result = response.json()
            except requests.RequestException as exc:
                st.error(f"API 호출 실패: {exc}")
            else:
                st.success("분석 완료")

                col1, col2, col3 = st.columns(3)
                col1.metric("총 문장 수", result["total_sentences"])
                col2.metric("위험 조항 수", result["risk_count"])
                col3.metric("분석 모델", result["model_used"])
                st.caption(f"계약서 유형: {CONTRACT_TYPE_OPTIONS.get(result['contract_type'], result['contract_type'])}")

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
