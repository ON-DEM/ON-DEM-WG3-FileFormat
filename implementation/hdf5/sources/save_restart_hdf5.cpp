// Blaze Data converter - save_restart_hdf5.cpp 

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025

#include"save_restart_hdf5.h"

#include<H5Cpp.h>

template <typename T>
void write1D(H5::H5File& file,
             const std::string& name,
             const std::vector<T>& data,
             const H5::PredType& type)
{
    hsize_t dims[1] = { data.size() };
    H5::DataSpace space(1, dims);
    H5::DataSet ds = file.createDataSet(name, type, space);
    ds.write(data.data(), type);
}

template <typename T>
void write2D(H5::H5File& file,
             const std::string& name,
             const std::vector<T>& data,
             size_t components,
             const H5::PredType& type)
{
    hsize_t dims[2] = { data.size(), components };
    H5::DataSpace space(2, dims);
    H5::DataSet ds = file.createDataSet(name, type, space);
    ds.write(data.data(), type);
}

void save_restart_hdf5(PARTICLES &p, particle_header &header, std::string filename)
{
    H5::H5File file(filename, H5F_ACC_TRUNC);

    // Write all
    write1D(file, "id", p.id, H5::PredType::NATIVE_INT);
    write1D(file, "type_id", p.type_id, H5::PredType::NATIVE_INT);
    write1D(file, "scale", p.scale, H5::PredType::NATIVE_DOUBLE);
    write1D(file, "radius", p.radius, H5::PredType::NATIVE_DOUBLE);
    write1D(file, "mass", p.mass, H5::PredType::NATIVE_DOUBLE);
    write1D(file, "volume", p.volume, H5::PredType::NATIVE_DOUBLE);
    write2D(file, "pos", p.pos_com, 3, H5::PredType::NATIVE_DOUBLE);
    write2D(file, "vel", p.vel_com, 3, H5::PredType::NATIVE_DOUBLE);
    write2D(file, "vel_ang", p.vel_ang, 3, H5::PredType::NATIVE_DOUBLE);
    write2D(file, "orient_quart", p.orient_quart, 4, H5::PredType::NATIVE_DOUBLE);
    write1D(file, "temp", p.temp, H5::PredType::NATIVE_DOUBLE);
    write1D(file, "coh", p.coh, H5::PredType::NATIVE_DOUBLE);

    write1D(file, "density", p.density, H5::PredType::NATIVE_DOUBLE);
}
