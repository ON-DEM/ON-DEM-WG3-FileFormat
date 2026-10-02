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
  Scene/                         attributes: time, timestep, iteration (provisional)
                                 datasets: gravity, units, display_group_names
  Materials/<material id>/       one group per material, one scalar dataset per field
  Bodies/<shape group>/          sphere, box, polyhedron, wall, facet, clump, other
    attribute count
    body_id          (n,)  int64     the join key
    ...                              per-body fields not in the blocks (see table)
  Interactions/<type>/           one group per interaction type (snake_case)
    attribute count
    id1, id2, normal, normal_force, shear_force, kn, ks, friction_coefficient, ...
```

Rules:

- **One block per display group.** Every name in `scene.display_group_names` gets a block, also when no body is in that group, so the block tree is the same in every file of a series. Blocks are plain groups directly under `/VTKHDF`; the soft links in `/VTKHDF/Assembly` give the order and the names shown in ParaView. Groups under `/VTKHDF` are created with creation-order tracking, which VTK's reader needs.
- **Display groups.** `base_body.display_group` (optional, default 0) is an index into `scene.display_group_names` (default `['all']`). It is not written as a dataset: a body's display group is the index of the name of the block it is in. Display groups are only relevant for visualisation.
- **Geometry is stored once.** Body positions are only in the blocks (`Points`, float64). `/ONDEM/Bodies` holds no positions.
- **Restart reads the whole file.** The blocks and `/ONDEM/Bodies` are joined on `body_id`; every body must be in both.
- **Quaternions** are stored scalar first, (w, x, y, z), and the dataset has the attribute `order = "wxyz"`. The identity (no rotation) is (1, 0, 0, 0), and q converts body-frame coordinates to global-frame coordinates: v_global = q v_body q⁻¹ (equivalently, it rotates the global axes onto the body axes). This convention was decided on 2 October 2026 (see `base_state.orientation`). YADE indexes its quaternions as (x, y, z, w), so the YADE mapping reorders them on export and the importer reorders them back.
- **snake_case** for every name in the file. Groups whose content is not in the schema yet (`wall`, `facet`, `clump`, `other`, the interaction groups) are not normative.
- **`normal_force` is positive in traction**, as the schema says. Until 2026-10-02 the YADE exporter wrote it positive in compression. A contact in compression now has a negative `normal_force`.

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
| `orientation` | `PointData` | (w, x, y, z), attribute `order = "wxyz"` |
| `material_id`, `clump_id` | `/ONDEM/Bodies/<shape>/` | |
| `mass`, `volume` | `/ONDEM/Bodies/<shape>/` | |
| `inertia` | `/ONDEM/Bodies/<shape>/` | 3x3, flattened row-major, shape (n, 9) |
| `temperature`, `liquid_film_volume` | `/ONDEM/Bodies/<shape>/` | only written if the code provides them |
| box `dimensions` | `/ONDEM/Bodies/box/` | |
| wall `axis`, `sense` | `/ONDEM/Bodies/wall/` | not in the schema yet |
| facet `vertices`, `normal` | `/ONDEM/Bodies/facet/` | not in the schema yet |
| `blocked_dofs`, `group_mask`, `is_damped`, `angular_momentum`, `density_scaling` | `/ONDEM/Bodies/<shape>/` | provisional extras, see "Provisional extras" below |

### Materials (provisional)

`/ONDEM/Materials/<id>/` holds one scalar dataset per field, named as in the schema. Each group has the attribute `schema_classes` (the schema classes its fields come from) and, while the choice is open, `provisional`.

YADE's `FrictMat` does not match any schema class yet. It is written for now as `base_material` + `hertz_elastic` + `frictional_3D`:

| Schema field | YADE `FrictMat` | Note |
|---|---|---|
| `base_material.id` | `id` | |
| `base_material.density` | `density` | |
| `hertz_elastic.young_modulus` | `young` | in YADE a contact modulus: kn = 2 E₁R₁ E₂R₂ / (E₁R₁ + E₂R₂) |
| `hertz_elastic.poisson_ratio` | `poisson` | in YADE the stiffness ratio ks/kn, not a Poisson's ratio |
| `frictional_3D.shear_friction` | tan(`frictionAngle`) | |
| `frictional_3D.shear_damping` | none | mandatory in the schema, not written: FrictMat has no shear damping |

`label` and `material_type` are written as extra, YADE-specific datasets. The importer rebuilds only `FrictMat`. It needs the five fields above and stops with an error that names the material and the missing field; there are no default values.

**To settle with Bruno:** which schema class a linear contact law like FrictMat belongs to. FrictMat is a linear law, but `young_modulus` and `poisson_ratio` are in `hertz_elastic`. One option is a linear class with a contact modulus and a stiffness ratio. Another is to write `normal_stiffness`/`shear_stiffness`, but YADE computes those per contact, not per material. Also open: what to write for `shear_damping` when a code has none.

### Restart: what is restored

A file holds everything the importer needs to continue a run from the same state, contact history included. The engines are the exception: they cannot come from the file (see below), so the script creates `O.engines` first, then calls `import_vtkhdf`.

The importer reads and checks the whole file before it creates anything. An unsupported shape, contact type or material, a missing field, or a contact with a body that is not in the file raises an error that lists every problem. The scene is then left untouched; there are no default values.

| What | From | How |
|---|---|---|
| Spheres, walls, boxes | blocks + `/ONDEM/Bodies/<shape>/` | appended in increasing `body_id` (same ids in an empty scene, otherwise see `id_map`) |
| Body state | blocks + `/ONDEM/Bodies` | position, velocity, angular velocity, orientation, mass, inertia, and the provisional extras below |
| Clumps | `/ONDEM/Bodies/clump/` + members' `clump_id` | members first, then `O.bodies.clump(members)`; see the note below |
| Materials | `/ONDEM/Materials` | `FrictMat` only, see above |
| Contacts | `/ONDEM/Interactions/<type>/` | every real contact is rebuilt with `utils.createInteraction` and gets its stored history: `normal`, `shear_force`, `normal_force`, `kn`, `ks`, `friction_coefficient`, contact point, reference radii, frictional dissipation |
| `dt`, gravity | `/ONDEM/Scene` | gravity is set on the `NewtonIntegrator` |
| Time, iteration | `/ONDEM/Scene` | carried as offsets, see below |
| Display groups | blocks | returned, so they can be passed back to `export_vtkhdf` |

Contact types that can be restored: `(ScGeom, FrictPhys)`, as used for example by `Law2_ScGeom_FrictPhys_CundallStrack`. Other types raise an error. If the engines create another contact type than the one in the file, the importer stops with an error that says the engines differ.

The stored contact **normal is history too**. On each step the shear force is rotated from the previous normal to the new one, so the importer writes the stored normal back after creating the contact. Without that, the shear force is off by about 1e-6 relative after one step. With it, a restart without clumps continues **bit-identically** (`test_restart.py`: difference 0 after 1 and after 2000 steps).

**Clumps.** YADE recomputes a clump's frame (centre of mass, principal axes) and its members' relative positions and orientations from the members' positions when the clump is built. The relative poses cannot be set from Python. The importer keeps the recomputed frame, so members and clump stay consistent, and checks it against the file: the centre of mass must agree, and the stored inertia, rotated into the new frame, must be diagonal there. Mass, inertia, velocities and angular momentum come from the file. A restart with clumps therefore starts with round-off differences, about 1e-13 relative after one step. The granular dynamics amplify them, to about 5e-9 after 2000 steps in `test_restart.py`. It is not bit-identical.

**Time and iteration.** `O.time` and `O.iter` cannot be set in YADE. The importer stores the offsets (file value minus current value) in `O.tags["ondem_time_offset"]` and `O.tags["ondem_iteration_offset"]`, and the exporter adds them, so the file series continues across a restart. **Engines that depend on `O.time` or `O.iter` see them start again from zero after a restart**, even though the file series stays continuous: PyRunner `iterPeriod`/`virtPeriod`, time-dependent boundary motion, recorders, anything else that reads `O.time` or `O.iter`. Scripts have to add the offsets themselves (`r["time_offset"]`, `r["iteration_offset"]`).

### What a restart cannot restore

These do not come from the file. The script must set them up the same way as in the original run:

- the engines and their order, the functors (`Ig2`, `Ip2`, `Law2`) and their parameters (for example `neverErase`, `avoidGranularRatcheting`, `interactionDetectionFactor`);
- `NewtonIntegrator` settings other than gravity: `damping`, `kinSplit`, `exactAsphericalRot`;
- boundary motion imposed by engines (kinematic and translation engines, servo controllers and their internal state; the schema has `stress_control_boundary`, but it is not written);
- the counters of periodic engines (`iterLast`, `virtLast`), recorders, time steppers, the state of random generators;
- collider settings (they do not change the results) and the number of threads;
- the energy totals of `O.energy` (with `trackEnergy`);
- `refPos`, `refOri` (reference pose for output only, no effect on the dynamics);
- periodic cells: the exporter refuses a periodic scene (`O.periodic`), because the cell is not written yet.

### Provisional extras and questions for Bruno

To make the restart complete now, the files carry these provisional, non-normative fields. The schema has no field for them yet. Each one is a question for Bruno, and the names will change if the schema chooses others.

| Field | Where | YADE |
|---|---|---|
| `blocked_dofs` (string, e.g. `"xyz"`, `"xyzXYZ"`) | `/ONDEM/Bodies/<shape>/` | `state.blockedDOFs` |
| `group_mask` (int) | `/ONDEM/Bodies/<shape>/` | `groupMask`: which body pairs may interact |
| `is_damped` (bool) | `/ONDEM/Bodies/<shape>/` | `state.isDamped` |
| `angular_momentum` (vector) | `/ONDEM/Bodies/<shape>/` | `state.angMom` |
| `density_scaling` (float, −1 = not used) | `/ONDEM/Bodies/<shape>/` | `state.densityScaling` |
| shape group `clump` | `/ONDEM/Bodies/clump/` | the clump body |
| `iteration` (int attribute) | `/ONDEM/Scene` | `O.iter` (+ offset) |
| `frictional_dissipation` | `/ONDEM/Interactions/<type>/` | `phys.frictDissip` |
| `contact_point`, `overlap`, `reference_radius_1/2`, `geom_type`, `phys_type` | `/ONDEM/Interactions/<type>/` | contact geometry and types |

Questions for Bruno (none of them is decided here):

1. **Blocked degrees of freedom.** Should `base_state` get `blocked_dofs` (six flags: translations x, y, z and rotations x, y, z)? Or a `fixed` boolean?
2. **Collision mask.** Should `base_body` get `collision_mask`, saying which body pairs may interact (YADE `groupMask`)?
3. **Angular momentum.** For aspherical bodies and clumps: should `base_state` store `angular_momentum`, or is it always derived from inertia, orientation and angular velocity?
4. **Iteration.** Should `scene` get `iteration`, next to `time`?
5. **Clumps.** A shape class for the clump body, with members found through `clump_id`? Should the members' relative positions and orientations be stored?
6. **Walls/planes.** A shape class for infinite planes (axis + sense, or normal + point)? Today they are the non-normative group `wall`.
7. **Facets/mesh and polyhedra.** What layout should hold vertex lists of different lengths per body? (The mesh shape is already open; `polyhedron.vertices` is untyped.)
8. **Contact normal as history.** Can `normal.normal` be defined as "the contact normal of the last force evaluation", since the incremental shear force is rotated from it? Should `contact_point`, `overlap` and the reference radii become schema fields?
9. **Dissipation.** Are accumulated quantities part of the format: frictional dissipation per contact, energy totals?
10. **Periodic cell.** Where does `imposed_conditions.periodic_box` go in the file: `/ONDEM/Scene`, or a group of its own?
11. **Numerical settings per body.** Do per-body numerical damping on/off and density scaling belong in the format, or are they code-specific extras?

### Current limits

- **Non-sphere bodies appear as points.** Every body is one point (its position) in its block. Walls, facets, boxes and clump bodies are shown as points until the schema has a mesh/facet shape. Contacts are not visible in ParaView yet either: they stay in `/ONDEM/Interactions`.
- The importer restores spheres, walls, boxes and clumps. Facets, polyhedra and other shapes are refused with an error naming the bodies.
- The importer rebuilds `FrictMat` materials and `(ScGeom, FrictPhys)` contacts only.
- A restart with clumps is not bit-identical (see above).

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
O.engines = [...]                       # the same engines as the original run: they are not in the file
r = import_vtkhdf("output.vtkhdf")      # bodies, materials, contacts with history, dt, gravity
O.run(1000, wait=True)                  # O.time and O.iter start again from 0 here
export_vtkhdf("next.vtkhdf", r["display_group_names"], r["display_group"])   # time/iteration continue
```

Bodies are appended in increasing `body_id`. Into an empty scene YADE gives them the same ids as in the file; `r["id_map"]` gives the new id of each stored id.

#### Tests

- `vtkhdf/testing/test_multiblock_utils.py`: the code-agnostic multiblock helpers. Needs only `numpy` and `h5py`; if the `vtk` Python package is installed, it also reads the file back with `vtkHDFReader`.
  ```bash
  python3 implementation/vtkhdf/testing/test_multiblock_utils.py
  ```
- `vtkhdf/testing/test_export.py`: full round trip in YADE. It runs 36 spheres settling in a box of 5 walls, with two materials with non-default values. It exports them with display groups, checks the file (blocks, quaternion convention, materials, interactions), imports it into a reset scene, compares every body and every material field, runs 1000 steps and exports again. It also checks that a file with a missing material field is rejected. It prints `TEST PASSED` or `TEST FAILED` (exit code 1). The files are written to the temp directory.
  ```bash
  yadedaily -n -x implementation/vtkhdf/testing/test_export.py
  ```
  On Windows, YADE runs in WSL: `wsl -d Ubuntu-24.04 yadedaily -n -x <path in /mnt/c/...>/test_export.py`.
- `vtkhdf/testing/test_restart.py`: acceptance test for the restart.
  - Run A settles the box, tilts gravity so the contacts carry shear load, exports, and runs 2000 more steps. Run B imports into a fresh scene and runs 2000 steps.
  - At the restart instant the contacts and their restored values must be equal. After 1 step and after 2000 steps, positions, velocities and per-contact normal and shear forces must agree within the stated tolerance.
  - Two scenarios:
    - without clumps the restart must be bit-identical (tolerance 1e-10);
    - with clumps the tolerance is 1e-12 after 1 step and 1e-7 after 2000 steps (see "Clumps" above).
  - Negative controls (shear forces zeroed, stored normals ignored) must exceed the tolerance.
  - Needs 1 OpenMP thread, which is the yadedaily default.
  ```bash
  yadedaily -n -x implementation/vtkhdf/testing/test_restart.py
  ```

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
     - `_material_classes`: the schema classes whose fields are written for each material, and `_material_classes_note`: written as the `provisional` attribute;
     - `_extra_body_fields`, `_extra_scene_fields`: provisional per-body and scene fields that the schema does not have yet (see "Provisional extras");
     - `_refuse_if`: `{message: expression}`; the exporter raises `ValueError` with the message, and writes no file, when the expression is true (YADE: periodic scenes);
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
- `testing/test_multiblock_utils.py`, `testing/test_export.py`, `testing/test_restart.py`: tests, see above.
- `testing/test_5spheres.vtkhdf`, `testing/test_box_spheres.vtkhdf`: sample files written by an earlier version of the exporter (old single-block layout).
