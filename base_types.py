# generic types

from typing import List # for initialization of lists

class SomeStateClass:
    """abstract state class"""
    pass

class SomeShapeClass:
    """abstract shape class"""
    pass

class SomeMaterialClass:
    """abstract material class"""
    pass

# Simple vector, matrix, quaternion

class Vector3:
    """A simple 3D vector class."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"Vector3({self.x}, {self.y}, {self.z})"
    
    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        elif index == 2:
            return self.z
        else:
            raise IndexError("Index out of range for Vector3")

    def __setitem__(self, index: int, value: float) -> None:
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        elif index == 2:
            self.z = value
        else:
            raise IndexError("Index out of range for Vector3")

class Quaternion:
    """A simple quaternion class."""
    
    def __init__(self, x: float = 1.0, y: float = 0.0, z: float = 0.0, w: float = 0.0):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __repr__(self):
        return f"Vector3({self.x}, {self.y}, {self.z}, {self.w})"
    
    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        elif index == 2:
            return self.z
        elif index == 3:
            return self.w
        else:
            raise IndexError("Index out of range for Vector3")

    def __setitem__(self, index: int, value: float) -> None:
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        elif index == 2:
            self.z = value
        elif index == 3:
            self.z = value
        else:
            raise IndexError("Index out of range for Vector3")
        
class Matrix3:
    """A 3x3 matrix class"""
    
    zero = None
    identity = None

    def __init__(self, elements=None):
        if elements is None:
            elements = [[0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0]]
        self.elements = elements

    @staticmethod
    def initialize_static_attributes():
        Matrix3.zero = Matrix3([[0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0]])
        Matrix3.identity = Matrix3([[1.0, 0.0, 0.0],
                                    [0.0, 1.0, 0.0],
                                    [0.0, 0.0, 1.0]])


    def __repr__(self):
        return (f"Matrix3({self.m11}, {self.m12}, {self.m13},\n"
                f"        {self.m21}, {self.m22}, {self.m23},\n"
                f"        {self.m31}, {self.m32}, {self.m33})")
    
    @staticmethod
    def zero():
        return Matrix3()
