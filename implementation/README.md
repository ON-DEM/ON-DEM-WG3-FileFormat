# Implementation

This folder contains implementations of the ON-DEM data structures for specific DEM simulation codes.

## VTK HDF Implementation

The `vtkhdf/` folder provides tools to export/import simulation data in VTK HDF format, which is compatible with ParaView and other visualization tools.

### For YADE Users

YADE support is fully implemented. Use the generated `export_yade_vtkhdf.py` to export data from YADE simulations.

Example usage in YADE:
```python
from export_yade_vtkhdf import export_vtkhdf
export_vtkhdf("output.vtkhdf")
```

### Adapting for Other DEM Codes

To use this framework with another DEM code (e.g., LIGGGHTS, DEMETER, etc.), follow these steps:

1. **Create a Mapping File**: Define a JSON file that maps ON-DEM schema fields to your DEM code's API expressions. Use `yade_mapping.json` as a template.

   - Keys can be `class.field` or just `field` (more specific takes precedence).
   - Values are Python expressions that access the data in your DEM code's context.
   - Add helper functions if needed (like `_get_gravity()` in YADE).

2. **Run the Code Generator**: Use `codegen_yade.py` (rename it to something generic like `codegen_dem.py` if desired) to generate a custom exporter.

   ```bash
   python codegen_yade.py /path/to/schema --mapping your_mapping.json --out export_your_dem_vtkhdf.py
   ```

   - The schema directory is the root of this project (containing `bodies.py`, etc.).
   - Customize the generated code as needed for your DEM code's specifics.

3. **Integrate into Your Simulation**: Import and call the generated export function in your DEM code's scripts.

If you implement support for another DEM code, consider contributing it back to the project by adding your mapping file and any necessary modifications.

### Files Overview

- `schema_parser.py`: Parses the ON-DEM schema from Python files.
- `codegen_yade.py`: Code generator for YADE (adapt for other codes).
- `yade_mapping.json`: YADE-specific field mappings.
- `export_yade_vtkhdf_generated.py`: Auto-generated YADE exporter.
- `import_yade_vtkhdf.py`: YADE importer (if implemented).
- `test_export.py`: Testing scripts.
- `test_5spheres.vtkhdf`: Sample VTK HDF file for testing.