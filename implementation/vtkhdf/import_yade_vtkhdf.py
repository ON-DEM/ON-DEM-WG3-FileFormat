"""
import_yade_vtkhdf.py
ON-DEM WG3 - VTKHDF to YADE importer

Reads a .vtkhdf file written by export_yade_vtkhdf_generated.py and
reconstructs the YADE simulation state:
  - Scene metadata  (time, dt, gravity)
  - Materials       (FrictMat from /ONDEM/Materials/)
  - Sphere bodies   (from /VTKHDF/PointData/)
  - Walls           (from /ONDEM/Bodies/Walls/)
  - Interactions are NOT restored — YADE rebuilds them via the collider
    on the first time step, which is the correct approach.

File layout expected (written by the exporter):
  /VTKHDF/                     VTK PolyData structure
    Points          (N,3)      sphere centres (same as PointData/position)
    NumberOfPoints  (1,)
    PointData/
      body_id       (N,)  int32
      material_id   (N,)  int32
      clump_id      (N,)  int32
      position      (N,3) float64
      velocity      (N,3) float64
      angular_velocity (N,3) float64
      orientation   (N,4) float64   stored as [x, y, z, w]
      mass          (N,)  float64
      inertia       (N,9) float64   row-major diagonal 3x3
      volume        (N,)  float64
      radius        (N,)  float64
  /ONDEM/
    Scene/                     attrs: time, timestep  +  datasets: gravity, units
    Materials/<id>/            scalar datasets per material
    Bodies/
      Walls/                   axis, sense, position, body_id, material_id
    Interactions/              (not used for import)

Quaternion convention
---------------------
YADE stores q as (w, x, y, z) — q[0] = w.
The exporter writes  [x, y, z, w]  (see _quat() in the exporter).
This importer reverses that:  stored [x,y,z,w] → Quaternion(w, x, y, z).

Usage
-----
Inside a YADE script:

    from import_yade_vtkhdf import import_vtkhdf
    import_vtkhdf("sim_0000.vtkhdf")
    O.run(10000, wait=True)

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _v3(arr):
    """Convert a length-3 array-like to a YADE Vector3."""
    return Vector3(float(arr[0]), float(arr[1]), float(arr[2]))


def _read_scene(f):
    """Return (time, dt, gravity_Vector3) from /ONDEM/Scene."""
    sc = f["ONDEM/Scene"]
    time    = float(sc.attrs["time"])
    dt      = float(sc.attrs["timestep"])
    grav    = sc["gravity"][:]           # shape (3,)
    return time, dt, _v3(grav)


def _read_materials(f):
    """
    Reconstruct YADE materials from /ONDEM/Materials/<id>/ groups.
    Returns a dict  {stored_mat_id (int) -> yade_material_index}.
    """
    mat_grp = f["ONDEM/Materials"]
    id_map  = {}   # stored id -> O.materials index

    for key in mat_grp:
        g   = mat_grp[key]
        mid = int(g["id"][()])

        density  = float(g["density"][()])     if "density"  in g else 2600.0
        young    = float(g["young"][()])       if "young"    in g else 1e7
        poisson  = float(g["poisson"][()])     if "poisson"  in g else 0.3
        fric_rad = float(g["friction_angle_rad"][()])  if "friction_angle_rad" in g else 0.5
        label    = g["label"][()].decode()     if "label"    in g else f"mat_{mid}"

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


def _read_spheres(f, mat_id_map):
    """
    Reconstruct sphere bodies from /VTKHDF/PointData/.
    Returns list of newly added YADE body ids.
    """
    pd = f["VTKHDF/PointData"]

    body_ids_stored = pd["body_id"][:]          # (N,) int32
    mat_ids_stored  = pd["material_id"][:]      # (N,) int32
    positions       = pd["position"][:]         # (N,3)
    velocities      = pd["velocity"][:]         # (N,3)
    ang_vels        = pd["angular_velocity"][:] # (N,3)
    orientations    = pd["orientation"][:]      # (N,4) stored as [x,y,z,w]
    masses          = pd["mass"][:]             # (N,)
    inertias        = pd["inertia"][:]          # (N,9) row-major
    radii           = pd["radius"][:]           # (N,)

    N = len(radii)
    print(f"[import] Restoring {N} sphere(s) ...")

    yade_body_ids = []

    for i in range(N):
        r   = float(radii[i])
        mid = int(mat_ids_stored[i])

        # Resolve material — fall back to index 0 if stored id not found
        yade_mat = mat_id_map.get(mid, 0)

        b = utils.sphere(
            center   = (float(positions[i, 0]),
                        float(positions[i, 1]),
                        float(positions[i, 2])),
            radius   = r,
            material = yade_mat,
        )

        # --- linear velocity ---
        b.state.vel = _v3(velocities[i])

        # --- angular velocity ---
        b.state.angVel = _v3(ang_vels[i])

        # --- orientation ---
        # Stored as [x, y, z, w]; YADE Quaternion(w, x, y, z)
        qx, qy, qz, qw = (float(orientations[i, 0]),
                          float(orientations[i, 1]),
                          float(orientations[i, 2]),
                          float(orientations[i, 3]))
        b.state.ori = Quaternion(qw, qx, qy, qz)

        # --- mass (override utils.sphere() computed value) ---
        m = float(masses[i])
        if m > 0.0:
            b.state.mass = m

        # --- inertia (override; stored as flattened 3x3 diagonal) ---
        # inertia[i] = [Ixx, 0, 0, 0, Iyy, 0, 0, 0, Izz]
        Ixx = float(inertias[i, 0])
        Iyy = float(inertias[i, 4])
        Izz = float(inertias[i, 8])
        if Ixx > 0.0:
            b.state.inertia = Vector3(Ixx, Iyy, Izz)

        O.bodies.append(b)
        yade_body_ids.append(b.id)

    return yade_body_ids


def _read_walls(f, mat_id_map):
    """
    Reconstruct wall bodies from /ONDEM/Bodies/Walls/ if present.
    Returns list of newly added YADE body ids.
    """
    path = "ONDEM/Bodies/Walls"
    if path not in f:
        return []

    wg        = f[path]
    axes      = wg["axis"][:]       # (W,) int32
    senses    = wg["sense"][:]      # (W,) int32
    positions = wg["position"][:]   # (W,3)
    mat_ids   = wg["material_id"][:] # (W,) int32

    W = len(axes)
    print(f"[import] Restoring {W} wall(s) ...")

    yade_body_ids = []
    for i in range(W):
        mid      = int(mat_ids[i])
        yade_mat = mat_id_map.get(mid, 0)

        # Wall position scalar: coordinate along the wall's axis
        axis = int(axes[i])
        pos  = float(positions[i, axis])   # extract the relevant coordinate

        b = utils.wall(
            position = pos,
            axis     = axis,
            sense    = int(senses[i]),
            material = yade_mat,
        )
        O.bodies.append(b)
        yade_body_ids.append(b.id)

    return yade_body_ids


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
    restore_time    : bool  Set O.time from the file (default True).
    restore_dt      : bool  Set O.dt   from the file (default True).
    restore_gravity : bool  Set gravity on NewtonIntegrator (default True).
                            Only works if a NewtonIntegrator already exists
                            in O.engines.

    Returns
    -------
    dict with keys:
        'sphere_ids'  – list of YADE body ids for restored spheres
        'wall_ids'    – list of YADE body ids for restored walls
        'mat_id_map'  – dict {stored_material_id -> O.materials index}
    """
    print(f"[import] Reading '{filename}' ...")

    with h5py.File(filename, "r") as f:

        # 1. Scene metadata
        time, dt, gravity = _read_scene(f)

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

        # 3. Spheres
        sphere_ids = _read_spheres(f, mat_id_map)

        # 4. Walls
        wall_ids = _read_walls(f, mat_id_map)

    total = len(sphere_ids) + len(wall_ids)
    print(f"[import] Done. {len(sphere_ids)} sphere(s), {len(wall_ids)} wall(s) "
          f"added → {len(O.bodies)} total bodies in scene.")

    return {
        "sphere_ids" : sphere_ids,
        "wall_ids"   : wall_ids,
        "mat_id_map" : mat_id_map,
    }


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
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
