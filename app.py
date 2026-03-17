import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fatigue_calculator import calculate_fatigue_score

st.set_page_config(page_title="AeroVigil", layout="wide")

st.title("AeroVigil")
st.subheader("Predictive Fatigue Risk Analytics for Aviation Safety")
st.write(
    "A prototype aviation safety tool for estimating crew fatigue risk using duty time, "
    "segments, rest, time zone changes, circadian disruption, and a simplified alertness model."
)

st.divider()

# Sidebar inputs
st.sidebar.header("Crew Duty Inputs")

duty_hours = st.sidebar.slider("Duty Hours", 0, 16, 8)
segments = st.sidebar.slider("Flight Segments", 1, 8, 2)
timezone_changes = st.sidebar.slider("Time Zone Changes", 0, 6, 0)
rest_hours = st.sidebar.slider("Rest Hours Before Duty", 0, 16, 10)
circadian_disruption = st.sidebar.slider("Circadian Disruption Level", 0, 10, 3)
hours_awake = st.sidebar.slider("Hours Awake Before/During Duty", 0, 24, 10)

# Core fatigue score
score = calculate_fatigue_score(
    duty_hours,
    segments,
    timezone_changes,
    rest_hours,
    circadian_disruption
)

# Risk classification
if score < 35:
    risk_level = "LOW"
    recommendation = "Fatigue risk appears manageable. Continue normal monitoring."
elif score < 65:
    risk_level = "MODERATE"
    recommendation = "Consider additional rest, schedule review, or fatigue mitigation strategies."
else:
    risk_level = "HIGH"
    recommendation = "High fatigue risk detected. Consider schedule adjustment, additional rest, or operational mitigation."

# Simplified alertness model
alertness = 100
alertness -= hours_awake * 2.5
alertness -= circadian_disruption * 2.0
alertness -= timezone_changes * 3.0
alertness += rest_hours * 1.2
alertness = max(0, min(100, alertness))

if alertness >= 80:
    effectiveness_label = "HIGH"
elif alertness >= 60:
    effectiveness_label = "MODERATE"
else:
    effectiveness_label = "LOW"

# Circadian phase label
if 0 <= hours_awake <= 8:
    circadian_phase = "Optimal/Daytime Zone"
elif 9 <= hours_awake <= 16:
    circadian_phase = "Extended Wakefulness Zone"
else:
    circadian_phase = "Critical Fatigue Zone"

# Top metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Fatigue Score", f"{score}/100")

with col2:
    st.metric("Risk Level", risk_level)

with col3:
    st.metric("Alertness Effectiveness", f"{alertness:.0f}%")

st.divider()

st.subheader("Fatigue Assessment")
st.write(f"**Mitigation Recommendation:** {recommendation}")
st.write(f"**Circadian Phase:** {circadian_phase}")
st.write(f"**Operational Effectiveness Rating:** {effectiveness_label}")

# Scenario summary
summary_df = pd.DataFrame(
    {
        "Metric": [
            "Duty Hours",
            "Flight Segments",
            "Time Zone Changes",
            "Rest Hours",
            "Circadian Disruption",
            "Hours Awake",
            "Fatigue Score",
            "Risk Level",
            "Alertness Effectiveness",
        ],
        "Value": [
            duty_hours,
            segments,
            timezone_changes,
            rest_hours,
            circadian_disruption,
            hours_awake,
            score,
            risk_level,
            f"{alertness:.0f}%",
        ],
    }
)

st.subheader("Scenario Summary")
st.dataframe(summary_df, use_container_width=True)

# Scenario comparison chart
st.subheader("Scenario Comparison")

comparison_df = pd.DataFrame(
    {
        "Category": ["Fatigue Score", "Alertness Effectiveness"],
        "Value": [score, alertness],
    }
)

fig1, ax1 = plt.subplots(figsize=(8, 4))
ax1.bar(comparison_df["Category"], comparison_df["Value"])
ax1.set_ylim(0, 100)
ax1.set_ylabel("Score")
ax1.set_title("Fatigue vs Alertness")
st.pyplot(fig1)

# 4-day fatigue trend predictor
st.subheader("4-Day Fatigue Trend Predictor")

days = ["Day 1", "Day 2", "Day 3", "Day 4"]
fatigue_trend = []
alertness_trend = []

for day in range(4):
    projected_score = min(100, score + day * 5)
    projected_alertness = max(0, alertness - day * 6)
    fatigue_trend.append(projected_score)
    alertness_trend.append(projected_alertness)

trend_df = pd.DataFrame(
    {
        "Day": days,
        "Fatigue Score": fatigue_trend,
        "Alertness Effectiveness": alertness_trend,
    }
)

st.dataframe(trend_df, use_container_width=True)

fig2, ax2 = plt.subplots(figsize=(10, 4))
ax2.plot(trend_df["Day"], trend_df["Fatigue Score"], marker="o", label="Fatigue Score")
ax2.plot(
    trend_df["Day"],
    trend_df["Alertness Effectiveness"],
    marker="o",
    label="Alertness Effectiveness",
)
ax2.set_ylim(0, 100)
ax2.set_ylabel("Score / Effectiveness")
ax2.set_title("Projected 4-Day Fatigue and Alertness Trend")
ax2.legend()
st.pyplot(fig2)

# Alertness over time graph
st.subheader("Alertness Over Time")

hours = list(range(0, 25))
alertness_curve = []

for h in hours:
    curve_value = 100
    curve_value -= h * 2.8
    curve_value -= circadian_disruption * 2.0
    curve_value -= timezone_changes * 2.5
    curve_value += rest_hours * 1.1
    curve_value = max(0, min(100, curve_value))
    alertness_curve.append(curve_value)

curve_df = pd.DataFrame(
    {
        "Hours Awake": hours,
        "Alertness": alertness_curve,
    }
)

fig3, ax3 = plt.subplots(figsize=(10, 4))
ax3.plot(curve_df["Hours Awake"], curve_df["Alertness"], marker="o")
ax3.set_ylim(0, 100)
ax3.set_xlabel("Hours Awake")
ax3.set_ylabel("Alertness Effectiveness (%)")
ax3.set_title("Prototype Alertness Decay Curve")
st.pyplot(fig3)

# Disclaimer
st.info(
    "Disclaimer: This simplified alertness model is a prototype for educational and concept "
    "demonstration purposes only. It is not a validated SAFTE model and should not be used for operational safety decisions."
)
