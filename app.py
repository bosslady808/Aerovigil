import math
import random
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="AeroVigil V4 - Operations Risk Console",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# HELPERS / CORE LOGIC
# =========================
def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def risk_badge(score):
    if score >= 75:
        return "HIGH"
    if score >= 50:
        return "MODERATE"
    return "LOW"


def legality_check(rest_hours, duty_hours):
    legal_ok = rest_hours >= 10 and duty_hours <= 14
    reason = "Within basic legality thresholds" if legal_ok else "Potential legality concern"
    return legal_ok, reason


def calculate_fatigue_score(duty_hours, segments, timezone_changes, rest_hours, circadian_factor):
    score = 0
    score += max(0, (duty_hours - 8) * 6)
    score += segments * 4
    score += timezone_changes * 5
    score += max(0, (10 - rest_hours) * 8)
    score += circadian_factor * 12
    return clamp(round(score, 1))


def fatigue_call_probability(score, rest_hours, duty_hours, circadian_factor):
    base = 0.12
    prob = (
        base
        + (score / 100) * 0.45
        + max(0, (8 - rest_hours)) * 0.03
        + max(0, (duty_hours - 10)) * 0.02
        + circadian_factor * 0.06
    )
    return clamp(round(prob * 100, 1), 0, 95)


def operational_priority(score, legal_ok, departure_delay, reserve_available):
    priority = 0
    priority += score * 0.45
    priority += min(departure_delay, 180) * 0.15
    priority += 0 if legal_ok else 25
    priority += 0 if reserve_available else 15
    return clamp(round(priority, 1))


def mitigation_recommendation(score, legal_ok, reserve_available, departure_delay):
    if not legal_ok and reserve_available:
        return "Assign reserve crew immediately and protect legality."
    if not legal_ok and not reserve_available:
        return "Escalate to Crew Scheduling / OCC leadership. Current plan may not be legal."
    if score >= 75 and reserve_available:
        return "Swap crew or reduce exposure before departure."
    if score >= 75 and departure_delay >= 60:
        return "Delay recovery plan should include proactive crew replacement evaluation."
    if score >= 50:
        return "Monitor closely, compare alternate crew scenarios, and brief operations leadership."
    return "Proceed with caution. Risk currently manageable."


def generate_timeline(base_score, days=5):
    scores = []
    today = datetime.now().date()
    current = base_score
    for i in range(days):
        drift = random.randint(-8, 10)
        current = clamp(current + drift)
        scores.append(
            {
                "Date": today + timedelta(days=i),
                "Fatigue Risk Score": round(current, 1),
            }
        )
    return pd.DataFrame(scores)


def build_sample_cases():
    raw = [
        {
            "Case ID": "AV-401",
            "Flight": "DL1842",
            "Route": "ATL → DFW",
            "Crew Member": "Captain A",
            "Duty Hours": 11.5,
            "Segments": 4,
            "Timezone Changes": 1,
            "Rest Hours": 9.0,
            "Circadian Factor": 2,
            "Delay Minutes": 40,
            "Reserve Available": True,
        },
        {
            "Case ID": "AV-402",
            "Flight": "DL2207",
            "Route": "JFK → SFO",
            "Crew Member": "FO B",
            "Duty Hours": 12.8,
            "Segments": 3,
            "Timezone Changes": 3,
            "Rest Hours": 8.5,
            "Circadian Factor": 2,
            "Delay Minutes": 75,
            "Reserve Available": False,
        },
        {
            "Case ID": "AV-403",
            "Flight": "DL991",
            "Route": "MSP → ATL",
            "Crew Member": "FA C",
            "Duty Hours": 9.0,
            "Segments": 2,
            "Timezone Changes": 1,
            "Rest Hours": 11.5,
            "Circadian Factor": 1,
            "Delay Minutes": 20,
            "Reserve Available": True,
        },
        {
            "Case ID": "AV-404",
            "Flight": "DL3178",
            "Route": "LGA → MIA",
            "Crew Member": "Captain D",
            "Duty Hours": 13.2,
            "Segments": 5,
            "Timezone Changes": 0,
            "Rest Hours": 8.0,
            "Circadian Factor": 2,
            "Delay Minutes": 110,
            "Reserve Available": True,
        },
        {
            "Case ID": "AV-405",
            "Flight": "DL501",
            "Route": "SEA → ATL",
            "Crew Member": "FO E",
            "Duty Hours": 10.2,
            "Segments": 2,
            "Timezone Changes": 3,
            "Rest Hours": 10.0,
            "Circadian Factor": 1,
            "Delay Minutes": 55,
            "Reserve Available": False,
        },
    ]

    enriched = []
    for row in raw:
        legal_ok, legal_reason = legality_check(row["Rest Hours"], row["Duty Hours"])
        fatigue_score = calculate_fatigue_score(
            row["Duty Hours"],
            row["Segments"],
            row["Timezone Changes"],
            row["Rest Hours"],
            row["Circadian Factor"],
        )
        call_prob = fatigue_call_probability(
            fatigue_score,
            row["Rest Hours"],
            row["Duty Hours"],
            row["Circadian Factor"],
        )
        priority = operational_priority(
            fatigue_score,
            legal_ok,
            row["Delay Minutes"],
            row["Reserve Available"],
        )
        recommendation = mitigation_recommendation(
            fatigue_score,
            legal_ok,
            row["Reserve Available"],
            row["Delay Minutes"],
        )

        row["Legal OK"] = legal_ok
        row["Legal Status"] = "LEGAL" if legal_ok else "CHECK"
        row["Legal Reason"] = legal_reason
        row["Fatigue Score"] = fatigue_score
        row["Risk Level"] = risk_badge(fatigue_score)
        row["Fatigue Call %"] = call_prob
        row["Operational Priority"] = priority
        row["Recommendation"] = recommendation
        enriched.append(row)

    return pd.DataFrame(enriched)


# =========================
# SIDEBAR
# =========================
st.sidebar.title("AeroVigil V4")
st.sidebar.caption("Operations Risk Console")

mode = st.sidebar.radio(
    "Select View",
    [
        "Operations Console",
        "Case Simulator",
        "Scenario Comparison",
        "Executive Snapshot",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("About V4")
st.sidebar.write(
    """
AeroVigil V4 reframes fatigue as an **operational risk indicator**.

This version is designed more like an airline operations console:
- alert queue
- legality + fatigue awareness
- action recommendations
- scenario simulator
- executive KPI view
"""
)

# =========================
# DATA
# =========================
df_cases = build_sample_cases()

# =========================
# HEADER
# =========================
st.title("AeroVigil")
st.subheader("Predictive Crew Risk & Operational Decision Support")

st.caption(
    "A prototype console for evaluating crew legality, fatigue risk, and disruption recovery options in one decision view."
)

# =========================
# OPERATIONS CONSOLE
# =========================
if mode == "Operations Console":
    total_cases = len(df_cases)
    high_cases = int((df_cases["Risk Level"] == "HIGH").sum())
    moderate_cases = int((df_cases["Risk Level"] == "MODERATE").sum())
    legal_issues = int((df_cases["Legal OK"] == False).sum())
    avg_score = round(df_cases["Fatigue Score"].mean(), 1)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active Cases", total_cases)
    c2.metric("High Risk", high_cases)
    c3.metric("Moderate Risk", moderate_cases)
    c4.metric("Legality Checks", legal_issues)
    c5.metric("Avg Risk Score", avg_score)

    st.markdown("---")

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("### Alert Queue")

        display_df = df_cases[
            [
                "Case ID",
                "Flight",
                "Route",
                "Crew Member",
                "Risk Level",
                "Fatigue Score",
                "Legal Status",
                "Fatigue Call %",
                "Operational Priority",
            ]
        ].sort_values(by="Operational Priority", ascending=False)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with right:
        st.markdown("### Case Detail Panel")
        selected_case = st.selectbox("Select Case", df_cases["Case ID"].tolist())

        selected = df_cases[df_cases["Case ID"] == selected_case].iloc[0]

        st.write(f"**Flight:** {selected['Flight']}")
        st.write(f"**Route:** {selected['Route']}")
        st.write(f"**Crew Member:** {selected['Crew Member']}")
        st.write(f"**Risk Level:** {selected['Risk Level']}")
        st.write(f"**Fatigue Score:** {selected['Fatigue Score']}")
        st.write(f"**Legality Status:** {selected['Legal Status']}")
        st.write(f"**Fatigue Call Probability:** {selected['Fatigue Call %']}%")
        st.write(f"**Operational Priority:** {selected['Operational Priority']}")
        st.write(f"**Delay Impact:** {selected['Delay Minutes']} min")
        st.write(f"**Reserve Available:** {'Yes' if selected['Reserve Available'] else 'No'}")

        if selected["Risk Level"] == "HIGH":
            st.error(f"Recommendation: {selected['Recommendation']}")
        elif selected["Risk Level"] == "MODERATE":
            st.warning(f"Recommendation: {selected['Recommendation']}")
        else:
            st.success(f"Recommendation: {selected['Recommendation']}")

        st.info(f"Legality Note: {selected['Legal Reason']}")

    st.markdown("---")

    st.markdown("### Action Engine")
    st.write(
        "This section translates the case into likely operational actions rather than just displaying a score."
    )

    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:
        st.markdown("#### Immediate Action")
        if not selected["Legal OK"]:
            st.write("- Escalate legality concern")
            st.write("- Hold assignment until reviewed")
        elif selected["Fatigue Score"] >= 75:
            st.write("- Evaluate crew swap now")
            st.write("- Notify crew scheduling lead")
        else:
            st.write("- Continue monitoring")
            st.write("- Keep alternate plan ready")

    with action_col2:
        st.markdown("#### Recovery Impact")
        if selected["Delay Minutes"] >= 60:
            st.write("- Delay likely to cascade")
            st.write("- Check downstream crew utilization")
        else:
            st.write("- Limited immediate disruption")
            st.write("- Downline impact currently manageable")

    with action_col3:
        st.markdown("#### Resource Position")
        if selected["Reserve Available"]:
            st.write("- Reserve crew available")
            st.write("- Faster mitigation possible")
        else:
            st.write("- No reserve currently visible")
            st.write("- Mitigation options constrained")

    st.markdown("---")
    st.markdown("### Fatigue Trend Preview")
    trend_df = generate_timeline(selected["Fatigue Score"], days=6)
    trend_df = trend_df.set_index("Date")
    st.line_chart(trend_df)

# =========================
# CASE SIMULATOR
# =========================
elif mode == "Case Simulator":
    st.markdown("### Case Simulator")
    st.write(
        "Use this to test a crew scenario during irregular operations and see risk, legality, and likely action."
    )

    col1, col2 = st.columns(2)

    with col1:
        duty_hours = st.slider("Duty Hours", 4.0, 16.0, 11.0, 0.5)
        segments = st.slider("Flight Segments", 1, 6, 3)
        timezone_changes = st.slider("Timezone Changes", 0, 5, 2)

    with col2:
        rest_hours = st.slider("Rest Hours", 6.0, 16.0, 10.0, 0.5)
        circadian_factor = st.slider("Circadian Disruption", 0, 2, 1)
        delay_minutes = st.slider("Departure Delay (minutes)", 0, 240, 60, 5)

    reserve_available = st.checkbox("Reserve Crew Available", value=True)

    legal_ok, legal_reason = legality_check(rest_hours, duty_hours)
    score = calculate_fatigue_score(
        duty_hours, segments, timezone_changes, rest_hours, circadian_factor
    )
    risk = risk_badge(score)
    call_prob = fatigue_call_probability(score, rest_hours, duty_hours, circadian_factor)
    priority = operational_priority(score, legal_ok, delay_minutes, reserve_available)
    recommendation = mitigation_recommendation(score, legal_ok, reserve_available, delay_minutes)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Fatigue Score", score)
    m2.metric("Risk Level", risk)
    m3.metric("Fatigue Call %", f"{call_prob}%")
    m4.metric("Operational Priority", priority)

    if not legal_ok:
        st.error(f"Legality Status: CHECK — {legal_reason}")
    elif risk == "HIGH":
        st.error(f"Risk Status: HIGH — {recommendation}")
    elif risk == "MODERATE":
        st.warning(f"Risk Status: MODERATE — {recommendation}")
    else:
        st.success(f"Risk Status: LOW — {recommendation}")

    st.markdown("### Timeline Projection")
    simulated_timeline = generate_timeline(score, days=7).set_index("Date")
    st.line_chart(simulated_timeline)

    st.markdown("### Operational Interpretation")
    st.write(
        f"""
- **Legality:** {"Acceptable" if legal_ok else "Needs review"}
- **Fatigue posture:** {risk}
- **Call-off probability:** {call_prob}%
- **Operational recommendation:** {recommendation}
"""
    )

# =========================
# SCENARIO COMPARISON
# =========================
elif mode == "Scenario Comparison":
    st.markdown("### Scenario Comparison")
    st.write("Compare Plan A vs Plan B for decision-making during disruptions.")

    left, right = st.columns(2)

    with left:
        st.markdown("#### Plan A")
        a_duty = st.slider("A Duty Hours", 4.0, 16.0, 12.0, 0.5)
        a_segments = st.slider("A Segments", 1, 6, 4)
        a_tz = st.slider("A Timezone Changes", 0, 5, 2)
        a_rest = st.slider("A Rest Hours", 6.0, 16.0, 9.0, 0.5)
        a_circ = st.slider("A Circadian Disruption", 0, 2, 2)
        a_delay = st.slider("A Delay Minutes", 0, 240, 80, 5)
        a_reserve = st.checkbox("A Reserve Available", value=True)

    with right:
        st.markdown("#### Plan B")
        b_duty = st.slider("B Duty Hours", 4.0, 16.0, 10.0, 0.5)
        b_segments = st.slider("B Segments", 1, 6, 3)
        b_tz = st.slider("B Timezone Changes", 0, 5, 1)
        b_rest = st.slider("B Rest Hours", 6.0, 16.0, 11.0, 0.5)
        b_circ = st.slider("B Circadian Disruption", 0, 2, 1)
        b_delay = st.slider("B Delay Minutes", 0, 240, 45, 5)
        b_reserve = st.checkbox("B Reserve Available", value=False)

    a_legal, _ = legality_check(a_rest, a_duty)
    b_legal, _ = legality_check(b_rest, b_duty)

    a_score = calculate_fatigue_score(a_duty, a_segments, a_tz, a_rest, a_circ)
    b_score = calculate_fatigue_score(b_duty, b_segments, b_tz, b_rest, b_circ)

    a_call = fatigue_call_probability(a_score, a_rest, a_duty, a_circ)
    b_call = fatigue_call_probability(b_score, b_rest, b_duty, b_circ)

    a_priority = operational_priority(a_score, a_legal, a_delay, a_reserve)
    b_priority = operational_priority(b_score, b_legal, b_delay, b_reserve)

    comparison_df = pd.DataFrame(
        {
            "Metric": [
                "Legality",
                "Fatigue Score",
                "Risk Level",
                "Fatigue Call %",
                "Operational Priority",
            ],
            "Plan A": [
                "LEGAL" if a_legal else "CHECK",
                a_score,
                risk_badge(a_score),
                f"{a_call}%",
                a_priority,
            ],
            "Plan B": [
                "LEGAL" if b_legal else "CHECK",
                b_score,
                risk_badge(b_score),
                f"{b_call}%",
                b_priority,
            ],
        }
    )

    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    st.markdown("### Recommendation")
    if (b_legal and not a_legal) or (b_priority < a_priority and b_score <= a_score):
        st.success("Plan B appears operationally safer or more sustainable.")
    elif (a_legal and not b_legal) or (a_priority < b_priority and a_score <= b_score):
        st.success("Plan A appears operationally safer or more sustainable.")
    else:
        st.warning("The options are mixed. Leadership review may be needed.")

    chart_df = pd.DataFrame(
        {
            "Plan": ["Plan A", "Plan B"],
            "Fatigue Score": [a_score, b_score],
            "Operational Priority": [a_priority, b_priority],
        }
    ).set_index("Plan")
    st.bar_chart(chart_df)

# =========================
# EXECUTIVE SNAPSHOT
# =========================
elif mode == "Executive Snapshot":
    st.markdown("### Executive Snapshot")
    st.write(
        "A leadership-level view of active operational risk posture across cases."
    )

    total_cases = len(df_cases)
    avg_risk = round(df_cases["Fatigue Score"].mean(), 1)
    avg_call = round(df_cases["Fatigue Call %"].mean(), 1)
    high_count = int((df_cases["Risk Level"] == "HIGH").sum())
    legal_count = int((df_cases["Legal OK"] == False).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cases Reviewed", total_cases)
    c2.metric("Average Risk Score", avg_risk)
    c3.metric("Avg Fatigue Call %", f"{avg_call}%")
    c4.metric("Legality Escalations", legal_count)

    st.markdown("---")

    st.markdown("### Risk Distribution")
    risk_counts = df_cases["Risk Level"].value_counts().reset_index()
    risk_counts.columns = ["Risk Level", "Count"]
    st.dataframe(risk_counts, use_container_width=True, hide_index=True)

    st.markdown("### Operational Priority Ranking")
    ranked = df_cases[
        ["Case ID", "Flight", "Route", "Risk Level", "Fatigue Score", "Operational Priority", "Recommendation"]
    ].sort_values(by="Operational Priority", ascending=False)
    st.dataframe(ranked, use_container_width=True, hide_index=True)

    st.markdown("### Leadership Summary")
    if high_count >= 2 or legal_count >= 1:
        st.error(
            "System posture suggests elevated operational risk. High-risk and/or legality-sensitive cases require active oversight."
        )
    elif avg_risk >= 50:
        st.warning(
            "System posture is moderate. Recovery decisions should include alternate crew scenario reviews."
        )
    else:
        st.success(
            "System posture is stable. Continue monitoring and maintain reserve flexibility."
        )

    st.markdown("### Management Insight")
    st.write(
        """
AeroVigil V4 is designed to answer a more operational question:

**Not just “Is this crew legal?”**  
but also  
**“Which crew option creates less operational risk right now?”**

That is the value of this console:
- legality awareness
- fatigue awareness
- disruption context
- action-oriented recommendation
"""
    )
