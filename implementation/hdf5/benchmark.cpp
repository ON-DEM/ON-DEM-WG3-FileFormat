// Benchmark case, formerly known as convert_restart, showing how the integration of the Open file format shared library in external C++ code.

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This code is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 28.04.2026



/*

copy this file to the build directory

compile with:
g++ benchmark.cpp -L. -lopen_file_format_lib -DENABLE_TIMES -fopenmp -O3 -std=c++17

run with 
./a.out ${path_in}/ ${path_out}/
or 
./a.out ${path_in}/ ${path_out}/ t_min t_max
*/


#include "../sources/open_file_format.h"


#ifdef ENABLE_TIMES


#include<chrono>
#include<utility>

// #include"tools.h"

#include <fcntl.h>
#include <unistd.h>
#include <math.h>



std::pair<double, double> get_average(std::vector<std::pair<std::chrono::milliseconds, double>> &t)
{
  size_t N = t.size();
  
    // --- Extract mean ---
  double sum = 0.;
  
  for (const auto& entry : t)
    sum += entry.first.count();

  double mean = sum / N;

    // --- Variance / Standard deviation ---
  double variance = 0.0;
  for (const auto& entry : t) 
  {
    double diff = entry.first.count() - mean;
    variance += diff * diff;
  }
  variance /= N;             // population variance

  double stddev = std::sqrt(variance);
  double stderr = stddev / std::sqrt(N);


  return std::make_pair(mean, stddev);
    
}

std::string gen_stats(std::vector<std::pair<std::chrono::milliseconds, double>> &save)
{
  std::stringstream ss;
  int i=0;
  for( auto &t : save)
    ss << "file " << i++ << " - " << t.first.count()/1000. << " s, \t" << t.second/1024/1024<< " MB\t" << t.second/1024/1024/double(t.first.count()/1000.) << " MB/s\n";
  
  auto q=get_average(save);
  
  ss << "avg " << " - " << q.first/1000. << " s, \t" ;
  ss << "stderr " << " - " << q.second/1000. << " s \t avg - "<< save[0].second/1024/1024/double(q.first/1000.) << " MB/s \n";
  
  return ss.str();
}



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
#else
template<typename F, typename... Args>
  std::chrono::milliseconds measure_time(F&& func, Args&&... args)
  {
    std::forward<F>(func)(std::forward<Args>(args)...);
    return std::chrono::milliseconds(0);
  }
  
  void drop_cache_for_file(std::string &filename){}

#endif


int main(int argc, char *argv[])
{
    
  std::vector<std::filesystem::directory_entry> file_list;
  std::vector<double> t_step_list;

  double t_min=-1e6;
  double t_max=1e6;
  
  std::string out_dir=std::string(argv[2]);
  
  if(argc >= 5)
  {
    t_min=atof(argv[3]);
    t_max=atof(argv[4]);
  }
    // Collect all directory entries or single file
  OPEN_FILE_FORMAT::get_file_list(argv[1], file_list, t_step_list, t_min, t_max);
    
  std::cout << file_list.size() << std::endl;
  

  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_read_Blaze(file_list.size());
  
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_save_Blaze(file_list.size());
  
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_read_hdf5(file_list.size());
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_save_hdf5(file_list.size());
  
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_read_vtkhdf(file_list.size());
  std::vector<std::pair<std::chrono::milliseconds, double>> dur_per_thread_save_vtkhdf(file_list.size());

#ifdef ENABLE_TIMES    
  auto start=std::chrono::steady_clock::now();
#endif
  
  for (size_t i = 0; i < file_list.size(); ++i)
  {
    PARTICLES Particles;
    particle_header header;

//     read restart
    // auto t = measure_time(OPEN_FILE_FORMAT::read_restart_BlazeDEM, file_list[i], Particles, header);
//  or   get_fake_DEM
    auto t=measure_time(OPEN_FILE_FORMAT::fake_DEM_generator, Particles, header, 1000000);
    
    
    dur_per_thread_read_Blaze[i]=std::make_pair(t, Particles.get_size());
    
    
  
  
  // save as Blaze restart
    {
      std::stringstream out;
      out << out_dir << "/restart_" << i << ".txt";
      
      std::string file=out.str();
      drop_cache_for_file(file);
      
      auto t = measure_time(OPEN_FILE_FORMAT::save_restart_BlazeDEM, Particles, header, out.str());

      dur_per_thread_save_Blaze[i]=std::make_pair(t, Particles.get_size());
    }
  
    {
      std::stringstream out;
      out << out_dir <<"/restart_" << i << ".h5";
    
      std::string file=out.str();
      drop_cache_for_file(file);
      auto t = measure_time(OPEN_FILE_FORMAT::save_restart_hdf5, Particles, header, out.str());
      
      dur_per_thread_save_hdf5[i] = std::make_pair(t, Particles.get_size());
    }
    
    //read hdf5 
    {
      std::stringstream out;
      out << out_dir <<"/restart_" << i << ".h5";
      PARTICLES p_hdf5;
      
      std::string file=out.str();
      drop_cache_for_file(file);
      
      auto t = measure_time(OPEN_FILE_FORMAT::read_restart_hdf5, p_hdf5, header, out.str());
      
      dur_per_thread_read_hdf5[i] = std::make_pair(t, p_hdf5.get_size());
    }
    
    // save as vtkhdf restart
    {
      std::stringstream out;
      out << out_dir <<"/restart_" << i << ".vtkhdf";
      PARTICLES p_vtkhdf;
      
      std::string file=out.str();
      drop_cache_for_file(file);
      
      auto t = measure_time(OPEN_FILE_FORMAT::save_restart_vtkhdf, Particles, header, out.str());
      
      dur_per_thread_save_vtkhdf[i] = std::make_pair(t, p_vtkhdf.get_size());
    }
    
    //read vtkhdf 
    {
      std::stringstream out;
      out << out_dir <<"/restart_" << i << ".vtkhdf";
      PARTICLES p_vtkhdf;
      
      std::string file=out.str();
      drop_cache_for_file(file);
      
      auto t = measure_time(OPEN_FILE_FORMAT::read_restart_vtkhdf, p_vtkhdf, header, out.str());
      
      dur_per_thread_read_vtkhdf[i] = std::make_pair(t, p_vtkhdf.get_size());
    }
  }
#ifdef ENABLE_TIMES  

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
#endif
}
