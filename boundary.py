from base_types import *

class some_boundary:
     """This is abstract base boundary, at this level there is only an id"""
    id: int = None
    """ Unique identifier - mandatory"""


class some_geometry:
    """Most boundaries have a location they act in-on"""

class some_geometry(line):
    """Line class, this is defined by a vector and a distance of closes approch to the orgin""" 

    normal: Vector3 = Vector3(0,0,0)
    location: Int = None


    

    
    





