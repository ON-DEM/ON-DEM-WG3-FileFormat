"""
import_yade_vtkhdf.py
ON-DEM WG3 - VTKHDF to YADE importer

Reads a .vtkhdf file written by export_yade_vtkhdf.py and reconstructs the
YADE simulation state. Restart reads the whole file: the VTKHDF blocks (body
positions and the block fields) and /ONDEM (everything else), joined on
body_id.

Restored:
  - Scene metadata  (dt, gravity; time is only printed, O.time is read-only)
  - Materials       (FrictMat from /ONDEM/Materials/)
  - Spheres         (blocks + /ONDEM/Bodies/sphere/)
  - Walls           (blocks + /ONDEM/Bodies/wall/)
  - Display groups  (returned, so they can be passed back to export_vtkhdf)
Not restored:
  - Interactions: YADE rebuilds contacts with the collider on the first
    step, so the contact history (shear force, sliding state) is lost.
  - Boxes, facets, polyhedra and other shapes (reported as skipped).
  - Clumps (clump_id is read but clumps are not rebuilt).

File layout expected (written by the exporter):
  /VTKHDF/                       MultiBlockDataSet
    <group name>/                one PolyData block per display group
      Points            (N,3)    body positions, float64
      PointData/
        body_id         (N,)     int64, joins the block to /ONDEM
        radius          (N,)     NaN for non-spheres
        velocity        (N,3)
        angular_velocity (N,3)
        orientation     (N,4)    [w, x, y, z], attribute order = "wxyz"
    Assembly/<group name>        soft link -> /VTKHDF/<group name>
  /ONDEM/
    Scene/                       attrs: time, timestep; datasets: gravity,
                                 units, display_group_names
    Materials/<id>/              scalar datasets per material
    Bodies/<shape group>/        body_id + the fields not in the blocks
                                 (material_id, clump_id, mass, inertia, volume,
                                 wall axis/sense, ...)
    Interactions/<type>/         not used for import

A body's display group is the index of its block's name in
display_group_names.

Quaternion convention
---------------------
The file stores [w, x, y, z] (dataset attribute order = "wxyz"), identity
(1, 0, 0, 0), v_global = q v_body q^-1 (provisional, to be confirmed by Bruno).
YADE (minieigen) indexes a quaternion as q[0..3] = (x, y, z, w); the mapping
reorders on export. Its constructor takes Quaternion(w, x, y, z), so this
importer builds:  stored [w,x,y,z] → Quaternion(w, x, y, z).

Usage
-----
Inside a YADE script:

    from import_yade_vtkhdf import import_vtkhdf
    r = import_vtkhdf("sim_0000.vtkhdf")
    O.run(10000, wait=True)
    # write the next file with the same display groups
    export_vtkhdf("sim_0001.vtkhdf", r["display_group_names"], r["display_group"])

Standalone (YADE Python):

    yade import_yade_vtkhdf.py -- sim_0000.vtkhdf
"""

import sys
import numpy as np

try:
    import h5py
except ImportError:
    raise ImportError(
        "h5py is required.  Install with:  pip install h5py\n"
        "or:  apt install python3-h5py"
    )

from yade import O, utils, Vector3, Quaternion, FrictMat

from hdf5_utils import vtkhdf_read_blocks, ondem_read_bodies


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _v3(arr):
    """Convert a length-3 array-like to a YADE Vector3."""
    return Vector3(float(arr[0]), float(arr[1]), float(arr[2]))


def _read_scene(f):
    """Return (time, dt, gravity_Vector3, display_group_names) from /ONDEM/Scene."""
    sc = f["ONDEM/Scene"]
    time    = float(sc.attrs["time"])
    dt      = float(sc.attrs["timestep"])
    grav    = sc["gravity"][:]           # shape (3,)
    if "display_group_names" in sc:
        names = [str(n) for n in sc["display_group_names"].asstr()[:]]
    else:
        names = ["all"]                  # schema default
    return time, dt, _v3(grav), names


# Material fields a FrictMat needs (provisional mapping, see implementation/README.md):
# base_material.id, density; hertz_elastic.young_modulus, poisson_ratio;
# frictional_3D.shear_friction = tan(frictionAngle)
_FRICTMAT_FIELDS = ["id", "density", "young_modulus", "poisson_ratio", "shear_friction"]


def _read_materials(f):
    """
    Reconstruct YADE materials from /ONDEM/Materials/<id>/ groups.
    Returns a dict  {stored_mat_id (int) -> yade_material_index}.

    Every field of _FRICTMAT_FIELDS must be present; there are no defaults.
    Raises ValueError naming the material and the missing fields, or if the
    material is not a FrictMat.
    """
    mat_grp = f["ONDEM/Materials"]
    id_map  = {}   # stored id -> O.materials index

    for key in mat_grp:
        g   = mat_grp[key]
        mtype = g["material_type"][()].decode() if "material_type" in g else None
        if mtype != "FrictMat":
            raise ValueError(f"[import] /ONDEM/Materials/{key}: material_type {mtype!r} is not supported "
                             f"(this importer only rebuilds FrictMat)")
        missing = [k for k in _FRICTMAT_FIELDS if k not in g]
        if missing:
            raise ValueError(f"[import] /ONDEM/Materials/{key}: missing field(s) {missing}; "
                             f"a FrictMat needs {_FRICTMAT_FIELDS}")

        mid      = int(g["id"][()])
        density  = float(g["density"][()])
        young    = float(g["young_modulus"][()])
        poisson  = float(g["poisson_ratio"][()])
        fric_rad = float(np.arctan(float(g["shear_friction"][()])))
        label    = g["label"][()].decode()     if "label"    in g else ""

        yade_idx = O.materials.append(
            FrictMat(
                density       = density,
                young         = young,
                poisson       = poisson,
                frictionAngle = fric_rad,
                label         = label,
            )
        )
        id_map[mid] = yade_idx
        print(f"[import] Material id={mid} → O.materials[{yade_idx}]  label='{label}'")

    return id_map


def _read_bodies(f, names):
    """
    Join the VTKHDF blocks and /ONDEM/Bodies on body_id.
    Returns {body_id: record} with the fields of both parts, plus
    "display_group" (index of the block's name in names) and "shape_group".
    """
    blocks = vtkhdf_read_blocks(f, names)
    ondem  = ondem_read_bodies(f)

    only_blocks = sorted(set(blocks) - set(ondem))
    only_ondem  = sorted(set(ondem) - set(blocks))
    if only_blocks or only_ondem:
        raise ValueError(
            "[import] /VTKHDF blocks and /ONDEM/Bodies do not hold the same bodies: "
            f"only in blocks: {only_blocks[:20]}, only in /ONDEM: {only_ondem[:20]}")

    group_index = {name: i for i, name in enumerate(names)}
    bodies = {}
    for bid, rec in blocks.items():
        merged = dict(ondem[bid])
        merged.update(rec)
        merged["display_group"] = group_index[rec["block"]]
        bodies[bid] = merged
    return bodies


def _set_state(b, rec):
    """Set the dynamic state of YADE body b from a joined record."""
    if "velocity" in rec:
        b.state.vel = _v3(rec["velocity"])
    if "angular_velocity" in rec:
        b.state.angVel = _v3(rec["angular_velocity"])
    if "orientation" in rec:
        # stored [w, x, y, z]; YADE constructor Quaternion(w, x, y, z)
        qw, qx, qy, qz = (float(v) for v in rec["orientation"])
        b.state.ori = Quaternion(qw, qx, qy, qz)


def _make_sphere(rec, yade_mat):
    b = utils.sphere(center=_v3(rec["position"]), radius=float(rec["radius"]), material=yade_mat)
    _set_state(b, rec)
    # mass (override the value computed by utils.sphere)
    m = float(rec.get("mass", 0.0))
    if m > 0.0:
        b.state.mass = m
    # inertia: stored as a flattened 3x3 matrix, YADE keeps the diagonal
    if "inertia" in rec:
        I = rec["inertia"]
        if float(I[0]) > 0.0:
            b.state.inertia = Vector3(float(I[0]), float(I[4]), float(I[8]))
    return b


def _make_wall(rec, yade_mat):
    axis = int(rec["axis"])
    b = utils.wall(position=float(rec["position"][axis]), axis=axis,
                   sense=int(rec["sense"]), material=yade_mat)
    _set_state(b, rec)
    return b


_MAKERS = {"sphere": _make_sphere, "wall": _make_wall}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def import_vtkhdf(filename,
                  restore_time=True,
                  restore_dt=True,
                  restore_gravity=True):
    """
    Load a VTKHDF file into the current YADE scene.

    Parameters
    ----------
    filename        : str   Path to the .vtkhdf file.
    restore_time    : bool  Print the saved time (O.time is read-only in YADE).
    restore_dt      : bool  Set O.dt   from the file (default True).
    restore_gravity : bool  Set gravity on NewtonIntegrator (default True).
                            Only works if a NewtonIntegrator already exists
                            in O.engines.

    Bodies are appended in increasing stored body_id. Into an empty scene,
    with ids 0..N-1 in the file and every shape supported, YADE gives them
    the same ids; otherwise "id_map" says where each body went.

    Returns
    -------
    dict with keys:
        'sphere_ids'          – YADE body ids of the restored spheres
        'wall_ids'            – YADE body ids of the restored walls
        'skipped_ids'         – stored body ids not restored (unsupported shape)
        'id_map'              – {stored body_id -> YADE body id}
        'mat_id_map'          – {stored material id -> O.materials index}
        'display_group_names' – scene.display_group_names from the file
        'display_group'       – {YADE body id -> display group index}
    """
    print(f"[import] Reading '{filename}' ...")

    with h5py.File(filename, "r") as f:

        # 1. Scene metadata
        time, dt, gravity, names = _read_scene(f)

        if restore_time:
            # O.time and O.iter are both read-only in YADE (computed properties).
            # Print the saved value for reference only.
            print(f"[import] Note: saved time={time:.6g} s — O.time is read-only in YADE, resuming from iter=0.")

        if restore_dt:
            O.dt = dt
            print(f"[import] O.dt    = {dt}")

        if restore_gravity:
            for eng in O.engines:
                if type(eng).__name__ == "NewtonIntegrator":
                    eng.gravity = gravity
                    print(f"[import] gravity = {gravity}")
                    break
            else:
                print("[import] Warning: no NewtonIntegrator found — gravity not restored.")

        # 2. Materials
        mat_id_map = _read_materials(f)

        # 3. Bodies: blocks + /ONDEM joined on body_id
        bodies = _read_bodies(f, names)

    sphere_ids, wall_ids, skipped = [], [], {}
    id_map, display_group = {}, {}
    for bid in sorted(bodies):
        rec = bodies[bid]
        sg = rec["shape_group"]
        make = _MAKERS.get(sg)
        if make is None:
            skipped.setdefault(sg, []).append(bid)
            continue
        yade_mat = mat_id_map.get(int(rec.get("material_id", -1)), 0)
        b = make(rec, yade_mat)
        new_id = O.bodies.append(b)
        id_map[bid] = new_id
        display_group[new_id] = rec["display_group"]
        (sphere_ids if sg == "sphere" else wall_ids).append(new_id)

    for sg, ids in skipped.items():
        print(f"[import] Warning: {len(ids)} body(ies) of shape group '{sg}' not restored "
              f"(not supported by this importer): body_id {ids[:20]}")
    clumped = [bid for bid, rec in bodies.items() if int(rec.get("clump_id", -1)) >= 0]
    if clumped:
        print(f"[import] Warning: {len(clumped)} body(ies) belong to clumps; clumps are not rebuilt.")
    moved = {s: n for s, n in id_map.items() if s != n}
    if moved:
        print(f"[import] Note: {len(moved)} body id(s) changed (scene not empty or ids not contiguous); see 'id_map'.")

    print(f"[import] Done. {len(sphere_ids)} sphere(s), {len(wall_ids)} wall(s) "
          f"in {len(names)} display group(s) {names} → {len(O.bodies)} total bodies in scene.")

    return {
        "sphere_ids"          : sphere_ids,
        "wall_ids"            : wall_ids,
        "skipped_ids"         : sorted(i for ids in skipped.values() for i in ids),
        "id_map"              : id_map,
        "mat_id_map"          : mat_id_map,
        "display_group_names" : names,
        "display_group"       : display_group,
    }


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from yade import (ForceResetter, InsertionSortCollider, Bo1_Sphere_Aabb, Bo1_Wall_Aabb,
                      InteractionLoop, Ig2_Sphere_Sphere_ScGeom, Ig2_Wall_Sphere_ScGeom,
                      Ip2_FrictMat_FrictMat_FrictPhys, Law2_ScGeom_FrictPhys_CundallStrack,
                      NewtonIntegrator)

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print("Usage:  yade import_yade_vtkhdf.py -- <file.vtkhdf>")
        sys.exit(1)

    vtkhdf_file = args[0]

    # ------------------------------------------------------------------ #
    # Minimal engine setup — must exist before import so gravity can be   #
    # written to the NewtonIntegrator.  Adjust contact law as needed.     #
    # ------------------------------------------------------------------ #
    O.engines = [
        ForceResetter(),
        InsertionSortCollider([Bo1_Sphere_Aabb(), Bo1_Wall_Aabb()]),
        InteractionLoop(
            [Ig2_Sphere_Sphere_ScGeom(), Ig2_Wall_Sphere_ScGeom()],
            [Ip2_FrictMat_FrictMat_FrictPhys()],
            [Law2_ScGeom_FrictPhys_CundallStrack()],
        ),
        NewtonIntegrator(gravity=(0, 0, -9.81), damping=0.3),
    ]

    result = import_vtkhdf(vtkhdf_file)

    print(f"\nScene ready: {len(O.bodies)} bodies, O.dt={O.dt:.3g}, O.time={O.time:.6g}")
    print("Call O.run(N) or open the YADE GUI to continue the simulation.")
