"""
import_yade_vtkhdf.py
ON-DEM WG3 - VTKHDF to YADE importer

Reads a .vtkhdf file written by export_yade_vtkhdf.py and reconstructs the
YADE simulation state. Restart reads the whole file: the VTKHDF blocks (body
positions and the block fields) and /ONDEM (everything else), joined on
body_id.

Create O.engines before importing: engines cannot come from the file.

Restored:
  - Scene metadata  (dt, gravity; time is only printed, O.time is read-only)
  - Materials       (FrictMat from /ONDEM/Materials/)
  - Spheres         (blocks + /ONDEM/Bodies/sphere/)
  - Walls           (blocks + /ONDEM/Bodies/wall/)
  - Contacts        (/ONDEM/Interactions/: every real contact is rebuilt with
                     utils.createInteraction and gets its stored history:
                     normal, shear force, stiffnesses, friction)
  - Display groups  (returned, so they can be passed back to export_vtkhdf)
Refused (ValueError, nothing is created):
  - Shapes other than spheres and walls, clumps.
  - Contact types other than (ScGeom, FrictPhys).

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
    Interactions/<type>/         id1, id2, normal, normal_force, shear_force, kn, ks,
                                 friction_coefficient, geom_type, phys_type, ...

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

from hdf5_utils import vtkhdf_read_blocks, ondem_read_bodies, ondem_read_interactions


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


# ---------------------------------------------------------------------------
# Reading and checking the file (nothing is created in the scene here)
# ---------------------------------------------------------------------------

# Material fields a FrictMat needs (provisional mapping, see implementation/README.md):
# base_material.id, density; hertz_elastic.young_modulus, poisson_ratio;
# frictional_3D.shear_friction = tan(frictionAngle)
_FRICTMAT_FIELDS = ["id", "density", "young_modulus", "poisson_ratio", "shear_friction"]


def _read_materials(f):
    """
    Read /ONDEM/Materials/<id>/ groups.
    Returns {stored material id: keyword arguments of FrictMat}.

    Every field of _FRICTMAT_FIELDS must be present; there are no defaults.
    Raises ValueError naming the material and the missing fields, or if the
    material is not a FrictMat.
    """
    out = {}
    for key, g in f["ONDEM/Materials"].items():
        mtype = g["material_type"][()].decode() if "material_type" in g else None
        if mtype != "FrictMat":
            raise ValueError(f"[import] /ONDEM/Materials/{key}: material_type {mtype!r} is not supported "
                             f"(this importer only rebuilds FrictMat)")
        missing = [k for k in _FRICTMAT_FIELDS if k not in g]
        if missing:
            raise ValueError(f"[import] /ONDEM/Materials/{key}: missing field(s) {missing}; "
                             f"a FrictMat needs {_FRICTMAT_FIELDS}")
        out[int(g["id"][()])] = dict(
            density       = float(g["density"][()]),
            young         = float(g["young_modulus"][()]),
            poisson       = float(g["poisson_ratio"][()]),
            frictionAngle = float(np.arctan(float(g["shear_friction"][()]))),
            label         = g["label"][()].decode() if "label" in g else "",
        )
    return out


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


def _check_engines(restore_gravity):
    """Engines cannot come from the file: they must exist before the import."""
    names = [type(e).__name__ for e in O.engines]
    missing = []
    if "InteractionLoop" not in names:
        missing.append("InteractionLoop (contacts are rebuilt with its functors)")
    if restore_gravity and "NewtonIntegrator" not in names:
        missing.append("NewtonIntegrator (gravity is restored on it)")
    if missing:
        raise RuntimeError("[import] create O.engines before import_vtkhdf; engines cannot come from the file. "
                           "Missing: " + "; ".join(missing))


def _short(ids, n=20):
    ids = sorted(ids)
    return f"{ids[:n]}" + (f" (and {len(ids) - n} more)" if len(ids) > n else "")


def _check_file(bodies, materials, interactions):
    """Collect every reason why the file cannot be restored; raise them all at once."""
    errors = []

    unsupported = {}
    for bid, rec in bodies.items():
        if rec["shape_group"] not in _MAKERS:
            unsupported.setdefault(rec["shape_group"], []).append(bid)
    for sg, ids in sorted(unsupported.items()):
        errors.append(f"shape group '{sg}' is not supported by this importer: body_id {_short(ids)}")

    clumped = [bid for bid, rec in bodies.items() if int(rec.get("clump_id", -1)) >= 0]
    if clumped:
        errors.append(f"clumps are not rebuilt by this importer: body_id {_short(clumped)}")

    no_mat = [bid for bid, rec in bodies.items() if int(rec.get("material_id", -1)) not in materials]
    if no_mat:
        errors.append(f"material_id not found in /ONDEM/Materials: body_id {_short(no_mat)}")

    bad_types, bad_ids, missing, virtual = {}, [], {}, 0
    for rec in interactions:
        key = (str(rec.get("geom_type", "?")), str(rec.get("phys_type", "?")))
        if key not in _CONTACT_TYPES:
            bad_types[key] = bad_types.get(key, 0) + 1
            continue
        if int(rec["id1"]) not in bodies or int(rec["id2"]) not in bodies:
            bad_ids.append((int(rec["id1"]), int(rec["id2"])))
        lacking = tuple(k for k in _CONTACT_TYPES[key][0] if k not in rec)
        if lacking:
            missing[lacking] = missing.get(lacking, 0) + 1
        if int(rec.get("virtual", 0)):
            virtual += 1
    for (gt, pt), n in sorted(bad_types.items()):
        errors.append(f"{n} interaction(s) of contact type ({gt}, {pt}) cannot be restored; "
                      f"supported: {sorted(_CONTACT_TYPES)}")
    if bad_ids:
        errors.append(f"{len(bad_ids)} interaction(s) refer to bodies that are not in the file: {bad_ids[:10]}")
    for lacking, n in missing.items():
        errors.append(f"{n} interaction(s) lack the field(s) {list(lacking)}")
    if virtual:
        errors.append(f"{virtual} virtual (not real) interaction(s): only real contacts can be restored")

    if errors:
        raise ValueError("[import] the file cannot be restored, nothing was created:\n  - " + "\n  - ".join(errors))


# ---------------------------------------------------------------------------
# Building the scene
# ---------------------------------------------------------------------------

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


def _restore_frict(i, rec):
    """Contact history of a ScGeom + FrictPhys contact (e.g. Law2_ScGeom_FrictPhys_CundallStrack).

    The normal is history too: on the next step the shear force is rotated
    from this normal to the new one.
    """
    n = _v3(rec["normal"])
    i.geom.normal = n
    if "contact_point" in rec:
        i.geom.contactPoint = _v3(rec["contact_point"])
    if "reference_radius_1" in rec:
        i.geom.refR1 = float(rec["reference_radius_1"])
    if "reference_radius_2" in rec:
        i.geom.refR2 = float(rec["reference_radius_2"])
    i.phys.kn = float(rec["kn"])
    i.phys.ks = float(rec["ks"])
    i.phys.tangensOfFrictionAngle = float(rec["friction_coefficient"])
    i.phys.shearForce = _v3(rec["shear_force"])
    # normal_force is positive in traction: the force vector is -normal_force * normal
    i.phys.normalForce = n * (-float(rec["normal_force"]))
    if "frictional_dissipation" in rec:
        i.phys.frictDissip = float(rec["frictional_dissipation"])


# Contact types this importer can restore: (geom type, phys type) -> (required fields, restorer)
_CONTACT_TYPES = {
    ("ScGeom", "FrictPhys"): (["normal", "normal_force", "shear_force", "kn", "ks", "friction_coefficient"],
                              _restore_frict),
}


def _restore_interactions(interactions, id_map):
    for rec in interactions:
        key = (str(rec["geom_type"]), str(rec["phys_type"]))
        id1, id2 = id_map[int(rec["id1"])], id_map[int(rec["id2"])]
        i = utils.createInteraction(id1, id2)
        got = (type(i.geom).__name__, type(i.phys).__name__)
        if got != key:
            raise ValueError(f"[import] the engines create contact type {got} for bodies ({id1}, {id2}), "
                             f"the file has {key}: the engines differ from the ones that wrote the file "
                             f"(the scene is partially built; call O.reset())")
        _CONTACT_TYPES[key][1](i, rec)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def import_vtkhdf(filename,
                  restore_time=True,
                  restore_dt=True,
                  restore_gravity=True,
                  restore_interactions=True):
    """
    Load a VTKHDF file into the current YADE scene.

    Create O.engines first: engines cannot come from the file, contacts are
    rebuilt with the functors of the InteractionLoop, and gravity is set on
    the NewtonIntegrator.

    Parameters
    ----------
    filename             : str   Path to the .vtkhdf file.
    restore_time         : bool  Print the saved time (O.time is read-only in YADE).
    restore_dt           : bool  Set O.dt from the file (default True).
    restore_gravity      : bool  Set gravity on the NewtonIntegrator (default True).
    restore_interactions : bool  Rebuild every contact of /ONDEM/Interactions with its
                                 stored history (default True). False: contacts are
                                 rebuilt by the collider on the first step, without history.

    The whole file is read and checked before anything is created: an
    unsupported shape, contact type, missing field or missing material raises
    ValueError and leaves the scene untouched.

    Bodies are appended in increasing stored body_id. Into an empty scene,
    with ids 0..N-1 in the file, YADE gives them the same ids; otherwise
    "id_map" says where each body went.

    Returns
    -------
    dict with keys:
        'sphere_ids'          – YADE body ids of the restored spheres
        'wall_ids'            – YADE body ids of the restored walls
        'interaction_count'   – number of contacts rebuilt with their history
        'id_map'              – {stored body_id -> YADE body id}
        'mat_id_map'          – {stored material id -> O.materials index}
        'display_group_names' – scene.display_group_names from the file
        'display_group'       – {YADE body id -> display group index}
    """
    print(f"[import] Reading '{filename}' ...")
    _check_engines(restore_gravity)

    with h5py.File(filename, "r") as f:
        time, dt, gravity, names = _read_scene(f)
        materials    = _read_materials(f)
        bodies       = _read_bodies(f, names)
        interactions = ondem_read_interactions(f) if restore_interactions else []

    _check_file(bodies, materials, interactions)

    # --- from here on the scene is modified ---
    if restore_time:
        # O.time and O.iter are both read-only in YADE (computed properties).
        print(f"[import] Note: saved time={time:.6g} s — O.time is read-only in YADE, resuming from iter=0.")
    if restore_dt:
        O.dt = dt
        print(f"[import] O.dt    = {dt}")
    if restore_gravity:
        for eng in O.engines:
            if type(eng).__name__ == "NewtonIntegrator":
                eng.gravity = gravity
        print(f"[import] gravity = {gravity}")

    mat_id_map = {}
    for mid, kw in materials.items():
        mat_id_map[mid] = O.materials.append(FrictMat(**kw))
        print(f"[import] Material id={mid} → O.materials[{mat_id_map[mid]}]  label='{kw['label']}'")

    sphere_ids, wall_ids = [], []
    id_map, display_group = {}, {}
    for bid in sorted(bodies):
        rec = bodies[bid]
        sg = rec["shape_group"]
        b = _MAKERS[sg](rec, mat_id_map[int(rec["material_id"])])
        new_id = O.bodies.append(b)
        id_map[bid] = new_id
        display_group[new_id] = rec["display_group"]
        (sphere_ids if sg == "sphere" else wall_ids).append(new_id)

    _restore_interactions(interactions, id_map)

    moved = {s: n for s, n in id_map.items() if s != n}
    if moved:
        print(f"[import] Note: {len(moved)} body id(s) changed (scene not empty or ids not contiguous); see 'id_map'.")

    print(f"[import] Done. {len(sphere_ids)} sphere(s), {len(wall_ids)} wall(s) "
          f"in {len(names)} display group(s) {names}, {len(interactions)} contact(s) with history "
          f"→ {len(O.bodies)} total bodies in scene.")

    return {
        "sphere_ids"          : sphere_ids,
        "wall_ids"            : wall_ids,
        "interaction_count"   : len(interactions),
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
