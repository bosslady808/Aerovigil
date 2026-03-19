# AeroVigil – Operations Risk Console

AeroVigil is a predictive aviation decision-support prototype designed to help airline operations teams evaluate crew options during disruptions (IROPs).

It combines:
- Fatigue risk indicators
- Legal compliance awareness
- Scenario comparison
- Multi-flight disruption simulation

**Live Demo:** https://aerovigil-demo.streamlit.app

---

## Problem

Airline operations today rely heavily on:
- Legal compliance (rest rules)
- Availability

But often lack:
- Predictive fatigue awareness
- Proactive decision support during disruptions

This creates a gap between **“legal to operate”** and **“safe to operate.”**

---

## Solution

AeroVigil introduces a unified decision view that helps operations teams:
- Evaluate fatigue risk across crews
- Compare multiple scheduling scenarios
- Simulate IROPs situations
- Identify higher-risk crew assignments early

---

## Key Features

### Operations Risk Console
- Central dashboard for fatigue risk monitoring
- Alert-based decision support
- Risk visibility for operational choices

### IROPs Mode
- Simulates disruption scenarios
- Evaluates operational impact of crew fatigue
- Supports fast decision-making under pressure

### Multi-Flight Disruption Simulator
- Models multiple flights competing for limited reserve crews
- Highlights operational risk when resources are constrained
- Helps visualize reserve allocation pressure

### Case Simulator
- Allows users to test individual disruption and crew risk scenarios
- Demonstrates how different conditions affect fatigue indicators

### Scenario Comparison Tool
- Compare Plan A vs Plan B crew assignments
- Supports structured decision-making for operations teams

### Executive Snapshot
- High-level KPI view for leadership visibility
- Risk trends and operational overview

---

## Tech Stack

- Python
- Streamlit
- Pandas

---

## Current Limitations (Prototype Status)

- Fatigue model is simplified and not FAA-certified
- Uses simulated and hard-coded data rather than live airline data
- Fatigue timeline generation includes randomized demo behavior
- No automated test suite is currently implemented

---

## Known Issues

- Reserve allocation logic in the multi-flight simulator needs refinement
- Fatigue scoring logic exists in more than one place and should be unified
- Data pipeline is not yet connected to bundled CSV or external data sources

---

## Future Development

- Unified fatigue model across all modules
- Data-driven inputs from CSV or APIs
- Expanded IROPs decision engine
- Crew reassignment recommendations
- Real-time operational dashboards
- Improved consistency between simulation and scoring logic

---

## Vision

AeroVigil aims to become an operational decision-support tool that bridges the gap between legality, availability, and real-world fatigue risk in airline operations.

---

## Founder

**Bosslady Fifita**  
Founder, AeroVigil  
Aviation Operations • Human Factors • Safety Systems