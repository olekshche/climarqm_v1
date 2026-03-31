from __future__ import annotations

import re
from dataclasses import dataclass


class ProtocolParseError(ValueError):
    """Raised when protocol text cannot be parsed."""


@dataclass(slots=True)
class ProtocolSpec:
    """Structured representation of a parsed protocol."""

    parameters: dict[str, str]
    inputs: dict[str, str]
    rules: list[str]
    raw_text: str


_PARAM_RE = re.compile(
    r"!(?P<name>[A-Za-z_][A-Za-z0-9_]*)!\s*=\s*\"(?P<value>[^\"]*)\"\s*;"
)
_INPUT_RE = re.compile(
    r"%(?P<name>[A-Za-z_][A-Za-z0-9_]*)%\s*=\s*\"(?P<value>[^\"]*)\"\s*;"
)
_RULE_BLOCK_RE = re.compile(r"\[(?P<content>.*?)\]", re.DOTALL)


def parse_protocol(text: str) -> ProtocolSpec:
    """Parse protocol text into parameters, inputs, and rules.

    The current implementation is intentionally narrow and supports a single
    top-level rules block with protocol parameters and input declarations placed
    outside that block.
    """
    if text is None:
        raise ProtocolParseError("Protocol text is missing.")

    raw_text = str(text).strip()
    if not raw_text:
        raise ProtocolParseError("Protocol text is empty.")

    if not raw_text.startswith("{") or not raw_text.endswith("}"):
        raise ProtocolParseError("Protocol must start with '{' and end with '}'.")

    inner = raw_text[1:-1]
    rule_match = _RULE_BLOCK_RE.search(inner)
    if rule_match is None:
        raise ProtocolParseError("Protocol must contain a [ ... ] rules block.")

    if _RULE_BLOCK_RE.search(inner, rule_match.end()):
        raise ProtocolParseError("Only one [ ... ] rules block is supported in v1.")

    outside_rules = inner[: rule_match.start()] + inner[rule_match.end() :]
    rule_block = rule_match.group("content")

    parameters: dict[str, str] = {}
    for match in _PARAM_RE.finditer(outside_rules):
        name = match.group("name")
        if name in parameters:
            raise ProtocolParseError(f"Duplicate protocol parameter '!{name}!' found.")
        parameters[name] = match.group("value")

    inputs: dict[str, str] = {}
    for match in _INPUT_RE.finditer(outside_rules):
        name = match.group("name")
        if name in inputs:
            raise ProtocolParseError(f"Duplicate input variable '%{name}%' found.")
        inputs[name] = match.group("value")

    rules = [line.strip() for line in rule_block.split(";") if line.strip()]

    if not parameters:
        raise ProtocolParseError("No protocol parameters were found.")
    if not inputs:
        raise ProtocolParseError("No input variables were declared.")
    if not rules:
        raise ProtocolParseError("No executable rules were found inside [ ... ].")

    return ProtocolSpec(
        parameters=parameters,
        inputs=inputs,
        rules=rules,
        raw_text=raw_text,
    )
