"""
test_export.py
YADE simulation: spheres poured into a box (no top lid).
Guarantees sphere-sphere AND sphere-wall interactions at export time.

Exports with two display groups (spheres -> "particles", walls -> "geometry",
plus an empty group "unused"), checks the file, imports it into a reset scene,
compares every body by body_id and runs 1000 more steps.

Run with (from Windows):
    wsl -d Ubuntu-24.04 yadedaily -n -x <path>/implementation/vtkhdf/testing/test_export.py
Ends with "TEST PASSED" or "TEST FAILED" (exit code 1).
"""

from yade import pack, utils, O, Vector3
import sys, os
# exporter and hdf5_utils live in implementation/vtkhdf, one level up.
# Under "yadedaily -x" __file__ is the yadedaily binary; the script path is sys.argv[0].
HERE = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, os.path.dirname(HERE))

from export_yade_vtkhdf import export_vtkhdf
from import_yade_vtkhdf import import_vtkhdf
from hdf5_utils import SIMULATION_GROUP as SIM
import math, tempfile
from yade import Quaternion
import numpy as np
import h5py

# ---- Materials: non-default values, so a silent default cannot pass ----
mat = O.materials.append(
    # young * poisson / young != poisson for this pair (1 ulp): only yade_poisson restores it exactly
    FrictMat(density=2450, young=37123456.789, poisson=0.24,
             frictionAngle=radians(23), label="glass")
)
wall_mat = O.materials.append(
    FrictMat(density=7800, young=2.1e8, poisson=0.41,
             frictionAngle=radians(11), label="steel")
)

# ---- Box: 4 side walls + 1 floor (no lid) ----
# Box spans x: [-0.05, 0.05], y: [-0.05, 0.05], z: [0, ...]
half = 0.05

O.bodies.append(utils.wall( 0,      axis=2, sense= 1, material=wall_mat))  # floor  z=0
O.bodies.append(utils.wall(-half,   axis=0, sense= 1, material=wall_mat))  # left   x=-0.05
O.bodies.append(utils.wall( half,   axis=0, sense=-1, material=wall_mat))  # right  x=+0.05
O.bodies.append(utils.wall(-half,   axis=1, sense= 1, material=wall_mat))  # front  y=-0.05
O.bodies.append(utils.wall( half,   axis=1, sense=-1, material=wall_mat))  # back   y=+0.05

# ---- Pack spheres in a regular grid inside the box ----
r   = 0.012   # radius — large enough to touch neighbours
gap = 0.001   # small gap between spheres at start
step = 2*r + gap

xs = [-0.025, 0.0, 0.025]
ys = [-0.025, 0.0, 0.025]
zs = [r + k*step for k in range(4)]   # 4 layers → 36 spheres total

for z in zs:
    for x in xs:
        for y in ys:
            O.bodies.append(utils.sphere(Vector3(x, y, z), r, material=mat))

print(f"Bodies added: {len(O.bodies)} ({len(O.bodies)-5} spheres, 5 walls)")

# a flat fixed box under the corner sphere at (0.025, 0.025), rotated 10 deg about z,
# top face flush with the floor (z = 0): the sphere rests on floor and box (box-sphere contact)
BOX_ID = O.bodies.append(utils.box((0.025, 0.025, -0.002), (0.006, 0.006, 0.002),
                                   orientation=Quaternion((0, 0, 1), math.radians(10)),
                                   fixed=True, material=wall_mat))

# non-trivial orientations, to check the quaternion convention
O.bodies[5].state.ori = Quaternion((1, 2, 3), 0.7)          # a sphere: keeps rotating
O.bodies[0].state.ori = Quaternion((0, 0, 1), math.pi / 2)  # the floor wall is fixed: stays exact

# non-default per-body state (provisional extras): blocked DOFs, collision mask, damping
O.bodies[7].state.blockedDOFs = "xyz"
O.bodies[8].groupMask = 3
O.bodies[9].state.isDamped = False

# ---- Engines ----
def set_engines():
    O.engines = [
        ForceResetter(),
        InsertionSortCollider([Bo1_Sphere_Aabb(), Bo1_Wall_Aabb(), Bo1_Box_Aabb()]),
        InteractionLoop(
            [Ig2_Sphere_Sphere_ScGeom(), Ig2_Wall_Sphere_ScGeom(), Ig2_Box_Sphere_ScGeom()],
            [Ip2_FrictMat_FrictMat_FrictPhys()],
            [Law2_ScGeom_FrictPhys_CundallStrack()]
        ),
        NewtonIntegrator(gravity=(0, 0, -9.81), damping=0.4),
    ]

set_engines()
O.dt = 1e-5

# ---- Let spheres settle under gravity ----
# Run until kinetic energy is low (spheres have stacked and are touching)
O.run(8000, wait=True)

real_intrs = [i for i in O.interactions if i.isReal]
n_real = len(real_intrs)
print(f"Real interactions at export time: {n_real}")

# ---- Export with display groups ----
NAMES = ["particles", "geometry", "unused"]
group_of = lambda b: 0 if isinstance(b.shape, Sphere) else 1
out = os.path.join(tempfile.gettempdir(), "test_box_spheres.vtkhdf")
export_vtkhdf(out, NAMES, group_of)
time_at_export, iter_at_export = O.time, O.iter

# state before restart, per body id
before = {}
for b in O.bodies:
    before[b.id] = dict(
        pos=np.array(b.state.pos), vel=np.array(b.state.vel), angVel=np.array(b.state.angVel),
        ori=np.array([b.state.ori[k] for k in range(4)]), mass=b.state.mass,
        radius=b.shape.radius if isinstance(b.shape, Sphere) else None,
        wall=(b.shape.axis, b.shape.sense) if isinstance(b.shape, Wall) else None,
        box=tuple(b.shape.extents) if isinstance(b.shape, Box) else None,
        mat=dict(density=b.material.density, young=b.material.young, poisson=b.material.poisson,
                 frictionAngle=b.material.frictionAngle, label=b.material.label),
        group=group_of(b),
        extras=dict(blockedDOFs=b.state.blockedDOFs, groupMask=b.groupMask, isDamped=b.state.isDamped,
                    angMom=tuple(b.state.angMom), densityScaling=b.state.densityScaling))

failures = []
def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("  FAIL:", msg)

def rotate(q, v):
    """v_global = q v_body q^-1 for q = (w, x, y, z), the file convention."""
    w, u = q[0], np.asarray(q[1:])
    v = np.asarray(v, dtype=float)
    return v + 2 * w * np.cross(u, v) + 2 * np.cross(u, np.cross(u, v))

# ---- Check the file ----
print("Checking the file ...")
with h5py.File(out, "r") as f:
    check(list(f["VTKHDF/Assembly"]) == NAMES, f"Assembly links {list(f['VTKHDF/Assembly'])}")
    check(list(f[f"{SIM}/Scene/display_group_names"].asstr()[:]) == NAMES, f"display_group_names in /{SIM}/Scene")
    block_ids = set()
    for name in NAMES:
        blk = f["VTKHDF"][name]
        check(blk["Points"].dtype == np.float64, f"{name}: Points dtype {blk['Points'].dtype}")
        ids = [int(v) for v in blk["PointData/body_id"][:]]
        block_ids |= set(ids)
        expected = sorted(bid for bid, st in before.items() if NAMES[st["group"]] == name)
        check(sorted(ids) == expected, f"{name}: body ids {sorted(ids)} != {expected}")
    check(f["VTKHDF/unused/NumberOfPoints"][0] == 0, "empty group 'unused' has 0 points")

    # quaternions: order (w, x, y, z), identity (1, 0, 0, 0), v_global = q v_body q^-1
    stored = {}
    for name in NAMES:
        q_ds = f["VTKHDF"][name]["PointData/orientation"]
        check(q_ds.attrs["order"] == "wxyz", f"{name}: orientation order attribute {q_ds.attrs['order']!r}")
        for bid, q in zip(f["VTKHDF"][name]["PointData/body_id"][:], q_ds[:]):
            stored[int(bid)] = q
    c, s45 = math.cos(math.pi / 4), math.sin(math.pi / 4)
    check(np.allclose(stored[0], [c, 0, 0, s45], atol=1e-12), f"floor wall: stored {stored[0]} != (cos 45°, 0, 0, sin 45°)")
    check(abs(stored[5][0]) < 0.999, f"body 5 orientation is not trivial: {stored[5]}")
    for bid, q in stored.items():
        yq = O.bodies[bid].state.ori
        check(np.allclose(q, [yq[3], yq[0], yq[1], yq[2]], atol=1e-12), f"body {bid}: stored {q} is not YADE's (w, x, y, z)")
        for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            check(np.allclose(rotate(q, v), np.array(yq * Vector3(*v)), atol=1e-12),
                  f"body {bid}: q v q^-1 differs from YADE's rotation of {v}")
    # all per-body data in the blocks (decision 12): the simulation group keeps scene, materials, interactions
    check(sorted(f[SIM].keys()) == ["Interactions", "Materials", "Scene"],
          f"/{SIM} holds {sorted(f[SIM].keys())}, expected Interactions, Materials, Scene only")
    shape_names = list(f[f"{SIM}/Scene/shape_names"].asstr()[:])
    print(f"  shape_names: {shape_names}")
    arrays = {name: sorted(f["VTKHDF"][name]["PointData"].keys()) for name in NAMES}
    check(all(a == arrays[NAMES[0]] for a in arrays.values()), f"every block carries the same arrays: {arrays}")
    for fld in ("body_id", "shape_type", "material_id", "clump_id", "velocity", "angular_velocity", "orientation",
                "mass", "inertia", "volume", "blocked_dofs", "radius", "dimensions", "wall_axis", "wall_sense",
                "group_mask", "is_damped", "angular_momentum", "density_scaling"):
        check(fld in arrays[NAMES[0]], f"block field {fld} missing")
    yade_shape = {"Sphere": "sphere", "Wall": "wall", "Box": "box"}
    for name in NAMES:
        pd = f["VTKHDF"][name]["PointData"]
        for k, bid in enumerate(int(v) for v in pd["body_id"][:]):
            b = O.bodies[bid]
            shape = shape_names[int(pd["shape_type"][k])]          # by name, never by a fixed index
            check(shape == yade_shape[type(b.shape).__name__], f"body {bid}: shape {shape!r}")
            expected_mask = sum(1 << "xyzXYZ".index(c) for c in b.state.blockedDOFs)
            check(int(pd["blocked_dofs"][k]) == expected_mask, f"body {bid}: blocked_dofs {int(pd['blocked_dofs'][k])} != {expected_mask}")
            if shape == "sphere":
                check(pd["radius"][k] == b.shape.radius and int(pd["wall_axis"][k]) == -1
                      and np.isnan(pd["dimensions"][k]).all(), f"body {bid}: sphere fields, NaN / -1 elsewhere")
            if shape == "wall":
                check(np.isnan(pd["radius"][k]) and int(pd["wall_axis"][k]) == b.shape.axis
                      and int(pd["wall_sense"][k]) == b.shape.sense, f"body {bid}: wall fields, NaN radius")
            if shape == "box":
                check(np.isnan(pd["radius"][k]) and np.allclose(pd["dimensions"][k], 2 * np.array(b.shape.extents)),
                      f"body {bid}: box dimensions, NaN radius")
            check(int(pd["clump_id"][k]) == -1, f"body {bid}: clump_id -1 (no clumps in this test)")
    blocked = {bid: int(v) for name in NAMES for bid, v in zip(f["VTKHDF"][name]["PointData/body_id"][:],
                                                                 f["VTKHDF"][name]["PointData/blocked_dofs"][:])}
    check(blocked[7] == 7 and all(blocked[w] == 63 for w in range(5)) and blocked[BOX_ID] == 63,
          f"blocked_dofs: sphere 7 -> 7, walls and box -> 63 ({blocked[7]}, {[blocked[w] for w in range(5)]}, {blocked[BOX_ID]})")
    check(int(f[f"{SIM}/Scene"].attrs["iteration"]) == iter_at_export, "scene.iteration")

    # interactions: all real ones written, ids found in the blocks
    ig = f[f"{SIM}/Interactions"]
    n_file = sum(int(ig[t].attrs["count"]) for t in ig)
    check(n_real > 0, "the test scene has contacts at export time")
    check(n_file == n_real, f"interactions in file {n_file} != real interactions {n_real}")
    for t in ig:
        ids = set(int(v) for v in ig[t]["id1"][:]) | set(int(v) for v in ig[t]["id2"][:])
        check(ids <= block_ids, f"interaction ids not in the blocks: {sorted(ids - block_ids)}")
        check(t == t.lower(), f"interaction group name {t!r} is not snake_case")
    # materials: FrictMat -> linear_elastic_frictional_3D (decision 10)
    for key, g in f[f"{SIM}/Materials"].items():
        for fld in ("id", "density", "normal_stiffness", "shear_stiffness", "shear_friction", "shear_damping", "yade_poisson"):
            check(fld in g, f"material {key}: field {fld} missing")
        check(g.attrs.get("schema_classes") == "linear_elastic_frictional_3D", f"material {key}: schema_classes attribute")
        check("provisional" not in g.attrs, f"material {key}: no provisional attribute any more")
        ym = O.materials[int(g["id"][()])]
        check(g["normal_stiffness"][()] == ym.young, f"material {key}: normal_stiffness = young")
        check(g["shear_stiffness"][()] == ym.young * ym.poisson, f"material {key}: shear_stiffness = young * poisson")
        check(g["shear_damping"][()] == 0.0, f"material {key}: shear_damping = 0")
        check(g["yade_poisson"][()] == ym.poisson, f"material {key}: yade_poisson")
        check(math.isclose(g["shear_friction"][()], math.tan(ym.frictionAngle), rel_tol=1e-15), f"material {key}: shear_friction = tan(frictionAngle)")
    g0 = f[f"{SIM}/Materials"][str(mat)]
    check(g0["shear_stiffness"][()] / g0["normal_stiffness"][()] != g0["yade_poisson"][()],
          "test material: the quotient is 1 ulp off, so the test shows that yade_poisson is needed")
    check(len(f[f"{SIM}/Materials"]) == 2, f"{len(f[f'{SIM}/Materials'])} materials in the file, expected 2")
    pairs_file = sorted((int(a), int(b)) for t in ig for a, b in zip(ig[t]["id1"][:], ig[t]["id2"][:]))
    pairs_yade = sorted((i.id1, i.id2) for i in real_intrs)
    check(pairs_file == pairs_yade, "interaction pairs id1/id2 match the scene")
    check(any(BOX_ID in p for p in pairs_file), "a box-sphere contact exists (box contacts are covered)")

# ---- Restart: import into a reset scene ----
print("Restarting from the file ...")
O.reset()
set_engines()
r = import_vtkhdf(out)
check(r["display_group_names"] == NAMES, f"display_group_names {r['display_group_names']}")
check(r["interaction_count"] == n_real, f"{r['interaction_count']} contacts restored, {n_real} in the file")
check(all(s == n for s, n in r["id_map"].items()), "body ids unchanged after import into an empty scene")
check(len(O.bodies) == len(before), f"{len(O.bodies)} bodies after import, {len(before)} before")

def close(a, b):
    return np.allclose(a, b, rtol=0, atol=1e-12)

for bid, st in before.items():
    b = O.bodies[r["id_map"][bid]]
    check(close(np.array(b.state.pos), st["pos"]), f"body {bid}: position")
    check(close(np.array(b.state.vel), st["vel"]), f"body {bid}: velocity")
    check(close(np.array(b.state.angVel), st["angVel"]), f"body {bid}: angular velocity")
    q = np.array([b.state.ori[k] for k in range(4)])
    check(close(q, st["ori"]) or close(q, -st["ori"]), f"body {bid}: orientation {q} != {st['ori']}")
    check(b.material.young == st["mat"]["young"] and b.material.poisson == st["mat"]["poisson"],
          f"body {bid}: young and poisson restored exactly")
    for k, v in st["mat"].items():
        got = getattr(b.material, k)
        ok = math.isclose(got, v, rel_tol=1e-12) if isinstance(v, float) else got == v
        check(ok, f"body {bid}: material {k} {got!r} != {v!r}")
    check(r["display_group"][b.id] == st["group"], f"body {bid}: display group")
    got = dict(blockedDOFs=b.state.blockedDOFs, groupMask=b.groupMask, isDamped=b.state.isDamped,
               angMom=tuple(b.state.angMom), densityScaling=b.state.densityScaling)
    check(got == st["extras"], f"body {bid}: state extras {got} != {st['extras']}")
    if st["radius"] is not None:
        check(b.shape.radius == st["radius"], f"body {bid}: radius")
        check(b.state.mass == st["mass"], f"body {bid}: mass")
    if st["wall"] is not None:
        check((b.shape.axis, b.shape.sense) == st["wall"], f"body {bid}: wall axis/sense")
    if st["box"] is not None:
        check(isinstance(b.shape, Box) and tuple(b.shape.extents) == st["box"], f"body {bid}: box extents")
        check(b.state.mass == st["mass"], f"body {bid}: box mass")

# ---- The restarted scene runs ----
O.dt = 1e-5
O.run(1000, wait=True)
check(sum(1 for i in O.interactions if i.isReal) > 0, "contacts rebuilt after restart")
check(all(not np.isnan(b.state.pos[2]) for b in O.bodies), "positions finite after 1000 steps")

# ---- Export again with the groups returned by the importer ----
out2 = os.path.join(tempfile.gettempdir(), "test_box_spheres_restart.vtkhdf")
export_vtkhdf(out2, r["display_group_names"], r["display_group"])
with h5py.File(out2, "r") as f:
    for name in NAMES:
        ids = sorted(int(v) for v in f["VTKHDF"][name]["PointData/body_id"][:])
        expected = sorted(bid for bid, st in before.items() if NAMES[st["group"]] == name)
        check(ids == expected, f"re-export {name}: body ids")
    # the file series continues through the restart (O.time and O.iter restarted from 0)
    sc = f[f"{SIM}/Scene"].attrs
    check(int(sc["iteration"]) == iter_at_export + 1000, f"iteration {int(sc['iteration'])} != {iter_at_export + 1000}")
    check(math.isclose(float(sc["time"]), time_at_export + 1000 * 1e-5, rel_tol=1e-12),
          f"time {float(sc['time'])!r} != {time_at_export + 1000 * 1e-5!r}")
    check(O.iter == 1000, f"O.iter restarted from 0 ({O.iter})")
    print(f"  series continues: iteration {int(sc['iteration'])}, time {float(sc['time']):.6g} (O.iter = {O.iter})")

# ---- Default display groups (decision 18): Points (spheres) and Others ----
default_out = os.path.join(tempfile.gettempdir(), "test_default_groups.vtkhdf")
export_vtkhdf(default_out)
with h5py.File(default_out, "r") as f:
    check(list(f["VTKHDF/Assembly"]) == ["Points", "Others"], f"default groups {list(f['VTKHDF/Assembly'])}")
    shape_names = list(f[f"{SIM}/Scene/shape_names"].asstr()[:])
    for name, expected in (("Points", {"sphere"}), ("Others", {"wall", "box"})):
        got = {shape_names[int(t)] for t in f["VTKHDF"][name]["PointData/shape_type"][:]}
        check(got == expected, f"default group {name}: shapes {got}, expected {expected}")
    print(f"  default groups: Points {int(f['VTKHDF/Points/NumberOfPoints'][0])} bodies, "
          f"Others {int(f['VTKHDF/Others/NumberOfPoints'][0])} bodies")

# a group function without names is refused, and no file is written
no_names = os.path.join(tempfile.gettempdir(), "test_no_names.vtkhdf")
if os.path.exists(no_names):
    os.remove(no_names)
try:
    export_vtkhdf(no_names, display_group=lambda b: 0)
    check(False, "display_group without display_group_names must raise")
except ValueError as e:
    check("display_group_names" in str(e) and not os.path.exists(no_names), f"refused, no file: {e}")
    print("  display_group without names refused:", str(e)[:80], "...")

# ---- Periodic scene: the exporter must refuse and write nothing ----
O.periodic = True
periodic_out = os.path.join(tempfile.gettempdir(), "test_periodic.vtkhdf")
try:
    export_vtkhdf(periodic_out)
    check(False, "export of a periodic scene must raise")
except ValueError as e:
    check("periodic" in str(e) and not os.path.exists(periodic_out), f"periodic refused, no file: {e}")
    print("  periodic scene refused:", e)
O.periodic = False

# ---- Spheres only: the default block Others still exists, empty ----
O.reset()
O.bodies.append(utils.sphere((0, 0, 0), 0.012, material=O.materials.append(FrictMat(density=2000))))
only_spheres = os.path.join(tempfile.gettempdir(), "test_only_spheres.vtkhdf")
export_vtkhdf(only_spheres)
with h5py.File(only_spheres, "r") as f:
    check(list(f["VTKHDF/Assembly"]) == ["Points", "Others"] and int(f["VTKHDF/Others/NumberOfPoints"][0]) == 0
          and int(f["VTKHDF/Points/NumberOfPoints"][0]) == 1, "spheres only: Points has the sphere, Others exists and is empty")
    print("  spheres only: Others block present with 0 bodies")

# ---- A material field missing in the file: the importer must fail clearly ----
import shutil
broken = os.path.join(tempfile.gettempdir(), "test_box_spheres_no_young.vtkhdf")
shutil.copy(out, broken)
with h5py.File(broken, "a") as f:
    del f[f"{SIM}/Materials"][list(f[f"{SIM}/Materials"])[0]]["normal_stiffness"]
O.reset()
set_engines()
try:
    import_vtkhdf(broken)
    check(False, "import of a file without normal_stiffness must raise")
except ValueError as e:
    check("normal_stiffness" in str(e), f"error names the missing field: {e}")
    print("  missing field rejected:", e)

# ---- shear_damping != 0 cannot be a FrictMat: refused ----
damped = os.path.join(tempfile.gettempdir(), "test_box_spheres_damped.vtkhdf")
shutil.copy(out, damped)
with h5py.File(damped, "a") as f:
    g = f[f"{SIM}/Materials"][list(f[f"{SIM}/Materials"])[0]]
    del g["shear_damping"]
    g.create_dataset("shear_damping", data=0.5)
O.reset()
set_engines()
try:
    import_vtkhdf(damped)
    check(False, "import of shear_damping != 0 must raise")
except ValueError as e:
    check("shear_damping" in str(e) and len(O.bodies) == 0, f"shear_damping refused, nothing created: {e}")
    print("  shear_damping != 0 rejected:", e)

# ---- No engines: the importer must refuse before touching the scene ----
O.reset()
try:
    import_vtkhdf(out)
    check(False, "import without engines must raise")
except RuntimeError as e:
    check("engines" in str(e) and len(O.bodies) == 0, f"no-engines error and empty scene: {e}")
    print("  no engines rejected:", str(e)[:90], "...")

# ---- Unsupported contact type: ValueError naming it, nothing created ----
unsupported = os.path.join(tempfile.gettempdir(), "test_box_spheres_bad_contact.vtkhdf")
shutil.copy(out, unsupported)
with h5py.File(unsupported, "a") as f:
    g = f[f"{SIM}/Interactions"][list(f[f"{SIM}/Interactions"])[0]]
    del g["phys_type"]
    g.create_dataset("phys_type", data=["MindlinPhys"] * int(g.attrs["count"]), dtype=h5py.string_dtype())
O.reset()
set_engines()
try:
    import_vtkhdf(unsupported)
    check(False, "import of an unsupported contact type must raise")
except ValueError as e:
    check("MindlinPhys" in str(e) and len(O.bodies) == 0 and len(O.materials) == 0,
          f"unsupported contact type named, scene untouched: {e}")
    print("  unsupported contact type rejected:", str(e).splitlines()[1].strip())

print(f"Files: {out}, {out2}")
if failures:
    print(f"TEST FAILED ({len(failures)} check(s))")
    sys.exit(1)
print("TEST PASSED")
