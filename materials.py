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

class material_elastic_constants(material_general):
	"""This material describes linear-elastic behaviour with elasticity parameters"""

	young: float = None
	"""**[mandatory]** young modulus, $E$, [$F L^{-2}$]"""
	
	poisson: float = None
	"""**[mandatory]** poisson coefficient, $\nu$, [$-$]"""

class material_visco_elastic_constants_COR(material_elastic_constants):
	"""This material describes visco-elastic behaviour with constant coefficient of restitution"""

	damping_coefficient_normal: float = None
	"""**[mandatory]** normal damping coefficient, $c_{n}$, [$M T^{-1}$]"""
	
	damping_coefficient_shear: float = None
	"""**[mandatory]** shear damping coefficient, $c_{s}$, [$M T^{-1}$]"""

class material_visco_elastic_variable_COR(material_elastic_constants):
	"""This material describes visco-elastic behaviour with variable coefficient of restitution"""

	dissipative_constant: float = None
	"""**[mandatory]** dissipative constant, $A$, [$ $]"""

