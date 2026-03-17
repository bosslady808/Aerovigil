# app.py
import streamlit as st

def fatigue_risk_score(duty_hours, segments, timezone_changes, rest_hours, circadian_disruption):
    score = 0

    if duty_hours > 10:
        score += (duty_hours - 10) * 5

    score += segments * 3
    score += timezone_changes * 4

    if rest_hours < 10:
        score += (10 - rest_hours) * 6

    if circadian_disruption:
        score += 15

    return min(score, 100)


def risk_level(score):
    if score < 30:
        return "Low"
    elif score < 60:
        return "Moderate"
    elif score < 80:
        return "High"
    return "Critical"


st.set_page_config(page_title="AeroVigil", layout="centered")

st.title("AeroVigil")
st.subheader("Predictive Fatigue Risk Dashboard")
st.caption("Prototype for aviation safety teams and SMS programs")

duty_hours = st.number_input("Duty Hours", min_value=0.0, max_value=24.0, value=12.0, step=0.5)
segments = st.number_input("Flight Segments", min_value=0, max_value=10, value=4, step=1)
timezone_changes = st.number_input("Time Zone Changes", min_value=0, max_value=12, value=2, step=1)
rest_hours = st.number_input("Rest Hours Before Duty", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
circadian_disruption = st.checkbox("Circadian Disruption (overnight / sleep-window overlap)", value=True)

if st.button("Calculate Fatigue Risk"):
    score = fatigue_risk_score(
        duty_hours,
        segments,
        timezone_changes,
        rest_hours,
        circadian_disruption
    )

    level = risk_level(score)

    st.metric("Fatigue Risk Score", f"{score}/100")
    st.metric("Risk Level", level)

    if score >= 80:
        st.error("Critical fatigue risk. Review duty assignment immediately.")
    elif score >= 60:
        st.warning("High fatigue risk. Consider mitigation before release.")
    elif score >= 30:
        st.info("Moderate fatigue risk. Monitor closely.")
    else:
        st.success("Low fatigue risk. Operation appears acceptable.")

    st.markdown("### Operational Summary")
    st.write(f"- Duty Hours: {duty_hours}")
    st.write(f"- Segments: {segments}")
    st.write(f"- Time Zone Changes: {timezone_changes}")
    st.write(f"- Rest Hours: {rest_hours}")
    st.write(f"- Circadian Disruption: {'Yes' if circadian_disruption else 'No'}")
