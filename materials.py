from base_types import *


class base_material:
    """These are shared material variables for all materials"""
    
    density: float = None
    """**[mandatory]** material density - particle density, $\\rho$, [$ML^{-3}$]"""
    
    friction_coefficient: float = None
    """**[mandatory]** material friction coefficient, $\\mu$, [$-$]"""
    
    id: int = None
    """**[mandatory]** material id, $id$, [$-$]"""
    
class spring_constants(base_material):
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

class elastic_constants(base_material):
    """This material describes Hertzian-elastic behaviour with elasticity parameters"""

    young: float = None
    """**[mandatory]** young modulus, $E$, [$FL^{-2}$]"""
    
    poisson: float = None
    """**[mandatory]** poisson coefficient, $\\nu$, [$-$]"""

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

class base_thermal(elastic_constants):
    """This material describes thermal behaviour"""
    thermal_conduction: float = None
    """**[mandatory]** thermal conduction of the material, $c_v$, [$E/(L*\\theta)$]"""
    thermal_capacity: float = None
    """**[mandatory]** thermal capacity of the material, $c_p$, [$E/\\theta$]"""
    initial_themperature: float = None
    """**[mandatory]** initial temperature the material, $T_0$, [$\\theta$]"""
    min_temp: float = None
    """**[optional]** min temperature limit of the material,  $T_{min}$, [$\\theta$]"""
    max_temp: float = None
    """**[optional]** max temperature limit of the material,  $T_{max}$, [$\\theta$]"""

class thermal_blaze(base_thermal):
    """This material describes thermal behaviour dependent on friction and cohesion"""

    friction_source: float = None
    """**[mandatory]** friction value used for heat generation, $\mu_{\\theta}$, [$-$]"""
    contact_area_effective: float = None
    """**[mandatory]** \% of contact area, $A_{eff}$, [$-$]"""
    cohesion_rate: float = None
    """**[mandatory]** cohesion rate, $SE_{rate}$, [$E/(L^2*T)$]"""
    cohesion_limit: float = None
    """**[optional]** max surface energy value, $SE_{max}$, [$E/L^2$]"""
    thickness: float = None
    """**[optional]** artificial thickness for geometry, $\delta\ d$, [$L$]"""
    
class basic_luding(spring_constants):
    """This material describes linear-elastic behaviour with spring constants"""

    normal_stiffness_plastic: float = None
    """**[mandatory]** normal stiffness in plastic branch, $K_{1}$, [$FL^{-1}$]"""

    normal_stiffness_unloading_reloading: float = None
    """**[mandatory]** normal stiffness in unloading and reloading elastic branch, $K_{n}^{U}$, [$FL^{-1}$]"""
    
    normal_stiffness_tensile: float = None
    """**[mandatory]** normal stiffness in tensile adhesive branch, $K_{adh}^{U}$, [$FL^{-1}$]"""

class liquid_bridge(base_material):
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
