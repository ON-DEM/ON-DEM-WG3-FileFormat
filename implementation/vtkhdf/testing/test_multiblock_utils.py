"""
test_multiblock_utils.py
ON-DEM WG3 - test of the code-agnostic VTKHDF multiblock helpers in hdf5_utils.py.

Needs numpy and h5py, no DEM code. If the vtk Python package is installed,
the file is also read back with vtkHDFReader.

Run from anywhere:
    python3 test_multiblock_utils.py
"""

import os
import sys
import tempfile

import numpy as np
import h5py

# Use hdf5_utils.py from implementation/vtkhdf, not a copy in this folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hdf5_utils import (vtkhdf_init_multiblock, vtkhdf_write_polydata_block, vtkhdf_read_blocks,
                        validate_display_groups, point_array, column_array, hdf5_write_quaternion_array,
                        QUATERNION_ORDER, VTKHDF_VERSION)

NAMES = ["particles", "geometry", "unused"]          # "unused" stays empty
BODIES = {                                            # body_id: (group, position, radius)
    0: (1, (0.0, 0.0, 0.0), None),                    # e.g. a wall: no radius
    1: (0, (0.1, 0.2, 0.3), 0.01),
    2: (0, (0.4, 0.5, 0.6), 0.02),
    3: (1, (1.0, 0.0, 0.0), None),
    4: (0, (0.7, 0.8, 0.9), 0.03),
}


def write_file(path):
    groups = {bid: g for bid, (g, _, _) in BODIES.items()}
    validate_display_groups(NAMES, groups)
    with h5py.File(path, "w") as f:
        vtkhdf_init_multiblock(f)
        for gi, name in enumerate(NAMES):
            ids = [bid for bid in sorted(BODIES) if BODIES[bid][0] == gi]
            vtkhdf_write_polydata_block(
                f, name, ids,
                points=[BODIES[b][1] for b in ids],
                point_data={
                    "radius": point_array([BODIES[b][2] for b in ids]),
                    "orientation": point_array([(1, 0, 0, 0)] * len(ids), width=4),   # identity, (w, x, y, z)
                },
                point_data_attrs={"orientation": {"order": QUATERNION_ORDER}},
            )


def check_structure(path):
    with h5py.File(path, "r") as f:
        vtk = f["VTKHDF"]
        assert vtk.attrs["Type"] == b"MultiBlockDataSet", vtk.attrs["Type"]
        assert tuple(vtk.attrs["Version"]) == VTKHDF_VERSION
        assert list(vtk["Assembly"].keys()) == NAMES, list(vtk["Assembly"].keys())
        for name in NAMES:
            link = vtk["Assembly"].get(name, getlink=True)
            assert isinstance(link, h5py.SoftLink) and link.path == f"/VTKHDF/{name}", link

        for name in NAMES:   # VTK's reader needs Version on every block
            assert tuple(vtk[name].attrs["Version"]) == VTKHDF_VERSION, name

        p = vtk["particles"]
        assert p.attrs["Type"] == b"PolyData"
        assert p["Points"].dtype == np.float64 and p["Points"].shape == (3, 3)
        assert p["NumberOfPoints"][0] == 3
        assert p["PointData/body_id"].dtype == np.int64
        assert list(p["PointData/body_id"][:]) == [1, 2, 4]
        assert list(p["Vertices/Offsets"][:]) == [0, 1, 2, 3]
        assert list(p["Vertices/Connectivity"][:]) == [0, 1, 2]
        assert p["Vertices/NumberOfCells"][0] == 3
        for sec in ("Lines", "Polygons", "Strips"):
            assert p[f"{sec}/NumberOfCells"][0] == 0 and list(p[f"{sec}/Offsets"][:]) == [0]
        assert p["PointData/orientation"].attrs["order"] == QUATERNION_ORDER

        g = vtk["geometry"]
        assert np.isnan(g["PointData/radius"][:]).all()

        e = vtk["unused"]
        assert e["NumberOfPoints"][0] == 0
        assert e["Points"].shape == (0, 3) and e["Points"].dtype == np.float64
        assert e["PointData/body_id"].shape == (0,)
        assert list(e["Vertices/Offsets"][:]) == [0]
    print("  structure (h5py): OK")


def check_read_back(path):
    with h5py.File(path, "r") as f:
        blocks = vtkhdf_read_blocks(f, NAMES)
        assert sorted(blocks) == sorted(BODIES)
        for bid, (gi, pos, r) in BODIES.items():
            rec = blocks[bid]
            assert rec["block"] == NAMES[gi]
            assert np.allclose(rec["position"], pos)
            assert (np.isnan(rec["radius"]) if r is None else rec["radius"] == r)
        # default: names from the Assembly
        assert vtkhdf_read_blocks(f).keys() == blocks.keys()
    print("  read back (vtkhdf_read_blocks): OK")


def check_validation():
    def raises(names, groups):
        try:
            validate_display_groups(names, groups)
        except ValueError as e:
            return str(e)
        raise AssertionError(f"no ValueError for names={names} groups={groups}")

    assert "body_id 7" in raises(["all"], {7: 1})
    assert "body_id 7" in raises(["a", "b"], {7: -1})
    assert "unique" in raises(["a", "a"], {})
    raises(["Assembly"], {})
    raises(["a/b"], {})
    raises([""], {})
    raises([], {})
    raises(["all"], {3: 0.0})
    validate_display_groups(["all"], {0: 0, 1: np.int64(0)})
    print("  validate_display_groups: OK")


def check_not_applicable():
    """Values that do not apply to a body: NaN for floats, -1 for integers and booleans."""
    f = column_array([1.5, None], "scalar_float")
    assert f.dtype == np.float64 and f[0] == 1.5 and np.isnan(f[1])
    i = column_array([3, None], "scalar_int")
    assert i.dtype == np.int64 and list(i) == [3, -1]
    b = column_array([True, False, None], "scalar_bool")
    assert list(b) == [1, 0, -1]
    v = column_array([(1, 2, 3), None], "vector3")
    assert v.shape == (2, 3) and np.isnan(v[1]).all()
    q = column_array([(1, 0, 0, 0), None], "quaternion")
    assert q.shape == (2, 4) and np.isnan(q[1]).all()
    m = column_array([[[1, 0, 0], [0, 1, 0], [0, 0, 1]], None], "matrix3")
    assert m.shape == (2, 9) and np.isnan(m[1]).all()
    print("  not applicable -> NaN / -1: OK")


def check_quaternion_helper(path):
    with h5py.File(path, "a") as f:
        g = f.require_group("ONDEM/test")
        hdf5_write_quaternion_array(g, "q", [(0.9, 0.1, 0.2, 0.3), None])
        assert QUATERNION_ORDER == "wxyz"
        assert g["q"].attrs["order"] == QUATERNION_ORDER
        assert np.allclose(g["q"][:], [[0.9, 0.1, 0.2, 0.3], [1, 0, 0, 0]])   # None -> identity
    print("  quaternion helper keeps (w, x, y, z), identity (1, 0, 0, 0): OK")


def check_vtk(path):
    try:
        import vtk
    except ImportError:
        print("  vtkHDFReader: SKIPPED (vtk not installed)")
        return
    reader = vtk.vtkHDFReader()
    reader.SetFileName(path)
    reader.Update()
    out = reader.GetOutputDataObject(0)
    assert out.IsA("vtkMultiBlockDataSet"), out.GetClassName()
    assert out.GetNumberOfBlocks() == len(NAMES), out.GetNumberOfBlocks()
    expected_points = {name: sum(1 for b in BODIES.values() if NAMES[b[0]] == name) for name in NAMES}
    for i in range(out.GetNumberOfBlocks()):
        name = out.GetMetaData(i).Get(vtk.vtkCompositeDataSet.NAME())
        blk = out.GetBlock(i)
        assert name == NAMES[i], (i, name)
        n = blk.GetNumberOfPoints() if blk is not None else 0
        assert n == expected_points[name], (name, n)
        if n:
            assert blk.GetPoints().GetDataType() == vtk.VTK_DOUBLE
            assert blk.GetNumberOfVerts() == n
            ids = blk.GetPointData().GetArray("body_id")
            assert ids is not None and ids.GetNumberOfTuples() == n
            q = blk.GetPointData().GetArray("orientation")
            assert q is not None and q.GetNumberOfComponents() == 4
        print(f"    block {i} {name!r}: {n} points"
              + ("" if blk is not None else " (reader returned no dataset)"))
    print(f"  vtkHDFReader (VTK {vtk.vtkVersion.GetVTKVersion()}): OK")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "multiblock.vtkhdf")
        write_file(path)
        print(f"test_multiblock_utils (h5py {h5py.__version__}, numpy {np.__version__})")
        check_structure(path)
        check_read_back(path)
        check_vtk(path)
        check_validation()
        check_not_applicable()
        check_quaternion_helper(path)
    print("ALL OK")
