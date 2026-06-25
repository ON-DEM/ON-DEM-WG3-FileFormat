from base_types import *


class material_general:
	"""General properties shared by all materials"""

	id: int = None
	"""**[mandatory]** material id, $id$, [$-$]"""

	density: float = None
	"""**[mandatory]** particle density, $\\rho$, [$ML^{-3}$]"""


class linear_elastic:
	"""Linear-elastic behaviour"""

	normal_stiffness: float = None
	"""**[mandatory]** normal stiffness, $K_n$, [$FL^{-1}$]"""

	shear_stiffness: float = None
	"""**[mandatory]** shear stiffness, $K_s$, [$FL^{-1}$]"""


class hertz_elastic:
	"""Hertzian-elastic behaviour"""

	young_modulus: float = None
	"""**[mandatory]** Young's modulus, $E$, [$FL^{-2}$]"""

	poisson_ratio: float = None
	"""**[mandatory]** Poisson's ratio, $\\nu$, [$-$]"""


class linear_visco_elastic(linear_elastic):
	"""Visco-elastic damping behaviour"""

	normal_damping: float = None
	"""**[mandatory]** normal damping coefficient, $c_n$, [$MT^{-1}$]"""

class linear_visco_elastic_constant_COR(linear_elastic):
	"""This describes visco-elastic behaviour with mas-independent coefficient of restitution"""

	normal_damping_ratio: float = None
	"""**[mandatory]** normal damping coefficient, $\\beta_n$  [$-$]"""

class linear_visco_elastic_variable_COR(linear_elastic):
	"""This material describes visco-elastic behaviour with variable coefficient of restitution"""

	relaxation_time: float = None
	"""**[mandatory]** relaxation time, $A$, [$T$]"""


class frictional_3d:
	"""Sliding friction behaviour"""

	shear_friction: float = None
	"""**[mandatory]** sliding-friction coefficient, $\\mu_s$, [$-$]"""

	shear_damping: float = None
	"""**[mandatory]** shear damping coefficient, $c_s$, [$MT^{-1}$]"""

class frictional_6d(frictional_3d):
	"""Sliding, rolling and torsional friction behaviour"""

	model: str = "frictional_6d"
	"""friction model"""

	rolling_friction: float = None
	"""**[mandatory]** rolling-friction coefficient, $\\mu_r$, [$-$]"""

	rolling_damping: float = None
	"""**[mandatory]** shear damping coefficient, $c_s$, [$MT^{-1}$]"""

	torsion_friction: float = None
	"""**[mandatory]** torsional-friction coefficient, $\\mu_t$, [$-$]"""

	rolling_damping: float = None
	"""**[mandatory]** shear damping coefficient, $c_s$, [$MT^{-1}$]"""

class material_liquid_bridge(material_general):
	"""This material describes a liquid bridge model"""

	surfaceTension: float = None
	"""**[mandatory]** surface tension of the liquid, $\\gamma$ [$F/L$]"""

	contactAngle: float = None
	"""**[mandatory]** contact angle between particle and liquid bridge surface, $\\Theta$ [$-$]"""

class material_liquid_bridge_migration(material_liquid_bridge):
	"""This material describes a liquid bridge migration model"""

	liquid_bridge_volume_min: float = None
	"""**[mandatory]** the minimum liquid volume needed to form a bridge, $V_\\mathrm{min}$ [$L^3$]"""

	liquid_bridge_volume_max: float = None
	"""**[mandatory]** the maximum liquid volume, a liquid bridge gets during formation, $V_\\mathrm{max}$ [$L^3$]"""

	distribution_coefficient: float = None
	"""**[mandatory]** the fraction of the liquid that is to be distributed to the neighboring contacts of the particles after a liquid bridge rupture, $f$ [$-$]"""

class material_liquid_bridge_static(material_liquid_bridge):
	"This material describes a liquid bridge model, where every contact has the same liquid volume"

	liquid_bridge_volume: float = None
	"""**[mandatory]** the liquid volume of a bridge, $V$ [$L^3$]"""

class material_linear_elastic_frictional_3D(material_general, linear_elastic, frictional_3d):
	"""General material with linear elastic frictional contact forces"""
	pass
class material_linear_visco_elastic_frictional_3d(material_general, linear_visco_elastic, frictional_3d):
	"""General material with linear visco-elastic frictional_3d contact forces"""
	pass
class material_linear_elastic_frictional_6D(material_general, linear_visco_elastic, frictional_6d):
	"""General material with linear elastic frictional_6d contact forces"""
	pass

class material_liquid_bridge_linear_visco_elastic_frictional_3d(material_liquid_bridge, linear_visco_elastic, frictional_3d):
	"""Material with liquid bridges and linear visco-elastic frictional contact forces"""
	pass