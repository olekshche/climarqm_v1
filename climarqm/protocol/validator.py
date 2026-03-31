from __future__ import annotations

import re

from .parser import ProtocolSpec


class ProtocolValidationError(ValueError):
    """Raised when a parsed protocol violates current v1 rules."""


_INPUT_TOKEN_RE = re.compile(r"%([A-Za-z_][A-Za-z0-9_]*)%")
_OUTPUT_TOKEN_RE = re.compile(r"@([A-Za-z_][A-Za-z0-9_]*)")

_ALLOWED_PROTOCOL_TYPES = {"single_formula_calculation"}
_ALLOWED_GRID_POLICIES = {"strict_match"}
_ALLOWED_OUTPUT_FORMATS = {"PNG", "GeoJSON"}
_ALLOWED_INPUT_TYPES = {"NetCDF"}



def validate_single_formula_protocol(spec: ProtocolSpec) -> None:
    """Validate a protocol against the current narrow v1 contract."""
    protocol_type = spec.parameters.get("protocoltype")
    if protocol_type not in _ALLOWED_PROTOCOL_TYPES:
        raise ProtocolValidationError(
            "Unsupported !protocoltype! value. Supported values: "
            f"{sorted(_ALLOWED_PROTOCOL_TYPES)}"
        )

    grid_policy = spec.parameters.get("grid_policy")
    if grid_policy not in _ALLOWED_GRID_POLICIES:
        raise ProtocolValidationError(
            "Unsupported !grid_policy! value for v1. Supported values: "
            f"{sorted(_ALLOWED_GRID_POLICIES)}"
        )

    output_name = spec.parameters.get("output")
    if output_name is None:
        raise ProtocolValidationError("Missing required !output! parameter.")
    if not output_name.startswith("@"):
        raise ProtocolValidationError("!output! must reference an @variable.")

    output_format = spec.parameters.get("output_format")
    if output_format is None:
        raise ProtocolValidationError("Missing required !output_format! parameter.")
    if output_format not in _ALLOWED_OUTPUT_FORMATS:
        raise ProtocolValidationError(
            "Unsupported !output_format! value. Supported values: "
            f"{sorted(_ALLOWED_OUTPUT_FORMATS)}"
        )

    if len(spec.rules) != 1:
        raise ProtocolValidationError(
            "single_formula_calculation supports exactly one rule in v1."
        )

    for var_name, file_type in spec.inputs.items():
        if file_type not in _ALLOWED_INPUT_TYPES:
            raise ProtocolValidationError(
                f"Unsupported input type for %{var_name}%: {file_type}. "
                f"Supported values: {sorted(_ALLOWED_INPUT_TYPES)}"
            )

    rule = spec.rules[0]
    if "=" not in rule:
        raise ProtocolValidationError("The rule must contain '='.")

    lhs, rhs = [part.strip() for part in rule.split("=", 1)]
    if not lhs.startswith("@"):
        raise ProtocolValidationError(
            "The left-hand side of the rule must be an @variable."
        )

    declared_output = output_name[1:]
    produced_output = lhs[1:]
    if produced_output != declared_output:
        raise ProtocolValidationError(
            f"!output! points to '@{declared_output}', but the rule assigns '@{produced_output}'."
        )

    used_inputs = set(_INPUT_TOKEN_RE.findall(rhs))
    undeclared_inputs = sorted(used_inputs.difference(spec.inputs))
    if undeclared_inputs:
        raise ProtocolValidationError(
            "The rule references undeclared input variables: "
            + ", ".join(f"%{name}%" for name in undeclared_inputs)
        )

    produced_temps = {produced_output}
    used_temps = set(_OUTPUT_TOKEN_RE.findall(rhs))
    unknown_temps = sorted(used_temps.difference(produced_temps))
    if unknown_temps:
        raise ProtocolValidationError(
            "The rule references @variables that are not produced earlier in the protocol: "
            + ", ".join(f"@{name}" for name in unknown_temps)
        )
