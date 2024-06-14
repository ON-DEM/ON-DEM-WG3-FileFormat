from dataclasses import dataclass, field
from typing import List
from vector3 import Vector3

@dataclass
class ElasticFrictional3D:
    """
    Cundall's contact model with linear elasticity and Coulombian friction :cite:`Cundall1979`; :math:`F_n=k_n u_n`, :math:`\Delta F_s=k_s \dot u_s\, \Delta t`.
    """
    #implementations: list = ['MercuryDPM', 'YADE'] # codes implementing this model

@dataclass
class LinearViscoelasticFrictional3D(ElasticFrictional3D):
    """
    Elastic-frictional model with viscous damping
    """
    implementations: List[str] = field(default_factory=lambda: ['YADE', '...']) # codes implementing this model

@dataclass
class ElasticFrictional6D(ElasticFrictional3D):
    """
    Generalized elastic-frictional model with rolling and twisting.
    """
    #implementations: list = ['YADE', '...'] # codes implementing this model
