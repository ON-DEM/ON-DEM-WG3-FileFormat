from base_types import *

class ElasticFrictional3D:
    """
    Cundall's contact model with linear elasticity and Coulombian friction :cite:`Cundall1979`; :math:`F_n=k_n u_n`, :math:`\Delta F_s=k_s \dot u_s\, \Delta t`.
    """
    implementations: list = ['MercuryDPM', 'YADE']
    """codes implementing this model"""

class LinearViscoelasticFrictional3D(ElasticFrictional3D):
    """
    Elastic-frictional model with viscous damping
    """
    implementations: list = ['MercuryDPM', 'YADE']
    """codes implementing this model"""

class ElasticFrictional6D(ElasticFrictional3D):
    """
    Generalized elastic-frictional model with rolling and twisting.
    """
    implementations: list = ['YADE', '...']
    """codes implementing this model"""
