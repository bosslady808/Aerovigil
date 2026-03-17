import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


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


def fatigue_reason(duty_hours, segments, timezone_changes, rest_hours, circadian_disruption):
    reasons = []

    if duty_hours > 12:
        reasons.append("Long duty period")

    if segments >= 4:
        reasons.append("High flight segments")

    if timezone_changes >= 2:
        reasons.append("Multiple time zone crossings")

    if rest_hours < 10:
        reasons.append("Short rest period")

    if circadian_disruption:
        reasons.append("Circadian disruption")

    if not reasons:
        return "No major fatigue drivers"

    return ", ".join(reasons)


def risk_level(score):
    if score < 30:
        return "LOW"
    elif score < 60:
        return "MODERATE"
    elif score < 80:
        return "HIGH"
    return "CRITICAL"


def to_bool(value):
    return str(value).strip().lower() in ["yes", "true", "1"]


st.set_page_config(page_title="AeroVigil", layout="wide")

st.title("AeroVigil")
st.subheader("CSV Crew Fatigue Risk Analyzer")
st.caption("Prototype for airline safety teams and SMS programs")

uploaded_file = st.file_uploader("Upload crew schedule CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    st.info("No file uploaded yet. Using sample data.")
    df = pd.DataFrame({
        "Pilot": ["John", "Sarah", "Mike", "Lisa"],
        "Duty Hours": [12, 9, 14, 10],
        "Segments": [4, 3, 5, 2],
        "Time Zones": [2, 1, 3, 0],
        "Rest Hours": [8, 12, 7, 11],
        "Circadian Disruption": ["Yes", "No", "Yes", "No"]
    })

df["Fatigue Score"] = df.apply(
    lambda row: fatigue_risk_score(
        row["Duty Hours"],
        row["Segments"],
        row["Time Zones"],
        row["Rest Hours"],
        to_bool(row["Circadian Disruption"])
    ),
    axis=1
)

df["Why Flagged"] = df.apply(
    lambda row: fatigue_reason(
        row["Duty Hours"],
        row["Segments"],
        row["Time Zones"],
        row["Rest Hours"],
        to_bool(row["Circadian Disruption"])
    ),
    axis=1
)

df["Risk"] = df["Fatigue Score"].apply(risk_level)
df = df.sort_values(by="Fatigue Score", ascending=False).reset_index(drop=True)

st.markdown("### Crew Fatigue Risk Results")
st.dataframe(
    df[["Pilot", "Fatigue Score", "Risk", "Why Flagged"]],
    use_container_width=True
)

high_risk = df[df["Fatigue Score"] >= 60]

st.markdown("### Operational Alerts")
if not high_risk.empty:
    st.warning(f"{len(high_risk)} crew member(s) flagged as HIGH or CRITICAL fatigue risk.")
    st.dataframe(
        high_risk[["Pilot", "Fatigue Score", "Risk", "Why Flagged"]],
        use_container_width=True
    )
else:
    st.success("No crew members currently flagged as HIGH or CRITICAL risk.")

highest = df.iloc[0]
st.markdown("### Highest Risk Crew Member")
st.write(f"**Pilot:** {highest['Pilot']}")
st.write(f"**Fatigue Score:** {highest['Fatigue Score']}")
st.write(f"**Risk Level:** {highest['Risk']}")
st.write(f"**Why Flagged:** {highest['Why Flagged']}")

st.markdown("### Fatigue Risk Heatmap")

heatmap_data = df[["Pilot", "Fatigue Score"]].copy()
heatmap_values = [heatmap_data["Fatigue Score"].tolist()]

fig, ax = plt.subplots(figsize=(10, 2.5))
im = ax.imshow(heatmap_values, aspect="auto")

ax.set_yticks([0])
ax.set_yticklabels(["Fatigue Score"])
ax.set_xticks(range(len(heatmap_data["Pilot"])))
ax.set_xticklabels(heatmap_data["Pilot"], rotation=45, ha="right")

for i, score in enumerate(heatmap_data["Fatigue Score"]):
    ax.text(i, 0, str(score), ha="center", va="center")

plt.colorbar(im, ax=ax)
plt.tight_layout()

st.pyplot(fig)
