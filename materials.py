from base_types import *


class material_general:
	"""These are shared material variables for all materials"""
	
	density: float = None
	"""**[mandatory]** material density - particle density, $\rho$, [$M L^{-3}$]"""
	
	friction_coefficient: float = None
	"""**[mandatory]** material friction coefficient, $\mu$, [$-$]"""
	
	id: int = None
	"""**[mandatory]** material id, $id$, [$-$]"""
	
class material_spring_constants(material_general):
	"""This material describes linear-elastic behaviour with spring constants"""

	normal_stiffness: float = None
	"""**[mandatory]** normal stiffness, $K_{n}$, [$F L^{-1}$]"""
	
	shear_stiffness: float = None
	"""**[mandatory]** shear stiffness, $K_{s}$, [$F L^{-1}$]"""

class material_spring_dashpot(material_spring_constants):
	"""This material describes linear viscoelastic behaviour"""

	normal_viscosity: float = None
	"""**[mandatory]** normal damping coefficient, $c_{n}$, [$M T^{-1}$]"""
	
	shear_viscosity: float = None
	"""**[mandatory]** shear damping coefficient, $c_{s}$, [$M T^{-1}$]"""

class material_elastic_constants(material_general):
	"""This material describes Hertzian-elastic behaviour with elasticity parameters"""

	young: float = None
	"""**[mandatory]** young modulus, $E$, [$F L^{-2}$]"""
	
	poisson: float = None
	"""**[mandatory]** poisson coefficient, $\nu$, [$-$]"""

class material_visco_elastic_constant_COR(material_elastic_constants):
	"""This material describes visco-elastic behaviour with constant coefficient of restitution"""

	normal_damping_ratio: float = None
	"""**[mandatory]** normal damping coefficient, $\beta_{n}$, [$-$]"""
	
	shear_damping_ratio: float = None
	"""**[mandatory]** shear damping coefficient, $\beta_{s}$, [$-$]"""

class material_visco_elastic_variable_COR(material_elastic_constants):
	"""This material describes visco-elastic behaviour with variable coefficient of restitution"""

	relaxation_time: float = None
	"""**[mandatory]** relaxation time, $A$, [$T$]"""

