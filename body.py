from dataclasses import dataclass, field
from vector3 import Vector3, Quaternion, Matrix3

class SomeStateClass:
    pass

class SomeShapeClass:
    pass

class SomeMaterialClass:
    pass

@dataclass
class State:
    """
    Mechanical state
    """
    position: Vector3 = Vector3(0, 0, 0)  # coordinates - mandatory
    velocity: Vector3 = Vector3(0, 0, 0)  # translational velocity - mandatory
    orientation: Quaternion = Quaternion(0, 0, 0)  # orientation - mandatory
    spin: Vector3 = Vector3(0, 0, 0)  # rotational velocity - mandatory
    mass: float = 0  # body's mass - mandatory
    inertia: Matrix3 = Matrix3.zero  # tensor of inertia - mandatory

@dataclass
class ThermalState(State):
    """
    Mechanical + temperature state
    """
    temperature: float = 0  # body's temperature - optional

@dataclass
class Shape:
    """
    The shape of a body
    """
    color: Vector3 = Vector3(0, 0, 0)  # color of a body (RGB values)

@dataclass
class Sphere(Shape):
    """
    A sphere
    """
    radius: float = None  # sphere radius - mandatory

@dataclass
class Box(Shape):
    """
    A parallelepiped
    """
    sizes: Vector3 = Vector3(0, 0, 0)  # length in each direction of space

@dataclass
class Polyhedron(Shape):
    """
    A generic polyhedron
    """
    vertices: list = field(default_factory=list)  # list of positions of the vertices - mandatory

@dataclass
class Material:
    """
    Material parameters
    """
    id: int = None  # unique identifier - mandatory
    density: float = 0  # mass density - optional

@dataclass
class ElasticMat(Material):
    """
    Elastic material
    """
    young: float = 0  # uniaxial (Young) stiffness - mandatory
    nu: float = 0  # Poisson coefficient - mandatory

@dataclass
class ElasticFrictionalMat(ElasticMat):
    """
    Elastic-frictional material
    """
    friction: float = 0  # friction coefficient - optional

@dataclass
class body(SomeStateClass, SomeShapeClass, SomeMaterialClass):
    """
    A DEM body
    """
    state: SomeStateClass = SomeStateClass() # The state of the body, instance of a concrete state class
    shape: SomeShapeClass = SomeShapeClass()  # The shape of the body, instance of a concrete shape class
    material: SomeMaterialClass = SomeMaterialClass() # The material of the body, instance of a concrete material class
