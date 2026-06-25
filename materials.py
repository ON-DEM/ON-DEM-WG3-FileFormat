from base_types import *


class base_material:
    """General properties shared by all materials."""

    id: int = None
    """**[mandatory]** material id, $id$, [$-$]"""

    density: float = None
    """**[mandatory]** particle density, $\\rho$, [$ML^{-3}$]"""


class linear_elastic(base_material):
	"""Material with linear-elastic behaviour."""

	normal_stiffness: float = None
	"""**[mandatory]** normal stiffness, $K_n$, [$FL^{-1}$]"""

	shear_stiffness: float = None
	"""**[mandatory]** shear stiffness, $K_s$, [$FL^{-1}$]"""


class hertz_elastic(base_material):
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


class base_thermal(linear_elastic):
    """Material with linear-elastic and thermal behaviour."""

    thermal_conductivity: float = None
    """**[mandatory]** thermal conductivity, $k$, [$E/(LT\\theta)$]"""

    thermal_capacity: float = None
    """**[mandatory]** thermal capacity, $c_p$, [$E/\\theta$]"""

    initial_temperature: float = None
    """**[mandatory]** initial temperature, $T_0$, [$\\theta$]"""

    min_temp: float = None
    """*[optional]* minimum temperature, $T_\\mathrm{min}$, [$\\theta$]"""

    max_temp: float = None
    """*[optional]* maximum temperature, $T_\\mathrm{max}$, [$\\theta$]"""


class thermal_blaze(base_thermal):
    """Material with frictional heat generation and cohesion evolution."""

    friction_source: float = None
    """**[mandatory]** friction coefficient used for heat generation, $\\mu_\\theta$, [$-$]"""

    contact_area_effective: float = None
    """**[mandatory]** effective fraction of the contact area, $A_\\mathrm{eff}$, [$-$]"""

    cohesion_rate: float = None
    """**[mandatory]** cohesion rate, $SE_\\mathrm{rate}$, [$E/(L^2T)$]"""

    cohesion_limit: float = None
    """*[optional]* maximum surface energy, $SE_\\mathrm{max}$, [$E/L^2$]"""

    thickness: float = None
    """*[optional]* artificial geometrical thickness, $\\delta d$, [$L$]"""


class basic_luding(linear_elastic):
    """Material with Luding-type elasto-plastic adhesive behaviour."""

    normal_stiffness_plastic: float = None
    """**[mandatory]** plastic loading stiffness, $K_1$, [$FL^{-1}$]"""

    normal_stiffness_unloading_reloading: float = None
    """**[mandatory]** unloading and reloading stiffness, $K_n^U$, [$FL^{-1}$]"""

    normal_stiffness_tensile: float = None
    """**[mandatory]** tensile adhesive stiffness, $K_\\mathrm{adh}^U$, [$FL^{-1}$]"""


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
