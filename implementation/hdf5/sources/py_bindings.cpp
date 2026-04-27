// Open file format library - python bindings

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 28.04.2026


#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "open_file_format.h"    
//#include "wrappers.h"   

namespace py = pybind11;

PYBIND11_MODULE(py_open_file_format_lib, m) {
    // double3
    py::class_<double3>(m, "double3")
        .def(py::init<>())
        .def_readwrite("x", &double3::x)
        .def_readwrite("y", &double3::y)
        .def_readwrite("z", &double3::z);
    
    // double4
    py::class_<double4>(m, "double4")
        .def(py::init<>())
        .def_readwrite("w", &double4::w)
        .def_readwrite("x", &double4::x)
        .def_readwrite("y", &double4::y)
        .def_readwrite("z", &double4::z);

    // Expose PARTICLES
    py::class_<PARTICLES>(m, "PARTICLES")
        .def(py::init<>())
        .def("resize", &PARTICLES::resize)
        .def_readwrite("id", &PARTICLES::id)
        .def_readwrite("type_id", &PARTICLES::type_id)
        .def_readwrite("scale", &PARTICLES::scale)
        .def_readwrite("radius", &PARTICLES::radius)
        .def_readwrite("pos_com", &PARTICLES::pos_com)
        .def_readwrite("vel_com", &PARTICLES::vel_com)
        .def_readwrite("vel_ang", &PARTICLES::vel_ang)
        .def_readwrite("temp", &PARTICLES::temp)
        .def_readwrite("coh", &PARTICLES::coh)
        .def_readwrite("density", &PARTICLES::density)
        .def("resize", &PARTICLES::resize)
        .def("size", &PARTICLES::size)        
        .def("set_size", &PARTICLES::set_size) 
        .def("get_size", &PARTICLES::get_size);
    
    // Expose particle_header
    py::class_<P_LINE>(m, "P_LINE")
        .def(py::init<std::string, double, int, std::string, std::string>(),
    py::arg("name"), py::arg("volume"), py::arg("number"), py::arg("shape"), py::arg("type"))
        .def_readwrite("name", &P_LINE::name)
        .def_readwrite("shape", &P_LINE::shape)
        .def_readwrite("type", &P_LINE::type)
        .def_readwrite("number", &P_LINE::number)
        .def_readwrite("volume", &P_LINE::volume);
    
    py::class_<particle_header>(m, "particle_header")
        .def(py::init<>())
        .def_readwrite("VER", &particle_header::VER)
        .def_readwrite("time", &particle_header::time)
        .def_readwrite("n_DEM", &particle_header::n_DEM)
        .def_readwrite("n_Fluid", &particle_header::n_Fluid)
        .def_readwrite("numPTypes", &particle_header::numPTypes)
        .def_readwrite("ptype", &particle_header::ptype);

    // Optionally expose your wrappers
    m.def("get_file_list", &OPEN_FILE_FORMAT::get_file_list);
    m.def("read_restart_BlazeDEM", &OPEN_FILE_FORMAT::read_restart_BlazeDEM);
    m.def("read_restart_vtkhdf", &OPEN_FILE_FORMAT::read_restart_vtkhdf);
    m.def("read_restart_hdf5", &OPEN_FILE_FORMAT::read_restart_hdf5);
    m.def("save_restart_BlazeDEM", &OPEN_FILE_FORMAT::save_restart_BlazeDEM);
    m.def("save_restart_hdf5", &OPEN_FILE_FORMAT::save_restart_hdf5);
    m.def("save_restart_vtkhdf", &OPEN_FILE_FORMAT::save_restart_vtkhdf);
    m.def("fake_DEM_generator", &OPEN_FILE_FORMAT::fake_DEM_generator);
    
  
}
