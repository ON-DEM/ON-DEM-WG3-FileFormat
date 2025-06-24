from base_types import *

class some_boundary:
     """This is abstract base boundary, at this level there is only an id"""
    id: int = None
    """ Unique identifier - maddatory"""


class periodic_boundary (some_boundary):
    """Periodic boundary conditions defined by a normal direction and two positions.
    When a particle crosses the left wall, i.e. if 
      dot(particle_position,normal)<position_left_wall, 
    it will be shifted to the right, i.e. 
      particle_position += (position_right_wall-position_left_wall)*normal.
    Equivalently, when a particle crosses the right wall, it will be shifted to the left.
    """
    normal: Vector3 = Vector3(0,0,0)
    """normal vector of unit length - mandatory"""
    position_left_wall: float = 0
    """position of the left wall - mandatory"""
    position_right_wall: float = 0
    """position of the right wall - mandatory"""


class some_domain:
    

class

    
    





