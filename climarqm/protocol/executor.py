from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

from climarqm.io.netcdf_resolver import resolve_netcdf_inputs
from .parser import ProtocolSpec, parse_protocol
from .validator import validate_single_formula_protocol


class ProtocolExecutionError(RuntimeError):
    """Raised when protocol execution fails."""


_INPUT_TOKEN_RE = re.compile(r"%([A-Za-z_][A-Za-z0-9_]*)%")
_TEMP_TOKEN_RE = re.compile(r"@([A-Za-z_][A-Za-z0-9_]*)")



def _global_max(value: xr.DataArray) -> xr.DataArray:
    return value.max(skipna=True)



def _global_min(value: xr.DataArray) -> xr.DataArray:
    return value.min(skipna=True)


_ALLOWED_FUNCTIONS: dict[str, Any] = {
    "abs": np.abs,
    "max": _global_max,
    "min": _global_min,
    "global_max": _global_max,
    "global_min": _global_min,
}



def _select_active_2d_layer(da: xr.DataArray, selected_time: str | None = None) -> xr.DataArray:
    if da.ndim == 2:
        return da

    if da.ndim == 3 and "time" in da.dims:
        if selected_time is None:
            raise ProtocolExecutionError(
                f"Variable '{da.name}' requires a selected_time because it has a time dimension."
            )
        try:
            return da.sel(time=selected_time)
        except Exception as exc:
            raise ProtocolExecutionError(
                f"Failed to select time '{selected_time}' for variable '{da.name}': {exc}"
            ) from exc

    raise ProtocolExecutionError(
        f"Variable '{da.name}' must be 2D or 3D with a 'time' dimension; got dims={da.dims}."
    )



def _load_inputs(
    resolved_inputs: dict[str, tuple[Path, str]],
    selected_time: str | None = None,
) -> tuple[dict[str, xr.DataArray], list[xr.Dataset]]:
    loaded: dict[str, xr.DataArray] = {}
    opened_datasets: list[xr.Dataset] = []

    for protocol_name, (path, dataset_var_name) in resolved_inputs.items():
        try:
            ds = xr.open_dataset(path)
        except Exception as exc:
            raise ProtocolExecutionError(f"Failed to open '{path.name}': {exc}") from exc

        opened_datasets.append(ds)

        if dataset_var_name not in ds.data_vars:
            raise ProtocolExecutionError(
                f"Variable '{dataset_var_name}' is no longer available in '{path.name}'."
            )

        da = ds[dataset_var_name]
        loaded[protocol_name] = _select_active_2d_layer(da, selected_time=selected_time)

    return loaded, opened_datasets



def _validate_strict_match(inputs: dict[str, xr.DataArray]) -> None:
    names = list(inputs)
    if not names:
        raise ProtocolExecutionError("No input arrays are available for validation.")

    reference = inputs[names[0]]

    for name in names[1:]:
        current = inputs[name]

        if tuple(current.shape) != tuple(reference.shape):
            raise ProtocolExecutionError(
                f"Shape mismatch for '%{name}%': {current.shape} vs {reference.shape}."
            )

        if tuple(current.dims) != tuple(reference.dims):
            raise ProtocolExecutionError(
                f"Dimension mismatch for '%{name}%': {current.dims} vs {reference.dims}."
            )

        for dim in reference.dims:
            if dim in reference.coords and dim in current.coords:
                ref_coord = reference.coords[dim].values
                cur_coord = current.coords[dim].values
                if ref_coord.shape != cur_coord.shape or not np.array_equal(ref_coord, cur_coord):
                    raise ProtocolExecutionError(
                        f"Coordinate mismatch in dimension '{dim}' for '%{name}%'."
                    )



def _compile_expression(expression: str) -> str:
    expression = _INPUT_TOKEN_RE.sub(r'inputs["\1"]', expression)
    expression = _TEMP_TOKEN_RE.sub(r'temps["\1"]', expression)
    return expression



def _evaluate_rule(rule: str, inputs: dict[str, xr.DataArray], temps: dict[str, Any]) -> tuple[str, xr.DataArray]:
    if "=" not in rule:
        raise ProtocolExecutionError("The rule must contain '='.")

    lhs, rhs = [part.strip() for part in rule.split("=", 1)]
    if not lhs.startswith("@"):
        raise ProtocolExecutionError("The left-hand side of the rule must be an @variable.")

    output_name = lhs[1:]
    compiled_rhs = _compile_expression(rhs)

    safe_globals = {"__builtins__": {}}
    safe_locals = {
        "inputs": inputs,
        "temps": temps,
        **_ALLOWED_FUNCTIONS,
    }

    try:
        value = eval(compiled_rhs, safe_globals, safe_locals)
    except Exception as exc:
        raise ProtocolExecutionError(f"Failed to evaluate rule '{rule}': {exc}") from exc

    if not isinstance(value, xr.DataArray):
        raise ProtocolExecutionError(
            f"The evaluated rule must produce an xarray.DataArray, got {type(value).__name__}."
        )

    value.name = output_name
    return output_name, value



def execute_single_formula_protocol(
    protocol_text: str,
    uploaded_paths: list[str] | tuple[str, ...],
    selected_time: str | None = None,
) -> dict[str, Any]:
    """Parse, validate, resolve, and execute a single-formula protocol.

    Returns a small execution bundle containing the parsed protocol, the
    resolved input mapping, active 2D input arrays, and the final result.
    """
    spec: ProtocolSpec = parse_protocol(protocol_text)
    validate_single_formula_protocol(spec)

    resolved_inputs = resolve_netcdf_inputs(spec.inputs, uploaded_paths)
    loaded_inputs, opened_datasets = _load_inputs(
        resolved_inputs,
        selected_time=selected_time,
    )

    try:
        if spec.parameters.get("grid_policy") == "strict_match":
            _validate_strict_match(loaded_inputs)

        temps: dict[str, Any] = {}
        output_name, output_value = _evaluate_rule(
            spec.rules[0],
            inputs=loaded_inputs,
            temps=temps,
        )
        temps[output_name] = output_value

        declared_output = spec.parameters["output"].lstrip("@")
        if declared_output not in temps:
            raise ProtocolExecutionError(
                f"Declared output '@{declared_output}' was not produced during execution."
            )

        result = temps[declared_output]
        result.attrs.update(
            {
                "protocoltype": spec.parameters.get("protocoltype", ""),
                "grid_policy": spec.parameters.get("grid_policy", ""),
                "output_format": spec.parameters.get("output_format", ""),
                "selected_time": selected_time or "",
                "formula": spec.rules[0],
            }
        )

        return {
            "spec": spec,
            "resolved_inputs": resolved_inputs,
            "inputs": loaded_inputs,
            "result": result,
        }
    finally:
        for ds in opened_datasets:
            ds.close()
