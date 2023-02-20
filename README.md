# EnergyPLAN Output Parser/Converter

Since EnergyPLAN's output is the opposite of "easy to parse" for a program, I have created this script to convert it to a handy JSON file. You can use it both as a standalone program to convert the output file to JSON, or import it as a library in your python program and get the data as a standard Python dictionary. In the future, I might also add a CSV output format - although I think it's much less suited for such a structured output.

## Installation

```bash
$ pip install eplan_parser
```

## Usage as a Standalone Script

```bash
$ eplan_parser eplan_output.txt parsed_output.json
 ✓ - Read 8889 lines from "eplan_output.txt"
 ✓ - Parsed CO2 section
 ✓ - Parsed RES Share section
 ✓ - Parsed Fuel Consumption section
 ✓ - Parsed Annual Costs section
 ✓ - Parsed Yearly Totals section
 ✓ - Parsed Hourly Totals section
 ! - Costs overview parsing not yet implemented
 ! - Fuel balance parsing not yet implemented
 ✓ - Exported JSON dataset to "parsed_output.json" - 6.6 Mb (6928567 bytes) written
```

## Usage as a Helper Library

```python
import eplan_parser

# [...]
# Run EnergyPLAN & whatever
# [...]

data = load_dataset("eplan_output.txt")
co2_emission = data['CO2 Emissions']['total']
print(co2_emission)
```

---

*If you've used this script and found it useful, please let me know if you got any errors or had good compatibility, especially if you're using a different version of EnergyPLAN.*
