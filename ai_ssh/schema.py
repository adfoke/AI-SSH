from dataclasses import dataclass
from typing import Literal


class CommandValidationError(ValueError):
    pass


@dataclass
class CommandPayload:
    cmd: str
    risk: Literal["safe", "risky"]


VALID_RISK = {"safe", "risky"}


def parse_command_payload(data: dict) -> CommandPayload:
    if not isinstance(data, dict):
        raise CommandValidationError("AI response is not a JSON object")
    cmd = data.get("cmd")
    risk = data.get("risk")
    if not isinstance(cmd, str) or not cmd.strip():
        raise CommandValidationError("AI response missing cmd")
    if risk not in VALID_RISK:
        raise CommandValidationError("AI response missing or invalid risk")
    return CommandPayload(cmd=cmd.strip(), risk=risk)
