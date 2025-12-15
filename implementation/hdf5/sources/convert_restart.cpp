// Blaze Data converter - convert_restart.cpp

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 04.12.2025


//run with:
//./convert_restart $path_to_input $output_dir
//or
//./convert_restart $path_to_input $output_dir t_min t_max

// output dir must be valid path - created manually otherwise hdf will throw strange uninformative error

#include<iostream>
#include<sstream>
#include<vector>

#include<fstream>
#include<filesystem>
#include<string>
#include<math.h>
#include<utility>
#include<algorithm>     

#include<thread>
#include<omp.h>

#include"structs.h"
#include"read_restart.h"
#include"save_restart.h"

#include"save_restart_hdf5.h"
#include"read_restart_hdf5.h"

#include"save_restart_vtkhdf.h"
#include"read_restart_vtkhdf.h"

#include<chrono>
#include<utility>

#include"tools.h"

#include <fcntl.h>
#include <unistd.h>

//#define use_omp // uncomment for omp threads







template<typename F, typename... Args>
std::chrono::milliseconds measure_time(F&& func, Args&&... args)
{
    auto start = std::chrono::steady_clock::now();

    std::forward<F>(func)(std::forward<Args>(args)...);

    auto end = std::chrono::steady_clock::now();

    return std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
}

void drop_cache_for_file(std::string &filename)
{
    int fd = open(filename.c_str(), O_RDONLY);
    if (fd < 0) return;

    // Tell Linux we don’t need cached data for this file anymore
    posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED);

    close(fd);
}

int main(int argc, char *argv[])
{
  
  std::vector<std::filesystem::directory_entry> file_list;
  std::vector<double> t_step_list;

  double t_min=-1e6;
  double t_max=1e6;
  
  if(argc >= 5)
  {
    t_min=atof(argv[3]);
    t_max=atof(argv[4]);
  }
    // Collect all directory entries or single file
  get_file_list(argv[1], file_list, t_step_list, t_min, t_max);
 
  std::vector<std::string> str;
  str.resize(file_list.size());
//   std::cout << file_list.size() << std::endl;
 
  std::string out_dir=std::string(argv[2]);
  
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_read_Blaze(file_list.size());
//  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_read_Blaze_raw(file_list.size()); // will print that from elsewhere 
  
  
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_save_Blaze(file_list.size());
  
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_read_hdf5(file_list.size());
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_save_hdf5(file_list.size());
  
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_read_vtkhdf(file_list.size());
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_save_vtkhdf(file_list.size());
  
  
    
  auto start=std::chrono::steady_clock::now();
#ifdef use_omp
  #pragma omp parallel for num_threads(16) //hdf5 doesn't support threads, only MPI 
#endif
  for (size_t i = 0; i < file_list.size(); ++i)
  {
//  TODO -> read in parallel, but hdf5 writer goes serial  (thread pool, with check of available memory otherwise we are screwed).
//  TODO -> hdf5 writer using MPI -> explore that
    PARTICLES Particles;
    particle_header header;

    std::string file=file_list[i].path().string();
    drop_cache_for_file(file);
    
// read Blaze restart    
    {
      auto t = measure_time(read_restart_file, file_list[i], Particles, header);
      
      dur_per_thread_read_Blaze[i]=std::make_pair(t, Particles.get_size());
    }
    
    
// save as Blaze restart
    {
      std::stringstream out;
      out << out_dir << "/restart_" << i << ".txt";
      
      std::string file=out.str();
      drop_cache_for_file(file);
      
      auto t = measure_time(save_restart_BlazeDEM, Particles, header, out.str());

      dur_per_thread_save_Blaze[i]=std::make_pair(t, Particles.get_size());
    }

    
#ifndef use_omp    //hdf5 doesn't support threads, only MPI 
    // save as hdf5 restart
    {
      std::stringstream out;
      out << out_dir <<"/restart_" << i << ".h5";
    
      std::string file=out.str();
      drop_cache_for_file(file);
      auto t = measure_time(save_restart_hdf5, Particles, header, out.str());
      
      dur_per_thread_save_hdf5[i] = std::make_pair(t, Particles.get_size());
    }
    
    //read hdf5 
    {
      std::stringstream out;
      out << out_dir <<"/restart_" << i << ".h5";
      PARTICLES p_hdf5;
      
      std::string file=out.str();
      drop_cache_for_file(file);
      
      auto t = measure_time(read_restart_hdf5, p_hdf5, header, out.str());
      
      dur_per_thread_read_hdf5[i] = std::make_pair(t, p_hdf5.get_size());
    }
    
    // save as vtkhdf restart
    {
      std::stringstream out;
      out << out_dir <<"/restart_" << i << ".vtkhdf";
      PARTICLES p_vtkhdf;
      
      std::string file=out.str();
      drop_cache_for_file(file);
      
      auto t = measure_time(save_restart_vtkhdf, Particles, header, out.str());
      
      dur_per_thread_save_vtkhdf[i] = std::make_pair(t, p_vtkhdf.get_size());
    }
    
    //read vtkhdf 
    {
      std::stringstream out;
      out << out_dir <<"/restart_" << i << ".vtkhdf";
      PARTICLES p_vtkhdf;
      
      std::string file=out.str();
      drop_cache_for_file(file);
      
      auto t = measure_time(read_restart_vtkhdf, p_vtkhdf, header, out.str());
      
      dur_per_thread_read_vtkhdf[i] = std::make_pair(t, p_vtkhdf.get_size());
    }
#endif
  }

  auto end=std::chrono::steady_clock::now();
  
  auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
  
  std::stringstream stats;
  
  stats << "read Blaze:\n";
  stats << gen_stats(dur_per_thread_read_Blaze);

  
  stats << "save Blaze:\n";
  stats << gen_stats(dur_per_thread_save_Blaze);
  
  stats << "read hdf5:\n";
  stats << gen_stats(dur_per_thread_read_hdf5);

  stats << "save hdf5:\n";
  stats << gen_stats(dur_per_thread_save_hdf5);
   
  stats << "read vtkhdf:\n";
  stats << gen_stats(dur_per_thread_read_vtkhdf);
  
  stats << "save vtkhdf:\n";
  stats << gen_stats(dur_per_thread_save_vtkhdf);

  stats << "Total execution time: " << duration.count()/1000. << " s\n";
    
  
  std::cout << stats.str() << std::endl;

  return 0;
}
