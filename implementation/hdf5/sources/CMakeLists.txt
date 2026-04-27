# Blaze Data converter - CMmakeLists.txt 

# created by Rafal Kobylka 
# rkobylka@ipan.lublin.pl


# This library is provided 'as is,' and the author 
# assumes no responsibility for any errors, inaccuracies, 
# or faulty results arising from its use. 
# Users are advised to employ it at their own risk.

# last modified 28.04.2026


cmake_minimum_required (VERSION 3.26)

project(converter_Blaze LANGUAGES CXX )

set(DEFAULT_BUILD_TYPE "Release")

set(CMAKE_POSITION_INDEPENDENT_CODE ON)



set (CMAKE_CXX_COMPILER g++) 
set (CMAKE_CXX_STANDARD 17)
set (CMAKE_CXX_STANDARD_REQUIRED ON)
set (CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_VERBOSE_MAKEFILE ON)


set(HDF5_INCLUDE_DIR "/usr/local/HDF_Group/HDF5/2.0.0/include")
set(HDF5_LIBRARY_DIR "/usr/local/HDF_Group/HDF5/2.0.0/lib")

set(VTK_INCLUDE_DIR "/usr/local/include/vtk-9.5")

set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN YES)


############################################### regular c++ lib
add_library(open_file_format_lib SHARED structs.cpp tools.cpp 
                         read_restart.cpp save_restart.cpp 
                         read_restart_hdf5.cpp save_restart_hdf5.cpp   
                         save_restart_vtkhdf.cpp read_restart_vtkhdf.cpp 
                         fake_DEM_generator.cpp 
           )


#add_executable(convert_restart convert_restart.cpp  structs.cpp tools.cpp 
#                               read_restart.cpp save_restart.cpp 
#                               read_restart_hdf5.cpp save_restart_hdf5.cpp   
#                               save_restart_vtkhdf.cpp read_restart_vtkhdf.cpp )


target_compile_definitions(open_file_format_lib PRIVATE -DENABLE_TIMES)


target_include_directories(open_file_format_lib PRIVATE ${HDF5_INCLUDE_DIR} ${VTK_INCLUDE_DIR})

target_link_directories(open_file_format_lib PRIVATE  ${HDF5_LIBRARY_DIR} ${VTK_LIBRARY_DIR})

target_compile_options(open_file_format_lib PRIVATE -fopenmp -O3 )

target_link_libraries(open_file_format_lib PRIVATE hdf5_cpp hdf5 
                           vtkIOCore-9.5 vtksys-9.5 vtkIOHDF-9.5 vtkhdf5-9.5  vtkCommonDataModel-9.5 vtkCommonCore-9.5 vtkCommonExecutionModel-9.5 vtkIOXML-9.5
                           stdc++fs gomp pthread )


                           
############################################### with python bindings, do not use in c++, just for python

set(PYTHON_INCLUDE_DIR "/usr/include/python3.12/")
find_package(pybind11 REQUIRED)

pybind11_add_module(py_open_file_format_lib structs.cpp tools.cpp 
                         read_restart.cpp save_restart.cpp 
                         read_restart_hdf5.cpp save_restart_hdf5.cpp   
                         save_restart_vtkhdf.cpp read_restart_vtkhdf.cpp 
                         fake_DEM_generator.cpp py_bindings.cpp 
           )


target_compile_definitions(py_open_file_format_lib PRIVATE -DENABLE_TIMES)


target_include_directories(py_open_file_format_lib PRIVATE ${HDF5_INCLUDE_DIR} ${VTK_INCLUDE_DIR} ${PYTHON_INCLUDE_DIR})

target_link_directories(py_open_file_format_lib PRIVATE  ${HDF5_LIBRARY_DIR} ${VTK_LIBRARY_DIR})

target_compile_options(py_open_file_format_lib PRIVATE -fopenmp -O3 )

target_link_libraries(py_open_file_format_lib PRIVATE hdf5_cpp hdf5 
                           vtkIOCore-9.5 vtksys-9.5 vtkIOHDF-9.5 vtkhdf5-9.5  vtkCommonDataModel-9.5 vtkCommonCore-9.5 vtkCommonExecutionModel-9.5 vtkIOXML-9.5
                           stdc++fs gomp pthread )

