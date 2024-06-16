from base_types import *

class SomeStateClass:
    """abstract state class"""
    pass

class SomeShapeClass:
    """abstract shape class"""
    pass

class SomeMaterialClass:
    """abstract material class"""
    pass


class state:
    """mechanical state"""
    position: Vector3 = Vector3(0,0,0)
    """coordinates - mandatory"""
    velocity: Vector3 = Vector3(0,0,0)
    """translational velocity - mandatory"""
    orientation: Quaternion = Quaternion(0,0,0)
    """orientation - mandatory"""
    spin: Vector3 = Vector3(0,0,0)
    """rotational velocity - mandatory"""
    mass: float = 0
    """body's mass - mandatory"""
    inertia: Matrix3 = Matrix3.zero
    """tensor of inertia - mandatory"""

class thermal_state(state):
    """mechanical + temperature state"""
    temperature: float = 0
    """body's temperature - optional"""

class shape:
    """the shape of a body"""
    color: Vector3 = Vector3(0,0,0)
    """color of a body (RGB values)"""

class sphere(shape):
    """A sphere"""
    radius: float = None
    """sphere radius - mandatory"""


class box(shape):
    """A pearallelepiped"""
    sizes: Vector3 = Vector3(0,0,0)
    """length in each direction of space"""


class polyhedron(shape):
    """A generic polyhedron"""
    vertices: list = []
    """list of positions of the vertices - mandatory"""


class material:
    """material parameters"""
    id: int = None
    """unique identifier - mandatory"""
    density: float = 0
    """mass density - optional"""


class elastic_mat(material):
    """elastic material"""
    young: float = 0
    """uniaxial (Young) stiffness - mandatory"""
    nu: float = 0
    """Poisson coefficient (might be used as shear-to-normal stiffness ratio in some contact models) - mandatory"""


class elastic_frictional_mat(elastic_mat):
    """elastic-frictional material"""
    friction: float = 0
    """friction coefficient - optional"""


class body(SomeStateClass,SomeShapeClass,SomeMaterialClass):
    """a DEM body"""
    state: type(SomeStateClass) = SomeStateClass()
    """The state of the body, instance of a concrete state class"""
    shape: type(SomeShapeClass) = SomeShapeClass()
    """The shape of the body, instance of a concrete shape class"""
    material: type(SomeMaterialClass) = SomeMaterialClass()
    """The material of the body, instance of a concrete material class"""


