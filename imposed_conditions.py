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
	
class inserion:
	"""Defines the general variables needed for all insertion boundaries"""
 
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
	
class cube_insertion(inserion):
	"""Defines a cuboid shaped insertion region"""

	pos_min: Vector3
	"""**[mandatory]** the first corner of the defined region, [$L\\,L\\,L$]"""
	
	pos_max: Vector3
	"""**[mandatory]** the second corner of the defined region (pos_min < pos_max in all components), [$L\\,L\\,L$]"""
 
class cube_deletion:
	"""Defines a cuboid shaped deletion region. All particles entering this region will be deleted"""

	pos_min: Vector3
	"""**[mandatory]** the first corner of the defined region, [$L\\,L\\,L$]"""
	
	pos_max: Vector3
	"""**[mandatory]** the second corner of the defined region (pos_min < pos_max in all components), [$L\\,L\\,L$]"""

