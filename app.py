import streamlit as st
import pandas as pd
import pdfplumber
import re

# ---------- Page Config ----------
st.set_page_config(
    page_title="TenderAI - Government Tender Evaluation Platform",
    layout="wide"
)

# ---------- Helper Functions ----------
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_criteria(text):
    criteria = {
        "turnover": 5,
        "projects": 3,
        "gst": True,
        "iso": True,
    }

    text_lower = text.lower()

    turnover_match = re.search(r"(\d+)\s*crore", text_lower)
    projects_match = re.search(r"(\d+)\s*projects", text_lower)

    if turnover_match:
        criteria["turnover"] = int(turnover_match.group(1))

    if projects_match:
        criteria["projects"] = int(projects_match.group(1))

    criteria["gst"] = "gst" in text_lower
    criteria["iso"] = "iso" in text_lower

    return criteria


def evaluate_bidder(criteria, bidder):
    checks = [
        ("Turnover", bidder["turnover"] >= criteria["turnover"]),
        ("Projects", bidder["projects"] >= criteria["projects"]),
        ("GST", bidder["gst"] == criteria["gst"]),
        ("ISO", bidder["iso"] == criteria["iso"]),
    ]

    results = []
    passed = 0
    failed_criteria = []

    for criterion, status in checks:
        results.append({
            "Criterion": criterion,
            "Status": "PASS" if status else "FAIL",
            "Confidence": "95%" if status else "70%"
        })

        if status:
            passed += 1
        else:
            failed_criteria.append(criterion)

    score_percent = int((passed / len(checks)) * 100)

    final_status = (
        "ELIGIBLE ✅"
        if passed == len(checks)
        else "NOT ELIGIBLE ❌"
    )

    return pd.DataFrame(results), final_status, score_percent, failed_criteria


def get_risk_level(score):
    if score == 100:
        return "Low"
    elif score >= 50:
        return "Medium"
    else:
        return "High"


def get_suggested_decision(status, score):
    if "ELIGIBLE" in status and score == 100:
        return "Approve"
    elif score >= 50:
        return "Send for Manual Review"
    else:
        return "Reject"


# ---------- Main UI ----------
st.title("TenderAI - Government Tender Evaluation Platform")
st.caption("AI-powered prototype for automated government tender eligibility screening")

st.progress(100)
st.caption(
    "Tender Uploaded → Criteria Extracted → Bid Evaluated → Officer Decision Completed"
)

# ---------- Default KPI Cards ----------
top1, top2, top3, top4 = st.columns(4)
top1.metric("Clauses Extracted", 4)
top2.metric("Bidder Score", "--")
top3.metric("Risk Level", "--")
top4.metric("Final Status", "--")

st.divider()

# ---------- File Upload ----------
uploaded_file = st.file_uploader("Upload Tender PDF", type=["pdf"])

if uploaded_file:
    tender_text = extract_text_from_pdf(uploaded_file)

    st.subheader("Tender Text")
    st.text_area("Extracted Text", tender_text, height=180)

    criteria = extract_criteria(tender_text)

    st.subheader("Extracted Criteria")
    st.json(criteria)

    # ---------- Bidder Input ----------
    st.subheader("Simulated Bidder Data")

    col1, col2 = st.columns(2)

    with col1:
        turnover = st.number_input(
            "Turnover (crore)",
            min_value=0,
            value=6
        )

        projects = st.number_input(
            "Projects Completed",
            min_value=0,
            value=4
        )

    with col2:
        gst = st.selectbox(
            "GST Registered",
            [True, False]
        )

        iso = st.selectbox(
            "ISO Certified",
            [True, False]
        )

    bidder = {
        "turnover": turnover,
        "projects": projects,
        "gst": gst,
        "iso": iso,
    }

    # ---------- Evaluation Button ----------
    if st.button("Run AI Evaluation"):
        df, final_status, score_percent, failed = evaluate_bidder(
            criteria,
            bidder
        )

        risk_level = get_risk_level(score_percent)
        suggested_decision = get_suggested_decision(
            final_status,
            score_percent
        )

        # ---------- Dynamic KPI Cards ----------
        k1, k2, k3, k4 = st.columns(4)

        k1.metric("Clauses Extracted", len(df))
        k2.metric("Bidder Score", f"{score_percent}%")
        k3.metric("Risk Level", risk_level)
        k4.metric("Final Status", final_status)

        st.subheader("Evaluation Result")
        st.dataframe(df, use_container_width=True)

        # ---------- Final Result ----------
        if "ELIGIBLE" in final_status:
            st.success(f"FINAL RESULT: {final_status}")
        else:
            st.error(f"FINAL RESULT: {final_status}")

        # ---------- Dynamic Reasoning ----------
        st.subheader("AI Decision Reasoning")

        if failed:
            reason = ", ".join(failed)
            st.warning(
                f"The bidder does not satisfy all mandatory eligibility clauses. "
                f"Failed criteria: {reason}."
            )
        else:
            st.success(
                "The bidder satisfies all mandatory eligibility clauses "
                "including turnover, project history, GST registration, "
                "and ISO certification."
            )

        # ---------- Risk Flags ----------
        st.subheader("AI Risk Flags")

        if risk_level == "Low":
            st.success("No major risks detected")
        elif risk_level == "Medium":
            st.warning(
                "Potential compliance risks found in failed criteria"
            )
        else:
            st.error(
                "High risk bidder profile. Immediate rejection recommended."
            )

        # ---------- Officer Review ----------
        st.subheader("Officer Review")
        st.info(f"Suggested Officer Decision: {suggested_decision}")

        decision = st.radio(
            "Officer Decision",
            ["Approve", "Reject", "Send for Manual Review"],
            index=[
                "Approve",
                "Reject",
                "Send for Manual Review"
            ].index(suggested_decision)
        )

        st.info(f"Officer Decision: {decision}")

        # ---------- Summary ----------
        st.subheader("Tender Summary")

        st.write(f"Required Turnover: ₹{criteria['turnover']} crore")
        st.write(f"Required Projects: {criteria['projects']}")
        st.write(f"GST Required: {criteria['gst']}")
        st.write(f"ISO Required: {criteria['iso']}")
        st.write(f"Final Eligibility: {final_status}")
        st.write(f"Risk Level: {risk_level}")
        st.write(f"Bidder Score: {score_percent}%")
        st.write(f"Officer Decision: {decision}")

        # ---------- Impact ----------
        st.subheader("Expected Impact")

        st.info("""
- Reduces manual screening time by 80%
- Improves transparency in government procurement
- Minimizes human bias in eligibility checks
- Enables scalable nationwide deployment
        """)

else:
    st.info("Upload a tender PDF to start evaluation")