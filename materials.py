from base_types import *


class material_general:
	"""General properties shared by all materials."""

	id: int = None
	"""**[mandatory]** material id, $id$, [$-$]"""

	density: float = None
	"""**[mandatory]** particle density, $\\rho$, [$ML^{-3}$]"""


class linear_elastic(material_general):
	"""Material with linear-elastic behaviour."""

	normal_stiffness: float = None
	"""**[mandatory]** normal stiffness, $K_n$, [$FL^{-1}$]"""

	shear_stiffness: float = None
	"""**[mandatory]** shear stiffness, $K_s$, [$FL^{-1}$]"""


class hertz_elastic(material_general):
	"""Material with Hertzian-elastic behaviour."""

	young_modulus: float = None
	"""**[mandatory]** Young's modulus, $E$, [$FL^{-2}$]"""

	poisson_ratio: float = None
	"""**[mandatory]** Poisson's ratio, $\\nu$, [$-$]"""


class linear_visco_elastic(linear_elastic):
	"""Material with linear visco-elastic damping behaviour."""

	normal_damping: float = None
	"""**[mandatory]** normal damping coefficient, $c_n$, [$MT^{-1}$]"""


class linear_visco_elastic_constant_cor(linear_elastic):
	"""Material with linear visco-elastic damping behaviour and mass-independent coefficient of restitution."""

	normal_damping_ratio: float = None
	"""**[mandatory]** normal damping coefficient, $\\beta_n$  [$-$]"""


class linear_visco_elastic_variable_cor(linear_elastic):
	"""Material with linear visco-elastic damping behaviour and velocity-dependent coefficient of restitution."""

	relaxation_time: float = None
	"""**[mandatory]** relaxation time, $A$, [$T$]"""


class frictional_3D:
	"""Adds sliding friction behaviour to any material."""

	shear_friction: float = None
	"""**[mandatory]** sliding-friction coefficient, $\\mu_s$, [$-$]"""

	shear_damping: float = None
	"""**[mandatory]** shear damping coefficient, $c_s$, [$MT^{-1}$]"""


class frictional_6D(frictional_3D):
	"""Adds sliding, rolling and torsional friction to any material."""

	model: str = "frictional_6D"
	"""Friction model."""

	rolling_friction: float = None
	"""**[mandatory]** rolling-friction coefficient, $\\mu_r$, [$-$]"""

	rolling_damping: float = None
	"""**[mandatory]** rolling damping coefficient, $c_r$, [$MT^{-1}$]"""

	torsion_friction: float = None
	"""**[mandatory]** torsional-friction coefficient, $\\mu_t$, [$-$]"""

	torsion_damping: float = None
	"""**[mandatory]** torsional damping coefficient, $c_t$, [$MT^{-1}$]"""


class liquid_bridge:
	"""Adds a liquid-bridge model to any material."""

	surface_tension: float = None
	"""**[mandatory]** surface tension of the liquid, $\\gamma$ [$F/L$]"""

	contact_angle: float = None
	"""**[mandatory]** contact angle between particle and liquid bridge surface, $\\Theta$ [$-$]"""


class liquid_bridge_migration(liquid_bridge):
	"""Adds a liquid-bridge migration model to any material."""

	liquid_bridge_volume_min: float = None
	"""**[mandatory]** the minimum liquid volume needed to form a bridge, $V_\\mathrm{min}$ [$L^3$]"""

	liquid_bridge_volume_max: float = None
	"""**[mandatory]** the maximum liquid volume, a liquid bridge gets during formation, $V_\\mathrm{max}$ [$L^3$]"""

	distribution_coefficient: float = None
	"""**[mandatory]** the fraction of the liquid that is to be distributed to the neighboring contacts of the particles after a liquid bridge rupture, $f$ [$-$]"""


class liquid_bridge_static(liquid_bridge):
	"""Adds a liquid-bridge model in which every contact has the same liquid volume."""

	liquid_bridge_volume: float = None
	"""**[mandatory]** the liquid volume of a bridge, $V$ [$L^3$]"""


class linear_elastic_frictional_3D(linear_elastic, frictional_3D):
	"""Material with linear-elastic behaviour and sliding friction."""
	pass


class linear_visco_elastic_frictional_3D(linear_visco_elastic, frictional_3D):
	"""Material with linear visco-elastic behaviour and sliding friction."""
	pass


class linear_elastic_frictional_6D(linear_elastic, frictional_6D):
	"""Material with linear-elastic behaviour and sliding, rolling and torsional friction."""
	pass


class linear_visco_elastic_frictional_3D_liquid_bridge(
	linear_visco_elastic,
	frictional_3D,
	liquid_bridge
):
	"""Material with linear visco-elastic behaviour, sliding friction and liquid-bridge forces."""
	pass
