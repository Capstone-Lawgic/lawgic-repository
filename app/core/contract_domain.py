from typing import Literal

ContractDomain = Literal["employment", "lease"]


DOMAIN_LABELS: dict[ContractDomain, str] = {
    "employment": "근로계약서",
    "lease": "주택임대차계약서",
}

DOMAIN_DESCRIPTIONS: dict[ContractDomain, str] = {
    "employment": (
        "임금, 근로시간, 휴게시간, 수당, 해고, 퇴사, 위약금, "
        "개인정보, 경업금지, 근로조건 변경을 중심으로 검토한다."
    ),
    "lease": (
        "보증금, 차임, 계약기간, 계약갱신, 중도해지, 관리비, 수선의무, "
        "원상회복, 전입신고, 확정일자, 보증금 반환을 중심으로 검토한다."
    ),
}

DOMAIN_KEYWORDS: dict[ContractDomain, tuple[str, ...]] = {
    "employment": (
        "근로계약",
        "근로자",
        "사용자",
        "회사",
        "임금",
        "급여",
        "시급",
        "최저임금",
        "근로시간",
        "연장근로",
        "야간근로",
        "휴게시간",
        "수습기간",
        "퇴사",
        "해고",
        "경업금지",
    ),
    "lease": (
        "임대차",
        "임대인",
        "임차인",
        "보증금",
        "월세",
        "차임",
        "관리비",
        "전입신고",
        "확정일자",
        "계약갱신",
        "묵시적 갱신",
        "원상회복",
        "수선",
        "수리",
        "퇴거",
        "인도",
        "전세",
        "주택",
    ),
}


def detect_contract_domain(text: str) -> ContractDomain:
    normalized = text.replace(" ", "")
    scores: dict[ContractDomain, int] = {"employment": 0, "lease": 0}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword.replace(" ", "") in normalized:
                scores[domain] += 1

    if scores["lease"] > scores["employment"]:
        return "lease"
    return "employment"
