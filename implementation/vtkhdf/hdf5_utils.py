"""
hdf5_utils.py
ON-DEM WG3 - HDF5 Utilities for VTK HDF Export and Import

Generic utilities for reading and writing ON-DEM schema fields to/from HDF5 groups in VTK HDF format.
Not specific to any DEM code.
"""

import numpy as np
import h5py


# Component order of quaternions in the file: (w, x, y, z), scalar first,
# identity (1, 0, 0, 0), v_global = q v_body q^-1 (provisional, to be confirmed
# by Bruno). Written as the "order" attribute of every quaternion dataset.
QUATERNION_ORDER = "wxyz"

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
        # value is indexable in file order: value[0..3] = (w, x, y, z)
        ds = group.create_dataset(field_name, data=np.array([value[0], value[1], value[2], value[3]], dtype=np.float64))
        ds.attrs["order"] = QUATERNION_ORDER

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
    """Write an array of quaternions to an HDF5 dataset, in file order (w, x, y, z).
    Each value must be indexable in that order: q[0..3] = (w, x, y, z). None → identity (1, 0, 0, 0)."""
    ds = group.create_dataset(field_name, data=np.array([[q[0], q[1], q[2], q[3]] if q is not None else [1, 0, 0, 0] for q in values_list], dtype=np.float64))
    ds.attrs["order"] = QUATERNION_ORDER


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
        # Returned in file order (w, x, y, z)
        data = group[field_name][:]
        return [float(data[0]), float(data[1]), float(data[2]), float(data[3])]

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
    """Read an array of quaternions from an HDF5 dataset. Returns lists in file order (w, x, y, z)."""
    data = group[field_name][:]
    return [[float(v[0]), float(v[1]), float(v[2]), float(v[3])] for v in data]


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


# ---------------------------------------------------------------------------
# VTKHDF MultiBlockDataSet: one PolyData block per display group
# ---------------------------------------------------------------------------
#
# Layout (decisions 2026-10-01):
#   /VTKHDF                    Type = "MultiBlockDataSet", Version
#     <name>/                  one PolyData block per display group
#       Points      (N,3) float64   body positions (stored only here)
#       Vertices/               one vertex cell per point
#       Lines/ Polygons/ Strips/  empty
#       PointData/body_id (N,) int64, plus the other block fields
#     Assembly/<name>          soft link -> /VTKHDF/<name>
#
# ParaView only reads blocks linked from the Assembly; the Assembly link
# name is the block name shown in ParaView.

VTKHDF_VERSION = (2, 5)
_RESERVED_BLOCK_NAMES = {"Assembly"}


def _write_ascii_attr(obj, name: str, text: str):
    """Write a fixed-length ASCII string attribute (the form VTK expects for Type)."""
    data = text.encode("ascii")
    obj.attrs.create(name, data, dtype=h5py.string_dtype("ascii", len(data)))


def _write_cells(block, section: str, connectivity, offsets):
    """Write one PolyData cell section (Vertices, Lines, Polygons, Strips)."""
    g = block.create_group(section, track_order=True)
    connectivity = np.asarray(connectivity, dtype=np.int64)
    offsets = np.asarray(offsets, dtype=np.int64)
    g.create_dataset("NumberOfCells",           data=np.array([len(offsets) - 1], dtype=np.int64))
    g.create_dataset("NumberOfConnectivityIds", data=np.array([len(connectivity)], dtype=np.int64))
    g.create_dataset("Offsets",                 data=offsets)
    g.create_dataset("Connectivity",            data=connectivity)


def point_array(values, width: int = None):
    """Turn a list of per-body values into a float64 array, None → NaN.

    width=None gives shape (N,); width=k gives shape (N,k) and each value
    must be indexable with k components.
    """
    if width is None:
        return np.array([np.nan if v is None else float(v) for v in values], dtype=np.float64)
    out = np.full((len(values), width), np.nan, dtype=np.float64)
    for i, v in enumerate(values):
        if v is not None:
            out[i] = [float(v[k]) for k in range(width)]
    return out


def column_array(values, hdf5_type: str):
    """Turn a list of per-item values of one schema type into an array for HDF5.

    Missing values (None): NaN for float types, -1 for integers (the schema's
    "no id" value), 0 for booleans. Returns None for types that cannot be written
    as a column (the caller skips the field).
    """
    if hdf5_type == "scalar_float":
        return point_array(values)
    if hdf5_type == "scalar_int":
        return np.array([-1 if v is None else int(v) for v in values], dtype=np.int64)
    if hdf5_type == "scalar_bool":
        return np.array([0 if v is None else int(bool(v)) for v in values], dtype=np.int8)
    if hdf5_type == "vector3":
        return point_array(values, 3)
    if hdf5_type == "quaternion":
        return point_array(values, 4)
    if hdf5_type == "matrix3":
        out = np.full((len(values), 9), np.nan, dtype=np.float64)
        for i, m in enumerate(values):
            if m is not None:
                out[i] = [float(m[r][c]) for r in range(3) for c in range(3)]
        return out
    return None


def hdf5_write_column(group, field_name: str, values, hdf5_type: str) -> bool:
    """Write one per-item field (one value per body or interaction) as a dataset.

    Strings become a variable-length string dataset, quaternions get the
    order attribute. Returns False if the type cannot be written.
    """
    if hdf5_type == "string":
        hdf5_write_string_array(group, field_name, values)
        return True
    arr = column_array(values, hdf5_type)
    if arr is None:
        return False
    ds = group.create_dataset(field_name, data=arr)
    if hdf5_type == "quaternion":
        ds.attrs["order"] = QUATERNION_ORDER
    return True


def snake_case(name: str) -> str:
    """'FrictPhys' -> 'frict_phys': names written in the file are snake_case."""
    out = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0 and (not name[i - 1].isupper() or (i + 1 < len(name) and name[i + 1].islower())):
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def validate_display_groups(names, groups: dict):
    """Check display group names and the group index of every body.

    names  : list of str, scene.display_group_names
    groups : dict {body_id: display_group}
    Raises ValueError with the offending names or body ids.
    """
    if not names:
        raise ValueError("display_group_names must contain at least one name")
    for n in names:
        if not isinstance(n, str) or not n or "/" in n or n in (".", "..") or n in _RESERVED_BLOCK_NAMES:
            raise ValueError(f"invalid display group name {n!r}: names must be non-empty, "
                             f"without '/', and not one of {sorted(_RESERVED_BLOCK_NAMES)}")
    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise ValueError(f"display group names must be unique, duplicated: {dupes}")
    bad = sorted(bid for bid, g in groups.items()
                 if isinstance(g, bool) or not isinstance(g, (int, np.integer)) or not 0 <= g < len(names))
    if bad:
        shown = ", ".join(f"{bid}->{groups[bid]!r}" for bid in bad[:20])
        more = f" (and {len(bad) - 20} more)" if len(bad) > 20 else ""
        raise ValueError(f"display_group must be an integer in [0, {len(names) - 1}] "
                         f"(display_group_names = {list(names)}); invalid for body_id {shown}{more}")


def vtkhdf_init_multiblock(f):
    """Create /VTKHDF as a MultiBlockDataSet with an empty, creation-ordered Assembly.

    VTK's reader iterates the groups under /VTKHDF by creation order, so every
    group it reads is created with track_order=True.
    """
    vtk = f.create_group("VTKHDF", track_order=True)
    _write_ascii_attr(vtk, "Type", "MultiBlockDataSet")
    vtk.attrs.create("Version", data=np.array(VTKHDF_VERSION, dtype=np.int64))
    vtk.create_group("Assembly", track_order=True)
    return vtk


def vtkhdf_write_polydata_block(f, name: str, body_ids, points, point_data: dict = None,
                                point_data_attrs: dict = None):
    """Write one PolyData block /VTKHDF/<name> and link it from /VTKHDF/Assembly/<name>.

    Parameters
    ----------
    f : h5py.File
        File on which vtkhdf_init_multiblock() was called.
    name : str
        Block name (a display group name).
    body_ids : sequence of int, length N
        Written as PointData/body_id (int64): the key that joins the block to /ONDEM.
    points : array-like (N,3)
        Body positions, written as float64.
    point_data : dict {field_name: array-like with first dimension N}
        Further per-point fields.
    point_data_attrs : dict {field_name: {attr: value}}
        Attributes to set on point_data datasets (e.g. quaternion order).

    N may be 0: the block is then written empty, so every display group
    has a block in every file.
    """
    body_ids = np.asarray(body_ids, dtype=np.int64).reshape(-1)
    points = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    n = len(points)
    if len(body_ids) != n:
        raise ValueError(f"block {name!r}: {len(body_ids)} body ids for {n} points")

    blk = f["VTKHDF"].create_group(name, track_order=True)
    _write_ascii_attr(blk, "Type", "PolyData")
    blk.attrs.create("Version", data=np.array(VTKHDF_VERSION, dtype=np.int64))
    blk.create_dataset("NumberOfPoints", data=np.array([n], dtype=np.int64))
    blk.create_dataset("Points", data=points)

    # one vertex cell per point, so the points are rendered
    _write_cells(blk, "Vertices", np.arange(n), np.arange(n + 1))
    for section in ("Lines", "Polygons", "Strips"):
        _write_cells(blk, section, [], [0])

    pd = blk.create_group("PointData", track_order=True)
    pd.create_dataset("body_id", data=body_ids)
    for field_name, values in (point_data or {}).items():
        arr = np.asarray(values)
        if arr.shape[:1] != (n,):
            raise ValueError(f"block {name!r}: field {field_name!r} has shape {arr.shape}, expected first dimension {n}")
        ds = pd.create_dataset(field_name, data=arr)
        for k, v in (point_data_attrs or {}).get(field_name, {}).items():
            ds.attrs[k] = v

    f["VTKHDF/Assembly"][name] = h5py.SoftLink(f"/VTKHDF/{name}")
    return blk


def vtkhdf_read_blocks(f, names=None) -> dict:
    """Read the PolyData blocks of a multiblock /VTKHDF, per body.

    Parameters
    ----------
    names : list of str, optional
        Block names to read, normally scene.display_group_names. Default: the
        links of /VTKHDF/Assembly.

    Returns
    -------
    dict {body_id: {"block": name, "position": ndarray(3), <PointData field>: value}}

    Raises ValueError if a body_id appears more than once.
    """
    asm = f["VTKHDF/Assembly"]
    if names is None:
        names = list(asm.keys())
    out = {}
    for name in names:
        if name not in asm:
            raise KeyError(f"block {name!r} is not linked in /VTKHDF/Assembly")
        blk = asm[name]
        pd = blk["PointData"]
        ids = pd["body_id"][:]
        pts = blk["Points"][:]
        fields = {k: pd[k][:] for k in pd if k != "body_id"}
        for i, bid in enumerate(ids):
            bid = int(bid)
            if bid in out:
                raise ValueError(f"body_id {bid} appears in block {out[bid]['block']!r} and in block {name!r}")
            rec = {"block": name, "position": pts[i]}
            for k, v in fields.items():
                rec[k] = v[i]
            out[bid] = rec
    return out


def ondem_read_bodies(f) -> dict:
    """Read the per-body datasets of /ONDEM/Bodies/<shape group>/, per body.

    Returns dict {body_id: {"shape_group": name, <field>: value}} with every
    dataset whose first dimension is the group's number of bodies. Strings
    are decoded. Raises ValueError if a body_id appears more than once.
    """
    out = {}
    if "ONDEM/Bodies" not in f:
        return out
    for sg, g in f["ONDEM/Bodies"].items():
        ids = g["body_id"][:]
        n = len(ids)
        fields = {}
        for k, ds in g.items():
            if k == "body_id" or not isinstance(ds, h5py.Dataset) or ds.shape[:1] != (n,):
                continue
            fields[k] = ds.asstr()[:] if h5py.check_string_dtype(ds.dtype) else ds[:]
        for i, bid in enumerate(ids):
            bid = int(bid)
            if bid in out:
                raise ValueError(f"body_id {bid} appears in /ONDEM/Bodies/{out[bid]['shape_group']} and /ONDEM/Bodies/{sg}")
            rec = {"shape_group": sg}
            for k, v in fields.items():
                rec[k] = v[i]
            out[bid] = rec
    return out