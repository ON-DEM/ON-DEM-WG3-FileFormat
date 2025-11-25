from base_types import *

class some_state_class:
    """abstract state class"""
    pass

class some_shape_class:
    """abstract shape class"""
    pass

class some_material_class:
    """abstract material class"""
    pass

class state:
    """mechanical state of a body"""
    position: Vector3 = Vector3(0,0,0)
    """**[mandatory]** position [$L$]"""
    velocity: Vector3 = Vector3(0,0,0)
    """**[mandatory]** translational velocity [$L T^{-1}$]"""
    orientation: Quaternion = Quaternion(0,0,0,1)
    """**[mandatory]** orientation [$-$]"""
    angular_velocity: Vector3 = Vector3(0,0,0)
    """**[mandatory]** angular velocity [$T^{-1}$]"""
    mass: float = None
    """**[mandatory]** body's mass [$M$]"""
    inertia: Matrix3 = Matrix3.zero
    """**[mandatory]** tensor of inertia [$M L^{2}$]"""
    volume: float = None
    """**[mandatory]** volume [$L^{3}$]"""

class thermal_state(state):
    """mechanical + thermal state"""
    temperature: float = None
    """*[optional]* temperature [$\Theta$]"""

class liquid_film(state):
    """mechanical + liquid film state"""
    liquid_film_volume: float = None
    """*[optional]* liquid film volume [L^3]"""

class shape:
    """shape of a body"""
    color: Vector3 = Vector3(1,1,1)
    """*[optional]* RGB color values [$-$]"""

class sphere(shape):
    """sphere"""
    radius: float = None
    """**[mandatory]** radius"""

class box(shape):
    """cuboid"""
    dimensions: Vector3 = Vector3(0,0,0)
    """**[mandatory]** length in each direction of space"""

class polyhedron(shape):
    """A generic polyhedron"""
    vertices: list = []
    """*[optional]* list of positions of the vertices - mandatory"""


class body:
    """class defining a body"""
    material_id: int = -1
    """**[mandatory]** material id [$-$]"""
    clump_id: int = -1
    """**[mandatory]** clump id [$-$]"""
    body_id: int = None
    """**[mandatory]** body id [$-$]"""
    body_state: type(state) = state()
    """**[mandatory]** body state [$-$]"""
    body_shape: type(shape) = shape()
    """**[mandatory]** body shape [$-$]"""


#class body(SomeStateClass,SomeShapeClass,SomeMaterialClass):
#    """a DEM body"""
#    state: type(SomeStateClass) = SomeStateClass()
#    """The state of the body, instance of a concrete state class"""
#    shape: type(SomeShapeClass) = SomeShapeClass()
#    """The shape of the body, instance of a concrete shape class"""
#    material: type(SomeMaterialClass) = SomeMaterialClass()
#    """The material of the body, instance of a concrete material class"""

