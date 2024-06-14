from dataclasses import dataclass
from vector3 import Vector3

@dataclass
class Intr:
    """
    This is generic pair interaction and this is a long comment continuing here
    """
    id1: int = None  # **[mandatory]** id of body 1
    id2: int = None  # **[mandatory]** id of body 2
    virtual: bool = False  # *[optional]* whether the interaction is real (else it is in a virtual state - typically without contact)
    lifespan: float = 0  # *[optional]* time since the interaction was created (example of optional data)

@dataclass
class Normal(Intr):
    """
    Interaction in the normal direction
    """
    normal: Vector3 = Vector3(0, 0, 0)  # unit normal [-] - mandatory
    normal_force: float = 0  # normal force magnitude (positive in traction) [F] - mandatory

@dataclass
class Shear(Intr):
    """
    Interaction in the tangential (or shear) direction
    """
    shear_force: Vector3 = Vector3(0, 0, 0)  # shear force [F]

@dataclass
class Intr3D(Normal, Shear):
    """
    3 DOFs interaction combining normal and shear forces
    """
    pass

@dataclass
class ShearLinear(Shear):
    """
    Linear-elasticity
    """
    ks: float = None  # shear stiffness [F/L] - mandatory

@dataclass
class NormalLinear(Shear):
    """
    Linear-elasticity
    """
    ks: float = None  # shear stiffness [F/L] - mandatory

@dataclass
class NormalHertz(Normal):
    """
    Hertzian interaction in the normal direction
    """
    hertz_young: float = None  # equivalent Young modulus [F/L²] - mandatory
    hertz_poisson: float = None  # equivalent Poisson coefficient [-] - mandatory

@dataclass
class Linear3D(Intr3D, NormalLinear, ShearLinear):
    """
    Linear elastic interaction
    """
    pass

@dataclass
class Exotic(NormalHertz, ShearLinear):
    """
    This is an arbitrary combination "à la" MercuryDPM
    """
    pass
