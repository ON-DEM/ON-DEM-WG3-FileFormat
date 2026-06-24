from base_types import *


class material_general:
	"""General properties shared by all materials"""

	id: int = None
	"""**[mandatory]** material id, $id$, [$-$]"""

	name: str = None
	"""*[optional]* material name"""

	density: float = None
	"""**[mandatory]** particle density, $\\rho$, [$ML^{-3}$]"""


class linear_elastic:
	"""Linear-elastic behaviour"""

	model: str = "linear_elastic"
	"""elastic model"""

	normal_stiffness: float = None
	"""**[mandatory]** normal stiffness, $K_n$, [$FL^{-1}$]"""

	shear_stiffness: float = None
	"""**[mandatory]** shear stiffness, $K_s$, [$FL^{-1}$]"""


class hertz_elastic:
	"""Hertzian-elastic behaviour"""

	model: str = "hertz_elastic"
	"""elastic model"""

	young_modulus: float = None
	"""**[mandatory]** Young's modulus, $E$, [$FL^{-2}$]"""

	poisson_ratio: float = None
	"""**[mandatory]** Poisson's ratio, $\\nu$, [$-$]"""


class visco_elastic:
	"""Visco-elastic damping behaviour"""

	model: str = "visco_elastic"
	"""damping model"""

	normal_damping: float = None
	"""**[mandatory]** normal damping coefficient, $c_n$, [$MT^{-1}$]"""

	shear_damping: float = None
	"""**[mandatory]** shear damping coefficient, $c_s$, [$MT^{-1}$]"""


class frictional_3d:
	"""Sliding-friction behaviour"""

	model: str = "frictional_3d"
	"""friction model"""

	sliding_friction: float = None
	"""**[mandatory]** sliding-friction coefficient, $\\mu_s$, [$-$]"""


class frictional_6d(frictional_3d):
	"""Sliding, rolling and torsional friction behaviour"""

	model: str = "frictional_6d"
	"""friction model"""

	rolling_friction: float = None
	"""**[mandatory]** rolling-friction coefficient, $\\mu_r$, [$-$]"""

	torsion_friction: float = None
	"""**[mandatory]** torsional-friction coefficient, $\\mu_t$, [$-$]"""


class material:
	"""Complete material definition"""

	general: material_general = None
	"""**[mandatory]** general material properties"""

	elastic: object = None
	"""**[mandatory]** elastic behaviour (linear_elastic or hertz_elastic or linear)"""

	damping: object = None
	"""*[optional]* damping behaviour (visco_elastic)"""

	friction: object = None
	"""*[optional]* frictional behaviour (frictional_3d or frictional_6d)"""
