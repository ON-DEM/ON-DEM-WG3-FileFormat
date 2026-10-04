# Implementation

This folder contains implementations of the ON-DEM data structures for specific DEM simulation codes.

## VTK HDF Implementation

The `vtkhdf/` folder provides tools to export/import simulation data in VTK HDF format, which is compatible with ParaView and other visualization tools.

One file holds one timestep and everything needed to restart from it. The same file opens in ParaView for 3D visualisation.

### File layout

A file has two top-level groups. `/VTKHDF` is the part ParaView reads (the name is mandatory; ParaView ignores everything else). It holds every per-body field. The simulation group `/ONDEM` holds the scene, the materials and the interactions. It will be renamed (decision 19, name not decided yet); the code takes the name from one constant, `hdf5_utils.SIMULATION_GROUP`, so readers and writers change in one place.

```
/VTKHDF                          Type = "MultiBlockDataSet", Version = (2, 5)
  <group name>/                  one PolyData block per display group
    Type = "PolyData", Version = (2, 5)
    NumberOfPoints   (1,)
    Points           (N,3) float64   body positions
    Vertices/                         one vertex cell per point
    Lines/  Polygons/  Strips/        empty
    PointData/                        every per-body field, one value per body (see table below)
      body_id        (N,)  int64     interactions refer to bodies through it
      shape_type     (N,)  int64     index into /ONDEM/Scene/shape_names
      ...
  Assembly/
    <group name>  -> /VTKHDF/<group name>   (HDF5 soft link)
/ONDEM                           the simulation group (hdf5_utils.SIMULATION_GROUP)
  Scene/                         attributes: time, timestep, iteration
                                 datasets: gravity, units, display_group_names, shape_names
  Materials/<material id>/       one group per material, one scalar dataset per field
  Interactions/<type>/           one group per interaction type (snake_case)
    attribute count
    id1, id2, normal, normal_force, shear_force, kn, ks, friction_coefficient, ...
```

Rules:

- **One block per display group.** Every name in `scene.display_group_names` gets a block, also when no body is in that group, so the block tree is the same in every file of a series. Blocks are plain groups directly under `/VTKHDF`; the soft links in `/VTKHDF/Assembly` give the order and the names shown in ParaView. Groups under `/VTKHDF` are created with creation-order tracking, which VTK's reader needs.
- **Display groups.** `base_body.display_group` is an index into `scene.display_group_names`. It is not written as a dataset: a body's display group is the index of the name of the block it is in. Display groups are only relevant for visualisation.
  - **Default** (decision 18), when the user defines no groups: two groups `['Points', 'Others']`; spheres go to `Points` (bodies shown as points), every other shape to `Others`. Both blocks always exist, also when empty.
  - User-defined groups: `export_vtkhdf(..., display_group_names=[...], display_group=...)`. Names without `display_group` put every body in the first group. `display_group` without names is refused with an error: user-defined groups are never labelled `Points` / `Others`.
- **All per-body data in the blocks** (decision of 2 October 2026). Every block carries the same arrays, also an empty block (0 rows). A field is written when it applies to every body or when at least one body has a value. Where a field does not apply to a body, floats are **NaN** and integers (and booleans) are **−1**: for example, the `radius` of a wall, or the `wall_axis` of a sphere.
- **Geometry is stored once.** Body positions are only the block `Points`, in float64.
- **Shapes by name.** `shape_type` is an index into `scene.shape_names`. **Readers must map shapes by name from the file's `shape_names`, never by a fixed index**, because the list will change with the shapes proposal (planes, facets, meshes). The YADE exporter writes the list `sphere, box, polyhedron, clump, wall, facet, other`; `other` marks a shape the format does not support yet.
- **Restart reads the whole file:** the blocks for the bodies, `/ONDEM` for the scene, materials and contacts.
- **Quaternions** are stored scalar first, (w, x, y, z), and the dataset has the attribute `order = "wxyz"`. The identity (no rotation) is (1, 0, 0, 0), and q converts body-frame coordinates to global-frame coordinates: v_global = q v_body q⁻¹ (equivalently, it rotates the global axes onto the body axes). Decided on 2 October 2026 (see `base_state.orientation`). YADE indexes its quaternions as (x, y, z, w), so the YADE mapping reorders them on export and the importer reorders them back.
- **snake_case** for every name in the file. Fields of shapes that are not in the schema yet (`wall_*`, `facet_*`) and the interaction group names are not normative.
- **`normal_force` is positive in traction**, as the schema says. Until 2026-10-02 the YADE exporter wrote it positive in compression. A contact in compression has a negative `normal_force`.

### Per-body fields (all in the blocks)

| Field | Status | Notes |
|---|---|---|
| `position` | schema | the block `Points`, float64 |
| `body_id` | schema | int64 |
| `display_group` | schema | not a dataset: the index of the block's name in `display_group_names` |
| `shape_type` | schema | index into `scene.shape_names`; map by name |
| `material_id`, `clump_id` | schema | `clump_id` is the clump body's `body_id` for a member, −1 otherwise (also for the clump body itself); clump bodies have no material (−1) |
| `velocity`, `angular_velocity` | schema | angular velocity in the global frame |
| `orientation` | schema | (w, x, y, z), attribute `order = "wxyz"` |
| `mass`, `volume` | schema | |
| `inertia` | schema | 3x3, flattened row-major, shape (N, 9) |
| `blocked_dofs` | schema | bitmask: bits 0–2 translations x, y, z, bits 3–5 rotations x, y, z; 0 free, 63 fixed |
| `clump_relative_position`, `clump_relative_orientation` | schema | a member's pose relative to its clump body; NaN for bodies that are not members |
| `temperature`, `liquid_film_volume` | schema | only written if the code provides them |
| `radius` | schema (`sphere`) | NaN for other shapes |
| `dimensions` | schema (`box`) | full edge lengths; NaN for other shapes |
| `wall_axis`, `wall_sense` | not normative | YADE `Wall`; −1 for other shapes; replaced once the schema has a plane shape |
| `facet_vertices`, `facet_normal` | not normative | YADE `Facet`; NaN for other shapes; replaced once the schema has facets/meshes |
| `group_mask`, `is_damped`, `angular_momentum`, `density_scaling` | **provisional** | not decided, see "Open questions" |

`polyhedron.vertices` is not written: its length differs per body, which is part of the shapes proposal.

### Materials (provisional)

`/ONDEM/Materials/<id>/` holds one scalar dataset per field, named as in the schema; the attribute `schema_classes` names the schema class. YADE's `FrictMat` is written as `linear_elastic_frictional_3D` (decision 10). **This mapping is provisional again** (decision 24): the inheritance of some material classes will be reworked with the other codes, so each material group carries the attribute `provisional`.

| Schema field | YADE `FrictMat` |
|---|---|
| `id`, `density` | `id`, `density` |
| `normal_stiffness` | `young` |
| `shear_stiffness` | `young` × `poisson` |
| `shear_friction` | tan(`frictionAngle`) |
| `shear_damping` | 0 (FrictMat has none) |

On import: `young` = `normal_stiffness`, `poisson` = `shear_stiffness` / `normal_stiffness`, `frictionAngle` = atan(`shear_friction`). The importer refuses a missing field and `shear_damping` ≠ 0; there are no default values.

`label`, `material_type` and `yade_poisson` are written as non-normative YADE extras. `yade_poisson` is the exact `poisson`: for about 12 % of value pairs, `young` × `poisson` / `young` comes back 1 ulp off, and contacts formed after a restart would then get a slightly different `ks`. The importer uses `yade_poisson` when present and checks that it agrees with the quotient to round-off.

**Notes, waiting for a discussion with the other codes:**
- `normal_stiffness` and `shear_stiffness` hold a **material stiffness** (YADE's Young's modulus, force per length squared), while the schema text in `materials.py` says force per length. The material carries a material stiffness; the stiffness of each contact is computed from it and from the particles' size and shape, and stays stored per interaction (`kn`, `ks`).
- `shear_damping` is to be removed from `frictional_3D`. Until then, YADE files write 0.

### Restart: what is restored

A file holds everything the importer needs to continue a run from the same state, contact history included. The engines are the exception: they cannot come from the file (see below), so the script creates `O.engines` first, then calls `import_vtkhdf`.

The importer reads and checks the whole file before it creates anything. An unsupported shape, contact type or material, a missing field, or a contact with a body that is not in the file raises an error that lists every problem. The scene is then left untouched; there are no default values.

| What | From | How |
|---|---|---|
| Spheres, walls, boxes | blocks | appended in increasing `body_id` (same ids in an empty scene, otherwise see `id_map`) |
| Body state | blocks | position, velocity, angular velocity, orientation, mass, inertia, blocked DOFs, and the provisional fields |
| Clumps | blocks (shape `clump`, members' `clump_id` and relative poses) | members first, then `O.bodies.clump(members)`; see the note below |
| Materials | `/ONDEM/Materials` | `FrictMat` only, see above |
| Contacts | `/ONDEM/Interactions/<type>/` | every real contact is rebuilt with `utils.createInteraction` and gets its stored history: `normal`, `shear_force`, `normal_force`, `kn`, `ks`, `friction_coefficient`, contact point, reference radii, frictional dissipation |
| `dt`, gravity | `/ONDEM/Scene` | gravity is set on the `NewtonIntegrator` |
| Time, iteration | `/ONDEM/Scene` | carried as offsets, see below |
| Display groups | blocks | returned, so they can be passed back to `export_vtkhdf` |

Contact types that can be restored: `(ScGeom, FrictPhys)`, as used for example by `Law2_ScGeom_FrictPhys_CundallStrack`. Other types raise an error. If the engines create another contact type than the one in the file, the importer stops with an error that says the engines differ.

**Contact normal.** The format stores a contact normal at every timestep (decision 23; the specification does not say which force evaluation it belongs to). *YADE implementation note:* YADE's incremental shear law rotates the shear force from the previous normal to the new one on each step, so the importer writes the stored normal back after creating the contact. Without that, the shear force is off by about 1e-6 relative after one step. With it, a restart without clumps continues **bit-identically**, also for a contact that forms after the restart (`test_restart.py`: difference 0 after 1 and after 2000 steps).

**Clumps.** YADE recomputes a clump's frame (centre of mass, principal axes) and its members' relative positions and orientations from the members' poses when the clump is built; the relative poses cannot be set from Python. The importer keeps the recomputed frame, so members and clump stay consistent, and checks it against the file:
- the centre of mass must agree, and the stored inertia, rotated into the new frame, must be diagonal there (otherwise an error);
- each member's stored relative pose, mapped into the new frame, is compared with the one YADE recomputed. A difference beyond round-off (1e-10 of the clump size, or 1e-10 rad) is a **warning** naming clump and member, returned in `r["clump_warnings"]`; the clump is still built.

Mass, inertia, velocities and angular momentum come from the file. A restart with clumps therefore starts with round-off differences, about 1e-13 relative after one step, which the granular dynamics amplify. **A restart with clumps is not expected to stay identical over a long run.** The acceptance criterion in `test_restart.py` is the restart instant (contacts and restored values exact) and one step (1e-12). The 2000-step comparison of the quiet test packing is printed as information only: about 5e-9 there, and about 1e-5 in a trial run where a sphere hit a clump after the restart.

**Time and iteration.** `O.time` and `O.iter` cannot be set in YADE. The importer stores the offsets (file value minus current value) in `O.tags["ondem_time_offset"]` and `O.tags["ondem_iteration_offset"]`, and the exporter adds them, so the file series continues across a restart (`scene.time`, `scene.iteration`). **Engines that depend on `O.time` or `O.iter` see them start again from zero after a restart**, even though the file series stays continuous: PyRunner `iterPeriod`/`virtPeriod`, time-dependent boundary motion, recorders, anything else that reads `O.time` or `O.iter`. Scripts have to add the offsets themselves (`r["time_offset"]`, `r["iteration_offset"]`).

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

### Open questions

Not decided yet; the provisional fields keep their current names until they are:

1. **Name of the simulation group** (now `ONDEM`; something like "Open Format DEM" or "Simulation").
2. **Shapes: planes (YADE `Wall`), facets, meshes, polyhedra**, with two kinds of files (restart files with full data; light files that link to a reference restart file for the complex geometries, decision 20). A written design proposal is under review before any code.
3. **Contacts in ParaView** (decision 21): a VTKHDF block linked to the interaction data; which points the lines use, and one block or one per interaction type.
4. **Material classes** (decision 24): the inheritance to be made consistent across codes; with it, the dimension of `normal_stiffness` / `shear_stiffness` and removing `shear_damping` from `frictional_3D`.
5. **Still provisional:** collision mask (`group_mask`), `is_damped`, `angular_momentum`, `density_scaling`, frictional dissipation and energy totals, contact geometry fields (`contact_point`, `overlap`, reference radii), the periodic cell.
6. **YADE:** a setter for `O.time` / `O.iter`; setting clump members' relative poses from Python.

Decided and implemented: the quaternion convention, `display_group_names` with the default groups `Points` / `Others`, all per-body data in the blocks (blocked DOFs included), `shape_type` / `shape_names`, `blocked_dofs` as a bitmask, the `clump` shape with the members' relative poses, `scene.iteration`, a contact normal at every timestep. The FrictMat mapping is implemented but provisional.

### Current limits

- **Non-sphere bodies appear as points.** Every body is one point (its position) in its block. Walls, facets, boxes and clump bodies are shown as points until the schema has surface shapes. Contacts are not visible in ParaView yet either: they stay in `/ONDEM/Interactions`.
- The importer restores spheres, walls, boxes and clumps. Facets, polyhedra and other shapes are refused with an error naming the bodies.
- The importer rebuilds `FrictMat` materials and `(ScGeom, FrictPhys)` contacts only.
- A restart with clumps is not bit-identical (see above).
- Files written in the layout before 2 October 2026 (bodies in `/ONDEM/Bodies`) are refused with an error.

### For YADE Users

Use the generated `export_yade_vtkhdf.py` to export data from YADE simulations, and `import_yade_vtkhdf.py` to restart from a file. Both need `hdf5_utils.py` on the Python path.

Example usage in YADE:
```python
from export_yade_vtkhdf import export_vtkhdf

# default display groups: spheres in 'Points', every other shape in 'Others'
export_vtkhdf("output.vtkhdf")

# user-defined display groups (the names are required when display_group is given)
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

- `vtkhdf/testing/test_multiblock_utils.py`: the code-agnostic multiblock helpers, and the NaN / −1 conventions. Needs only `numpy` and `h5py`; if the `vtk` Python package is installed, it also reads the file back with `vtkHDFReader`.
  ```bash
  python3 implementation/vtkhdf/testing/test_multiblock_utils.py
  ```
- `vtkhdf/testing/test_export.py`: full round trip in YADE. 36 spheres settle in a box of 5 walls and a fixed box, with two materials with non-default values (one of them a pair whose `young` × `poisson` / `young` is 1 ulp off). It exports them with display groups (and once with the default groups `Points` / `Others`, and once for a scene of spheres only, where `Others` is empty) and checks the file: `/ONDEM` holds only Scene, Materials and Interactions; every block has the same arrays; shapes by name; NaN / −1 where a field does not apply; `blocked_dofs`; quaternion convention; materials; interactions. It then imports into a reset scene, compares every body and every material field (`young` and `poisson` exactly), runs 1000 steps and exports again. It also checks that a missing material field, `shear_damping` ≠ 0, missing engines, an unsupported contact type, and `display_group` without `display_group_names` are rejected. It prints `TEST PASSED` or `TEST FAILED` (exit code 1). The files are written to the temp directory.
  ```bash
  yadedaily -n -x implementation/vtkhdf/testing/test_export.py
  ```
  On Windows, YADE runs in WSL: `wsl -d Ubuntu-24.04 yadedaily -n -x <path in /mnt/c/...>/test_export.py`.
- `vtkhdf/testing/test_restart.py`: acceptance test for the restart.
  - Run A settles the box, tilts gravity so the contacts carry shear load, exports, and runs 2000 more steps. Run B imports into a fresh scene and runs 2000 steps.
  - At the restart instant the contacts and their restored values must be equal. After 1 step and after 2000 steps, positions, velocities and per-contact normal and shear forces must agree within the stated tolerance.
  - Two scenarios:
    - without clumps, with a sphere that lands after the restart (a new contact whose `ks` comes from the restored materials): the restart must be bit-identical (tolerance 1e-10);
    - with clumps (quiet packing): acceptance at the restart instant and after 1 step (1e-12); the 2000-step comparison is information only; no clump warning on import, and a corrupted relative pose must give one.
  - Negative controls (shear forces zeroed, stored normals ignored) must exceed the tolerance where the criterion is (after 2000 steps without clumps, after 1 step with clumps).
  - Needs 1 OpenMP thread, which is the yadedaily default.
  ```bash
  yadedaily -n -x implementation/vtkhdf/testing/test_restart.py
  ```

### Adapting for Other DEM Codes

To use this framework with another DEM code (e.g., LIGGGHTS, DEMETER, etc.), follow these steps:

1. **Create a Mapping File**: Define a JSON file that maps ON-DEM schema fields to your DEM code's API expressions. Use `yade_mapping.json` as a template.

   - Keys are schema class names (`base_body`, `base_state`, `sphere`, `base_interaction`, ...) holding `field: expression` pairs. If a field is not found under its class, the first class entry with that field name is used.
   - Values are Python expressions that access the data in your DEM code's context: `b` is a body, `i` an interaction, `mat` a material. An expression may return `None` for a body it does not apply to (written as NaN / −1).
   - Keys starting with `_` are not schema classes:
     - `_collections`: expressions for the list of bodies and the list of interactions;
     - `_shape_type`: an expression for the body's shape type in the code, `_shape_groups`: code shape type -> schema shape name, and `_shape_names`: the list written as `scene.shape_names`;
     - `_extra_shapes`: fields of shapes that are not in the schema yet (written as `<shape>_<field>`, e.g. `wall_axis`);
     - `_interaction_type`: an expression for the interaction type (the group name in `/ONDEM/Interactions`, written snake_case);
     - `_material_classes`: the schema classes whose fields (inherited ones included) are written for each material;
     - `_extra_body_fields`: provisional per-body fields that are not decided yet;
     - `_refuse_if`: `{message: expression}`; the exporter raises `ValueError` with the message, and writes no file, when the expression is true (YADE: periodic scenes);
     - `_interaction_geometry`, `_extra_interaction_attributes`, `_extra_material_attributes`: extra fields not in the schema.
   - `display_group`, `display_group_names`, `shape_type` and `shape_names` map to the helpers `_display_group(b)`, `_display_group_names()`, `_shape_type_index(b)` and `_shape_names()`. Keep them as they are.
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
- `codegen_yade.py`: Code generator for YADE (adapt for other codes).
- `yade_mapping.json`: YADE-specific field mappings.
- `hdf5_utils.py`: Code-agnostic HDF5 reading and writing, including the VTKHDF multiblock helpers and the constants `SIMULATION_GROUP` (name of the simulation group) and `QUATERNION_ORDER`.
- `export_yade_vtkhdf.py`: YADE exporter, generated by `codegen_yade.py` (do not edit by hand).
- `import_yade_vtkhdf.py`: YADE importer (restart).
- `testing/test_multiblock_utils.py`, `testing/test_export.py`, `testing/test_restart.py`: tests, see above.
- `testing/test_5spheres.vtkhdf`, `testing/test_box_spheres.vtkhdf`: sample files written by an earlier version of the exporter (old single-block layout).
