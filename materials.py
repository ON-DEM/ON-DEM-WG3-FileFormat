from base_types import *


class material_general:
	"""These are shared material variables for all materials"""
	
	density: float = None
	"""**[mandatory]** material density - particle density [M L^{-3}]"""
	
	friction_coefficient: float = None
	"""**[mandatory]** material friction coefficient [-]"""
	
	id: int = None
	"""**[mandatory]** material id [-]"""
	
class material_spring_constants(material_general):
	"""This material describes linear-elastic behaviour with spring constants"""

	normal_stiffness: float = None
	"""**[mandatory]** normal stiffness [F L^{-1}]"""
	
	shear_stiffness: float = None
	"""**[mandatory]** shear stiffness [F L^{-1}]"""
