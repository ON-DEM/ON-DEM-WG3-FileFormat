from base_types import *

class elastic_frictional_3D:
    """
    Cundall's contact model with linear elasticity and Coulombian friction \cite{Cundall1979}; $F_n=k_n u_n$, $\Delta F_s=k_s \dot u_s\, \Delta t$.
    """
    implementations: list = ['MercuryDPM', 'YADE']
    """codes implementing this model"""

class linear_viscoelastic_frictional_3D(elastic_frictional_3D):
    """
    Elastic-frictional model with viscous damping
    """
    implementations: list = ['MercuryDPM', 'YADE']
    """codes implementing this model"""

class elastic_frictional_6D(elastic_frictional_3D):
    """
    Generalized elastic-frictional model with rolling and twisting.
    """
    implementations: list = ['YADE', '...']
    """codes implementing this model"""
