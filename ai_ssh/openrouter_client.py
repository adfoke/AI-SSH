import json
from json import JSONDecodeError
from typing import Dict

import requests

from .config import OPENROUTER_API_KEY
from .utils import redact_sensitive

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-3-flash-preview"

SYSTEM_PROMPT = (
    "You are a Linux Expert. Output only a JSON object with keys: cmd, risk. "
    "cmd must be a safe shell command string. risk must be one of: safe, risky. "
    "Do not include any extra text."
)


def generate_command(user_input: str, server_alias: str) -> Dict[str, str]:
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    sanitized_input = redact_sensitive(user_input, server_alias)
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Target: {server_alias}. Task: {sanitized_input}",
            },
        ],
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except JSONDecodeError as exc:
        raise ValueError("AI response is not valid JSON") from exc


def select_target_alias(user_input: str, aliases: list[str]) -> str:
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    sanitized_input = redact_sensitive(user_input, "HOST_ALIAS")
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Linux assistant. Choose the best matching host alias from the list. "
                    "Output JSON only: {\"alias\": \"...\"}. If unsure, return empty alias."
                ),
            },
            {
                "role": "user",
                "content": f"Aliases: {aliases}. Task: {sanitized_input}",
            },
        ],
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    try:
        data = json.loads(content)
    except JSONDecodeError as exc:
        raise ValueError("AI response is not valid JSON") from exc
    alias = data.get("alias") if isinstance(data, dict) else None
    return alias or ""
