// Blaze Data converter - read_restart_hdf5.cpp

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025

#include "read_restart_hdf5.h"

#include <H5Cpp.h>


void read_restart_hdf5(PARTICLES &p, particle_header &header, std::string filename)
{

    H5::H5File file(filename, H5F_ACC_RDONLY);

    // First, detect number of particles from any 1D dataset
    H5::DataSet id_set = file.openDataSet("id");
    H5::DataSpace idspace = id_set.getSpace();

    hsize_t dims[1];
    idspace.getSimpleExtentDims(dims);
    size_t N = dims[0];

    p.resize(N);  // resize all vectors inside p
    

    // Read id
    id_set.read(p.id.data(), H5::PredType::NATIVE_INT);
    
//    type_id
    {
      H5::DataSet tid_set = file.openDataSet("type_id");
      tid_set.read(p.type_id.data(), H5::PredType::NATIVE_INT);
    }
    
//  scale
    {
      H5::DataSet d_set = file.openDataSet("scale");
      d_set.read(p.scale.data(), H5::PredType::NATIVE_DOUBLE);
    }
    
//  radius
    {
      H5::DataSet d_set = file.openDataSet("radius");
      d_set.read(p.radius.data(), H5::PredType::NATIVE_DOUBLE);
    }
    
    // mass
    {
      H5::DataSet d_set = file.openDataSet("mass");
      d_set.read(p.mass.data(), H5::PredType::NATIVE_DOUBLE);
    }
    
    // volume
    {
      H5::DataSet d_set = file.openDataSet("volume");
      d_set.read(p.volume.data(), H5::PredType::NATIVE_DOUBLE);
    }
    
    // density
    {
      H5::DataSet d_set = file.openDataSet("density");
      d_set.read(p.density.data(), H5::PredType::NATIVE_DOUBLE);
    }
    
    // temperature
    {
      H5::DataSet d_set = file.openDataSet("temp");
      d_set.read(p.temp.data(), H5::PredType::NATIVE_DOUBLE);
    }
    
    // cohesion
    {
      H5::DataSet d_set = file.openDataSet("coh");
      d_set.read(p.coh.data(), H5::PredType::NATIVE_DOUBLE);
    }
    

    // pos (Nx3)
    {
        H5::DataSet d_set = file.openDataSet("pos");

        // no native double3, so we need to convert after reading 2d matrix
        std::vector<double> tmp(N * 3); 
        d_set.read(tmp.data(), H5::PredType::NATIVE_DOUBLE);

        for (size_t i = 0; i < N; i++)
            p.pos_com[i] = make_double3(tmp[3*i], tmp[3*i+1], tmp[3*i+2]);
    }
    
    // vel (Nx3)
    {
        H5::DataSet d_set = file.openDataSet("vel");

        std::vector<double> tmp(N * 3);
        d_set.read(tmp.data(), H5::PredType::NATIVE_DOUBLE);

        for (size_t i = 0; i < N; i++)
            p.vel_com[i] = make_double3(tmp[3*i], tmp[3*i+1], tmp[3*i+2]);
    }
    
        // ang_vel (Nx3)
    {
        H5::DataSet d_set = file.openDataSet("vel_ang");

        std::vector<double> tmp(N * 3);
        d_set.read(tmp.data(), H5::PredType::NATIVE_DOUBLE);

        for (size_t i = 0; i < N; i++)
            p.vel_ang[i] = make_double3(tmp[3*i], tmp[3*i+1], tmp[3*i+2]);
    }
    
    // orient (Nx4)
    {
        H5::DataSet d_set = file.openDataSet("orient_quart");

        std::vector<double> tmp(N * 4);
        d_set.read(tmp.data(), H5::PredType::NATIVE_DOUBLE);

        for (size_t i = 0; i < N; i++)
            p.vel_ang[i] = make_double4(tmp[3*i], tmp[3*i+1], tmp[3*i+2], tmp[3*i+3]);
    }
    
    return;
}
