# Protocol Grammar Specification

## Purpose

This document describes the current protocol grammar used by CLIMARQ.

At the current stage, the grammar is intentionally limited and supports a constrained single-formula workflow for raster-based calculations on compatible input files. A protocol is stored as plain text and is selected in the user interface from the local `protocols` folder. During execution, the selected protocol is parsed, validated, run against the currently selected local input files, and the result is rendered to PNG for display on the interactive map.

---

## Current execution model

The current prototype supports the following workflow:

1. The user selects one or more local input files.
2. The application inspects those files and discovers available time values.
3. The user selects one saved protocol.
4. The user optionally selects a single time/date value.
5. The protocol is executed through the current single-formula executor.
6. The result is rendered to PNG.
7. The PNG is displayed as a map overlay.
8. A textual result summary is shown in the UI, including resolved inputs and basic statistics.

This means that the grammar is only one part of the execution chain. Some execution parameters, especially time selection, are currently controlled by the UI rather than encoded directly in the grammar.

---

## Current scope

The current grammar is designed for:

- one protocol block per file;
- one main calculation block;
- one declared output target;
- one current output format used in practice for visualisation: `PNG`;
- raster-compatible input variables resolved from selected local files;
- a constrained expression syntax suitable for the current executor.

The grammar and executor are expected to evolve later, but this document describes the currently intended working subset rather than future features.

---

## Core syntax elements

### 1. Protocol block

A protocol is wrapped in curly braces:

```text
{
    ...
}

### 2. Directives

Protocol-level directives use ! ... ! syntax on the left-hand side:

!protocoltype! = "single_formula_calculation";
!grid_policy! = "strict_match";
!output! = "@result";
!output_format! = "PNG";

These directives define how the protocol should be interpreted and executed.

### 3. Input variable declarations

Input variables use % ... % syntax:

%rr% = "NetCDF";
%elevation% = "NetCDF";
%slope_degrees% = "NetCDF";

Each declared input variable acts as a symbolic placeholder inside expressions.

### 4. Output variables and named results

Named results use @ ... syntax:

@result

At the current stage, the output directive typically points to one named result:

!output! = "@result";

### 5. Calculation block

Calculation expressions are written inside square brackets:

[
    @result = ... ;
]

At the current stage, the calculation block is intended for the current single-formula workflow.



## Example protocol

The following example matches the current prototype and the example shown in the UI placeholder.

{
    !protocoltype! = "single_formula_calculation";
    !grid_policy! = "strict_match";
    !output! = "@result";
    !output_format! = "PNG";

    %rr% = "NetCDF";
    %elevation% = "NetCDF";
    %slope_degrees% = "NetCDF";

    [
        @result = %rr% * 0.22 * (%elevation% / global_max(%elevation%))
                + %rr% * 0.55 * (%slope_degrees% / global_max(%slope_degrees%));
    ]
}


### Meaning of the main directives

!protocoltype!

Example:

	!protocoltype! = "single_formula_calculation";

This identifies the protocol as belonging to the currently supported single-formula execution mode.

	!grid_policy!

Example:

	!grid_policy! = "strict_match";

This indicates that inputs are expected to be grid-compatible according to the current strict matching logic. At the current stage, this is the standard grid compatibility mode used by the prototype.

	!output!

Example:

	!output! = "@result";

This declares which named result should be treated as the final protocol output.

	!output_format!

Example:

	!output_format! = "PNG";

At the current stage, the practical visual output path is PNG rendering for map display. The executor result is rendered to PNG and then shown as an overlay on the interactive map.

### Input declarations
General form
	%variable_name% = "InputType";

Example:

%rr% = "NetCDF";
%elevation% = "NetCDF";
%slope_degrees% = "NetCDF";

### Current interpretation

At the current stage, these declarations act as protocol variables that must be resolved against the files currently selected in the UI. After execution, the UI reports which actual file and dataset variable were used for each protocol variable, for example:

	%rr% → filename.nc :: rr

This means that the execution layer resolves each declared protocol variable to a real dataset variable found in one of the selected input files. If a variable cannot be resolved correctly, protocol execution fails.

### Supported input types

The current UI example uses "NetCDF" for all declared inputs. This is the safest documented choice for the present prototype.

Other raster formats may become part of the broader project vision, but this document describes the currently supported working grammar example rather than future extensions.

### Expression syntax
Assignment form

The current calculation form uses a named result on the left-hand side:

	@result = expression;

### Basic operators

The current example demonstrates the use of:

addition: +
multiplication: *
division: /
parentheses for grouping: ( ... )

Example
@result = %rr% * 0.22 * (%elevation% / global_max(%elevation%)) + %rr% * 0.55 * (%slope_degrees% / global_max(%slope_degrees%));

This expression combines one precipitation-like variable with two terrain-related variables normalised by their global maxima. The exact scientific meaning depends on the selected inputs and the user’s chosen methodology.

### Supported helper functions
	
	global_max(...)

The current example uses:

global_max(%elevation%)
global_max(%slope_degrees%)

This indicates support, at least at the current documented level, for a helper function that returns the global maximum of the referenced input array for use in normalisation.

At the current stage, users should treat global_max(...) as part of the supported example subset. Other functions should not be assumed to be supported unless they are explicitly implemented and documented.

### Time handling

Time handling is currently UI-driven rather than grammar-driven.

The application scans the selected input files for available time values and populates the Time / date selector in the interface. If a time value is selected, it is passed into protocol execution as selected_time.

This means:

the protocol text does not currently contain explicit grammar for selecting time;
time selection is performed outside the protocol text;
the executor receives the selected time from the UI.

So, for the current prototype, temporal control belongs to the execution context rather than to the grammar itself.

### Result handling

After successful execution, the current workflow produces:

a computed result array;
a rendered PNG image;
map bounds and centre metadata for overlay display;
a UI summary including:
protocol file name,
output variable name,
selected time,
dimensions,
minimum,
maximum,
mean,
rendered PNG file name,
render range,
resolved inputs.

This makes the current protocol system both computational and visual: the protocol does not only define a formula, but also participates in a pipeline that ends in map display.

### Validation expectations

A valid current protocol should satisfy all of the following:

it is enclosed in { ... };
it declares a supported !protocoltype!;
it declares an !output! target;
it declares an output format consistent with the current workflow;
it declares input variables before using them in expressions;
it contains a calculation block in [ ... ];
it assigns the final result to the declared output variable;
it ends assignments and declarations with semicolons.

If the protocol is malformed or incompatible with the selected files, execution fails and the UI displays an error message.


### Current limitations

The present grammar is intentionally limited.

Current practical limitations include:

support is focused on the single_formula_calculation workflow;
time selection is not yet expressed directly in grammar syntax;
input resolution depends on the currently selected local files;
grid compatibility currently relies on strict matching logic;
the documented working output format is PNG for rendered map display;
the set of supported helper functions is limited and should not be assumed beyond the current documented example.
Recommended authoring pattern

For the current prototype, users should follow this pattern:

- declare protocol directives first;
- declare all input variables next;
- write one clear calculation block;
- assign the final computed array to @result;
- use !output! = "@result";;
- use !output_format! = "PNG";;
- keep expressions simple and aligned with the currently supported subset.

### Recommended template:

{
    !protocoltype! = "single_formula_calculation";
    !grid_policy! = "strict_match";
    !output! = "@result";
    !output_format! = "PNG";

    %input1% = "NetCDF";
    %input2% = "NetCDF";

    [
        @result = %input1% + %input2%;
    ]
}


## Notes for future extension

This specification describes the current working subset only.

Future versions of CLIMARQ may extend the grammar with richer validation rules, additional helper functions, more output formats, more explicit temporal syntax, and more advanced multi-step or rule-based protocols. Those future capabilities are not part of the present specification unless they are explicitly implemented in code and documented accordingly.