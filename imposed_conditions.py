from base_types import *


class periodic_box:
	"""Defines 3D-periodic space and its deformation rate"""
	
	shape: Matrix3 = Matrix3.identity
	"""**[mandatory]** defines the shape of the periodic pattern, $H$  , [$L$]"""
	
	velocity_gradient: Matrix3 = Matrix3.zero
	"""**[mandatory]** velocity gradient, $D$, [$L$]"""
	

