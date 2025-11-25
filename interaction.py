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
    """unit normal [-] - mandatory"""
    normal_force: float = 0
    """normal force magnitude (positive in traction) [F] - mandatory"""

class shear(intr):
    """interaction in the tangential (or shear) direction"""
    shear_force: Vector3 = Vector3(0,0,0)
    """shear force [F]"""

class intr3D(normal, shear):
    """3 DOFs interaction combining normal and shear forces"""


class shear_linear(shear):
    """linear-elasticity"""
    ks: float = None
    """shear stiffness [F/L] - mandatory"""

class normal_linear(normal):
    """linear-elasticity"""
    kn: float = None
    """normal stiffness [F/L] - mandatory"""

class normal_hertz(normal):
    """Hertzian interaction in the normal direction"""
    hertz_young: float = None
    """equivalent Young modulus [F/L²] - mandatory"""
    hertz_poisson: float = None
    """equivalent Poisson coefficient [-] - mandatory"""


class linear_3D(intr3D, normal_linear, shear_linear):
    """linear elastic interaction"""
    pass

class exotic(normal_hertz, shear_linear):
    """This is an arbitrary combination "à la" MercuryDPM"""
    pass

