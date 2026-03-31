from __future__ import annotations

from pathlib import Path

import xarray as xr


class NetCDFResolutionError(RuntimeError):
    """Raised when required NetCDF variables cannot be resolved."""



def list_netcdf_files(uploaded_paths: list[str] | tuple[str, ...]) -> list[Path]:
    """Return existing uploaded files that look like NetCDF datasets."""
    paths = [Path(path) for path in uploaded_paths or []]
    return [path for path in paths if path.exists() and path.suffix.lower() == ".nc"]



def inspect_netcdf_variables(netcdf_path: str | Path) -> list[str]:
    """Return data variable names available in a NetCDF file."""
    path = Path(netcdf_path)
    try:
        with xr.open_dataset(path) as ds:
            return list(ds.data_vars)
    except Exception as exc:  # pragma: no cover - defensive wrapper
        raise NetCDFResolutionError(f"Failed to inspect '{path.name}': {exc}") from exc



def _find_variable_matches(variable_name: str, netcdf_files: list[Path]) -> list[tuple[Path, str]]:
    matches: list[tuple[Path, str]] = []

    for path in netcdf_files:
        try:
            with xr.open_dataset(path) as ds:
                if variable_name in ds.data_vars:
                    matches.append((path, variable_name))
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise NetCDFResolutionError(f"Failed to inspect '{path.name}': {exc}") from exc

    return matches



def resolve_netcdf_inputs(inputs: dict[str, str], uploaded_paths: list[str] | tuple[str, ...]) -> dict[str, tuple[Path, str]]:
    """Resolve each declared NetCDF input variable against uploaded files.

    Each variable must be found in exactly one uploaded NetCDF file.
    """
    netcdf_files = list_netcdf_files(uploaded_paths)
    if not netcdf_files:
        raise NetCDFResolutionError("No uploaded NetCDF files were found.")

    resolved: dict[str, tuple[Path, str]] = {}

    for variable_name, file_type in inputs.items():
        if file_type != "NetCDF":
            raise NetCDFResolutionError(
                f"Unsupported input type '{file_type}' for variable '%{variable_name}%'."
            )

        matches = _find_variable_matches(variable_name, netcdf_files)

        if not matches:
            raise NetCDFResolutionError(
                f"Variable '%{variable_name}%' was not found in uploaded NetCDF files."
            )

        if len(matches) > 1:
            file_list = ", ".join(path.name for path, _ in matches)
            raise NetCDFResolutionError(
                f"Variable '%{variable_name}%' was found in multiple NetCDF files: {file_list}"
            )

        resolved[variable_name] = matches[0]

    return resolved

def discover_time_values(uploaded_paths: list[str] | tuple[str, ...]) -> list[str]:
    """
    Inspect uploaded NetCDF files and collect unique time values
    from variables that contain a 'time' dimension.

    Returns
    -------
    list[str]
        Sorted unique time values converted to strings.
    """
    netcdf_files = list_netcdf_files(uploaded_paths)
    if not netcdf_files:
        return []

    collected: list[str] = []

    for path in netcdf_files:
        try:
            with xr.open_dataset(path) as ds:
                for var_name in ds.data_vars:
                    da = ds[var_name]

                    if "time" not in da.dims:
                        continue

                    if "time" not in ds.coords:
                        continue

                    time_values = ds["time"].values

                    for value in time_values:
                        try:
                            ts = str(value)
                            if "T" in ts:
                                ts = ts.split("T")[0]
                            collected.append(ts)
                        except Exception:
                            continue

        except Exception:
            continue

    return sorted(set(collected))


def has_time_dimension(uploaded_paths: list[str] | tuple[str, ...]) -> bool:
    """
    Return True if at least one uploaded NetCDF data variable
    contains a 'time' dimension.
    """
    netcdf_files = list_netcdf_files(uploaded_paths)
    if not netcdf_files:
        return False

    for path in netcdf_files:
        try:
            with xr.open_dataset(path) as ds:
                for var_name in ds.data_vars:
                    if "time" in ds[var_name].dims:
                        return True
        except Exception:
            continue

    return False