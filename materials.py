from base_types import *


class material_base:
	"""These are shared material variables for all materials"""
	
	density: float = None
	"""**[mandatory]** material density - particle density, $\rho$, [$ML^{-3}$]"""
	
	friction_coefficient: float = None
	"""**[mandatory]** material friction coefficient, $\\mu$, [$-$]"""
	
	id: int = None
	"""**[mandatory]** material id, $id$, [$-$]"""
	
class spring_constants(material_base):
	"""This material describes linear-elastic behaviour with spring constants"""

	normal_stiffness: float = None
	"""**[mandatory]** normal stiffness, $K_{n}$, [$FL^{-1}$]"""
	
	shear_stiffness: float = None
	"""**[mandatory]** shear stiffness, $K_{s}$, [$FL^{-1}$]"""

class spring_dashpot(spring_constants):
	"""This material describes linear viscoelastic behaviour"""

	normal_viscosity: float = None
	"""**[mandatory]** normal damping coefficient, $c_{n}$, [$MT^{-1}$]"""
	
	shear_viscosity: float = None
	"""**[mandatory]** shear damping coefficient, $c_{s}$, [$MT^{-1}$]"""

class elastic_constants(material_base):
	"""This material describes Hertzian-elastic behaviour with elasticity parameters"""

	young: float = None
	"""**[mandatory]** young modulus, $E$, [$FL^{-2}$]"""
	
	poisson: float = None
	"""**[mandatory]** poisson coefficient, $\nu$, [$-$]"""

class visco_elastic_constant_COR(elastic_constants):
	"""This material describes visco-elastic behaviour with constant coefficient of restitution"""

	normal_damping_ratio: float = None
	"""**[mandatory]** normal damping coefficient, $\\beta_n$  [$-$]"""
	
	shear_damping_ratio: float = None
	"""**[mandatory]** shear damping coefficient, $\\beta_s$ [$-$]"""

class visco_elastic_variable_COR(elastic_constants):
	"""This material describes visco-elastic behaviour with variable coefficient of restitution"""

	relaxation_time: float = None
	"""**[mandatory]** relaxation time, $A$, [$T$]"""

class liquid_bridge(material_base):
	"""This material describes a liquid bridge model"""

	surfaceTension_: float = None
	"""**[mandatory]** surface tension of the liquid, $\\gamma$ [$F/L$]"""

	contactAngle_: float = None
	"""**[mandatory]** contact angle between particle and liquid bridge surface, $\\Theta$ [$-$]"""

class liquid_bridge_migration(liquid_bridge):
	"""This material describes a liquid bridge migration model"""

	liquid_bridge_volume_min: float = None
	"""**[mandatory]** the minimum liquid volume needed to form a bridge, $V_\\mathrm{min}$ [$L^3$]"""

	liquid_bridge_volume_max: float = None
	"""**[mandatory]** the maximum liquid volume, a liquid bridge gets during formation, $V_\\mathrm{max}$ [$L^3$]"""

	distribution_coefficient: float = None
	"""**[mandatory]** the fraction of the liquid that is to be distributed to the neighboring contacts of the particles after a liquid bridge rupture, $f$ [$-$]"""

class liquid_bridge_static(liquid_bridge):
	"This material describes a liquid bridge model, where every contact has the same liquid volume"

	liquid_bridge_volume: float = None
	"""**[mandatory]** the liquid volume of a bridge, $V$ [$L^3$]"""