from base_types import *


class intr:
    """This is generic pair interaction and this is a long comment continuing here"""
    id1: int = None
    """**[mandatory]** id of body 1"""
    id2: int = None
    """**[mandatory]** id of body 2"""
    virtual: bool = False
    """*[optional]* weither the interaction is real (else it is in a virtual state - typically without contact)"""
    lifespan: float = 0
    """*[optional]* time since the interaction was created (example of optional data)"""

class normal(intr):
    """interaction in the normal direction"""
    normal: Vector3 = Vector3(0,0,0)
    """**[mandatory]** unit normal [$-$]"""
    normal_force: float = 0
    """**[mandatory]** normal force magnitude (positive in traction) [$F$]"""

class shear(intr):
    """interaction in the tangential (or shear) direction"""
    shear_force: Vector3 = Vector3(0,0,0)
    """shear force [$F$]"""

class intr3D(normal, shear):
    """3 DOFs interaction combining normal and shear forces"""

class shear_linear(shear):
    """linear-elasticity"""
    ks: float = None
    """**[mandatory]** shear stiffness [$F/L$]"""

class normal_linear(normal):
    """linear-elasticity"""
    kn: float = None
    """**[mandatory]** normal stiffness [$F/L$]"""

class normal_linear_viscoelastic(normal_linear):
    """linear-elasticity with viscosity (linear spring dashpot)"""
    normal_damping_ratio: float = None
    """**[mandatory]** normal damping ratio, $\beta_{n}$,  [$F T / L$]"""

class normal_hertz(normal):
    """Hertzian interaction in the normal direction"""
    hertz_young: float = None
    """**[mandatory]** equivalent Young modulus [$F/L²$]"""
    hertz_poisson: float = None
    """**[mandatory]** equivalent Poisson coefficient [$-$]"""


class linear_3D(intr3D, normal_linear, shear_linear):
    """linear elastic interaction"""
    pass

class exotic(normal_hertz, shear_linear):
    """This is an arbitrary combination "à la" MercuryDPM"""
    pass

