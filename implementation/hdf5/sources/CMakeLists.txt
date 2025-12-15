# Blaze Data converter - CMmakeLists.txt 

# created by Rafal Kobylka 
# rkobylka@ipan.lublin.pl


# This library is provided 'as is,' and the author 
# assumes no responsibility for any errors, inaccuracies, 
# or faulty results arising from its use. 
# Users are advised to employ it at their own risk.

# last modified 20.11.2025


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

add_executable(convert_restart convert_restart.cpp  structs.cpp tools.cpp 
                               read_restart.cpp save_restart.cpp 
                               read_restart_hdf5.cpp save_restart_hdf5.cpp   
                               save_restart_vtkhdf.cpp read_restart_vtkhdf.cpp )

target_include_directories(convert_restart PRIVATE ${HDF5_INCLUDE_DIR} ${VTK_INCLUDE_DIR})

target_link_directories(convert_restart PRIVATE  ${HDF5_LIBRARY_DIR} ${VTK_LIBRARY_DIR})

target_compile_options(convert_restart PRIVATE -fopenmp -O3 )

target_link_libraries(convert_restart PRIVATE hdf5_cpp hdf5 
                           vtkIOCore-9.5 vtksys-9.5 vtkIOHDF-9.5 vtkhdf5-9.5  vtkCommonDataModel-9.5 vtkCommonCore-9.5 vtkCommonExecutionModel-9.5 vtkIOXML-9.5
                           stdc++fs gomp pthread )


                           
###############################################
