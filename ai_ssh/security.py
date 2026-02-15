RISKY_KEYWORDS = {
    "rm ",
    "kill",
    "shutdown",
    "reboot",
    "docker stop",
    "systemctl stop",
}


def classify_command(cmd: str, ai_risk: str) -> str:
    lowered = cmd.lower()
    if any(keyword in lowered for keyword in RISKY_KEYWORDS):
        return "risky"
    if ai_risk not in {"safe", "risky"}:
        return "risky"
    return ai_risk
