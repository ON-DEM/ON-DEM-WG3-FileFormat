// Open file format library - wrappers for namespace

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 28.04.2026


#pragma once

#include "structs.h"   

#include "read_restart.h"
#include "read_restart_hdf5.h"
#include "read_restart_vtkhdf.h"

#include "save_restart.h"
#include "save_restart_hdf5.h"
#include "save_restart_vtkhdf.h"

#include "fake_DEM_generator.h"

#include "open_file_format.h"



// wrappers for public API
namespace OPEN_FILE_FORMAT 
{
 
  class PARTICLES 
  {
public:
    PARTICLES() = default;

    // Resize
    void resize(int n) { impl.resize(n); }

    // Accessor for size
    size_t size() { return impl.size(); }
    void set_size(int n) { impl.set_size(n); }

    // Compute memory footprint (proxy to internal)
    size_t get_size() const { return impl.get_size(); }

    // Access internal vectors by reference
    std::vector<int>& id() { return impl.id; }
    std::vector<int>& type_id() { return impl.type_id; }
    std::vector<double>& scale() { return impl.scale; }
    std::vector<double>& radius() { return impl.radius; }
    std::vector<double>& mass() { return impl.mass; }
    std::vector<double>& volume() { return impl.volume; }

    std::vector<::double3>& pos_com() { return impl.pos_com; }
    std::vector<::double3>& vel_com() { return impl.vel_com; }
    std::vector<::double4>& orient_quart() { return impl.orient_quart; }
    std::vector<::double3>& vel_ang() { return impl.vel_ang; }

    std::vector<double>& temp() { return impl.temp; }
    std::vector<double>& coh() { return impl.coh; }
    std::vector<double>& density() { return impl.density; }

private:
    ::PARTICLES impl;  // internal PARTICLES
  };

  
//  wrapper for header
  
  class particle_header 
  {
public:
    particle_header() = default;

    // Accessors for simple members
    std::string& VER() { return impl.VER; }
    double& time() { return impl.time; }
    int& n_DEM() { return impl.n_DEM; }
    int& n_Fluid() { return impl.n_Fluid; }
    int& numPTypes() { return impl.numPTypes; }

    // Access vector of structs
    std::vector<::P_LINE>& ptype() { return impl.ptype; }

private:
      ::particle_header impl;  // internal object
  };

  void get_file_list(const char *path, std::vector<std::filesystem::directory_entry> &file_list, std::vector<double> &t_step_list, double t_min, double t_max)
  {
    return ::get_file_list(path, file_list, t_step_list, t_min, t_max);
  }
  
  
  void read_restart_BlazeDEM(const std::filesystem::directory_entry &f, ::PARTICLES &p, ::particle_header &header)
  {
    return ::read_restart_file(f, p, header);
  }
    
  void read_restart_vtkhdf(::PARTICLES &p, ::particle_header &header, std::string filename)
  {
    return ::read_restart_vtkhdf(p, header, filename);
  }
  
  void read_restart_hdf5(::PARTICLES &p, ::particle_header &header, std::string filename)
  {
    return ::read_restart_hdf5(p, header, filename);
  }
  
  
  void save_restart_BlazeDEM(::PARTICLES &p, ::particle_header &header, std::string filename)
  {
    return ::save_restart_BlazeDEM(p, header, filename);
  }
  
  void save_restart_hdf5(::PARTICLES &p, ::particle_header &header, std::string filename)
  {
    return ::save_restart_hdf5(p, header, filename);
  }
  
  void save_restart_vtkhdf(::PARTICLES &p, ::particle_header &header, std::string filename)
  {
    return ::save_restart_vtkhdf(p, header, filename);
  }
  
  void fake_DEM_generator(::PARTICLES& p, ::particle_header &header, int n_p)
  {
    return ::fake_DEM_generator(p, header, n_p);
  }
  
  
//  size_t PARTICLES::get_size() const 
//  {
//    return ::PARTICLES::get_size();
//  }
  
}

