# generic types

from typing import List # for initialization of lists

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
        return f"Quaternion({self.x}, {self.y}, {self.z}, {self.w})"
    
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
            raise IndexError("Index out of range for Quaternion")

    def __setitem__(self, index: int, value: float) -> None:
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        elif index == 2:
            self.z = value
        elif index == 3:
            self.w = value
        else:
            raise IndexError("Index out of range for Quaternion")
        
class Matrix3:
    """A simple 3x3 matrix class."""

    def __init__(self, elements=None):
        if elements is None:
            elements = [
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
            ]

        if len(elements) != 3 or any(len(row) != 3 for row in elements):
            raise ValueError("Matrix3 must be initialized with a 3x3 list")

        self.elements = [[float(value) for value in row] for row in elements]

    def __repr__(self):
        return (
            f"Matrix3([{self.elements[0][0]}, {self.elements[0][1]}, {self.elements[0][2]}], "
            f"[{self.elements[1][0]}, {self.elements[1][1]}, {self.elements[1][2]}], "
            f"[{self.elements[2][0]}, {self.elements[2][1]}, {self.elements[2][2]}])"
        )

    def __getitem__(self, index: int):
        return self.elements[index]

    def __setitem__(self, index: int, value):
        if len(value) != 3:
            raise ValueError("Each row of Matrix3 must have exactly 3 elements")
        self.elements[index] = [float(v) for v in value]

    @classmethod
    def zero(cls):
        return cls([
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ])

    @classmethod
    def identity(cls):
        return cls([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
