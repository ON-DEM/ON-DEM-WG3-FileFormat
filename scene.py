from base_types import *

class scene:
    """
    Information on a simulation
    """
    timestep: float = None
    """time step [seconds]"""
    time: float = None
    """simulated time [seconds]"""
    gravity: Vector3 = Vector3(0,0,0)
    """Gravitational acceleration [length per squared time]"""
