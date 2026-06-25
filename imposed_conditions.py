from base_types import *


class periodic_box:
    """Defines 3D-periodic space and its deformation rate"""
    
    shape: Matrix3 = Matrix3.identity
    """**[mandatory]** defines the shape of the periodic pattern, $H$  , [$L$]"""
    
    velocity_gradient: Matrix3 = Matrix3.zero
    """**[mandatory]** velocity gradient, $D$, [$L$]"""

    implementations: list = ['YADE','LAMMPS']

class periodic_walls:
	"""Defines two parrallel planes enclosing a periodic space"""
	
	normal: Vector3 = None
	"""**[mandatory]** the direction normal to the planes"""
 
	distance_left: float = 0
	"""**[mandatory]** the distance of the wall from the origin against the direction of the normal"""
 
	distance_right: float = 0
	"""**[mandatory]** the distance of the wall from the origin in the direction of the normal"""

	implementations: list = ['MercuryDPM']
	
class insertion:
	"""Defines the general variables needed for all insertion boundaries"""
	
	position: Vector3
	"""**[mandatory]** the position of the insertion region"""
 
	orientation: Quaternion
	"""**[mandatory]** the orientation of the insertion region"""
 
	initial_volume: float
	"""**[mandatory]** volume of particles that get's inserted initially, $V$, [$L^3$]"""
  
	volume_flow_rate: float
	"""**[mandatory]** volume of particles that get's inserted per time unit, $q$, [$L^3/T$]"""
	
	velocity_min: Vector3
	"""**[mandatory]** particles get a random initial velocity, uniformly distributed between velocity_min and velocity_max, $v_\\mathrm{min}$, [$L/T$]"""
	
	velocity_max: Vector3
	"""**[mandatory]** particles get a random initial velocity, uniformly distributed between velocity_min and velocity_max, $v_\\mathrm{min}$, [$L/T$]"""
	
	particle_size_distribution: Vector3
	"""**[mandatory]** particle size is distributed according to a certain volumetric particle size distribution, [$-$]"""
	
	material: int
	"""**[mandatory]** index indicating which material properties are given to the inserted particles, [$-$]"""
	
class cube_insertion(insertion):
	"""Defines a cuboid shaped insertion region"""

	extent: Vector3
	"""**[mandatory]** the dimension of the box in the unrotated frame. The box spans from position-extent/2 to position+extent/2, [$L,\\,L,\\,L$]"""
 
class cube_deletion:
	"""Defines a cuboid shaped deletion region. All particles entering this region will be deleted"""
	
	position: Vector3
	"""**[mandatory]** the position of the deletion region"""
 
	orientation: Quaternion
	"""**[mandatory]** the orientation of the deletion region"""

	extent: Vector3
	"""**[mandatory]** the dimension of the box in the unrotated frame. The box spans from position-extent/2 to position+extent/2, [$L,\\,L,\\,L$]"""

class stress_control_boundary:
    """Defines a boundary or set of boundaries that may include stress/strain servo-control algorithms"""

    boundary_id: int = None
    """**[mandatory]** identifies the boundary to be controlled, $b_{id}$, [$-$]"""

    boundary_activate: bool = None
    """**[mandatory]** if True, this boundary moves according to the target value (stress or strain rate), $A$ [$-$]"""
    
    goal: float = None
    """**[mandatory]** defines the desired/required stress, $\sigma_{req}$  , [$FL^{-2}$]"""

    current_stress: float = None
    """**[mandatory]** defines the current/measured stress, $\sigma_{curr}$  , [$FL^{-2}$]"""

    max_strain_rate: float = None
    """**[mandatory]** defines the maximum strain rate allowed for stress/strain control, $\dot{\epsilon}$, [$T^{-1}$]"""

    strain_rate: float = None
    """**[mandatory]** defines the current strain rate allowed for stress/strain control, $\dot{\epsilon}_{curr}$. This required for re-start files, [$T^{-1}$]"""	

    bit_mask: int = None
    """**[mandatory]** determines whether the imposed goal values are stresses (0) or strains (1). Different values for boundary pairs (or sets), $b$, [$-$]"""

    tolerance: float = None
    """**[optional]** if servo-control is used for stress, a tolerance for comparison may be provided, $\sigma_{tol}$, [$-$]"""

    gain: float = None
    """**[optional]** if servo-control is used for stress, a gain parameter (or more) may be provide to modify strain rates, $g$, [$-$]"""

    interval: int = None
    """**[optional]** if servo-control is used for stress, an iteration interval may be used to verify stress and/or strain rates, $\Delta_{check}$, [$-$]"""

    implementations: list = ['YADE','LAMMPS']
    

