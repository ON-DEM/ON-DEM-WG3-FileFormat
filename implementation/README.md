# Implementation

This folder contains implementations of the ON-DEM data structures for specific DEM simulation codes.

## VTK HDF Implementation

The `vtkhdf/` folder provides tools to export/import simulation data in VTK HDF format, which is compatible with ParaView and other visualization tools.

One file holds one timestep and everything needed to restart from it. The same file opens in ParaView for 3D visualisation.

### File layout

A file has two top-level groups. `/VTKHDF` is the part ParaView reads (the name is mandatory; ParaView ignores everything else). `/ONDEM` holds the rest of the simulation state.

```
/VTKHDF                          Type = "MultiBlockDataSet", Version = (2, 5)
  <group name>/                  one PolyData block per display group
    Type = "PolyData", Version = (2, 5)
    NumberOfPoints   (1,)
    Points           (N,3) float64   body positions (stored only here)
    Vertices/                         one vertex cell per point
    Lines/  Polygons/  Strips/        empty
    PointData/
      body_id        (N,)  int64     joins the block to /ONDEM
      radius, velocity, angular_velocity, orientation   (see table below)
  Assembly/
    <group name>  -> /VTKHDF/<group name>   (HDF5 soft link)
/ONDEM
  Scene/                         attributes: time, timestep
                                 datasets: gravity, units, display_group_names
  Materials/<material id>/       one group per material, one scalar dataset per field
  Bodies/<shape group>/          sphere, box, polyhedron, wall, facet, other
    attribute count
    body_id          (n,)  int64     the join key
    ...                              per-body fields not in the blocks (see table)
  Interactions/<type>/           one group per interaction type (snake_case)
    attribute count
    id1, id2, normal, normal_force, shear_force, ...
```

Rules:

- **One block per display group.** Every name in `scene.display_group_names` gets a block, also when no body is in that group, so the block tree is the same in every file of a series. Blocks are plain groups directly under `/VTKHDF`; the soft links in `/VTKHDF/Assembly` give the order and the names shown in ParaView. Groups under `/VTKHDF` are created with creation-order tracking, which VTK's reader needs.
- **Display groups.** `base_body.display_group` (optional, default 0) is an index into `scene.display_group_names` (default `['all']`). It is not written as a dataset: a body's display group is the index of the name of the block it is in. Display groups are only relevant for visualisation.
- **Geometry is stored once.** Body positions are only in the blocks (`Points`, float64). `/ONDEM/Bodies` holds no positions.
- **Restart reads the whole file.** The blocks and `/ONDEM/Bodies` are joined on `body_id`; every body must be in both.
- **Quaternions** are stored as (x, y, z, w), and the dataset has the attribute `order = "xyzw"`. The convention is still to be confirmed by Bruno (see the schema).
- **snake_case** for every name in the file. Groups whose content is not in the schema yet (`wall`, `facet`, `other`, the interaction groups) are not normative.

### Which body field is where (provisional)

The split between the blocks and `/ONDEM` is an open point; this is the current proposal. It is set in one place: `_BLOCK_FIELDS` in `vtkhdf/codegen_yade.py`.

| Field | Where | Notes |
|---|---|---|
| `position` | `/VTKHDF/<group>/Points` | float64, stored only here |
| `body_id` | `PointData/body_id` and `/ONDEM/Bodies/<shape>/body_id` | int64, the join key |
| `display_group` | not a dataset | index of the block's name in `display_group_names` |
| `radius` | `PointData` | NaN for bodies that are not spheres |
| `velocity` | `PointData` | |
| `angular_velocity` | `PointData` | global frame |
| `orientation` | `PointData` | (x, y, z, w), attribute `order` |
| `material_id`, `clump_id` | `/ONDEM/Bodies/<shape>/` | |
| `mass`, `volume` | `/ONDEM/Bodies/<shape>/` | |
| `inertia` | `/ONDEM/Bodies/<shape>/` | 3x3, flattened row-major, shape (n, 9) |
| `temperature`, `liquid_film_volume` | `/ONDEM/Bodies/<shape>/` | only written if the code provides them |
| box `dimensions` | `/ONDEM/Bodies/box/` | |
| wall `axis`, `sense` | `/ONDEM/Bodies/wall/` | not in the schema yet |
| facet `vertices`, `normal` | `/ONDEM/Bodies/facet/` | not in the schema yet |

### Current limits

- **Interactions are not restored on import.** They are written to `/ONDEM/Interactions` but the importer does not read them: YADE rebuilds the contacts with its collider on the first step, so the contact history (accumulated shear force, sliding state) is lost on restart. Interactions are not visible in ParaView yet either.
- **Non-sphere bodies appear as points.** Every body is one point (its position) in its block. Walls, facets and boxes are shown as points until the schema has a mesh/facet shape.
- The importer restores spheres and walls only. Boxes, facets, polyhedra and other shapes are reported as skipped; clumps are not rebuilt.

### For YADE Users

Use the generated `export_yade_vtkhdf.py` to export data from YADE simulations, and `import_yade_vtkhdf.py` to restart from a file. Both need `hdf5_utils.py` on the Python path.

Example usage in YADE:
```python
from export_yade_vtkhdf import export_vtkhdf

# one display group: everything in the block 'all'
export_vtkhdf("output.vtkhdf")

# two display groups: spheres and the rest are separate blocks in ParaView
export_vtkhdf("output.vtkhdf",
              display_group_names=["particles", "geometry"],
              display_group=lambda b: 0 if isinstance(b.shape, Sphere) else 1)
```

`display_group` is a function `body -> index` or a dict `{body_id: index}` (bodies not in the dict get 0). An invalid name or index raises `ValueError`, and no file is written.

Restart:
```python
from import_yade_vtkhdf import import_vtkhdf
r = import_vtkhdf("output.vtkhdf")      # create the engines first, for gravity
O.run(1000, wait=True)
export_vtkhdf("next.vtkhdf", r["display_group_names"], r["display_group"])
```

Bodies are appended in increasing `body_id`. Into an empty scene YADE gives them the same ids as in the file; `r["id_map"]` gives the new id of each stored id.

#### Tests

- `vtkhdf/testing/test_multiblock_utils.py`: the code-agnostic multiblock helpers. Needs only `numpy` and `h5py`; if the `vtk` Python package is installed, it also reads the file back with `vtkHDFReader`.
  ```bash
  python3 implementation/vtkhdf/testing/test_multiblock_utils.py
  ```
- `vtkhdf/testing/test_export.py`: full round trip in YADE. It runs 36 spheres settling in a box of 5 walls, exports them with display groups, checks the file (blocks, interactions), imports it into a reset scene, compares every body, runs 1000 steps and exports again. It prints `TEST PASSED` or `TEST FAILED` (exit code 1). The files are written to the temp directory.
  ```bash
  yadedaily -n -x implementation/vtkhdf/testing/test_export.py
  ```
  On Windows, YADE runs in WSL: `wsl -d Ubuntu-24.04 yadedaily -n -x <path in /mnt/c/...>/test_export.py`.

### Adapting for Other DEM Codes

To use this framework with another DEM code (e.g., LIGGGHTS, DEMETER, etc.), follow these steps:

1. **Create a Mapping File**: Define a JSON file that maps ON-DEM schema fields to your DEM code's API expressions. Use `yade_mapping.json` as a template.

   - Keys are schema class names (`base_body`, `base_state`, `sphere`, `base_interaction`, ...) holding `field: expression` pairs. If a field is not found under its class, the first class entry with that field name is used.
   - Values are Python expressions that access the data in your DEM code's context: `b` is a body, `i` an interaction, `mat` a material.
   - Keys starting with `_` are not schema classes:
     - `_collections`: expressions for the list of bodies and the list of interactions;
     - `_shape_type`: an expression for the body's shape type, and `_shape_groups`: shape type -> group name in `/ONDEM/Bodies`;
     - `_extra_shapes`: fields of shapes that are not in the schema yet (e.g. walls);
     - `_interaction_type`: an expression for the interaction type (the group name in `/ONDEM/Interactions`, written snake_case);
     - `_interaction_geometry`, `_extra_interaction_attributes`, `_extra_material_attributes`: extra fields not in the schema.
   - `display_group` and `display_group_names` map to the helpers `_display_group(b)` and `_display_group_names()`, which take their values from the `export_vtkhdf` arguments. Keep them as they are.
   - Add helper functions if needed (like `_get_gravity()` in YADE).

2. **Run the Code Generator**: Use `codegen_yade.py` (rename it to something generic like `codegen_dem.py` if desired) to generate a custom exporter.

   ```bash
   python codegen_yade.py /path/to/schema --mapping your_mapping.json --out export_your_dem_vtkhdf.py
   ```

   - The schema directory is the root of this project (containing `bodies.py`, etc.).
   - The writing itself (`hdf5_utils.py`) does not depend on the DEM code.
   - Customize the generated code as needed for your DEM code's specifics.

3. **Integrate into Your Simulation**: Import and call the generated export function in your DEM code's scripts.

If you implement support for another DEM code, consider contributing it back to the project by adding your mapping file and any necessary modifications.

### Files Overview

- `schema_parser.py`: Parses the ON-DEM schema from Python files.
- `codegen_yade.py`: Code generator for YADE (adapt for other codes). Holds the provisional split of body fields (`_BLOCK_FIELDS`).
- `yade_mapping.json`: YADE-specific field mappings.
- `hdf5_utils.py`: Code-agnostic HDF5 reading and writing, including the VTKHDF multiblock helpers.
- `export_yade_vtkhdf.py`: YADE exporter, generated by `codegen_yade.py` (do not edit by hand).
- `import_yade_vtkhdf.py`: YADE importer (restart).
- `testing/test_multiblock_utils.py`, `testing/test_export.py`: tests, see above.
- `testing/test_5spheres.vtkhdf`, `testing/test_box_spheres.vtkhdf`: sample files written by an earlier version of the exporter (old single-block layout).
