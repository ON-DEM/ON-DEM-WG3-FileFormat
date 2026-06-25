from base_types import *

class linear_elastic_frictional_3D:
    """
    Cundall's contact model with linear elasticity and Coulombian friction \cite{Cundall1979}; $F_n=k_n u_n$, $\Delta F_s=k_s \dot u_s\, \Delta t$.
    """
    implementations: list = ['MercuryDPM', 'YADE']
    """codes implementing this model"""

class linear_viscoelastic_frictional_3D(linear_elastic_frictional_3D):
    """
    Elastic-frictional model with viscous damping
    """
    implementations: list = ['MercuryDPM', 'YADE']
    """codes implementing this model"""

class linear_elastic_frictional_6D(linear_elastic_frictional_3D):
    """
    Generalized elastic-frictional model with rolling and twisting.
    """
    implementations: list = ['YADE', 'MercuryDPM']
    """codes implementing this model"""

class liquid_bridge_linear_visco_elastic_frictional_3d(linear_viscoelastic_frictional_3D):
    """
    Elastic-frictional model with viscous damping, rolling, twisting, and liquid bridges
    """
    implementations: list = ['YADE', 'MercuryDPM']
    """codes implementing this model"""
    pass