"""
hdf5_utils.py
ON-DEM WG3 - HDF5 Utilities for VTK HDF Export and Import

Generic utilities for reading and writing ON-DEM schema fields to/from HDF5 groups in VTK HDF format.
Not specific to any DEM code.
"""

import numpy as np
import h5py


def _mat3_flat(m):
    """Flatten a 3x3 matrix to row-major list."""
    return [m[i][j] for i in range(3) for j in range(3)]


def hdf5_write_field(group, field_name: str, hdf5_type: str, value, scalar_as_dataset: bool = False):
    """Write a single field value to an HDF5 group.

    Parameters
    ----------
    group : h5py.Group
        The HDF5 group to write to.
    field_name : str
        Name of the field/dataset.
    hdf5_type : str
        HDF5 type from schema: "scalar_float", "vector3", etc.
    value : any
        The value to write.
    scalar_as_dataset : bool
        If True, write scalars as 0-d datasets; else as attributes.
    """
    if hdf5_type == "scalar_float":
        if scalar_as_dataset:
            group.create_dataset(field_name, data=np.float64(value))
        else:
            group.attrs[field_name] = value

    elif hdf5_type in ("scalar_int",):
        if scalar_as_dataset:
            group.create_dataset(field_name, data=np.int32(value))
        else:
            group.attrs[field_name] = value

    elif hdf5_type in ("scalar_bool",):
        if scalar_as_dataset:
            group.create_dataset(field_name, data=np.int8(value))
        else:
            group.attrs[field_name] = value

    elif hdf5_type == "string":
        if scalar_as_dataset:
            group.create_dataset(field_name, data=np.bytes_(str(value)))
        else:
            group.attrs[field_name] = str(value)

    elif hdf5_type == "string_list":
        _dt = h5py.special_dtype(vlen=str)
        _ds = group.create_dataset(field_name, (len(value),), dtype=_dt)
        for _ii, _v in enumerate(value): _ds[_ii] = _v

    elif hdf5_type == "vector3":
        group.create_dataset(field_name, data=np.array([value[0], value[1], value[2]], dtype=np.float64))

    elif hdf5_type == "quaternion":
        # Assume YADE format [w,x,y,z], convert to [x,y,z,w]
        group.create_dataset(field_name, data=np.array([value[1], value[2], value[3], value[0]], dtype=np.float64))

    elif hdf5_type == "matrix3":
        _mf = _mat3_flat(value)
        group.create_dataset(field_name, data=np.array(_mf, dtype=np.float64))

    else:
        print(f'WARNING: unknown HDF5 type "{hdf5_type}" for field "{field_name}", skipping')


def hdf5_write_scalar_array(group, field_name: str, values_list, dtype):
    """Write an array of scalar values to an HDF5 dataset."""
    group.create_dataset(field_name, data=np.array(values_list, dtype=dtype))


def hdf5_write_vector3_array(group, field_name: str, values_list):
    """Write an array of 3D vectors to an HDF5 dataset. Handles None values."""
    group.create_dataset(field_name, data=np.array([[v[0], v[1], v[2]] if v is not None else [0, 0, 0] for v in values_list], dtype=np.float64))


def hdf5_write_quaternion_array(group, field_name: str, values_list):
    """Write an array of quaternions to an HDF5 dataset. Assumes YADE format [w,x,y,z], converts to [x,y,z,w]. Handles None."""
    group.create_dataset(field_name, data=np.array([[q[1], q[2], q[3], q[0]] if q is not None else [0, 0, 0, 1] for q in values_list], dtype=np.float64))


def hdf5_read_field(group, field_name: str, hdf5_type: str, scalar_as_dataset: bool = False):
    """Read a single field value from an HDF5 group.

    Parameters
    ----------
    group : h5py.Group
        The HDF5 group to read from.
    field_name : str
        Name of the field/dataset.
    hdf5_type : str
        HDF5 type from schema: "scalar_float", "vector3", etc.
    scalar_as_dataset : bool
        If True, read scalars from datasets; else from attributes.

    Returns
    -------
    value : any
        The read value.
    """
    if hdf5_type == "scalar_float":
        if scalar_as_dataset:
            return float(group[field_name][()])
        else:
            return group.attrs[field_name]

    elif hdf5_type in ("scalar_int",):
        if scalar_as_dataset:
            return int(group[field_name][()])
        else:
            return group.attrs[field_name]

    elif hdf5_type in ("scalar_bool",):
        if scalar_as_dataset:
            return bool(group[field_name][()])
        else:
            return group.attrs[field_name]

    elif hdf5_type == "string":
        if scalar_as_dataset:
            return group[field_name][()].decode('utf-8')
        else:
            return group.attrs[field_name]

    elif hdf5_type == "vector3":
        data = group[field_name][:]
        return [float(data[0]), float(data[1]), float(data[2])]

    elif hdf5_type == "quaternion":
        # Stored as [x,y,z,w], convert back to YADE [w,x,y,z]
        data = group[field_name][:]
        return [float(data[3]), float(data[0]), float(data[1]), float(data[2])]

    elif hdf5_type == "matrix3":
        data = group[field_name][:]
        # Reconstruct 3x3 matrix
        return [[data[0], data[1], data[2]],
                [data[3], data[4], data[5]],
                [data[6], data[7], data[8]]]

    else:
        print(f'WARNING: unknown HDF5 type "{hdf5_type}" for field "{field_name}", returning None')
        return None


def hdf5_read_scalar_array(group, field_name: str, dtype):
    """Read an array of scalar values from an HDF5 dataset."""
    data = group[field_name][:]
    return [dtype(v) for v in data]


def hdf5_read_vector3_array(group, field_name: str):
    """Read an array of 3D vectors from an HDF5 dataset. Returns list of lists."""
    data = group[field_name][:]
    return [[float(v[0]), float(v[1]), float(v[2])] for v in data]


def hdf5_read_quaternion_array(group, field_name: str):
    """Read an array of quaternions from an HDF5 dataset. Returns list in YADE format [w,x,y,z]."""
    data = group[field_name][:]
    return [[float(v[3]), float(v[0]), float(v[1]), float(v[2])] for v in data]


def hdf5_read_string_array(group, field_name: str):
    """Read an array of strings from an HDF5 dataset."""
    data = group[field_name][:]
    return [s.decode('utf-8') if isinstance(s, bytes) else str(s) for s in data]


def hdf5_write_matrix3_array(group, field_name: str, values_list):
    """Write an array of 3x3 matrices to an HDF5 dataset. Handles None values."""
    def _mat3_flat(m):
        if m is None:
            return [0]*9
        return [m[i][j] for i in range(3) for j in range(3)]
    group.create_dataset(field_name, data=np.array([_mat3_flat(m) for m in values_list], dtype=np.float64))


def hdf5_write_string_array(group, field_name: str, values_list):
    """Write an array of strings to an HDF5 dataset."""
    _dt = h5py.special_dtype(vlen=str)
    _ds = group.create_dataset(field_name, (len(values_list),), dtype=_dt)
    for _ii, _v in enumerate(values_list): _ds[_ii] = str(_v) if _v else ""