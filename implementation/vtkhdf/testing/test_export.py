"""
test_export.py
Minimal YADE simulation: 5 spheres on a base plane.
Run with:  yade test_export.py
"""

from yade import pack, utils, O, Vector3
from export_yade_vtkhdf_generated import export_vtkhdf

# ---- Material ----
mat = O.materials.append(
    FrictMat(density=2600, young=1e7, poisson=0.3,
             frictionAngle=radians(30), label="glass")
)

# ---- Base wall ----
O.bodies.append(utils.wall(0, axis=2, sense=1, material=mat))

# ---- 5 spheres ----
r = 0.01   # 1 cm radius
positions = [
    Vector3( 0.00,  0.00, r),
    Vector3( 0.03,  0.00, r),
    Vector3(-0.03,  0.00, r),
    Vector3( 0.00,  0.03, r),
    Vector3( 0.00, -0.03, r),
]
for pos in positions:
    O.bodies.append(utils.sphere(pos, r, material=mat))

# ---- Engines ----
O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb(), Bo1_Wall_Aabb()]),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom(), Ig2_Wall_Sphere_ScGeom()],
        [Ip2_FrictMat_FrictMat_FrictPhys()],
        [Law2_ScGeom_FrictPhys_CundallStrack()]
    ),
    NewtonIntegrator(gravity=(0, 0, -9.81), damping=0.3),
]

O.dt = 1e-5

# ---- Run a few steps so contacts form ----
O.run(100, wait=True)

# ---- Export ----
export_vtkhdf("test_5spheres.vtkhdf")

print("Done. Inspect with: h5ls -r test_5spheres.vtkhdf")
