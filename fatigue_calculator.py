# fatigue_calculator.py

def fatigue_risk_score(duty_hours, segments, timezone_changes, rest_hours, circadian_disruption):
    """
    Calculate a simple fatigue risk score from 0 to 100.

    Inputs:
    - duty_hours (float): total duty period length
    - segments (int): number of flight segments
    - timezone_changes (int): number of time zones crossed
    - rest_hours (float): hours of rest before duty
    - circadian_disruption (bool): True if duty overlaps normal sleep window
    """

    score = 0

    # Duty length factor
    if duty_hours > 10:
        score += (duty_hours - 10) * 5

    # Flight segments factor
    score += segments * 3

    # Time zone crossing factor
    score += timezone_changes * 4

    # Rest penalty
    if rest_hours < 10:
        score += (10 - rest_hours) * 6

    # Circadian disruption factor
    if circadian_disruption:
        score += 15

    # Cap final score at 100
    return min(score, 100)


if __name__ == "__main__":
    # Example test case
    duty_hours = 12
    segments = 4
    timezone_changes = 2
    rest_hours = 8
    circadian_disruption = True

    risk = fatigue_risk_score(
        duty_hours,
        segments,
        timezone_changes,
        rest_hours,
        circadian_disruption
    )

    print(f"Fatigue Risk Score: {risk}/100")
