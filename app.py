import random
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="AeroVigil V4 - Operations Risk Console",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================
# HELPERS
# =========================================
def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def risk_badge(score):
    if score >= 75:
        return "HIGH"
    elif score >= 50:
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
        return "Swap crew or assign reserve before departure."
    if score >= 75 and departure_delay >= 60:
        return "Review recovery plan and evaluate proactive crew replacement."
    if score >= 50:
        return "Monitor closely, compare alternate crew scenarios, and brief operations leadership."
    return "Proceed with caution. Risk currently manageable."


def generate_timeline(base_score, days=6):
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


# =========================================
# DATA
# =========================================
df_cases = build_sample_cases()

# =========================================
# SIDEBAR
# =========================================
st.sidebar.title("AeroVigil V4")
st.sidebar.caption("Operations Risk Console")

mode = st.sidebar.radio(
    "Select View",
    [
        "Operations Console",
        "IROPs Mode 🚨",
        "Multi-Flight Disruption Simulator ✈️",
        "Case Simulator",
        "Scenario Comparison",
        "Executive Snapshot",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("About")
st.sidebar.write(
    """
AeroVigil V4 reframes fatigue as an operational risk indicator.

This version includes:
- alert queue
- legality + fatigue awareness
- IROPs decision support
- multi-flight disruption logic
- scenario comparison
- executive view
"""
)

# =========================================
# HEADER
# =========================================
st.title("AeroVigil")
st.subheader("Predictive Crew Risk & Operational Decision Support")
st.caption(
    "A prototype console for evaluating crew legality, fatigue risk, disruption recovery, and operational decision-making in one view."
)

# =========================================
# OPERATIONS CONSOLE
# =========================================
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

    left, right = st.columns([1.3, 1])

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
    a1, a2, a3 = st.columns(3)

    with a1:
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

    with a2:
        st.markdown("#### Recovery Impact")
        if selected["Delay Minutes"] >= 60:
            st.write("- Delay likely to cascade")
            st.write("- Check downstream crew utilization")
        else:
            st.write("- Limited immediate disruption")
            st.write("- Downline impact manageable")

    with a3:
        st.markdown("#### Resource Position")
        if selected["Reserve Available"]:
            st.write("- Reserve crew available")
            st.write("- Faster mitigation possible")
        else:
            st.write("- No reserve currently visible")
            st.write("- Mitigation options constrained")

    st.markdown("---")
    st.markdown("### Fatigue Trend Preview")
    trend_df = generate_timeline(selected["Fatigue Score"], days=6).set_index("Date")
    st.line_chart(trend_df)

# =========================================
# IROPs MODE
# =========================================
elif mode == "IROPs Mode 🚨":
    st.markdown("## IROPs Mode 🚨")
    st.write("Simulate a single disruption scenario and compare immediate crew recovery options.")

    c1, c2 = st.columns(2)

    with c1:
        delay = st.slider("Flight Delay (minutes)", 0, 300, 90, 10)
        segments = st.slider("Remaining Segments", 1, 5, 3)
        timezone_changes = st.slider("Timezone Changes", 0, 5, 2)

    with c2:
        duty_hours = st.slider("Current Duty Hours", 4.0, 16.0, 11.5, 0.5)
        rest_hours = st.slider("Previous Rest Hours", 6.0, 16.0, 9.0, 0.5)
        circadian = st.slider("Circadian Disruption", 0, 2, 2)

    st.markdown("---")
    st.markdown("### Crew Recovery Options")

    reserve_available = st.checkbox("Reserve Crew Available", value=True)
    include_swap = st.checkbox("Include Crew Swap Option", value=True)

    # Continue current crew
    option_a_duty = duty_hours + (delay / 60)
    legal_a, _ = legality_check(rest_hours, option_a_duty)
    score_a = calculate_fatigue_score(
        option_a_duty, segments, timezone_changes, rest_hours, circadian
    )
    call_a = fatigue_call_probability(score_a, rest_hours, option_a_duty, circadian)
    priority_a = operational_priority(score_a, legal_a, delay, reserve_available)

    # Reserve crew
    if reserve_available:
        legal_b, _ = legality_check(12, 8)
        score_b = calculate_fatigue_score(8, segments, timezone_changes, 12, 1)
        call_b = fatigue_call_probability(score_b, 12, 8, 1)
        priority_b = operational_priority(score_b, legal_b, delay, True)
    else:
        legal_b, score_b, call_b, priority_b = False, 100, 95, 100

    # Swap crew
    if include_swap:
        legal_c, _ = legality_check(11, 9)
        score_c = calculate_fatigue_score(9, segments, timezone_changes, 11, 1)
        call_c = fatigue_call_probability(score_c, 11, 9, 1)
        priority_c = operational_priority(score_c, legal_c, delay, reserve_available)
    else:
        legal_c, score_c, call_c, priority_c = False, 100, 95, 100

    comparison = pd.DataFrame(
        {
            "Option": ["Continue Crew", "Reserve Crew", "Swap Crew"],
            "Legality": [
                "LEGAL" if legal_a else "CHECK",
                "LEGAL" if legal_b else "CHECK",
                "LEGAL" if legal_c else "CHECK",
            ],
            "Fatigue Score": [score_a, score_b, score_c],
            "Risk Level": [risk_badge(score_a), risk_badge(score_b), risk_badge(score_c)],
            "Fatigue Call %": [call_a, call_b, call_c],
            "Operational Priority": [priority_a, priority_b, priority_c],
        }
    )

    st.markdown("### Decision Comparison")
    st.dataframe(comparison, use_container_width=True, hide_index=True)

    best_option = comparison.sort_values(by="Operational Priority", ascending=True).iloc[0]

    st.markdown("### Recommendation Engine")
    if best_option["Option"] == "Continue Crew":
        st.warning("Continue current crew — monitor closely and protect downstream operation.")
    elif best_option["Option"] == "Reserve Crew":
        st.success("Assign reserve crew — best operational outcome based on current inputs.")
    else:
        st.info("Swap crew — balanced recovery option under current disruption conditions.")

    st.markdown("### Operational Insight")
    st.write(
        f"""
- **Delay Impact:** {delay} minutes
- **Best Option:** {best_option['Option']}
- **Risk Score:** {best_option['Fatigue Score']}
- **Fatigue Call Probability:** {best_option['Fatigue Call %']}%
- **Priority Level:** {best_option['Operational Priority']}

This simulates OCC-style recovery decision support during disruptions.
"""
    )

# =========================================
# MULTI-FLIGHT DISRUPTION SIMULATOR
# =========================================
elif mode == "Multi-Flight Disruption Simulator ✈️":
    st.markdown("## Multi-Flight Disruption Simulator ✈️")
    st.write("Simulate a network-style disruption and rank flights by operational urgency.")

    top1, top2, top3 = st.columns(3)
    with top1:
        disruption_type = st.selectbox(
            "Disruption Type",
            ["Weather", "Crew Shortage", "ATC Delay", "Maintenance", "System Irregularity"],
        )
    with top2:
        flight_count = st.slider("Number of Affected Flights", 2, 8, 4)
    with top3:
        reserve_pool = st.slider("Available Reserve Crews", 0, 5, 2)

    st.markdown("---")
    st.markdown("### Network Inputs")

    flights = []
    for i in range(flight_count):
        with st.expander(f"Flight {i+1}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                flight_num = st.text_input(f"Flight Number {i+1}", value=f"DL10{i+1}", key=f"fnum_{i}")
                route = st.text_input(f"Route {i+1}", value="ATL → JFK", key=f"route_{i}")
                delay = st.slider(f"Delay Minutes {i+1}", 0, 300, 60 + (i * 15), 5, key=f"delay_{i}")

            with col2:
                duty_hours = st.slider(f"Duty Hours {i+1}", 4.0, 16.0, 10.0 + (i * 0.5), 0.5, key=f"duty_{i}")
                rest_hours = st.slider(f"Rest Hours {i+1}", 6.0, 16.0, 10.0, 0.5, key=f"rest_{i}")
                segments = st.slider(f"Segments {i+1}", 1, 6, 2 + (i % 3), key=f"seg_{i}")

            with col3:
                tz = st.slider(f"Timezone Changes {i+1}", 0, 5, i % 3, key=f"tz_{i}")
                circadian = st.slider(f"Circadian Disruption {i+1}", 0, 2, 1, key=f"circ_{i}")
                passengers = st.slider(f"Passenger Impact {i+1}", 50, 300, 120 + (i * 20), 10, key=f"pax_{i}")

            legal_ok, _ = legality_check(rest_hours, duty_hours + (delay / 60))
            score = calculate_fatigue_score(
                duty_hours + (delay / 60), segments, tz, rest_hours, circadian
            )
            call_prob = fatigue_call_probability(score, rest_hours, duty_hours + (delay / 60), circadian)

            # passenger impact factor for network severity
            passenger_factor = min(passengers / 300, 1.0) * 20

            # reserve assumption: reserve available only if pool still exists
            reserve_assumed = reserve_pool > 0
            priority = operational_priority(score, legal_ok, delay, reserve_assumed)
            network_priority = clamp(round(priority + passenger_factor, 1))

            recommendation = mitigation_recommendation(score, legal_ok, reserve_assumed, delay)

            flights.append(
                {
                    "Flight": flight_num,
                    "Route": route,
                    "Disruption": disruption_type,
                    "Delay Minutes": delay,
                    "Duty Hours": round(duty_hours + (delay / 60), 1),
                    "Rest Hours": rest_hours,
                    "Segments": segments,
                    "Timezone Changes": tz,
                    "Circadian": circadian,
                    "Passenger Impact": passengers,
                    "Legality": "LEGAL" if legal_ok else "CHECK",
                    "Fatigue Score": score,
                    "Risk Level": risk_badge(score),
                    "Fatigue Call %": call_prob,
                    "Priority Score": priority,
                    "Network Priority": network_priority,
                    "Recommendation": recommendation,
                }
            )

    network_df = pd.DataFrame(flights).sort_values(by="Network Priority", ascending=False).reset_index(drop=True)

    st.markdown("---")
    st.markdown("### Network Alert Board")
    st.dataframe(
        network_df[
            [
                "Flight",
                "Route",
                "Delay Minutes",
                "Passenger Impact",
                "Legality",
                "Fatigue Score",
                "Risk Level",
                "Fatigue Call %",
                "Network Priority",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Reserve Crew Allocation Suggestion")
    allocation_df = network_df.copy()
    allocation_df["Reserve Assigned"] = "No"

    reserves_left = reserve_pool
    for idx in allocation_df.index:
        if reserves_left > 0 and allocation_df.loc[idx, "Network Priority"] >= 55:
            allocation_df.loc[idx, "Reserve Assigned"] = "Yes"
            reserves_left -= 1

    st.dataframe(
        allocation_df[
            [
                "Flight",
                "Route",
                "Network Priority",
                "Risk Level",
                "Legality",
                "Reserve Assigned",
                "Recommendation",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Executive Network Summary")
    total_high = int((network_df["Risk Level"] == "HIGH").sum())
    total_checks = int((network_df["Legality"] == "CHECK").sum())
    avg_network_priority = round(network_df["Network Priority"].mean(), 1)
    top_flight = network_df.iloc[0]["Flight"]

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Affected Flights", len(network_df))
    s2.metric("High-Risk Flights", total_high)
    s3.metric("Legality Checks", total_checks)
    s4.metric("Avg Network Priority", avg_network_priority)

    if total_checks > 0:
        st.error(
            f"Highest urgency flight: {top_flight}. Network includes legality-sensitive flying that should be escalated."
        )
    elif total_high >= 2:
        st.warning(
            f"Highest urgency flight: {top_flight}. Multiple flights are elevated and reserves should be prioritized carefully."
        )
    else:
        st.success(
            f"Highest urgency flight: {top_flight}. Network disruption appears manageable with current reserve capacity."
        )

    chart_df = network_df.set_index("Flight")[["Fatigue Score", "Network Priority"]]
    st.markdown("### Network Risk Chart")
    st.bar_chart(chart_df)

# =========================================
# CASE SIMULATOR
# =========================================
elif mode == "Case Simulator":
    st.markdown("### Case Simulator")
    st.write("Test a single crew scenario and evaluate fatigue, legality, and operational action.")

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

# =========================================
# SCENARIO COMPARISON
# =========================================
elif mode == "Scenario Comparison":
    st.markdown("### Scenario Comparison")
    st.write("Compare Plan A vs Plan B for disruption decision-making.")

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

# =========================================
# EXECUTIVE SNAPSHOT
# =========================================
elif mode == "Executive Snapshot":
    st.markdown("### Executive Snapshot")
    st.write("Leadership-level view of active operational risk posture.")

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
AeroVigil is built to answer a more operational question:

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
