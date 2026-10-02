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
    iteration: int = 0
    """*[optional]* iteration number (time steps done) at ``time``. Default 0 [$-$]"""
    gravity: Vector3 = Vector3(0,0,0)
    """Gravitational acceleration [L/T²]"""
    display_group_names: List[str] = ['all']
    """*[optional]* names of the display groups, indexed by ``base_body.display_group``. Each name is the name of one block of the VTKHDF MultiBlockDataSet. Default ``['all']``, so index 0 is always valid; the user may overwrite it, e.g. ``['particles', 'geometry']``. Every ``display_group`` used by a body must be a valid index into this list. Names must be unique and non-empty, must not contain ``/`` and must not be ``Assembly`` [$-$]"""
    shape_names: List[str] = []
    """**[mandatory]** names of the shape classes used in the file (e.g. ``sphere``, ``box``, ``clump``), indexed by ``base_body.shape_type``. Readers must map shapes by name through this list, never by a fixed index: the list may change between versions of the format [$-$]"""
