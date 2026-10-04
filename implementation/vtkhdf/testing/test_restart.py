"""
test_restart.py
Acceptance test: a restart from the file continues the simulation as if it
had never stopped, contact history included.

  A: settle 36 spheres in a box of 5 walls (+ a fixed box, one sphere with
     blocked translations), tilt gravity so the contacts carry shear load,
     export at step N, run M more steps.
  B: fresh scene, same engines, import the file, run M steps.

Compared between A and B:
  - at the restart instant (B just imported, A just exported): the set of
    contacts and every restored contact value (normal, shear force, kn, ks,
    friction, dissipation exactly; normal force within 1e-15 relative, as
    it is rebuilt from the stored scalar);
  - after 1 step and after M steps: the set of contacts, body positions,
    velocities, angular velocities, and per-contact normal and shear force
    vectors, relative to reference scales (sphere radius, largest velocity,
    angular velocity and normal force in A);
  - time and iteration of a file exported by B at the end (series continues).

Two scenarios, with stated acceptance criteria:
  1. without clumps: the restart must be bit-identical; tolerance 1e-10 after
     1 step and after M steps (observed: 0).
  2. with 3 two-sphere clumps: YADE recomputes the members' relative poses
     from their positions when the clump is rebuilt (they cannot be set from
     Python), so B starts with round-off differences, which the granular
     dynamics amplify. Acceptance: the restart instant and 1e-12 after 1 step
     (round-off). The comparison after M steps is printed as information only:
     a restart with clumps is not expected to stay identical over a long run
     (observed on 2026-10-02 in this quiet scene: about 5e-9 after 2000 steps).

Negative controls in each scenario (must exceed the tolerance where the
acceptance criterion is: after M steps without clumps, after 1 step with
clumps), to show the test can fail:
  - import, then set every shear force to zero (history lost);
  - import, then replace the stored normals of sphere-sphere contacts by the
    current centre line (normal history lost).

Run with (from Windows):
    wsl -d Ubuntu-24.04 yadedaily -n -x <path>/implementation/vtkhdf/testing/test_restart.py
yadedaily uses 1 OpenMP thread by default; the test requires it (with
several threads the order of force summation, and so the round-off, varies
from run to run). Ends with "TEST PASSED" or "TEST FAILED" (exit code 1).
"""

import sys, os, math, shutil, tempfile
# exporter and importer live in implementation/vtkhdf, one level up.
# Under "yadedaily -x" __file__ is the yadedaily binary; the script path is sys.argv[0].
HERE = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np
import h5py
from yade import utils, O, Vector3, Quaternion
from export_yade_vtkhdf import export_vtkhdf
from import_yade_vtkhdf import import_vtkhdf
from hdf5_utils import SIMULATION_GROUP as SIM

N_SETTLE, N_TILT, M = 8000, 2000, 2000
R = 0.012            # sphere radius: reference length
DROP_Z = 0.143       # start height of the sphere that lands after the restart

failures = []
def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("  FAIL:", msg)


# ---------------------------------------------------------------------------
# Scene and engines (engines cannot come from the file: A and B share them)
# ---------------------------------------------------------------------------

def set_engines():
    O.engines = [
        ForceResetter(),
        InsertionSortCollider([Bo1_Sphere_Aabb(), Bo1_Wall_Aabb(), Bo1_Box_Aabb()]),
        InteractionLoop(
            [Ig2_Sphere_Sphere_ScGeom(), Ig2_Wall_Sphere_ScGeom(), Ig2_Box_Sphere_ScGeom()],
            [Ip2_FrictMat_FrictMat_FrictPhys()],
            [Law2_ScGeom_FrictPhys_CundallStrack()]
        ),
        NewtonIntegrator(gravity=(0, 0, -9.81), damping=0.4, label="newton"),
    ]


def build_scene(with_clumps, with_drop):
    # young * poisson / young != poisson for this pair (1 ulp): the restart is exact only
    # because the file also carries yade_poisson
    mat = O.materials.append(FrictMat(density=2450, young=37123456.789, poisson=0.24,
                                      frictionAngle=math.radians(23), label="glass"))
    wall_mat = O.materials.append(FrictMat(density=7800, young=2.1e8, poisson=0.41,
                                           frictionAngle=math.radians(11), label="steel"))
    half = 0.05
    O.bodies.append(utils.wall( 0,    axis=2, sense= 1, material=wall_mat))
    O.bodies.append(utils.wall(-half, axis=0, sense= 1, material=wall_mat))
    O.bodies.append(utils.wall( half, axis=0, sense=-1, material=wall_mat))
    O.bodies.append(utils.wall(-half, axis=1, sense= 1, material=wall_mat))
    O.bodies.append(utils.wall( half, axis=1, sense=-1, material=wall_mat))
    step = 2 * R + 0.001
    for z in [R + k * step for k in range(4)]:
        for x in (-0.025, 0.0, 0.025):
            for y in (-0.025, 0.0, 0.025):
                O.bodies.append(utils.sphere(Vector3(x, y, z), R, material=mat))
    O.bodies.append(utils.box((0.025, 0.025, -0.002), (0.006, 0.006, 0.002),
                              orientation=Quaternion((0, 0, 1), math.radians(10)),
                              fixed=True, material=wall_mat))
    O.bodies[7].state.blockedDOFs = "xyz"     # one sphere that may only rotate
    if with_drop:
        # a sphere that is still falling at the export and lands after the restart (about
        # step 10500): its new contacts get ks from the restored materials, which is exact
        # only with yade_poisson
        O.bodies.append(utils.sphere(Vector3(0.0, 0.0, DROP_Z), R, material=mat))
    clumps = []
    if with_clumps:
        # three clumps of two overlapping spheres, dropped into hollows of the top layer
        for (x, y), (dx, dy) in (((-0.0125, -0.0125), (0.006, 0.0)), ((0.0125, 0.0125), (0.0, 0.006)),
                                 ((-0.0125, 0.0125), (0.0045, 0.0045))):
            cid, _ = O.bodies.appendClumped([utils.sphere((x - dx, y - dy, 0.104), 0.008, material=mat),
                                             utils.sphere((x + dx, y + dy, 0.104), 0.008, material=mat)])
            clumps.append(cid)
    O.dt = 1e-5
    return clumps


# ---------------------------------------------------------------------------
# Snapshots and comparison
# ---------------------------------------------------------------------------

def body_states():
    return {b.id: dict(pos=np.array(b.state.pos), vel=np.array(b.state.vel),
                       angVel=np.array(b.state.angVel))
            for b in O.bodies}


def contacts():
    out = {}
    for i in O.interactions:
        if not i.isReal:
            continue
        out[(i.id1, i.id2)] = dict(
            normal=np.array(i.geom.normal), fn=np.array(i.phys.normalForce), fs=np.array(i.phys.shearForce),
            kn=i.phys.kn, ks=i.phys.ks, tan=i.phys.tangensOfFrictionAngle, dissip=i.phys.frictDissip)
    return out


def max_diff(a, b, key):
    return max(np.max(np.abs(np.asarray(a[k][key]) - np.asarray(b[k][key]))) for k in a) if a else 0.0


def compare(label, sA, cA, sB, cB, tol, report):
    """Compare B against A; returns the largest relative difference.
    tol=None: print the differences as information only (no check)."""
    if report:
        check(set(cA) == set(cB), f"{label}: contact sets differ "
              f"(only A: {sorted(set(cA) - set(cB))[:5]}, only B: {sorted(set(cB) - set(cA))[:5]})")
    common = [k for k in cA if k in cB]
    vmax = max(np.max(np.abs(s["vel"])) for s in sA.values()) or 1.0
    wmax = max(np.max(np.abs(s["angVel"])) for s in sA.values()) or 1.0
    fmax = max(np.linalg.norm(c["fn"]) for c in cA.values()) or 1.0
    rel = {
        "position":         max_diff(sA, sB, "pos") / R,
        "velocity":         max_diff(sA, sB, "vel") / vmax,
        "angular velocity": max_diff(sA, sB, "angVel") / wmax,
        "normal force":     max_diff({k: cA[k] for k in common}, cB, "fn") / fmax,
        "shear force":      max_diff({k: cA[k] for k in common}, cB, "fs") / fmax,
    }
    if report:
        note = f"(tolerance {tol:.0e})" if tol is not None else "(information only, not checked)"
        print(f"    {label}: " + ", ".join(f"{k} {v:.1e}" for k, v in rel.items()) + f"  {note}")
        if tol is not None:
            for k, v in rel.items():
                check(v <= tol, f"{label}: {k} differs by {v:.2e} (relative), tolerance {tol:.0e}")
    return max(rel.values())


# ---------------------------------------------------------------------------
# One scenario: A uninterrupted, B restarted, negative controls
# ---------------------------------------------------------------------------

def zero_shear():
    for i in O.interactions:
        if i.isReal:
            i.phys.shearForce = Vector3(0, 0, 0)

def centre_line_normals():
    for i in O.interactions:
        if i.isReal and isinstance(O.bodies[i.id1].shape, Sphere) and isinstance(O.bodies[i.id2].shape, Sphere):
            d = O.bodies[i.id2].state.pos - O.bodies[i.id1].state.pos
            i.geom.normal = d / d.norm()


def scenario(name, with_clumps, with_drop, tol_1, tol_M):
    print(f"Scenario: {name}")
    out = os.path.join(tempfile.gettempdir(), f"test_restart_{'clumps' if with_clumps else 'plain'}.vtkhdf")

    # --- A: uninterrupted
    O.reset()
    set_engines()
    clumps = build_scene(with_clumps, with_drop)
    O.run(N_SETTLE, wait=True)
    newton.gravity = (2.0, 1.0, -9.81)          # tilt: contacts carry shear load, some slide
    O.run(N_TILT, wait=True)
    export_vtkhdf(out)
    A0_c = contacts()
    O.run(1, wait=True)
    A1_s, A1_c = body_states(), contacts()
    seen = set(A1_c)
    for _ in range(M - 1):                      # step by step, to see contacts that form and break again
        O.run(1, wait=True)
        seen |= {(i.id1, i.id2) for i in O.interactions if i.isReal}
    AM_s, AM_c = body_states(), contacts()
    A_end_time, A_end_iter = O.time, O.iter
    sliding = sum(1 for c in A0_c.values()
                  if np.linalg.norm(c["fs"]) >= c["tan"] * np.linalg.norm(c["fn"]) * (1 - 1e-9))
    fs_max = max(np.linalg.norm(c["fs"]) for c in A0_c.values())
    formed = len(seen - set(A0_c))
    print(f"  A at restart: {len(A0_c)} contacts, {sliding} sliding, max |Fs| {fs_max:.3e} N; "
          f"{formed} contact(s) formed after the restart (their ks comes from the restored materials)")
    if with_drop:
        check(formed >= 1, f"{name}: a contact forms after the restart (restored materials are exercised)")
    check(fs_max > 1e-3, f"{name}: contacts carry shear load at the restart (otherwise the test proves little)")
    if with_clumps:
        members = {m for c in clumps for m in O.bodies[c].shape.members.keys()}
        n = sum(1 for k in A0_c if k[0] in members or k[1] in members)
        print(f"  clumps: {len(clumps)}, contacts of clump members at restart: {n}")
        check(n >= len(clumps), f"{name}: clumps are in contact at the restart")

    # --- B: restart from the file
    def run_B(mutate=None):
        O.reset()
        set_engines()
        r = import_vtkhdf(out)
        check(all(s == n for s, n in r["id_map"].items()), f"{name}: body ids unchanged after import")
        check(r["clump_ids"] == clumps, f"{name}: clumps rebuilt with their ids {r['clump_ids']} != {clumps}")
        check(r["clump_warnings"] == [], f"{name}: stored and recomputed clump relative poses agree: {r['clump_warnings']}")
        if mutate:
            mutate()
        c0 = contacts()
        O.run(1, wait=True)
        s1, c1 = body_states(), contacts()
        O.run(M - 1, wait=True)
        return c0, s1, c1, body_states(), contacts()

    B0_c, B1_s, B1_c, BM_s, BM_c = run_B()
    check(set(B0_c) == set(A0_c), f"{name}: restart instant: same contacts as A")
    bad_exact = [(k, key) for k in A0_c if k in B0_c for key in ("normal", "fs", "kn", "ks", "tan", "dissip")
                 if not np.array_equal(np.asarray(A0_c[k][key]), np.asarray(B0_c[k][key]))]
    check(not bad_exact, f"{name}: restart instant: values not exactly restored: {bad_exact[:5]}")
    fmax0 = max(np.linalg.norm(c["fn"]) for c in A0_c.values())
    dfn0 = max_diff({k: A0_c[k] for k in A0_c if k in B0_c}, B0_c, "fn") / fmax0
    check(dfn0 <= 1e-15, f"{name}: restart instant: normal force differs by {dfn0:.1e} relative")
    print(f"  B restart instant: {len(B0_c)} contacts; normal, shear force, kn, ks, friction, dissipation "
          f"{'exactly equal' if not bad_exact else 'NOT equal'}; normal force within {dfn0:.1e}")
    compare("after 1 step", A1_s, A1_c, B1_s, B1_c, tol_1, report=True)
    compare(f"after {M} steps", AM_s, AM_c, BM_s, BM_c, tol_M, report=True)

    out_end = os.path.join(tempfile.gettempdir(), "test_restart_end.vtkhdf")
    export_vtkhdf(out_end)
    with h5py.File(out_end, "r") as f:
        sc = f[f"{SIM}/Scene"].attrs
        check(int(sc["iteration"]) == A_end_iter, f"{name}: iteration {int(sc['iteration'])} != A's {A_end_iter}")
        check(math.isclose(float(sc["time"]), A_end_time, rel_tol=1e-12), f"{name}: time {float(sc['time'])!r} != A's {A_end_time!r}")
        print(f"  series continues: iteration {int(sc['iteration'])} (A: {A_end_iter}), time {float(sc['time']):.9g} (A: {A_end_time:.9g})")

    if with_clumps:
        # the file: clump bodies have clump_id -1, members point to their clump and
        # carry their relative pose; a corrupted relative pose must produce a warning
        # (default display groups: members, being spheres, are in Points, clump bodies in Others)
        keys = ("body_id", "clump_id", "clump_relative_position", "clump_relative_orientation")
        rows = {}                                      # body_id -> (block, row, record)
        with h5py.File(out, "r") as f:
            for blk in f["VTKHDF/Assembly"]:
                pd = f["VTKHDF/Assembly"][blk]["PointData"]
                data = {k: pd[k][:] for k in keys}
                for k, bid in enumerate(data["body_id"]):
                    rows[int(bid)] = (blk, k, {key: data[key][k] for key in keys})
        for c in clumps:
            check(int(rows[c][2]["clump_id"]) == -1, f"{name}: clump body {c} has clump_id -1")
            check(np.isnan(rows[c][2]["clump_relative_position"]).all(), f"{name}: clump body {c}: no relative pose")
        members = sorted(bid for bid, (_b, _k, rec) in rows.items() if int(rec["clump_id"]) in clumps)
        check(len(members) == 2 * len(clumps) and all(np.isfinite(rows[m][2]["clump_relative_position"]).all()
              and np.isfinite(rows[m][2]["clump_relative_orientation"]).all() for m in members),
              f"{name}: every member has a relative pose")
        corrupted = os.path.join(tempfile.gettempdir(), "test_restart_clump_corrupted.vtkhdf")
        shutil.copy(out, corrupted)
        bad_member = members[0]
        blk, k, _rec = rows[bad_member]
        with h5py.File(corrupted, "a") as f:
            rp = f["VTKHDF/Assembly"][blk]["PointData/clump_relative_position"]
            v = rp[k]
            rp[k] = v * (1 + 1e-2)                     # 1 % off: well beyond round-off
        O.reset()
        set_engines()
        r = import_vtkhdf(corrupted)
        check(len(r["clump_warnings"]) == 1 and f"member {bad_member}" in r["clump_warnings"][0],
              f"{name}: a corrupted relative pose is reported: {r['clump_warnings']}")
        print(f"  corrupted relative pose reported: {r['clump_warnings']}")

    # --- negative controls
    # judged where the acceptance criterion is: after M steps, or after 1 step when
    # the long run is information only (clumps)
    for label, mutate in (("control: shear history lost", zero_shear),
                          ("control: stored normals ignored", centre_line_normals)):
        _, s1, c1, sM, cM = run_B(mutate)
        if tol_M is not None:
            worst, tol, when = compare(label, AM_s, AM_c, sM, cM, tol_M, report=False), tol_M, f"{M} steps"
        else:
            worst, tol, when = compare(label, A1_s, A1_c, s1, c1, tol_1, report=False), tol_1, "1 step"
        print(f"  {label}: largest relative difference after {when} {worst:.1e} (must exceed {tol:.0e})")
        check(worst > tol, f"{name}: {label}: the test did not detect the lost history ({worst:.1e})")


check(O.numThreads == 1, f"the test needs 1 OpenMP thread (yadedaily default), got {O.numThreads}")
scenario("without clumps, a sphere lands after the restart (bit-identical)",
         with_clumps=False, with_drop=True, tol_1=1e-10, tol_M=1e-10)
# with clumps the acceptance criterion is the restart instant and one step; the long
# run is information only (a restart with clumps is not expected to stay identical)
scenario("with clumps (members' relative poses recomputed by YADE)",
         with_clumps=True, with_drop=False, tol_1=1e-12, tol_M=None)

if failures:
    print(f"TEST FAILED ({len(failures)} check(s))")
    sys.exit(1)
print("TEST PASSED")
