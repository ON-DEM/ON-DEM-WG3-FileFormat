from base_types import *

class base_state:
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
    inertia: Matrix3 = Matrix3.zero()
    """**[mandatory]** tensor of inertia [$M L^{2}$]"""
    volume: float = None
    """**[mandatory]** volume [$L^{3}$]"""

class thermal(base_state):
    """mechanical + thermal state"""
    temperature: float = None
    """*[optional]* temperature [$\\Theta$]"""

class liquid_film(base_state):
    """mechanical + liquid film state"""
    liquid_film_volume: float = None
    """*[optional]* liquid film volume [L^3]"""

class base_shape:
    """shape of a body"""
    color: Vector3 = Vector3(1,1,1)
    """*[optional]* RGB color values [$-$]"""

class sphere(base_shape):
    """sphere"""
    radius: float = None
    """**[mandatory]** radius"""

class box(base_shape):
    """cuboid"""
    dimensions: Vector3 = Vector3(0,0,0)
    """**[mandatory]** length in each direction of space"""

class polyhedron(base_shape):
    """A generic polyhedron"""
    vertices: list = []
    """**[mandatory]** list of positions of the vertices"""


class base_body:
    """class defining a body"""
    material_id: int = -1
    """**[mandatory]** material id [$-$]"""
    clump_id: int = -1
    """**[mandatory]** clump id [$-$]"""
    body_id: int = None
    """**[mandatory]** body id [$-$]"""
    body_state: type(base_state) = base_state()
    """**[mandatory]** body state [$-$]"""
    body_shape: type(base_shape) = base_shape()
    """**[mandatory]** body shape [$-$]"""
    display_group: int = 0
    """*[optional]* display group of the body: index into ``scene.display_group_names``. It selects the VTKHDF block in which the body is shown. Only relevant for visualisation, no effect on the mechanics. Default 0, so a file without display groups puts every body in the single default group [$-$]"""


#class body(SomeStateClass,SomeShapeClass,SomeMaterialClass):
#    """a DEM body"""
#    state: type(SomeStateClass) = SomeStateClass()
#    """The state of the body, instance of a concrete state class"""
#    shape: type(SomeShapeClass) = SomeShapeClass()
#    """The shape of the body, instance of a concrete shape class"""
#    material: type(SomeMaterialClass) = SomeMaterialClass()
#    """The material of the body, instance of a concrete material class"""

