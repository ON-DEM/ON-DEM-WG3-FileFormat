// An example showing how to integrate and use the Open file format shared library in external C++ code.

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This code is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 28.04.2026

/*

copy this file to Your build directory

compile with:
g++ test.cpp -L. -lopen_file_format_lib -DENABLE_TIMES -fopenmp -O3 -std=c++17

run with: 
./a.out ${path_out}/ num_particles n_files

*/


#include "../sources/open_file_format.h"


#include<utility>

template<typename F, typename... Args>
std::chrono::milliseconds measure_time(F&& func, Args&&... args)
{
    auto start = std::chrono::steady_clock::now();

    std::forward<F>(func)(std::forward<Args>(args)...);

    auto end = std::chrono::steady_clock::now();

    return std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
}


int main(int argc, char *argv[])
{
    
  if(argc !=4 )
    throw std::invalid_argument("invalid number of arguments use:\n a.out out_dir num_particles n_files\n");
  
  std::string out_dir=std::string(argv[1]);
  
  int n_p=atoi(argv[2]);
    
  int n_files=atoi(argv[3]);
  
  for (size_t i = 0; i < n_files; ++i)
  {
    PARTICLES Particles;
    particle_header header;


//  get_fake_DEM
    OPEN_FILE_FORMAT::fake_DEM_generator(Particles, header, n_p);
        
    {
      std::stringstream out;
      out << out_dir <<"/restart_" << i ;
    
      std::string file=out.str();
    
      //save as hdf5 
      OPEN_FILE_FORMAT::save_restart_hdf5(Particles, header, out.str()+".h5");
    
      std::cout << "write " <<  out.str()+".h5" << std::endl;
    //read hdf5 
    
      PARTICLES p_hdf5;
      
      OPEN_FILE_FORMAT::read_restart_hdf5(p_hdf5, header, out.str()+".h5");
      std::cout << "read " <<  out.str()+".h5" << std::endl;
    // save as vtkhdf restart
      
      OPEN_FILE_FORMAT::save_restart_vtkhdf(Particles, header, out.str()+".vtkhdf");
          
      std::cout << "write " <<  out.str()+".vtkhdf" << std::endl;
    //read vtkhdf 
      PARTICLES p_vtkhdf;
          
      OPEN_FILE_FORMAT::read_restart_vtkhdf(p_vtkhdf, header, out.str()+".vtkhdf");
      std::cout << "read " <<  out.str()+".vtkhdf" << std::endl;
    }
    
  }

}
