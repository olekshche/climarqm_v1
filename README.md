# CLIMARQ

CLIMARQ is a prototype Python + Panel application skeleton for climate risk visualisation and future risk computation workflows.

At this stage, the project provides:

- a Panel-based user interface
- a Folium/Leaflet map with fullscreen mode
- local file selection via `FileSelector`
- automatic detection of available time values from selected NetCDF files
- selection of a saved protocol from the local `protocols` folder
- execution of a single-formula calculation protocol
- rendering of the calculation result to PNG
- display of the rendered result as a map overlay
- a separate **Protocols** tab for editing and saving protocol files

The current version is an early working prototype. It already supports basic protocol-driven calculations for compatible raster/NetCDF inputs, time-step selection, protocol execution, PNG rendering, and result display on an interactive map. The grammar and execution engine are still limited to a constrained subset of operations and will be extended further.
---

## Project idea

CLIMARQ is intended as a protocol-driven climate risk platform for raster-based environmental and climate calculations.

The current prototype already supports a basic protocol workflow in which the user:

1. selects local input files;
2. chooses a saved protocol;
3. selects a time/date if available;
4. runs the protocol;
5. views the rendered result on the map.

In the longer term, the project may support two complementary modes:

1. **Built-in risk calculation modules**
2. **User-defined calculations through saved protocols**

At the current stage, a protocol is a structured text definition that declares input variables, output settings, and a calculation expression executed by the application.


Example protocol:

```text
{
    !protocoltype! = "single_formula_calculation";
    !grid_policy! = "strict_match";
    !output! = "@result";
    !output_format! = "PNG";

    %rr% = "NetCDF";
    %elevation% = "NetCDF";
    %slope_degrees% = "NetCDF";

    [
@result = %rr% * 0.22 * (%elevation% / global_max(%levation%)) + %rr% * 0.55 * (%slope_degrees% / global_max(%slope_degrees%));
    ]
}


In the current grammar:

- `{ ... }` defines the full protocol block
- `! ... !` defines protocol-level directives and metadata
- `% ... %` declares input variables
- `@ ...` denotes output variables or named calculation results
- `[ ... ]` contains calculation expressions


The long-term goal is to let users copy a methodology from a paper, website, or technical source into the app as a protocol, save it, and later run calculations without needing software updates.


## Current project structure

CLIMARQM/
├─ app.py
├─ environment.yml
├─ README.md
├─ Protocol Grammar Specification.md
└─ climarqm/
   ├─ __init__.py
   ├─ config/
   │  ├─ __init__.py
   │  └─ paths.py
   ├─ functions/
   │  ├─ __init__.py
   │  ├─ file_handlers.py
   │  └─ protocol_manager.py
   ├─ io/
   │  ├─ __init__.py
   │  └─ netcdf_resolver.py
   ├─ protocol/
   │  ├─ __init__.py
   │  ├─ parser.py
   │  ├─ validator.py
   │  └─ executor.py
   ├─ rendering/
   │  ├─ __init__.py
   │  └─ map_output.py
   ├─ ui/
   │  ├─ __init__.py
   │  └─ main_view.py
   ├─ protocols/
   │  └─ *.txt
   ├─ outputs/
   │  └─ result.png
   ├─ data/
   └─ temp/


## Main files

app.py

Application entry point.

## Main files

### `app.py`
Application entry point for launching the Panel app.

### `climarqm/ui/main_view.py`
Contains the main Panel user interface, including:
- local file selection
- saved protocol selection
- time/date selection
- protocol execution controls
- result summary display
- interactive Folium map
- protocol editor tab
- protocol saving

### `climarqm/io/netcdf_resolver.py`
Contains helper logic for discovering available time values from selected NetCDF files.

### `climarqm/protocol/parser.py`
Parses protocol text into an internal structured representation.

### `climarqm/protocol/validator.py`
Validates protocol structure and execution rules.

### `climarqm/protocol/executor.py`
Executes the current single-formula protocol workflow on resolved inputs.

### `climarqm/rendering/map_output.py`
Builds PNG output and map overlays for visualising calculation results.

### `climarqm/functions/protocol_manager.py`
Contains helper functions for:
- sanitising protocol names
- listing saved protocols
- loading protocol text
- saving protocol text

### `climarqm/functions/file_handlers.py`
Contains helper functions for:
- formatting summaries of selected file paths for the UI

### `climarqm/config/paths.py`
Defines project directories and ensures they exist:
- `protocols`
- `data`
- `outputs`
- `temp`


## Current limitations

- the current protocol engine supports a constrained single-formula workflow
- input variables are resolved from the currently selected local files
- grid compatibility currently relies on strict matching logic
- time selection is controlled by the UI rather than explicitly encoded in the grammar
- the current visual output is rendered as PNG and displayed as a map overlay
- the grammar and execution engine currently support only a limited subset of operations and helper functions

## AI assistance statement

Artificial intelligence tools, including GPT-5.4 Thinking, were used during development of this prototype to assist with code refinement, implementation adjustments, debugging support, and editing of project documentation.

AI tools were used only as auxiliary support instruments and not as a source of scientific methodology or scientific validation. All methodological choices, project decisions, final review, and responsibility for the resulting code and documentation remain with the author.

## Installation

Create and activate the Conda environment:

```bash
conda env create -f environment.yml
conda activate climarqm


## Run the app

From the project root:

```bash
panel serve app.py --autoreload --show


## Demonstration data bundle

A demonstration data bundle for the current CLIMARQ prototype is available here:

https://drive.google.com/file/d/1dTe0CBgRKQmFCvppdxiAQWPmto0WYiSK/view?usp=sharing


The bundle includes:
- precipitation data based on E-OBS;
- a static elevation grid;
- a slope grid derived from elevation;
- a demonstration protocol;
- a description file for the bundle.

**Important:** the included protocol is provided for demonstration purposes only. It has no scientific validation and must not be interpreted as a real risk model.

## Demonstration video:
https://drive.google.com/file/d/17f1VktzQEAQsDNOfseChNX63GSnatnsx/view?usp=sharing
