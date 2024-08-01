from base_types import *

class scene:
    """
    Information on a simulation
    """
    units: List[str] = ["second","meter","kilogram"]
    """Units for time (T), length (L) and mass (M)."""
    timestep: float = None
    """time step [T]"""
    time: float = None
    """simulated time [T]"""
    gravity: Vector3 = Vector3(0,0,0)
    """Gravitational acceleration [L/T²]"""
