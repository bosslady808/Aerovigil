# AeroVigil

AeroVigil is a Streamlit prototype for aviation fatigue and disruption risk analysis.

It helps operations teams inspect crew fatigue, legality checks, reserve availability, and recovery options in a single dashboard. The current implementation is intentionally transparent: the scoring rules are simple, readable, and easy to adapt.

## Current Status

- Prototype
- Demo-oriented
- Heuristic scoring, not certified fatigue management
- No automated test suite yet
- Uses sample cases defined in `app.py`

## What the App Does

The dashboard can:

- Score fatigue on a 0 to 100 scale
- Classify risk as `LOW`, `MODERATE`, or `HIGH`
- Flag basic legality concerns using rest and duty thresholds
- Estimate fatigue call probability
- Rank operational priority for active cases
- Simulate IROPs recovery choices
- Compare Plan A vs Plan B
- Summarize network-level disruption impact
- Show an executive snapshot for leadership review

## Screenshots

### Executive Dashboard
![Executive Dashboard](aerovigil_1.png)

### IROPs Impact Analysis
![IROPs Impact Analysis](aerovigil_2.png)

### Plan A vs Plan B Simulator
![Plan A vs Plan B Simulator](aerovigil_3.png)

### Crew Risk Table
![Crew Risk Table](aerovigil_4.png)

### Recommendation Engine
![Recommendation Engine](aerovigil_5.png)

## App Views

| View | Purpose |
| --- | --- |
| Operations Console | Review sample cases, risk queues, and action guidance |
| IROPs Mode | Compare crew recovery options during a disruption |
| Multi-Flight Disruption Simulator | Rank flights by urgency and reserve allocation need |
| Case Simulator | Test one crew scenario and inspect the output |
| Scenario Comparison | Compare two plans side by side |
| Executive Snapshot | Review a leadership summary of current risk posture |

## How It Works

AeroVigil combines operational inputs into a weighted heuristic model.

Inputs used in the current app:

- Duty hours
- Flight segments
- Time zone changes
- Rest hours before duty
- Circadian disruption
- Departure delay
- Reserve availability

The app then derives:

- Fatigue score
- Risk level
- Legality status
- Fatigue call probability
- Operational priority
- Mitigation recommendation

## Repository Layout

```bash
AeroVigil/
âââ app.py
âââ fatigue_calculator.py
âââ crew_data
âââ requirements.txt
âââ README.md
âââ LICENSE
âââ aerovigil_*.png
```

## Key Files

- `app.py` contains the Streamlit UI and the current business logic
- `fatigue_calculator.py` contains a standalone fatigue scoring helper
- `crew_data` is a small sample CSV-like dataset bundled with the repo
- `requirements.txt` lists the Python dependencies

## Quick Start

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

If Streamlit opens the browser automatically, you are ready to explore the dashboard.

## Requirements

- Python 3.10 or newer is recommended
- Streamlit
- Pandas
- Matplotlib

Install them with:

```bash
pip install -r requirements.txt
```

## Data Notes

- The main dashboard currently uses in-memory sample cases defined in `app.py`
- The repo also includes a small `crew_data` sample file for reference
- The timeline chart is intentionally simulated, so it may vary between runs

## Limitations

AeroVigil is a prototype and should not be treated as a certified fatigue management system.

Known limitations:

- No automated tests are included yet
- No live airline scheduling integration is present
- The scoring model is heuristic rather than regulatory or medically validated
- The timeline forecast is randomized for demo purposes

## Development Notes

- The app currently defines the scoring and recommendation logic inline
- A useful next step is to move shared business rules into one module
- Another good next step is to add unit tests for score, legality, and recommendation behavior

## Suggested Next Steps

1. Replace the sample data with a real CSV import path
2. Consolidate scoring logic into a shared module
3. Add unit tests for core decision rules
4. Make the timeline projection deterministic
5. Add export support for reports or case summaries

## Disclaimer

AeroVigil is intended for educational, research, and demonstration purposes only.

It is not a substitute for certified aviation fatigue management systems, regulatory compliance tools, or operational decision-making processes used by airlines or aviation authorities.

## License

MIT License. See [LICENSE](LICENSE) for details.