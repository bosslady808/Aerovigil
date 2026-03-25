from datetime import datetime, timedelta
from typing import List, Dict, Tuple

import pandas as pd
import streamlit as st


# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="AeroVigil V6 — Operational Decision Console",
    page_icon="✈️",
    layout="wide"
)


# ---------------------------------------------------
# HELPERS (CORE LOGIC PRESERVED / EXTENDED LIGHTLY)
# ---------------------------------------------------
def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def calculate_fatigue_score(
    duty_hours: float,
    segments: int,
    timezone_changes: int,
    rest_hours: float,
    circadian_disruption: bool,
    delay_hours: float,
    delay_type: str
) -> Tuple[float, str]:
    """
    Returns fatigue score (0-100) and risk level.
    """
    score = 0.0

    # Base fatigue components
    score += duty_hours * 3.5
    score += segments * 5.0
    score += timezone_changes * 4.0
    score += max(0, 10 - rest_hours) * 4.5

    if circadian_disruption:
        score += 15

    # Delay effect
    score += delay_hours * 5.0

    # Delay type effect
    delay_type_weights = {
        "Mechanical": 8,
        "Weather": 6,
        "ATC": 5,
        "Crew": 7,
        "Security": 4,
        "Other": 3
    }
    score += delay_type_weights.get(delay_type, 3)

    score = clamp(score, 0, 100)

    if score < 35:
        risk = "LOW"
    elif score < 70:
        risk = "MODERATE"
    else:
        risk = "HIGH"

    return round(score, 1), risk


def calculate_legality(
    duty_hours: float,
    rest_hours: float,
    segments: int,
    delay_hours: float
) -> Tuple[bool, List[str]]:
    """
    Simplified legality check for operational demonstration.
    """
    reasons = []
    projected_duty = duty_hours + delay_hours

    if projected_duty > 14:
        reasons.append("Projected duty exceeds 14 hours")

    if rest_hours < 10:
        reasons.append("Rest below 10 hours")

    if segments > 6:
        reasons.append("High segment count may increase operational strain")

    legal = len([r for r in reasons if "exceeds 14 hours" in r or "Rest below 10 hours" in r]) == 0
    return legal, reasons


def generate_recommendation(
    fatigue_score: float,
    risk_level: str,
    legal_ok: bool,
    delay_type: str,
    delay_hours: float,
    reserve_available: bool,
    maintenance_hold: bool
) -> str:
    """
    Recommendation engine.
    """
    if maintenance_hold and delay_type == "Mechanical":
        return "HOLD AIRCRAFT / COORDINATE WITH MAINTENANCE before crew reassignment."

    if not legal_ok:
        if reserve_available:
            return "SWAP CREW - current crew projected illegal."
        return "DELAY OR CANCEL - current crew projected illegal and no reserve available."

    if risk_level == "HIGH":
        if reserve_available:
            return "CONSIDER CREW SWAP - crew legal but fatigue risk is HIGH."
        return "DELAY WITH MITIGATION - crew legal but fatigue risk HIGH; no reserve available."

    if risk_level == "MODERATE":
        if delay_hours >= 3:
            return "MONITOR CLOSELY - moderate fatigue risk with extended disruption."
        return "PROCEED WITH CAUTION - moderate fatigue risk."

    return "PROCEED - crew legal and fatigue risk acceptable."


def disruption_priority(
    fatigue_score: float,
    legal_ok: bool,
    delay_hours: float,
    reserve_available: bool
) -> str:
    if not legal_ok and not reserve_available:
        return "CRITICAL"
    if not legal_ok:
        return "HIGH"
    if fatigue_score >= 70:
        return "HIGH"
    if fatigue_score >= 35 or delay_hours >= 2:
        return "MEDIUM"
    return "LOW"


def build_alert_tags(
    fatigue_score: float,
    risk_level: str,
    legal_ok: bool,
    reserve_available: bool,
    delay_type: str,
    maintenance_hold: bool,
    delay_hours: float
) -> List[str]:
    tags = []

    if fatigue_score >= 70:
        tags.append("HIGH FATIGUE RISK")
    if not legal_ok:
        tags.append("ILLEGAL RISK")
    if not reserve_available:
        tags.append("NO RESERVE AVAILABLE")
    if delay_type == "Mechanical" and (risk_level == "HIGH" or maintenance_hold):
        tags.append("MECHANICAL + FATIGUE COMPOUND")
    if delay_hours >= 3:
        tags.append("EXTENDED DISRUPTION")
    if delay_type == "Crew":
        tags.append("CREW RECOVERY PRESSURE")

    return tags


def build_decision_basis(
    fatigue_score: float,
    risk_level: str,
    legal_ok: bool,
    reserve_available: bool,
    delay_hours: float,
    delay_type: str,
    maintenance_hold: bool,
    reasons: List[str]
) -> List[str]:
    basis = []

    if fatigue_score >= 70:
        basis.append("Fatigue score is in HIGH risk range.")
    elif fatigue_score >= 35:
        basis.append("Fatigue score is in MODERATE risk range.")
    else:
        basis.append("Fatigue score remains in acceptable range.")

    if not legal_ok:
        basis.append("Legality check failed based on projected duty and/or rest.")
    else:
        basis.append("Crew remains legal under current demonstration thresholds.")

    if reserve_available:
        basis.append("Reserve coverage is available.")
    else:
        basis.append("No reserve coverage available.")

    if delay_hours >= 3:
        basis.append(f"Extended disruption active ({delay_hours} hours).")

    if delay_type:
        basis.append(f"Primary disruption type: {delay_type}.")

    if maintenance_hold:
        basis.append("Maintenance hold is active.")

    basis.extend(reasons)
    return basis


def build_case_row(
    flight_id: str,
    delay_type: str,
    delay_hours: float,
    duty_hours: float,
    segments: int,
    timezone_changes: int,
    rest_hours: float,
    circadian_disruption: bool,
    reserve_available: bool,
    maintenance_hold: bool,
    original_departure: datetime | None = None
) -> Dict:
    fatigue_score, risk_level = calculate_fatigue_score(
        duty_hours=duty_hours,
        segments=segments,
        timezone_changes=timezone_changes,
        rest_hours=rest_hours,
        circadian_disruption=circadian_disruption,
        delay_hours=delay_hours,
        delay_type=delay_type
    )

    legal_ok, reasons = calculate_legality(
        duty_hours=duty_hours,
        rest_hours=rest_hours,
        segments=segments,
        delay_hours=delay_hours
    )

    recommendation = generate_recommendation(
        fatigue_score=fatigue_score,
        risk_level=risk_level,
        legal_ok=legal_ok,
        delay_type=delay_type,
        delay_hours=delay_hours,
        reserve_available=reserve_available,
        maintenance_hold=maintenance_hold
    )

    priority = disruption_priority(
        fatigue_score=fatigue_score,
        legal_ok=legal_ok,
        delay_hours=delay_hours,
        reserve_available=reserve_available
    )

    tags = build_alert_tags(
        fatigue_score=fatigue_score,
        risk_level=risk_level,
        legal_ok=legal_ok,
        reserve_available=reserve_available,
        delay_type=delay_type,
        maintenance_hold=maintenance_hold,
        delay_hours=delay_hours
    )

    decision_basis = build_decision_basis(
        fatigue_score=fatigue_score,
        risk_level=risk_level,
        legal_ok=legal_ok,
        reserve_available=reserve_available,
        delay_hours=delay_hours,
        delay_type=delay_type,
        maintenance_hold=maintenance_hold,
        reasons=reasons
    )

    if original_departure is None:
        base_hour = 6 + (abs(hash(flight_id)) % 14)
        original_departure = datetime.now().replace(hour=base_hour, minute=0, second=0, microsecond=0)

    delay_start = original_departure - timedelta(minutes=45)
    projected_departure = original_departure + timedelta(hours=delay_hours)
    projected_duty_end = projected_departure + timedelta(hours=max(1.0, 2.5 + segments * 1.2))
    required_rest_ready = projected_duty_end + timedelta(hours=max(10.0, rest_hours))

    return {
        "Flight": flight_id,
        "Delay Type": delay_type,
        "Delay Hrs": delay_hours,
        "Duty Hrs": duty_hours,
        "Segments": segments,
        "TZ Changes": timezone_changes,
        "Rest Hrs": rest_hours,
        "Circadian": "Yes" if circadian_disruption else "No",
        "Reserve": "Yes" if reserve_available else "No",
        "Maintenance Hold": "Yes" if maintenance_hold else "No",
        "Legal": "Yes" if legal_ok else "No",
        "Fatigue Score": fatigue_score,
        "Risk": risk_level,
        "Priority": priority,
        "Recommendation": recommendation,
        "Reason Notes": "; ".join(reasons) if reasons else "No major legal flags",
        "Decision Basis": decision_basis,
        "Alert Tags": tags,
        "Original Departure": original_departure,
        "Delay Start": delay_start,
        "Projected Departure": projected_departure,
        "Projected Duty End": projected_duty_end,
        "Required Rest Ready": required_rest_ready,
    }


def make_sample_irrops_data() -> pd.DataFrame:
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    rows = [
        build_case_row("DL104", "Mechanical", 3.5, 10.0, 4, 1, 11.0, True, True, True, now.replace(hour=7)),
        build_case_row("AA221", "Weather", 2.0, 9.0, 5, 0, 10.5, False, False, False, now.replace(hour=9)),
        build_case_row("UA515", "ATC", 1.5, 11.0, 3, 2, 9.5, True, True, False, now.replace(hour=11)),
        build_case_row("WN880", "Crew", 4.0, 12.0, 6, 0, 8.5, False, False, False, now.replace(hour=13)),
        build_case_row("JB390", "Security", 1.0, 7.5, 2, 0, 12.0, False, True, False, now.replace(hour=15)),
    ]
    return pd.DataFrame(rows)


def priority_rank(priority: str) -> int:
    ranks = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    return ranks.get(priority, 99)


def risk_color(risk: str) -> str:
    if risk == "LOW":
        return "#16a34a"
    if risk == "MODERATE":
        return "#f59e0b"
    return "#ef4444"


def badge_html(label: str, bg: str, color: str = "white") -> str:
    return (
        f"<span style='display:inline-block; padding:4px 10px; border-radius:999px; "
        f"background:{bg}; color:{color}; font-size:12px; font-weight:600; margin:2px 6px 2px 0;'>{label}</span>"
    )


def format_dt(value: datetime) -> str:
    return value.strftime("%H:%M")


def operational_impact_text(case: Dict) -> str:
    if case["Legal"] == "No" and case["Reserve"] == "No":
        return "Severe network pressure likely."
    if case["Risk"] == "HIGH":
        return "Elevated downstream disruption risk."
    if case["Delay Hrs"] >= 3:
        return "Moderate operational spillover likely."
    return "Contained operational impact."


def estimate_network_impact(df: pd.DataFrame) -> Dict[str, int | str]:
    high_priority_count = int(df["Priority"].isin(["CRITICAL", "HIGH"]).sum()) if not df.empty else 0
    high_delay_count = int((df["Delay Hrs"] >= 3).sum()) if not df.empty else 0
    no_reserve_count = int((df["Reserve"] == "No").sum()) if not df.empty else 0

    impacted_flights = max(1, high_priority_count * 2 + high_delay_count)
    reserve_pressure = "HIGH" if no_reserve_count >= 2 else "MODERATE" if no_reserve_count == 1 else "LOW"
    disruption_level = "HIGH" if high_priority_count >= 2 else "MODERATE" if high_priority_count == 1 else "LOW"

    return {
        "Impacted Flights": impacted_flights,
        "Reserve Pressure": reserve_pressure,
        "Disruption Level": disruption_level,
        "Downstream Delay Estimate": high_priority_count * 35 + high_delay_count * 20
    }


def scenario_rank(case_dict: Dict) -> float:
    penalty = 0
    if case_dict["Legal"] == "No":
        penalty += 100
    if case_dict["Priority"] == "CRITICAL":
        penalty += 50
    elif case_dict["Priority"] == "HIGH":
        penalty += 25
    return float(case_dict["Fatigue Score"]) + penalty


def simulate_decision_options(case: Dict) -> pd.DataFrame:
    base_delay_hours = float(case["Delay Hrs"])
    base_duty_hours = float(case["Duty Hrs"])
    segments = int(case["Segments"])
    tz_changes = int(case["TZ Changes"])
    rest_hours = float(case["Rest Hrs"])
    circadian = case["Circadian"] == "Yes"
    delay_type = str(case["Delay Type"])
    reserve_available = case["Reserve"] == "Yes"
    maintenance_hold = case["Maintenance Hold"] == "Yes"

    options = []

    # Keep Current Crew
    keep_case = build_case_row(
        "Keep Current Crew",
        delay_type,
        base_delay_hours,
        base_duty_hours,
        segments,
        tz_changes,
        rest_hours,
        circadian,
        reserve_available,
        maintenance_hold
    )
    options.append({
        "Option": "Keep Current Crew",
        "Fatigue Score": keep_case["Fatigue Score"],
        "Risk": keep_case["Risk"],
        "Legal": keep_case["Legal"],
        "Priority": keep_case["Priority"],
        "Operational Impact": operational_impact_text(keep_case),
        "Recommendation": keep_case["Recommendation"],
        "Rank": scenario_rank(keep_case)
    })

    # Assign Reserve
    assign_reserve_case = build_case_row(
        "Assign Reserve",
        delay_type,
        max(0.0, base_delay_hours - 0.5),
        max(0.0, base_duty_hours - 3.0),
        segments,
        tz_changes,
        max(10.0, rest_hours + 1.5),
        False if case["Risk"] == "MODERATE" else circadian,
        True,
        maintenance_hold
    )
    options.append({
        "Option": "Assign Reserve",
        "Fatigue Score": assign_reserve_case["Fatigue Score"],
        "Risk": assign_reserve_case["Risk"],
        "Legal": assign_reserve_case["Legal"],
        "Priority": assign_reserve_case["Priority"],
        "Operational Impact": "Lower crew fatigue risk, uses reserve coverage.",
        "Recommendation": assign_reserve_case["Recommendation"],
        "Rank": scenario_rank(assign_reserve_case)
    })

    # Delay Flight
    delay_case = build_case_row(
        "Delay Flight",
        delay_type,
        base_delay_hours + 1.5,
        base_duty_hours + 1.0,
        segments,
        tz_changes,
        rest_hours,
        circadian,
        reserve_available,
        maintenance_hold
    )
    options.append({
        "Option": "Delay Flight",
        "Fatigue Score": delay_case["Fatigue Score"],
        "Risk": delay_case["Risk"],
        "Legal": delay_case["Legal"],
        "Priority": delay_case["Priority"],
        "Operational Impact": "Reduces immediate decision pressure but increases schedule disruption.",
        "Recommendation": delay_case["Recommendation"],
        "Rank": scenario_rank(delay_case)
    })

    # Swap Crew
    swap_case = build_case_row(
        "Swap Crew",
        delay_type,
        max(0.0, base_delay_hours + 0.25),
        max(0.0, base_duty_hours - 2.5),
        segments,
        max(0, tz_changes - 1),
        max(10.0, rest_hours + 1.0),
        False,
        True,
        maintenance_hold
    )
    options.append({
        "Option": "Swap Crew",
        "Fatigue Score": swap_case["Fatigue Score"],
        "Risk": swap_case["Risk"],
        "Legal": swap_case["Legal"],
        "Priority": swap_case["Priority"],
        "Operational Impact": "Improves legality and fatigue posture; coordination overhead required.",
        "Recommendation": swap_case["Recommendation"],
        "Rank": scenario_rank(swap_case)
    })

    return pd.DataFrame(options).sort_values("Rank", ascending=True).reset_index(drop=True)


# ---------------------------------------------------
# STYLES
# ---------------------------------------------------
st.markdown(
    """
    <style>
        .main-title {
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .subtitle {
            color: #94a3b8;
            margin-bottom: 12px;
        }
        .panel {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 14px;
            padding: 14px;
            background: rgba(255,255,255,0.03);
        }
        .small-label {
            font-size: 12px;
            color: #94a3b8;
        }
        .timeline-step {
            border-left: 4px solid #3b82f6;
            padding: 8px 12px;
            margin: 6px 0;
            background: rgba(59,130,246,0.08);
            border-radius: 8px;
        }
        .decision-box {
            border: 1px solid rgba(16, 185, 129, 0.25);
            background: rgba(16, 185, 129, 0.08);
            border-radius: 12px;
            padding: 12px;
        }
        .alert-row {
            border: 1px solid rgba(148,163,184,0.15);
            border-radius: 12px;
            padding: 10px;
            margin-bottom: 8px;
            background: rgba(15, 23, 42, 0.45);
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------
if "case_statuses" not in st.session_state:
    st.session_state.case_statuses = {}

if "action_logs" not in st.session_state:
    st.session_state.action_logs = {}


# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.header("AeroVigil V6 Controls")
show_demo_data = st.sidebar.toggle("Load sample IROPs cases", value=True)
show_methodology = st.sidebar.toggle("Show scoring methodology", value=False)
executive_view = st.sidebar.toggle("Executive View", value=False)

st.sidebar.markdown("---")
sort_by = st.sidebar.selectbox("Sort Alert Queue By", ["Priority", "Fatigue Score", "Delay Hours"])
filter_risk = st.sidebar.multiselect("Filter Risk", ["LOW", "MODERATE", "HIGH"], default=["LOW", "MODERATE", "HIGH"])
filter_legal = st.sidebar.multiselect("Filter Legal Status", ["Yes", "No"], default=["Yes", "No"])
filter_delay_type = st.sidebar.multiselect(
    "Filter Delay Type",
    ["Mechanical", "Weather", "ATC", "Crew", "Security", "Other"],
    default=["Mechanical", "Weather", "ATC", "Crew", "Security", "Other"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Theme: OCC / Crew Scheduling / Safety Decision Support")
current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
st.sidebar.write(f"**System Time:** {current_time}")


# ---------------------------------------------------
# DATASET
# ---------------------------------------------------
if show_demo_data:
    base_df = make_sample_irrops_data()
else:
    base_df = pd.DataFrame(columns=[
        "Flight", "Delay Type", "Delay Hrs", "Duty Hrs", "Segments", "TZ Changes",
        "Rest Hrs", "Circadian", "Reserve", "Maintenance Hold", "Legal",
        "Fatigue Score", "Risk", "Priority", "Recommendation", "Reason Notes",
        "Decision Basis", "Alert Tags", "Original Departure", "Delay Start",
        "Projected Departure", "Projected Duty End", "Required Rest Ready"
    ])

if not base_df.empty:
    filtered_df = base_df[
        base_df["Risk"].isin(filter_risk)
        & base_df["Legal"].isin(filter_legal)
        & base_df["Delay Type"].isin(filter_delay_type)
    ].copy()

    if sort_by == "Priority":
        filtered_df["Priority Rank"] = filtered_df["Priority"].apply(priority_rank)
        filtered_df = filtered_df.sort_values(["Priority Rank", "Fatigue Score"], ascending=[True, False])
        filtered_df = filtered_df.drop(columns=["Priority Rank"])
    elif sort_by == "Fatigue Score":
        filtered_df = filtered_df.sort_values("Fatigue Score", ascending=False)
    else:
        filtered_df = filtered_df.sort_values("Delay Hrs", ascending=False)
else:
    filtered_df = base_df.copy()


# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.markdown('<div class="main-title">✈️ AeroVigil V6 — Operational Decision Console</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Predictive fatigue, legality, and disruption decision support for airline operations teams.</div>',
    unsafe_allow_html=True
)

# KPI ROW
k1, k2, k3, k4 = st.columns(4)
active_alerts = len(filtered_df)
high_risk_cases = int((filtered_df["Risk"] == "HIGH").sum()) if not filtered_df.empty else 0
avg_fatigue = round(filtered_df["Fatigue Score"].mean(), 1) if not filtered_df.empty else 0.0
network_pct = (
    round(((filtered_df["Priority"].isin(["CRITICAL", "HIGH"])).sum() / max(1, len(filtered_df))) * 100, 0)
    if not filtered_df.empty else 0
)
k1.metric("Active Alerts", active_alerts)
k2.metric("High Risk Cases", high_risk_cases)
k3.metric("Avg Fatigue Score", avg_fatigue)
k4.metric("Network Disruption %", f"{network_pct}%")

st.markdown("---")

# ---------------------------------------------------
# MAIN 3-COLUMN OCC LAYOUT
# ---------------------------------------------------
left_col, center_col, right_col = st.columns([1.45, 2.2, 1.35], gap="large")


# ---------------------------------------------------
# LEFT PANEL — ALERT QUEUE
# ---------------------------------------------------
with left_col:
    st.markdown("### Alert Queue")

    if filtered_df.empty:
        st.info("No active alerts match the current filters.")
        selected_flight = None
    else:
        flight_options = filtered_df["Flight"].tolist()
        selected_flight = st.selectbox("Select Flight", flight_options, index=0)

        st.markdown("#### Queue Snapshot")
        for _, row in filtered_df.iterrows():
            risk_badge = badge_html(row["Risk"], risk_color(row["Risk"]), "white")
            legal_color = "#16a34a" if row["Legal"] == "Yes" else "#ef4444"
            legal_badge = badge_html(f"LEGAL: {row['Legal']}", legal_color, "white")

            highlight = "2px solid #3b82f6" if row["Flight"] == selected_flight else "1px solid rgba(148,163,184,0.15)"
            st.markdown(
                f"""
                <div class="alert-row" style="border:{highlight};">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:700;">{row['Flight']}</div>
                            <div class="small-label">Priority: {row['Priority']} • Duty: {row['Duty Hrs']}h • Delay: {row['Delay Hrs']}h</div>
                        </div>
                        <div>{risk_badge}</div>
                    </div>
                    <div style="margin-top:8px;">{legal_badge}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ---------------------------------------------------
# CENTER PANEL — CASE DETAIL + TIMELINE + DECISION SIMULATOR
# ---------------------------------------------------
with center_col:
    st.markdown("### Case Detail")

    if selected_flight is None:
        st.info("Select a flight from the alert queue.")
        case = None
    else:
        case_row = filtered_df[filtered_df["Flight"] == selected_flight]
        if case_row.empty:
            st.error("Selected case not found.")
            case = None
        else:
            case = case_row.iloc[0].to_dict()

    if case:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Flight", case["Flight"])
        c2.metric("Fatigue Score", case["Fatigue Score"])
        c3.metric("Risk", case["Risk"])
        c4.metric("Legal", case["Legal"])

        # Status tracking
        st.markdown("#### Case Status")
        default_status = st.session_state.case_statuses.get(case["Flight"], "New")
        status = st.selectbox(
            "Workflow Status",
            ["New", "Under Review", "Actioned", "Resolved"],
            index=["New", "Under Review", "Actioned", "Resolved"].index(default_status),
            key=f"status_{case['Flight']}"
        )
        st.session_state.case_statuses[case["Flight"]] = status

        # Tags
        st.markdown("#### Alert Intelligence Tags")
        if case["Alert Tags"]:
            tags_html = "".join([badge_html(tag, "#7c3aed") for tag in case["Alert Tags"]])
            st.markdown(tags_html, unsafe_allow_html=True)
        else:
            st.caption("No alert tags.")

        # Crew summary
        st.markdown("#### Crew Duty Summary")
        s1, s2, s3 = st.columns(3)
        s1.metric("Duty Hours", case["Duty Hrs"])
        s2.metric("Rest Hours", case["Rest Hrs"])
        s3.metric("Segments", case["Segments"])

        st.markdown("#### Circadian + Time Zone Impact")
        t1, t2, t3 = st.columns(3)
        t1.metric("TZ Changes", case["TZ Changes"])
        t2.metric("Circadian", case["Circadian"])
        t3.metric("Delay Type", case["Delay Type"])

        st.markdown("#### Fatigue Visualization")
        st.progress(int(float(case["Fatigue Score"])))
        st.caption(f"Fatigue Score: {case['Fatigue Score']} / 100")

        st.markdown("#### Legal Status + Violations")
        legal_badge_color = "#16a34a" if case["Legal"] == "Yes" else "#ef4444"
        st.markdown(badge_html(f"LEGAL: {case['Legal']}", legal_badge_color), unsafe_allow_html=True)
        st.write(case["Reason Notes"])

        if not executive_view:
            st.markdown("#### Decision Basis")
            for item in case["Decision Basis"]:
                st.write(f"- {item}")

        # Operations timeline
        st.markdown("#### Operations Timeline")
        tl1, tl2 = st.columns(2)
        with tl1:
            st.markdown(
                f"""
                <div class="timeline-step"><b>Original Departure</b><br>{format_dt(case['Original Departure'])}</div>
                <div class="timeline-step"><b>Delay Start</b><br>{format_dt(case['Delay Start'])}</div>
                """,
                unsafe_allow_html=True
            )
        with tl2:
            st.markdown(
                f"""
                <div class="timeline-step"><b>Projected Departure</b><br>{format_dt(case['Projected Departure'])}</div>
                <div class="timeline-step"><b>Projected Duty End</b><br>{format_dt(case['Projected Duty End'])}</div>
                """,
                unsafe_allow_html=True
            )
        st.markdown(
            f"""
            <div class="timeline-step"><b>Rest Requirement Impact / Earliest Ready Time</b><br>{case['Required Rest Ready'].strftime('%Y-%m-%d %H:%M')}</div>
            """,
            unsafe_allow_html=True
        )

        # Decision simulator
        st.markdown("#### Decision Simulator")
        decision_df = simulate_decision_options(case)
        best_option = decision_df.iloc[0]["Option"]
        st.markdown(
            f"""
            <div class="decision-box">
                <b>Best Operational Decision:</b> {best_option}
            </div>
            """,
            unsafe_allow_html=True
        )
        show_df = decision_df[[
            "Option", "Fatigue Score", "Risk", "Legal", "Priority", "Operational Impact"
        ]]
        st.dataframe(show_df, use_container_width=True, hide_index=True)

        if not executive_view:
            st.markdown("#### Full Case Data")
            detail_df = pd.DataFrame([case]).drop(columns=[
                "Decision Basis", "Alert Tags"
            ], errors="ignore").T.rename(columns={0: "Value"})
            st.table(detail_df)


# ---------------------------------------------------
# RIGHT PANEL — ACTION ENGINE + NETWORK IMPACT + ACTION LOG
# ---------------------------------------------------
with right_col:
    st.markdown("### Action Engine")

    if case is None:
        st.info("Select a case to surface actions.")
    else:
        st.markdown("#### Recommended Action")
        st.markdown(f"**{case['Recommendation']}**")

        st.markdown("#### Decision Basis")
        for item in case["Decision Basis"][:4]:
            st.write(f"- {item}")

        st.markdown("#### Action Controls")
        action_message = None

        a1, a2 = st.columns(2)
        if a1.button("Assign Reserve", use_container_width=True):
            action_message = f"{case['Flight']}: Assign Reserve"
        if a2.button("Delay Flight", use_container_width=True):
            action_message = f"{case['Flight']}: Delay Flight"

        a3, a4 = st.columns(2)
        if a3.button("Swap Crew", use_container_width=True):
            action_message = f"{case['Flight']}: Swap Crew"
        if a4.button("Escalate", use_container_width=True):
            action_message = f"{case['Flight']}: Escalate to OCC Lead"

        if action_message:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if case["Flight"] not in st.session_state.action_logs:
                st.session_state.action_logs[case["Flight"]] = []
            st.session_state.action_logs[case["Flight"]].insert(0, f"{ts} — {action_message}")
            st.success(action_message)

        st.markdown("---")
        st.markdown("#### Network Impact")
        impact = estimate_network_impact(filtered_df if not filtered_df.empty else base_df)
        n1, n2 = st.columns(2)
        n1.metric("Impacted Flights", impact["Impacted Flights"])
        n2.metric("Downstream Delay Est.", f"{impact['Downstream Delay Estimate']} min")
        st.markdown(
            badge_html(f"Reserve Pressure: {impact['Reserve Pressure']}", "#0ea5e9")
            + badge_html(f"Disruption Level: {impact['Disruption Level']}", "#f97316"),
            unsafe_allow_html=True
        )

        st.markdown("#### Case History / Action Log")
        flight_logs = st.session_state.action_logs.get(case["Flight"], [])
        if flight_logs:
            for entry in flight_logs[:8]:
                st.write(f"- {entry}")
        else:
            st.caption("No logged actions yet.")


# ---------------------------------------------------
# EXECUTIVE SUMMARY STRIP
# ---------------------------------------------------
st.markdown("---")
st.markdown("### Executive Snapshot")

if filtered_df.empty:
    st.info("No data available for executive summary.")
else:
    exec_col1, exec_col2, exec_col3 = st.columns(3)

    with exec_col1:
        st.markdown("#### Operational Summary")
        st.write(f"- Active alerts in view: **{len(filtered_df)}**")
        st.write(f"- High risk crews: **{int((filtered_df['Risk'] == 'HIGH').sum())}**")
        st.write(f"- Illegal cases: **{int((filtered_df['Legal'] == 'No').sum())}**")

    with exec_col2:
        top_case = filtered_df.sort_values(
            by=["Fatigue Score"], ascending=False
        ).iloc[0]
        st.markdown("#### Highest Concern Case")
        st.write(f"- Flight: **{top_case['Flight']}**")
        st.write(f"- Fatigue Score: **{top_case['Fatigue Score']}**")
        st.write(f"- Recommendation: **{top_case['Recommendation']}**")

    with exec_col3:
        impact = estimate_network_impact(filtered_df)
        st.markdown("#### Network Outlook")
        st.write(f"- Disruption Level: **{impact['Disruption Level']}**")
        st.write(f"- Reserve Pressure: **{impact['Reserve Pressure']}**")
        st.write(f"- Estimated impacted flights: **{impact['Impacted Flights']}**")

# ---------------------------------------------------
# OPTIONAL METHODOLOGY
# ---------------------------------------------------
if show_methodology:
    st.markdown("---")
    st.info(
        """
**Scoring Logic Summary**
- Higher duty hours increase fatigue risk
- More segments increase workload burden
- Time zone changes increase circadian strain
- Lower rest increases fatigue risk
- Circadian disruption adds penalty
- Longer disruptions increase fatigue pressure
- Mechanical / crew-related disruptions add operational stress weighting

**Legality Demonstration Logic**
- Projected duty > 14 hours triggers legal concern
- Rest below 10 hours triggers legal concern
- Segment count > 6 creates operational strain note
"""
    )
