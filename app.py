import streamlit as st
import pandas as pd
from fatigue_calculator import calculate_fatigue_score

st.set_page_config(page_title="AeroVigil", layout="wide")

st.title("AeroVigil")
st.subheader("Predictive Fatigue Risk Analytics for Aviation Safety")
st.write(
    "A prototype aviation safety tool for estimating crew fatigue risk using duty time, segments, rest, timezone changes, and circadian disruption."
)

st.divider()


def classify_risk(score):
    if score < 35:
        return "LOW", "Crew member appears fit for duty based on current inputs.", "green"
    elif score < 65:
        return "MODERATE", "Fatigue risk is elevated. Consider monitoring or mitigation strategies.", "orange"
    else:
        return "HIGH", "High fatigue risk detected. Schedule review or fatigue mitigation recommended.", "red"


def build_recommendations(duty_hours, segments, timezone_changes, rest_hours, circadian_disruption):
    recommendations = []

    if duty_hours >= 12:
        recommendations.append("Reduce duty period or split assignments to lower fatigue exposure.")
    if segments >= 4:
        recommendations.append("Reduce the number of flight segments to decrease workload and task saturation.")
    if timezone_changes >= 2:
        recommendations.append("Limit additional timezone transitions or allow more adaptation time.")
    if rest_hours <= 8:
        recommendations.append("Increase pre-duty rest opportunity before assigning the next trip.")
    if circadian_disruption >= 6:
        recommendations.append("Avoid scheduling during peak circadian low periods when possible.")

    if not recommendations:
        recommendations.append("No major fatigue mitigations indicated from the current inputs.")

    return recommendations


def build_timeline_data(duty_hours, segments, timezone_changes, rest_hours, circadian_disruption):
    timeline = [
        {
            "Day": "Day 1",
            "Duty Hours": duty_hours,
            "Segments": segments,
            "Time Zones": timezone_changes,
            "Rest Hours": rest_hours,
            "Circadian Disruption": circadian_disruption,
        },
        {
            "Day": "Day 2",
            "Duty Hours": min(duty_hours + 1, 16),
            "Segments": segments,
            "Time Zones": timezone_changes,
            "Rest Hours": max(rest_hours - 1, 0),
            "Circadian Disruption": min(circadian_disruption + 1, 10),
        },
        {
            "Day": "Day 3",
            "Duty Hours": min(duty_hours + 2, 16),
            "Segments": min(segments + 1, 8),
            "Time Zones": min(timezone_changes + 1, 6),
            "Rest Hours": max(rest_hours - 2, 0),
            "Circadian Disruption": min(circadian_disruption + 2, 10),
        },
        {
            "Day": "Day 4",
            "Duty Hours": max(duty_hours - 1, 0),
            "Segments": max(segments - 1, 1),
            "Time Zones": timezone_changes,
            "Rest Hours": min(rest_hours + 2, 16),
            "Circadian Disruption": max(circadian_disruption - 1, 0),
        },
    ]

    for day in timeline:
        score = calculate_fatigue_score(
            day["Duty Hours"],
            day["Segments"],
            day["Time Zones"],
            day["Rest Hours"],
            day["Circadian Disruption"],
        )
        risk_level, _, _ = classify_risk(score)
        day["Fatigue Score"] = score
        day["Risk Level"] = risk_level

    return pd.DataFrame(timeline)


# Sidebar inputs
st.sidebar.header("Crew Duty Inputs")
duty_hours = st.sidebar.slider("Duty Hours", 0, 16, 8)
segments = st.sidebar.slider("Flight Segments", 1, 8, 2)
timezone_changes = st.sidebar.slider("Time Zone Changes", 0, 6, 0)
rest_hours = st.sidebar.slider("Rest Hours Before Duty", 0, 16, 10)
circadian_disruption = st.sidebar.slider("Circadian Disruption Level", 0, 10, 3)

st.subheader("Current Crew Input Summary")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Duty Hours", duty_hours)
    st.metric("Flight Segments", segments)

with col2:
    st.metric("Timezone Changes", timezone_changes)
    st.metric("Rest Hours", rest_hours)

with col3:
    st.metric("Circadian Disruption", circadian_disruption)

st.divider()

if st.button("Calculate Fatigue Risk", use_container_width=True):
    score = calculate_fatigue_score(
        duty_hours,
        segments,
        timezone_changes,
        rest_hours,
        circadian_disruption
    )

    risk_level, status_message, gauge_color = classify_risk(score)

    st.subheader("Fatigue Risk Results")
    result_col1, result_col2 = st.columns([2, 1])

    with result_col1:
        st.subheader(f"Fatigue Score: {score}/100")
        st.progress(score / 100)

        if risk_level == "LOW":
            st.success(f"Fatigue Risk Level: {risk_level}")
        elif risk_level == "MODERATE":
            st.warning(f"Fatigue Risk Level: {risk_level}")
        else:
            st.error(f"Fatigue Risk Level: {risk_level}")

        st.write(status_message)

    with result_col2:
        st.metric("Operational Status", risk_level)

    st.divider()
    st.subheader("Fatigue Risk Gauge")

    st.markdown(
        f"""
        <div style="background-color:{gauge_color};
                    padding:25px;
                    border-radius:12px;
                    text-align:center;
                    font-size:28px;
                    color:white;
                    font-weight:bold;">
            Fatigue Risk Score: {score}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()
    st.subheader("Mitigation Recommendations")

    recommendations = build_recommendations(
        duty_hours, segments, timezone_changes, rest_hours, circadian_disruption
    )

    for rec in recommendations:
        st.write(f"• {rec}")

    st.divider()
    st.subheader("Operational Summary")

    st.info(
        f"""
AeroVigil assessment complete.

Risk Level: {risk_level}
Fatigue Score: {score}/100

This prototype suggests that current scheduling conditions create a {risk_level.lower()} fatigue risk profile.
Use this result as a decision-support signal for safety review, crew planning, and mitigation action.
        """
    )

    st.divider()
    st.subheader("Fatigue Trend Scenario Chart")

    scenario_data = [
        {
            "Scenario": "Current",
            "Score": calculate_fatigue_score(
                duty_hours, segments, timezone_changes, rest_hours, circadian_disruption
            ),
        },
        {
            "Scenario": "+2 Duty Hours",
            "Score": calculate_fatigue_score(
                min(duty_hours + 2, 16), segments, timezone_changes, rest_hours, circadian_disruption
            ),
        },
        {
            "Scenario": "+1 Segment",
            "Score": calculate_fatigue_score(
                duty_hours, min(segments + 1, 8), timezone_changes, rest_hours, circadian_disruption
            ),
        },
        {
            "Scenario": "-2 Rest Hours",
            "Score": calculate_fatigue_score(
                duty_hours, segments, timezone_changes, max(rest_hours - 2, 0), circadian_disruption
            ),
        },
        {
            "Scenario": "+2 Time Zones",
            "Score": calculate_fatigue_score(
                duty_hours, segments, min(timezone_changes + 2, 6), rest_hours, circadian_disruption
            ),
        },
    ]

    scenario_df = pd.DataFrame(scenario_data)
    st.line_chart(scenario_df.set_index("Scenario"))
    st.dataframe(scenario_df, use_container_width=True)

    st.divider()
    st.subheader("4-Day Fatigue Timeline Predictor")

    timeline_df = build_timeline_data(
        duty_hours, segments, timezone_changes, rest_hours, circadian_disruption
    )

    st.line_chart(timeline_df.set_index("Day")["Fatigue Score"])
    st.dataframe(
        timeline_df[
            ["Day", "Duty Hours", "Segments", "Time Zones", "Rest Hours", "Circadian Disruption", "Fatigue Score", "Risk Level"]
        ],
        use_container_width=True
    )

    highest_day = timeline_df.loc[timeline_df["Fatigue Score"].idxmax()]
    st.warning(
        f"Highest projected fatigue day: {highest_day['Day']} "
        f"with score {highest_day['Fatigue Score']}/100 ({highest_day['Risk Level']})."
    )
