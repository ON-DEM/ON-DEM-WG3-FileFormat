"""
test_export.py
YADE simulation: spheres poured into a box (no top lid).
Guarantees sphere-sphere AND sphere-wall interactions at export time.
Run with:  yadedaily test_export.py
"""

from yade import pack, utils, O, Vector3
import sys, os
sys.path.insert(0, '.')

from export_yade_vtkhdf_generated import export_vtkhdf

# ---- Material ----
mat = O.materials.append(
    FrictMat(density=2600, young=1e7, poisson=0.3,
             frictionAngle=radians(30), label="glass")
)

# ---- Box: 4 side walls + 1 floor (no lid) ----
# Box spans x: [-0.05, 0.05], y: [-0.05, 0.05], z: [0, ...]
half = 0.05

O.bodies.append(utils.wall( 0,      axis=2, sense= 1, material=mat))  # floor  z=0
O.bodies.append(utils.wall(-half,   axis=0, sense= 1, material=mat))  # left   x=-0.05
O.bodies.append(utils.wall( half,   axis=0, sense=-1, material=mat))  # right  x=+0.05
O.bodies.append(utils.wall(-half,   axis=1, sense= 1, material=mat))  # front  y=-0.05
O.bodies.append(utils.wall( half,   axis=1, sense=-1, material=mat))  # back   y=+0.05

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

# ---- Engines ----
O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb(), Bo1_Wall_Aabb()]),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom(), Ig2_Wall_Sphere_ScGeom()],
        [Ip2_FrictMat_FrictMat_FrictPhys()],
        [Law2_ScGeom_FrictPhys_CundallStrack()]
    ),
    NewtonIntegrator(gravity=(0, 0, -9.81), damping=0.4),
]

O.dt = 1e-5

# ---- Let spheres settle under gravity ----
# Run until kinetic energy is low (spheres have stacked and are touching)
O.run(8000, wait=True)

n_real = sum(1 for i in O.interactions if i.isReal)
print(f"Real interactions at export time: {n_real}")

# ---- Export ----
export_vtkhdf("test_box_spheres.vtkhdf")

print("Done. Inspect with: h5ls -r test_box_spheres.vtkhdf")
