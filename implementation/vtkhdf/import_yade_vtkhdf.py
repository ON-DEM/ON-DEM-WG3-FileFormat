"""
import_yade_vtkhdf.py
ON-DEM WG3 - VTKHDF to YADE importer

Reads a .vtkhdf file written by export_yade_vtkhdf.py and reconstructs the
YADE simulation state. Restart reads the whole file: the VTKHDF blocks (body
positions and every per-body field) and the simulation group /<SIM> (scene,
materials, interactions; SIM = hdf5_utils.SIMULATION_GROUP).

Create O.engines before importing: engines cannot come from the file.

Restored:
  - Scene metadata  (dt, gravity; time is only printed, O.time is read-only)
  - Materials       (FrictMat from /<SIM>/Materials/)
  - Spheres, walls, boxes (blocks)
  - Clumps          (members restored first, then O.bodies.clump; the frame YADE
                     recomputes is checked against the file, see _make_clump)
  - Contacts        (/<SIM>/Interactions/: every real contact is rebuilt with
                     utils.createInteraction and gets its stored history:
                     normal, shear force, stiffnesses, friction)
  - Display groups  (returned, so they can be passed back to export_vtkhdf)
Refused (ValueError, nothing is created):
  - Shapes other than spheres, walls, boxes and clumps.
  - Contact types other than (ScGeom, FrictPhys).

File layout expected (written by the exporter):
  /VTKHDF/                       MultiBlockDataSet
    <group name>/                one PolyData block per display group
      Points            (N,3)    body positions, float64
      PointData/                 every per-body field (NaN / -1 where it does not apply)
        body_id         (N,)     int64; interactions refer to bodies through it
        shape_type      (N,)     index into scene shape_names
        material_id, clump_id, velocity, angular_velocity, mass, inertia,
        volume, blocked_dofs, radius, dimensions, clump_relative_position,
        clump_relative_orientation, wall_axis, wall_sense, facet_vertices, ...
        orientation     (N,4)    [w, x, y, z], attribute order = "wxyz"
    Assembly/<group name>        soft link -> /VTKHDF/<group name>
  /<SIM>/                        the simulation group, hdf5_utils.SIMULATION_GROUP
    Scene/                       attrs: time, timestep, iteration; datasets:
                                 gravity, units, display_group_names, shape_names
    Materials/<id>/              scalar datasets per material
    Interactions/<type>/         id1, id2, normal, normal_force, shear_force, kn, ks,
                                 friction_coefficient, geom_type, phys_type, ...

Shapes are mapped by name through shape_names, never by a fixed index.

A body's display group is the index of its block's name in
display_group_names.

Quaternion convention
---------------------
The file stores [w, x, y, z] (dataset attribute order = "wxyz"), identity
(1, 0, 0, 0), v_global = q v_body q^-1.
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

from hdf5_utils import vtkhdf_read_blocks, ondem_read_interactions, SIMULATION_GROUP

SIM = SIMULATION_GROUP      # top-level simulation group, "ONDEM" until it is renamed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _v3(arr):
    """Convert a length-3 array-like to a YADE Vector3."""
    return Vector3(float(arr[0]), float(arr[1]), float(arr[2]))


def _read_scene(f):
    """Return (time, iteration, dt, gravity_Vector3, display_group_names, shape_names)
    from /<SIM>/Scene. iteration is optional (default 0); shape_names is mandatory."""
    sc = f[f"{SIM}/Scene"]
    time    = float(sc.attrs["time"])
    iteration = int(sc.attrs["iteration"]) if "iteration" in sc.attrs else 0
    dt      = float(sc.attrs["timestep"])
    grav    = sc["gravity"][:]           # shape (3,)
    if "display_group_names" in sc:
        names = [str(n) for n in sc["display_group_names"].asstr()[:]]
    else:
        names = ["Points", "Others"]     # schema default (decision 18)
    if "shape_names" not in sc:
        raise ValueError(f"[import] /{SIM}/Scene has no shape_names: the file was written in the layout "
                         f"before 2 October 2026 (bodies in /{SIM}/Bodies), which this importer does not read")
    shape_names = [str(n) for n in sc["shape_names"].asstr()[:]]
    return time, iteration, dt, _v3(grav), names, shape_names


# ---------------------------------------------------------------------------
# Reading and checking the file (nothing is created in the scene here)
# ---------------------------------------------------------------------------

# FrictMat <-> linear_elastic_frictional_3D (decision 10 of 2 October 2026):
#   normal_stiffness = young, shear_stiffness = young * poisson,
#   shear_friction = tan(frictionAngle), shear_damping = 0 (FrictMat has none).
# The stiffnesses hold a material stiffness (YADE's Young's modulus), not a
# force per length as the schema text says; see implementation/README.md.
_FRICTMAT_FIELDS = ["id", "density", "normal_stiffness", "shear_stiffness", "shear_friction", "shear_damping"]


def _read_materials(f):
    """
    Read /<SIM>/Materials/<id>/ groups.
    Returns {stored material id: keyword arguments of FrictMat}.

    Every field of _FRICTMAT_FIELDS must be present; there are no defaults.
    young = normal_stiffness, poisson = shear_stiffness / normal_stiffness,
    frictionAngle = atan(shear_friction). The YADE extra yade_poisson, when
    present, gives poisson exactly (the quotient can be 1 ulp off); it must
    agree with the quotient to round-off. Raises ValueError naming the material
    and the problem: missing fields, a non-FrictMat material, shear_damping != 0
    (FrictMat cannot represent it), or an inconsistent yade_poisson.
    """
    out = {}
    for key, g in f[f"{SIM}/Materials"].items():
        where = f"[import] /{SIM}/Materials/{key}"
        mtype = g["material_type"][()].decode() if "material_type" in g else None
        if mtype != "FrictMat":
            raise ValueError(f"{where}: material_type {mtype!r} is not supported "
                             f"(this importer only rebuilds FrictMat)")
        missing = [k for k in _FRICTMAT_FIELDS if k not in g]
        if missing:
            raise ValueError(f"{where}: missing field(s) {missing}; a FrictMat needs {_FRICTMAT_FIELDS}")
        kn = float(g["normal_stiffness"][()])
        ks = float(g["shear_stiffness"][()])
        damping = float(g["shear_damping"][()])
        if damping != 0.0:
            raise ValueError(f"{where}: shear_damping = {damping!r}; FrictMat has no shear damping")
        poisson = ks / kn
        if "yade_poisson" in g:
            exact = float(g["yade_poisson"][()])
            if abs(exact - poisson) > 4 * np.finfo(float).eps * abs(poisson):
                raise ValueError(f"{where}: yade_poisson {exact!r} disagrees with "
                                 f"shear_stiffness / normal_stiffness = {poisson!r}")
            poisson = exact
        out[int(g["id"][()])] = dict(
            density       = float(g["density"][()]),
            young         = kn,
            poisson       = poisson,
            frictionAngle = float(np.arctan(float(g["shear_friction"][()]))),
            label         = g["label"][()].decode() if "label" in g else "",
        )
    return out


def _read_bodies(f, names, shape_names):
    """
    Read the bodies from the VTKHDF blocks (every per-body field is there).
    Returns {body_id: record} with the PointData fields, "position", plus
    "display_group" (index of the block's name in names) and "shape_group"
    (the shape name, looked up by name through shape_names).
    """
    blocks = vtkhdf_read_blocks(f, names)
    group_index = {name: i for i, name in enumerate(names)}
    bodies = {}
    bad = []
    for bid, rec in blocks.items():
        st = int(rec.get("shape_type", -1))
        if not 0 <= st < len(shape_names):
            bad.append(bid)
            continue
        rec["shape_group"] = shape_names[st]
        rec["display_group"] = group_index[rec["block"]]
        bodies[bid] = rec
    if bad:
        raise ValueError(f"[import] shape_type missing or not an index into shape_names {shape_names}: "
                         f"body_id {sorted(bad)[:20]}")
    return bodies


def _given(v):
    """False for values that do not apply to a body: NaN (floats), -1 (integers)."""
    arr = np.asarray(v)
    if np.issubdtype(arr.dtype, np.integer):
        return bool(np.all(arr != -1))
    return not bool(np.any(np.isnan(arr.astype(float))))


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
        if rec["shape_group"] not in _MAKERS and rec["shape_group"] != "clump":
            unsupported.setdefault(rec["shape_group"], []).append(bid)
    for sg, ids in sorted(unsupported.items()):
        errors.append(f"shape group '{sg}' is not supported by this importer: body_id {_short(ids)}")

    clumps = {bid for bid, rec in bodies.items() if rec["shape_group"] == "clump"}
    orphans = [bid for bid, rec in bodies.items()
               if int(rec.get("clump_id", -1)) >= 0 and int(rec["clump_id"]) not in clumps and bid not in clumps]
    if orphans:
        errors.append(f"clump members whose clump body is not in the file: body_id {_short(orphans)}")
    members = {c: _clump_members(bodies, c) for c in clumps}
    empty = [c for c, m in members.items() if not m]
    if empty:
        errors.append(f"clump bodies without members: body_id {_short(empty)}")
    nested = [m for ms in members.values() for m in ms if bodies[m]["shape_group"] == "clump"]
    if nested:
        errors.append(f"clumps inside clumps are not supported: body_id {_short(nested)}")

    # clump bodies have no material in YADE
    no_mat = [bid for bid, rec in bodies.items()
              if rec["shape_group"] != "clump" and int(rec.get("material_id", -1)) not in materials]
    if no_mat:
        errors.append(f"material_id not found in /{SIM}/Materials: body_id {_short(no_mat)}")

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


def _blocked_dofs_string(mask):
    """base_state.blocked_dofs bitmask (bits 0-2 translations, 3-5 rotations)
    -> YADE blockedDOFs string, e.g. 7 -> "xyz", 63 -> "xyzXYZ"."""
    return "".join(c for k, c in enumerate("xyzXYZ") if (int(mask) >> k) & 1)


def _set_extras(b, rec):
    """blocked_dofs (schema) and the provisional per-body fields (collision mask,
    damping flag, angular momentum, density scaling; not decided, see
    implementation/README.md). Absent or not applicable (-1, NaN): YADE defaults stay."""
    if "blocked_dofs" in rec and _given(rec["blocked_dofs"]):
        b.state.blockedDOFs = _blocked_dofs_string(rec["blocked_dofs"])
    if "group_mask" in rec and _given(rec["group_mask"]):
        b.groupMask = int(rec["group_mask"])
    if "is_damped" in rec and _given(rec["is_damped"]):
        b.state.isDamped = bool(rec["is_damped"])
    if "angular_momentum" in rec and _given(rec["angular_momentum"]):
        b.state.angMom = _v3(rec["angular_momentum"])
    if "density_scaling" in rec and _given(rec["density_scaling"]):
        b.state.densityScaling = float(rec["density_scaling"])


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
    axis = int(rec["wall_axis"])
    b = utils.wall(position=float(rec["position"][axis]), axis=axis,
                   sense=int(rec["wall_sense"]), material=yade_mat)
    _set_state(b, rec)
    return b


def _make_box(rec, yade_mat):
    d = rec["dimensions"]                   # full edge lengths; YADE takes half extents
    b = utils.box(center=_v3(rec["position"]),
                  extents=Vector3(float(d[0]) / 2, float(d[1]) / 2, float(d[2]) / 2),
                  material=yade_mat)
    _set_state(b, rec)
    b.state.mass = float(rec["mass"])
    I = rec["inertia"]
    b.state.inertia = Vector3(float(I[0]), float(I[4]), float(I[8]))
    return b


_MAKERS = {"sphere": _make_sphere, "wall": _make_wall, "box": _make_box}


def _clump_members(bodies, clump_bid):
    """Stored body ids of the members of a clump (their clump_id is the clump's body_id;
    in YADE the clump body's own clump_id is its own id, so it is excluded)."""
    return sorted(bid for bid, rec in bodies.items()
                  if int(rec.get("clump_id", -1)) == clump_bid and bid != clump_bid)


def _rotation_matrix(q):
    """3x3 rotation matrix of a unit quaternion given as (w, x, y, z)."""
    w, x, y, z = (float(v) for v in q)
    return np.array([[1 - 2*(y*y + z*z), 2*(x*y - z*w),     2*(x*z + y*w)],
                     [2*(x*y + z*w),     1 - 2*(x*x + z*z), 2*(y*z - x*w)],
                     [2*(x*z - y*w),     2*(y*z + x*w),     1 - 2*(x*x + y*y)]])


def _quat_mul(a, b):
    """Hamilton product of quaternions given as (w, x, y, z)."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return np.array([aw*bw - ax*bx - ay*by - az*bz,
                     aw*bx + ax*bw + ay*bz - az*by,
                     aw*by - ax*bz + ay*bw + az*bx,
                     aw*bz + ax*by - ay*bx + az*bw])


def _quat_conj(q):
    return np.array([q[0], -q[1], -q[2], -q[3]])


def _rotation_angle(a, b):
    """Angle (rad) of the rotation between two quaternions (w, x, y, z).

    Both are normalized first (YADE lets orientations drift from unit length by
    about 1e-13), and the angle is 2 atan2(|v|, |w|) of conj(a) b: well
    conditioned near zero, unlike 2 acos(a . b).
    """
    a = np.asarray(a, dtype=float) / np.linalg.norm(a)
    b = np.asarray(b, dtype=float) / np.linalg.norm(b)
    d = _quat_mul(_quat_conj(a), b)
    return 2.0 * float(np.arctan2(np.linalg.norm(d[1:]), abs(d[0])))


# Beyond these, a stored relative pose and the one YADE recomputes are not
# just round-off apart (relative to the clump size, and in radians)
_CLUMP_POSE_TOL = 1e-10


def _check_clump_relative_poses(bid, c, q_file, members, size):
    """Compare each member's stored relative pose with the one YADE recomputed.

    q_file: the clump's stored orientation (w, x, y, z). members: list of
    (stored body_id, YADE body id, record). The stored pose is relative to the
    stored clump frame; it is mapped into the frame YADE recomputed before
    comparing. Returns a list of warning strings.
    """
    q_new = np.array([c.state.ori[3], c.state.ori[0], c.state.ori[1], c.state.ori[2]])  # YADE: (x, y, z, w)
    table = c.shape.members
    warnings = []
    for sbid, new_id, mrec in members:
        if not ("clump_relative_position" in mrec and "clump_relative_orientation" in mrec
                and _given(mrec["clump_relative_position"]) and _given(mrec["clump_relative_orientation"])):
            continue
        R = _rotation_matrix(q_new).T @ _rotation_matrix(q_file)        # stored clump frame -> new frame
        expected_pos = R @ np.asarray(mrec["clump_relative_position"], dtype=float)
        expected_ori = _quat_mul(_quat_mul(_quat_conj(q_new), q_file),
                                 np.asarray(mrec["clump_relative_orientation"], dtype=float))
        got_pos, got_q = table[new_id]
        got_ori = np.array([got_q[3], got_q[0], got_q[1], got_q[2]])
        dpos = np.linalg.norm(np.array(got_pos) - expected_pos) / size
        dang = _rotation_angle(got_ori, expected_ori)
        if dpos > _CLUMP_POSE_TOL or dang > _CLUMP_POSE_TOL:
            warnings.append(f"clump {bid}, member {sbid}: stored relative pose differs from the one YADE "
                            f"recomputed (position {dpos:.1e} of the clump size, orientation {dang:.1e} rad)")
    return warnings


def _make_clump(bid, rec, members):
    """Rebuild a clump from its (already restored) members.

    YADE computes the clump frame (centre of mass, principal axes) and the
    members' relative poses from the members' current positions; the members'
    relative poses cannot be set from Python. The frame YADE computes is kept,
    so members and clump stay consistent, and the file is checked against it:
    the centre of mass must agree, and the stored inertia, rotated into the new
    frame, must be diagonal there (principal axes may come out permuted or with
    another sign). Otherwise the clump cannot be reproduced: ValueError.
    Mass and inertia are then taken from the file, velocities and angular
    momentum (global quantities) too.

    members: list of (stored body_id, YADE body id, record). The members' stored
    relative poses are compared with the ones YADE recomputed; differences
    beyond round-off are returned as warnings (the clump is still built).
    Returns (YADE clump id, warnings).
    """
    member_ids = [new_id for _s, new_id, _r in members]
    cid = O.bodies.clump(member_ids)
    c = O.bodies[cid]
    pos = np.array(c.state.pos)
    size = max(np.linalg.norm(np.array(O.bodies[m].state.pos) - pos) for m in member_ids) or 1.0
    if np.linalg.norm(pos - np.asarray(rec["position"], dtype=float)) > 1e-9 * size:
        raise ValueError(f"[import] clump {bid}: centre of mass recomputed from the members "
                         f"{pos} differs from the stored position {rec['position']}; the clump cannot be "
                         f"rebuilt without the members' relative poses (scene partially built; call O.reset())")
    q_new = c.state.ori
    R_new = _rotation_matrix((q_new[3], q_new[0], q_new[1], q_new[2]))   # YADE indexes (x, y, z, w)
    R_file = _rotation_matrix(rec["orientation"])
    I = np.asarray(rec["inertia"], dtype=float).reshape(3, 3)
    R = R_new.T @ R_file                       # file frame -> new frame
    I_new = R @ I @ R.T
    off = np.max(np.abs(I_new - np.diag(np.diag(I_new))))
    if off > 1e-9 * np.max(np.abs(np.diag(I_new))):
        raise ValueError(f"[import] clump {bid}: the principal axes recomputed from the members do "
                         f"not match the stored orientation and inertia (off-diagonal {off:.2e}); "
                         f"(scene partially built; call O.reset())")
    c.state.mass = float(rec["mass"])
    c.state.inertia = Vector3(*(float(v) for v in np.diag(I_new)))
    c.state.vel = _v3(rec["velocity"])
    c.state.angVel = _v3(rec["angular_velocity"])
    q_file = np.asarray(rec["orientation"], dtype=float)
    return cid, _check_clump_relative_poses(bid, c, q_file, members, size)


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
    restore_time         : bool  Carry the file's time and iteration on (default True).
                                 O.time and O.iter are read-only in YADE, so the
                                 offsets file − current are stored in
                                 O.tags["ondem_time_offset"] and
                                 O.tags["ondem_iteration_offset"]; the exporter adds
                                 them, so a file series stays continuous. Engines that
                                 read O.time or O.iter still see them from zero.
    restore_dt           : bool  Set O.dt from the file (default True).
    restore_gravity      : bool  Set gravity on the NewtonIntegrator (default True).
    restore_interactions : bool  Rebuild every contact of /<SIM>/Interactions with its
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
        'box_ids'             – YADE body ids of the restored boxes
        'clump_ids'           – YADE body ids of the rebuilt clump bodies
        'clump_warnings'      – stored relative poses of clump members that differ from
                                the ones YADE recomputed beyond round-off (empty if none)
        'interaction_count'   – number of contacts rebuilt with their history
        'id_map'              – {stored body_id -> YADE body id}
        'mat_id_map'          – {stored material id -> O.materials index}
        'display_group_names' – scene.display_group_names from the file
        'display_group'       – {YADE body id -> display group index}
        'time_offset'         – file time − O.time at import (0.0 if restore_time=False)
        'iteration_offset'    – file iteration − O.iter at import
    """
    print(f"[import] Reading '{filename}' ...")
    _check_engines(restore_gravity)

    with h5py.File(filename, "r") as f:
        time, iteration, dt, gravity, names, shape_names = _read_scene(f)
        materials    = _read_materials(f)
        bodies       = _read_bodies(f, names, shape_names)
        interactions = ondem_read_interactions(f) if restore_interactions else []

    _check_file(bodies, materials, interactions)

    # --- from here on the scene is modified ---
    time_offset, iteration_offset = 0.0, 0
    if restore_time:
        # O.time and O.iter are read-only in YADE: carry the file's values as offsets
        time_offset, iteration_offset = time - O.time, iteration - O.iter
        O.tags["ondem_time_offset"] = repr(time_offset)
        O.tags["ondem_iteration_offset"] = str(iteration_offset)
        print(f"[import] time={time:.6g} s, iteration={iteration}: O.time and O.iter are read-only in YADE; "
              f"offsets {time_offset:.6g} s / {iteration_offset} stored in O.tags (engines still see O.time, O.iter).")
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

    sphere_ids, wall_ids, box_ids, clump_ids, clump_warnings = [], [], [], [], []
    id_map, display_group = {}, {}

    def add_clump(bid):
        rec = bodies[bid]
        members = [(m, id_map[m], bodies[m]) for m in _clump_members(bodies, bid)]
        new_id, warnings = _make_clump(bid, rec, members)
        for w in warnings:
            print(f"[import] Warning: {w}")
        clump_warnings.extend(warnings)
        _set_extras(O.bodies[new_id], rec)
        id_map[bid] = new_id
        display_group[new_id] = rec["display_group"]
        clump_ids.append(new_id)

    # increasing body_id; a clump is built when its members exist (normally they
    # have smaller ids, so ids are kept), otherwise at the end
    deferred = []
    for bid in sorted(bodies):
        rec = bodies[bid]
        sg = rec["shape_group"]
        if sg == "clump":
            if all(m in id_map for m in _clump_members(bodies, bid)):
                add_clump(bid)
            else:
                deferred.append(bid)
            continue
        b = _MAKERS[sg](rec, mat_id_map[int(rec["material_id"])])
        _set_extras(b, rec)
        new_id = O.bodies.append(b)
        id_map[bid] = new_id
        display_group[new_id] = rec["display_group"]
        {"sphere": sphere_ids, "wall": wall_ids, "box": box_ids}[sg].append(new_id)
    for bid in deferred:
        add_clump(bid)

    _restore_interactions(interactions, id_map)

    moved = {s: n for s, n in id_map.items() if s != n}
    if moved:
        print(f"[import] Note: {len(moved)} body id(s) changed (scene not empty or ids not contiguous); see 'id_map'.")

    print(f"[import] Done. {len(sphere_ids)} sphere(s), {len(wall_ids)} wall(s), {len(box_ids)} box(es), "
          f"{len(clump_ids)} clump(s) "
          f"in {len(names)} display group(s) {names}, {len(interactions)} contact(s) with history "
          f"→ {len(O.bodies)} total bodies in scene.")

    return {
        "sphere_ids"          : sphere_ids,
        "wall_ids"            : wall_ids,
        "box_ids"             : box_ids,
        "clump_ids"           : clump_ids,
        "clump_warnings"      : clump_warnings,
        "interaction_count"   : len(interactions),
        "id_map"              : id_map,
        "mat_id_map"          : mat_id_map,
        "display_group_names" : names,
        "display_group"       : display_group,
        "time_offset"         : time_offset,
        "iteration_offset"    : iteration_offset,
    }


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from yade import (ForceResetter, InsertionSortCollider, Bo1_Sphere_Aabb, Bo1_Wall_Aabb, Bo1_Box_Aabb,
                      InteractionLoop, Ig2_Sphere_Sphere_ScGeom, Ig2_Wall_Sphere_ScGeom, Ig2_Box_Sphere_ScGeom,
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
        InsertionSortCollider([Bo1_Sphere_Aabb(), Bo1_Wall_Aabb(), Bo1_Box_Aabb()]),
        InteractionLoop(
            [Ig2_Sphere_Sphere_ScGeom(), Ig2_Wall_Sphere_ScGeom(), Ig2_Box_Sphere_ScGeom()],
            [Ip2_FrictMat_FrictMat_FrictPhys()],
            [Law2_ScGeom_FrictPhys_CundallStrack()],
        ),
        NewtonIntegrator(gravity=(0, 0, -9.81), damping=0.3),
    ]

    result = import_vtkhdf(vtkhdf_file)

    print(f"\nScene ready: {len(O.bodies)} bodies, O.dt={O.dt:.3g}, O.time={O.time:.6g}")
    print("Call O.run(N) or open the YADE GUI to continue the simulation.")
