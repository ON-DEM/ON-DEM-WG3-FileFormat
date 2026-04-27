// Open file format library public header

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 28.04.2026

#ifndef public_header__
#define public_header__

#include <iostream>
#include <sstream>
#include <vector>
#include <filesystem>
#include <string>

// Forward declare types used in the wrapper

// container for Particles
class double3
{
public:
    double x, y, z;
    double3(double x_, double y_, double z_):x(x_), y(y_), z(z_){}
    double3():x(0), y(0), z(0){}

};

class double4:public double3
{
public:
  double w;
  double4(double w_, double x_, double y_, double z_):double3(x_,y_,z_), w(w_){}
  double4():double3(), w(0){};
};

class PARTICLES
{
public:
    std::vector<int> id;
    std::vector<int> type_id;
    std::vector<double> scale;
    std::vector<double> radius;
    std::vector<double> mass;
    std::vector<double> volume;
    std::vector<double3> pos_com;
    std::vector<double3> vel_com;
    std::vector<double4> orient_quart;
    std::vector<double3> vel_ang;
    std::vector<double> temp;
    std::vector<double> coh; 
    
    std::vector<double> density;
    
    PARTICLES() = default;
    
    __attribute__((visibility("default"))) 
    void resize(int n);
    
    __attribute__((visibility("default"))) 
    inline size_t size(){return n_p;}
    
    __attribute__((visibility("default"))) 
    inline void set_size(int n){n_p=n;}

    __attribute__((visibility("default"))) 
    size_t get_size() const;
    
private:
    size_t n_p;
    
};

class P_LINE
{
public:
    std::string name, shape, type;
    int number;
    double volume;
    P_LINE(std::string n, double v, int nu, std::string s, std::string t):name(n), shape(s), type(t), number(nu), volume(v){};
};

class particle_header
{
public:
    std::string VER;
    double time;
    int n_DEM;
    int n_Fluid;
    int numPTypes;
    std::vector<P_LINE> ptype;

};

  
//inline size_t PARTICLES::get_size() const;
  
  
//class PARTICLES;
//class particle_header;



namespace OPEN_FILE_FORMAT 
{

  
  
  __attribute__((visibility("default")))
    void get_file_list(const char *path, std::vector<std::filesystem::directory_entry> &file_list, std::vector<double> &t_step_list, double t_min=-1e6, double t_max=1e6);

  
  __attribute__((visibility("default")))
    void read_restart_BlazeDEM(const std::filesystem::directory_entry &f, ::PARTICLES &p, ::particle_header &header);

  __attribute__((visibility("default")))
  void read_restart_vtkhdf(::PARTICLES &p, ::particle_header &header, std::string filename);
  
  __attribute__((visibility("default")))
  void read_restart_hdf5(::PARTICLES &p, ::particle_header &header, std::string filename);
  
  
  __attribute__((visibility("default")))
  void save_restart_BlazeDEM(PARTICLES &p, particle_header &header, std::string filename);
  
  __attribute__((visibility("default")))
    void save_restart_hdf5(PARTICLES &p, particle_header &header, std::string filename);
  
  __attribute__((visibility("default")))
  void save_restart_vtkhdf(PARTICLES &p, particle_header &header, std::string filename);
  
  
    
  __attribute__((visibility("default")))
  void fake_DEM_generator(PARTICLES &p, particle_header &header, int n_p);
  
  

}

//__attribute__((visibility("default")))

#endif