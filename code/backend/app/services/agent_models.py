"""Static configuration of available models per agent adapter."""

AGENT_MODELS: dict[str, list[dict[str, str]]] = {
    "claude": [
        {"id": "claude-sonnet-4-6", "label": "Claude Sonnet 4"},
        {"id": "claude-opus-4-6", "label": "Claude Opus 4"},
        {"id": "claude-haiku-4-5-20251001", "label": "Claude Haiku 4"},
    ],
    "codex": [
        {"id": "gpt-5.4", "label": "GPT 5.4"},
        {"id": "gpt-5.4-mini", "label": "GPT 5.4 Mini"},
        {"id": "gpt-5.3-codex", "label": "GPT 5.3 Codex"},
    ],
    "opencode": [
        {"id": "default", "label": "Default"},
    ],
}
