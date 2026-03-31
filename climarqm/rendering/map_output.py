from __future__ import annotations

import base64
from pathlib import Path

import folium
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from climarqm.config.paths import OUTPUTS_DIR


class MapRenderError(Exception):
    pass


def _get_lat_lon_names(da: xr.DataArray) -> tuple[str, str]:
    lat_candidates = ("latitude", "lat", "y")
    lon_candidates = ("longitude", "lon", "x")

    lat_name = None
    lon_name = None

    for name in da.coords:
        if name in lat_candidates:
            lat_name = name
            break

    for name in da.coords:
        if name in lon_candidates:
            lon_name = name
            break

    if lat_name is None or lon_name is None:
        raise MapRenderError(
            f"Could not determine latitude/longitude coordinates for '{da.name}'. "
            f"Available coords: {list(da.coords)}"
        )

    return lat_name, lon_name


def _normalize_array(values: np.ndarray) -> tuple[np.ndarray, float, float]:
    finite_mask = np.isfinite(values)
    if not finite_mask.any():
        raise MapRenderError("Result contains no finite values.")

    vmin = float(np.nanmin(values))
    vmax = float(np.nanmax(values))

    if np.isclose(vmin, vmax):
        norm = np.zeros_like(values, dtype=float)
    else:
        norm = (values - vmin) / (vmax - vmin)

    norm[~finite_mask] = np.nan
    return norm, vmin, vmax


def render_dataarray_to_png(
    da: xr.DataArray,
    output_name: str | None = None,
    cmap_name: str = "YlOrBr",
) -> dict:
    """
    Render a 2D DataArray to a PNG image and prepare overlay metadata for folium.

    Returns
    -------
    dict
        {
            "png_path": str,
            "image_data_uri": str,
            "bounds": [[lat_min, lon_min], [lat_max, lon_max]],
            "center": [lat_center, lon_center],
            "vmin": float,
            "vmax": float,
        }
    """
    if da.ndim != 2:
        raise MapRenderError(
            f"Expected a 2D DataArray for rendering, got ndim={da.ndim}"
        )

    lat_name, lon_name = _get_lat_lon_names(da)

    values = da.values.astype(float)
    norm, vmin, vmax = _normalize_array(values)

    cmap = plt.get_cmap(cmap_name)
    rgba = cmap(np.nan_to_num(norm, nan=0.0))
    rgba[..., 3] = np.where(np.isfinite(norm), 1.0, 0.0)

    output_dir = Path(OUTPUTS_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = output_name or da.name or "result"
    safe_name = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in safe_name)
    png_path = output_dir / f"{safe_name}.png"

    plt.imsave(png_path, rgba)

    image_bytes = png_path.read_bytes()
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    image_data_uri = f"data:image/png;base64,{image_b64}"

    lat_values = np.asarray(da[lat_name].values, dtype=float)
    lon_values = np.asarray(da[lon_name].values, dtype=float)

    lat_min = float(np.nanmin(lat_values))
    lat_max = float(np.nanmax(lat_values))
    lon_min = float(np.nanmin(lon_values))
    lon_max = float(np.nanmax(lon_values))

    bounds = [[lat_min, lon_min], [lat_max, lon_max]]
    center = [(lat_min + lat_max) / 2.0, (lon_min + lon_max) / 2.0]

    return {
        "png_path": str(png_path),
        "image_data_uri": image_data_uri,
        "bounds": bounds,
        "center": center,
        "vmin": vmin,
        "vmax": vmax,
    }


def build_result_map(
    image_data_uri: str,
    bounds: list,
    center: list | None = None,
    zoom_start: int = 6,
    layer_name: str = "Protocol result",
) -> folium.Map:
    """
    Create a folium map with the rendered PNG overlay.
    """
    if center is None:
        center = [
            (bounds[0][0] + bounds[1][0]) / 2.0,
            (bounds[0][1] + bounds[1][1]) / 2.0,
        ]

    fmap = folium.Map(
        location=center,
        zoom_start=zoom_start,
        control_scale=True,
        tiles="OpenStreetMap",
    )

    folium.raster_layers.ImageOverlay(
        image=image_data_uri,
        bounds=bounds,
        name=layer_name,
        opacity=0.75,
        interactive=True,
        cross_origin=False,
    ).add_to(fmap)

    folium.LayerControl().add_to(fmap)
    return fmap