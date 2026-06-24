from base_types import *


class material_general:
	"""These are shared material variables for all materials"""
	
	density: float = None
	"""**[mandatory]** material density - particle density, $\rho$, [$ML^{-3}$]"""
	
	friction_coefficient: float = None
	"""**[mandatory]** material friction coefficient, $\mu$, [$-$]"""
	
	id: int = None
	"""**[mandatory]** material id, $id$, [$-$]"""
	
class material_spring_constants(material_general):
	"""This material describes linear-elastic behaviour with spring constants"""

	normal_stiffness: float = None
	"""**[mandatory]** normal stiffness, $K_{n}$, [$FL^{-1}$]"""
	
	shear_stiffness: float = None
	"""**[mandatory]** shear stiffness, $K_{s}$, [$FL^{-1}$]"""

class material_spring_dashpot(material_spring_constants):
	"""This material describes linear viscoelastic behaviour"""

	normal_viscosity: float = None
	"""**[mandatory]** normal damping coefficient, $c_{n}$, [$MT^{-1}$]"""
	
	shear_viscosity: float = None
	"""**[mandatory]** shear damping coefficient, $c_{s}$, [$MT^{-1}$]"""

class material_elastic_constants(material_general):
	"""This material describes Hertzian-elastic behaviour with elasticity parameters"""

	young: float = None
	"""**[mandatory]** young modulus, $E$, [$FL^{-2}$]"""
	
	poisson: float = None
	"""**[mandatory]** poisson coefficient, $\nu$, [$-$]"""

class material_visco_elastic_constant_COR(material_elastic_constants):
	"""This material describes visco-elastic behaviour with constant coefficient of restitution"""

	normal_damping_ratio: float = None
	"""**[mandatory]** normal damping coefficient, $\\beta_n$  [$-$]"""
	
	shear_damping_ratio: float = None
	"""**[mandatory]** shear damping coefficient, $\\beta_s$ [$-$]"""

class material_visco_elastic_variable_COR(material_elastic_constants):
	"""This material describes visco-elastic behaviour with variable coefficient of restitution"""

	relaxation_time: float = None
	"""**[mandatory]** relaxation time, $A$, [$T$]"""

class thermal_Blaze(material_elastic_constants):
	"""This material describes thermal behaviour dependent on friction and cohesion"""

	friction_source: float = None
	"""**[mandatory]** friction value used for heat generation, $\mu_{\theta}$, [$-$]"""
    thermal_conduction: float = None
    """**[mandatory]** thermal conduction of the material, $c_v$, [$E/(L*\theta)$]"""
    thermal_capacity: float = None
    """**[mandatory]** thermal capacity of the material, $c_p$, [$E/\theta$]"""
    initial_themperature: float = None
    """**[mandatory]** initial temperature the material, $T_0$, [$\theta$]"""
    contact_area_effective: float = None
    """**[mandatory]** \% of contact area, $A_{eff}$, [$-$]"""
    cohesion_rate: float = None
    """**[mandatory]** cohesion rate, ${SE_rate}$, [$E/(L^2*T)$]"""
    min_temp: float = None
    """**[optional]** min temperature limit of the material,  $T_{min}$, [$\theta$]"""
    max_temp: float = None
    """**[optional]** max temperature limit of the material,  $T_{max}$, [$\theta$]"""
    cohesion_limit: float = None
    """**[optional]** max surface energy value, ${SE_max}$, [$E/L^2$]"""
    thickness: float = None
    """**[optional]** artificial thickness for geometry, $\delta\ d$, [$L$]"""
    
