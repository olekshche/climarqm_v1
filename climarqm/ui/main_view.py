from pathlib import Path

import folium
import panel as pn
from folium.plugins import Fullscreen

from climarqm.config.paths import PROTOCOLS_DIR
from climarqm.functions.file_handlers import format_saved_paths_markdown
from climarqm.functions.protocol_manager import (
    list_protocol_names,
    load_protocol_text,
    save_protocol_text,
)
from climarqm.io.netcdf_resolver import discover_time_values
from climarqm.protocol.executor import execute_single_formula_protocol
from climarqm.rendering.map_output import build_result_map, render_dataarray_to_png

pn.extension(sizing_mode="stretch_width")


def _build_map_view():
    fmap = folium.Map(
        location=[48.0, 15.0],
        zoom_start=5,
        control_scale=True,
        tiles="OpenStreetMap",
    )

    Fullscreen(
        position="topright",
        title="Full screen",
        title_cancel="Exit full screen",
        force_separate_button=True,
    ).add_to(fmap)

    folium.LayerControl().add_to(fmap)

    return pn.panel(
        fmap,
        height=700,
        sizing_mode="stretch_width",
    )


def create_app():
    state = {
        "uploaded_paths": [],
    }

    file_selector = pn.widgets.FileSelector(
        str(Path.cwd()),
        only_files=True,
        sizing_mode="stretch_width",
    )

    uploaded_files_info = pn.pane.Markdown(
        "No files selected yet.",
        height=180,
        sizing_mode="stretch_width",
    )


    protocol_select = pn.widgets.Select(
        name="Protocol",
        options=[],
        value=None,
        sizing_mode="stretch_width",
    )

    time_select = pn.widgets.Select(
        name="Time / date",
        options=[],
        value=None,
        disabled=True,
        sizing_mode="stretch_width",
    )

    run_button = pn.widgets.Button(
        name="Run protocol",
        button_type="primary",
        disabled=True,
        sizing_mode="stretch_width",
    )

    run_status = pn.pane.Alert(
        "Upload data files and select a protocol.",
        alert_type="info",
        sizing_mode="stretch_width",
    )

    result_info = pn.pane.Markdown(
        "No calculation result yet.",
        height=160,
        sizing_mode="stretch_width",
    )

    protocol_name_input = pn.widgets.TextInput(
        name="Protocol file name",
        placeholder="example_protocol",
    )

    protocol_text_input = pn.widgets.TextAreaInput(
        name="Protocol text",
        placeholder=(
            "{\n"
            '    !protocoltype! = "single_formula_calculation";\n'
            '    !grid_policy! = "strict_match";\n'
            '    !output! = "@result";\n'
            '    !output_format! = "PNG";\n'
            "\n"
            '    %rr% = "NetCDF";\n'
            '    %elevation% = "NetCDF";\n'
            '    %slope_degrees% = "NetCDF";\n'
            "\n"
            "    [\n"
            "        @result = %rr% * 0.22 * (%elevation% / global_max(%elevation%))\n"
            "                + %rr% * 0.55 * (%slope_degrees% / global_max(%slope_degrees%));\n"
            "    ]\n"
            "}"
        ),
        height=360,
        sizing_mode="stretch_both",
    )

    save_protocol_button = pn.widgets.Button(
        name="Save protocol",
        button_type="primary",
    )

    protocol_status = pn.pane.Alert(
        f"Protocol folder: `{Path(PROTOCOLS_DIR).as_posix()}`",
        alert_type="info",
        sizing_mode="stretch_width",
    )

    saved_protocols_list = pn.pane.Markdown(
        "No saved protocols found.",
        sizing_mode="stretch_width",
    )

    map_pane = _build_map_view()

    def refresh_protocol_list():
        protocol_names = list_protocol_names(PROTOCOLS_DIR)

        protocol_select.options = protocol_names

        if protocol_names:
            if protocol_select.value not in protocol_names:
                protocol_select.value = protocol_names[0]
        else:
            protocol_select.value = None

        if not protocol_names:
            saved_protocols_list.object = "No saved protocols found."
            return

        lines = ["### Saved protocols", ""]
        for filename in protocol_names:
            lines.append(f"- `{filename}`")

        saved_protocols_list.object = "\n".join(lines)

    def update_run_button_state():
        has_files = len(state["uploaded_paths"]) > 0
        has_protocol = protocol_select.value is not None
        run_button.disabled = not (has_files and has_protocol)

    def refresh_time_select():
        time_values = discover_time_values(state["uploaded_paths"])

        if time_values:
            time_select.options = time_values
            time_select.value = time_values[0]
            time_select.disabled = False
        else:
            time_select.options = []
            time_select.value = None
            time_select.disabled = True

    
    def on_files_changed(event):
        selected_paths = list(file_selector.value) if file_selector.value else []
        state["uploaded_paths"] = selected_paths

        if selected_paths:
            uploaded_files_info.object = format_saved_paths_markdown(selected_paths)

            try:
                refresh_time_select()

                run_status.object = "Files selected successfully."
                run_status.alert_type = "success"
            except Exception as exc:
                time_select.options = []
                time_select.value = None
                time_select.disabled = True
                run_status.object = f"Failed to inspect selected files: `{exc}`"
                run_status.alert_type = "danger"
        else:
            uploaded_files_info.object = "No files selected yet."
            time_select.options = []
            time_select.value = None
            time_select.disabled = True
            run_status.object = "No files selected."
            run_status.alert_type = "warning"

        update_run_button_state()

    file_selector.param.watch(on_files_changed, "value")

    def on_protocol_selected(event):
        update_run_button_state()

    protocol_select.param.watch(on_protocol_selected, "value")

    def on_run_clicked(event):
        if not state["uploaded_paths"]:
            run_status.object = "No uploaded files are available."
            run_status.alert_type = "warning"
            return

        if not protocol_select.value:
            run_status.object = "No protocol is selected."
            run_status.alert_type = "warning"
            return

        protocol_filename = protocol_select.value

        try:
            protocol_text = load_protocol_text(protocol_filename, PROTOCOLS_DIR)

            selected_time = None
            if not time_select.disabled and time_select.value:
                selected_time = str(time_select.value)

            run_status.object = "Running protocol..."
            run_status.alert_type = "info"

            bundle = execute_single_formula_protocol(
                protocol_text=protocol_text,
                uploaded_paths=state["uploaded_paths"],
                selected_time=selected_time,
            )

            result = bundle["result"]

            render_bundle = render_dataarray_to_png(
                result,
                output_name=result.name or "result",
            )

            result_map = build_result_map(
                image_data_uri=render_bundle["image_data_uri"],
                bounds=render_bundle["bounds"],
                center=render_bundle["center"],
                layer_name=result.name or "Protocol result",
            )
            map_pane.object = result_map

            dims_str = ", ".join(f"{dim}={result.sizes[dim]}" for dim in result.dims)

            min_val = float(result.min(skipna=True).values)
            max_val = float(result.max(skipna=True).values)
            mean_val = float(result.mean(skipna=True).values)

            resolved_lines = []
            for protocol_var, (path, dataset_var) in bundle["resolved_inputs"].items():
                resolved_lines.append(
                    f"- `%{protocol_var}%` → `{Path(path).name}` :: `{dataset_var}`"
                )

            result_info.object = (
                f"## Calculation result\n\n"
                f"**Protocol:** `{protocol_filename}`  \n"
                f"**Output variable:** `{result.name}`  \n"
                f"**Selected time:** `{selected_time}`  \n"
                f"**Dimensions:** `{dims_str}`  \n"
                f"**Min:** `{min_val:.6f}`  \n"
                f"**Max:** `{max_val:.6f}`  \n"
                f"**Mean:** `{mean_val:.6f}`  \n"
                f"**Rendered PNG:** `{Path(render_bundle['png_path']).name}`  \n"
                f"**Render range:** `{render_bundle['vmin']:.6f}` to `{render_bundle['vmax']:.6f}`  \n\n"
                f"### Resolved inputs\n"
                + "\n".join(resolved_lines)
            )

            run_status.object = "Protocol executed successfully and displayed on the map."
            run_status.alert_type = "success"

        except Exception as exc:
            result_info.object = "No calculation result yet."
            run_status.object = f"Protocol execution failed: `{exc}`"
            run_status.alert_type = "danger"

    run_button.on_click(on_run_clicked)

    def on_save_protocol(event):
        try:
            output_path = save_protocol_text(
                protocol_name=protocol_name_input.value,
                protocol_text=protocol_text_input.value,
                protocols_dir=PROTOCOLS_DIR,
            )
            protocol_status.object = f"Protocol saved: `{output_path.name}`"
            protocol_status.alert_type = "success"
            refresh_protocol_list()
        except Exception as exc:
            protocol_status.object = f"Failed to save protocol: `{exc}`"
            protocol_status.alert_type = "danger"

    save_protocol_button.on_click(on_save_protocol)

    refresh_protocol_list()

    upload_controls = pn.Card(
        pn.pane.Markdown("### Data input"),
        pn.pane.Markdown(
            "Select existing local files from disk. "
            "This mode is intended for large NetCDF files."
        ),
        file_selector,
        uploaded_files_info,
        title="Inputs",
        width=700,
        min_width=700,
        max_width=700,
        sizing_mode="fixed",
    )

    calculation_controls = pn.Card(
        pn.pane.Markdown("### Calculation"),
        protocol_select,
        time_select,
        run_button,
        run_status,
        result_info,
        title="Protocol execution",
        width=700,
        height=700,
        min_width=700,
        max_width=700,
        sizing_mode="fixed",
    )

    map_card = pn.Card(
        map_pane,
        title="Map",
        max_width=1300,
        max_height=900,
        sizing_mode="stretch_both",
    )

    main_tab = pn.Row(
        pn.Column(
            upload_controls,
            calculation_controls,
            width=700,
            min_width=700,
            max_width=700,
            sizing_mode="fixed",
        ),
        pn.Spacer(width=20),
        pn.Column(
            map_card,
            sizing_mode="stretch_both",
            max_width=1300,
            max_height=900,
        ),
        sizing_mode="stretch_both",
    )

    protocols_tab = pn.Column(
        pn.pane.Markdown("## Protocol editor"),
        protocol_name_input,
        protocol_text_input,
        pn.Row(save_protocol_button),
        protocol_status,
        saved_protocols_list,
        sizing_mode="stretch_both",
    )

    tabs = pn.Tabs(
        ("Main", main_tab),
        ("Protocols", protocols_tab),
        dynamic=True,
        sizing_mode="stretch_both",
    )

    template = pn.template.BootstrapTemplate(
        title="CLIMARQM",
        sidebar=[
            pn.pane.Markdown(
                """
## CLIMARQM

Protocol-driven climate risk app.

Current stage:
- file upload
- protocol editor
- protocol selection
- temporary file saving
- time detection from NetCDF
- protocol execution
- PNG rendering
- map overlay display
"""
            )
        ],
        main=[tabs],
    )

    return template