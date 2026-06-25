from base_types import *


class periodic_box:
    """Defines 3D-periodic space and its deformation rate"""
    
    shape: Matrix3 = Matrix3.identity
    """**[mandatory]** defines the shape of the periodic pattern, $H$  , [$L$]"""
    
    velocity_gradient: Matrix3 = Matrix3.zero
    """**[mandatory]** velocity gradient, $D$, [$L$]"""

    implementations: list = ['YADE','LAMMPS']
    

class stress_control_boundary:
    """Defines a boundary or set of boundaries that may include stress/strain servo-control algorithms"""

    boundary_id: int = None
    """**[mandatory]** identifies the boundary to be controlled, $b_{id}$, [$-$]"""

    boundary_activate: bool = None
    """**[mandatory]** if True, this boundary moves according to the target value (stress or strain rate), $A$ [$-$]"""
    
    goal: float = None
    """**[mandatory]** defines the desired/required stress, $\sigma_{req}$  , [$FL^{-2}$]"""

    current_stress: float = None
    """**[mandatory]** defines the current/measured stress, $\sigma_{curr}$  , [$FL^{-2}$]"""

    max_strain_rate: float = None
    """**[mandatory]** defines the maximum strain rate allowed for stress/strain control, $\dot{\epsilon}$, [$T^{-1}$]"""

    strain_rate: float = None
    """**[mandatory]** defines the current strain rate allowed for stress/strain control, $\dot{\epsilon}_{curr}$. This required for re-start files, [$T^{-1}$]"""	

    bit_mask: int = None
    """**[mandatory]** determines whether the imposed goal values are stresses (0) or strains (1). Different values for boundary pairs (or sets), $b$, [$-$]"""

    tolerance: float = None
    """**[optional]** if servo-control is used for stress, a tolerance for comparison may be provided, $\sigma_{tol}$, [$-$]"""

    gain: float = None
    """**[optional]** if servo-control is used for stress, a gain parameter (or more) may be provide to modify strain rates, $g$, [$-$]"""

    interval: int = None
    """**[optional]** if servo-control is used for stress, an iteration interval may be used to verify stress and/or strain rates, $\Delta_{check}$, [$-$]"""

    implementations: list = ['YADE','LAMMPS']
    

