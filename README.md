# AeroVigil

**Predictive Fatigue Risk Analytics for Aviation Safety**

AeroVigil is a prototype aviation safety tool designed to estimate **crew fatigue risk** using key operational factors such as duty hours, flight segments, time zone changes, rest periods, and circadian disruption.

This project was built as an early proof-of-concept for a larger vision: helping airlines and aviation safety teams identify fatigue risk **before flights operate**.

---

## Live Demo

👉 **AeroVigil App:**  
https://aerovigil-demo.streamlit.app

---

## Overview

Fatigue remains one of the most critical human factors issues in aviation safety. AeroVigil explores how operational inputs from crew scheduling and duty periods can be converted into a clear **fatigue risk score**.

This prototype allows users to experiment with different operational scenarios and instantly see how fatigue risk changes.

---

## Features

- Calculates a **fatigue risk score** from 0–100
- Uses operational inputs such as:
  - Duty hours
  - Flight segments
  - Time zone changes
  - Rest hours before duty
  - Circadian disruption
- Displays a fatigue **classification level**:
  - LOW
  - MODERATE
  - HIGH
- Provides a **mitigation recommendation**
- Includes a **scenario comparison chart**
- Includes a **4-day fatigue trend / timeline predictor**
- Built with an interactive **Streamlit dashboard**

---

## Why AeroVigil Matters

Airlines, cargo carriers, and corporate flight departments often rely on scheduling rules and compliance-based fatigue management, but fatigue risk is still difficult to visualize in a simple, predictive way.

AeroVigil is an early prototype for a future aviation safety platform that could support:

- Fatigue Risk Management Systems (FRMS)
- Airline safety departments
- Crew scheduling teams
- Safety Management Systems (SMS)
- Human factors research applications

---

## Tech Stack

- **Python**
- **Streamlit**
- **Pandas**
- **Matplotlib**

---

## Project Structure

```bash
AeroVigil/
│
├── app.py
├── fatigue_calculator.py
├── requirements.txt
└── README.md
