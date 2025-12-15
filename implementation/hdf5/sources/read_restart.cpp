// Blaze Data converter - read_restart.cpp

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025


#include"read_restart.h"
#include<chrono>

double extract_timestep(const std::string &filename) 
{
  size_t last_underscore = filename.rfind('_');
  if (last_underscore == std::string::npos) 
    return -1; // No underscore found

  std::string timestep_str = filename.substr(last_underscore + 1); // Extract substring after '_'
  try 
  {
    return std::stod(timestep_str); // Convert to double
  }
  catch (const std::invalid_argument&) 
  {
    return -1;
  }
  catch (const std::out_of_range&) 
  {
    return -2;
  }
  
}


void get_file_list(const char *path, std::vector<std::filesystem::directory_entry> &file_list, std::vector<double> &t_step_list, double t_min, double t_max)
{
  std::error_code ec;
  std::filesystem::path p(path);

    
  if (std::filesystem::is_regular_file(p, ec)) 
  {
    file_list.emplace_back(p); // Add single file
    double t=extract_timestep(std::string(path));
    t_step_list.push_back(t);
  } 
  else if (std::filesystem::is_directory(p, ec)) 
  {
    for (const auto& dir_entry : std::filesystem::directory_iterator{p, ec}) 
    {
      if (std::filesystem::is_regular_file(dir_entry.path(), ec)) 
      {
        
        double t=extract_timestep(std::string(dir_entry.path()));
        
        if(t>=0)
        {
          if(t>=t_min && t<=t_max)
          {
            file_list.push_back(dir_entry);
            t_step_list.push_back(t);
          }
        }
        else
        {
          std::cout <<"file " << dir_entry.path() << " ignored " << std::endl;
        }
      }
    }
  } 
  else
  {
    std::cerr << "Invalid path: " << path << std::endl;
    exit(1);
  }
  
  // Sort files by name (mimicking Linux `ls` default behavior)
    std::sort(file_list.begin(), file_list.end(),
              [](const std::filesystem::directory_entry &a, const std::filesystem::directory_entry &b) 
              {
                  return a.path().filename() < b.path().filename();
              });
    
    std::sort(t_step_list.begin(), t_step_list.end(),
              [](const double &a, const double &b) 
              {
                  return a < b;
              });
}
  
  

void parse_stream_to_particles_3_1(char* &file, PARTICLES &p, particle_header &header)   //3.1
{
//     std::string(file).substr(0,100);
    std::stringstream in;
    in << std::string(file);
    
    std::string line;
    
    std::getline(in, line); //ver
        
    std::getline(in, line); //time
    
       
    double time;
    int n_DEM=0, n_Fluid=0;
    
    
    std::string ttt;
    
    std::stringstream tmp;
    tmp << line;
    tmp >> ttt >> header.time >> ttt >> header.n_DEM >> ttt >> header.n_Fluid;
    
    tmp.str("");
    tmp.clear();
    
    std::getline(in, line); //numPTypes
    
    tmp << line;
    tmp >> ttt >> header.numPTypes;
    
    for(int i=0; i<header.numPTypes; ++i)
    {
      tmp.str("");
      tmp.clear();
      std::string name, shape, type;
      double volume;
      int number;
      std::getline(in, line); //numPTypes
      tmp << line;
      tmp >> ttt >> name >> ttt >> volume >> ttt >> number >> ttt >> shape >> ttt >> type;
      
      if(type=="DEM")
        n_DEM+=number;
      if(type=="Fluid")
        n_Fluid+=number;
      
      header.ptype.push_back(P_LINE(name, volume, number, shape, type));
    }
    
    std::getline(in, line); //column names
    std::getline(in, line); //empty
    
//    p.resize(n_DEM);
    while (std::getline(in, line))
    {
       if(line.size()>0 && line[0]!='#') // 10 is to prevent garbage, should be fixed at some day
       {
         if (isdigit(line[0]))
         {
           std::stringstream tmp;
           tmp << line;
           tmp >> p;

         }
       }
        
     }
//     std::cout << "particle read - " << p.size() << "\t particle DEM expected - " << n_DEM 
//               << " particle SPH expected - " << n_Fluid << std::endl;  
    

}



void parse_stream_to_particles(char* &file, PARTICLES &p, particle_header &header)   //3.0
{
//     std::string(file).substr(0,100);
    std::stringstream in;
    in << std::string(file);
    
    std::string line;
    // just for header
    std::getline(in, line); //ver
    
    std::stringstream lne;
    lne << line;
    std::string tmp;
    std::string ver;
    lne >> tmp >> ver;
    
    header.VER=ver;
    
    if(ver=="3.1")
    {
      parse_stream_to_particles_3_1(file, p, header);
    }
    else
    {
      std::cout << "Ver " << ver << "unsupported" << std::endl;
      exit(0);
    }
  
      
      
}


void read_restart_file(const std::filesystem::directory_entry &f, PARTICLES &p, particle_header &header)
{
  std::string file=f.path().string();
//   std::cout << file << std::endl;
  
  std::error_code ec; // For noexcept overload usage.
  if (std::filesystem::exists(file, ec) && !ec)
  {
    

    std::ifstream in;
//     in.open(file.c_str());  // reading file into stringstream
    in.open(f.path());  // reading file into stringstream
  
    if(in.is_open())
    {
      char *buff;

      auto start=std::chrono::steady_clock::now();
  
  
      in.seekg(0, std::ios::end);
      long long file_lenght=in.tellg();
      in.seekg(0, std::ios::beg);
      buff=new char [file_lenght+1];
      in.read (buff, file_lenght); // reading full file, can be replaced with mpi_recv at some point
      buff[file_lenght]='\0';
//       std::cout << file_lenght/1024 << std::endl;
      auto end=std::chrono::steady_clock::now();
      auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
      std::cout << "Read raw data: " << sizeof(char)*(file_lenght+1)/1024/1024/double(duration.count()/1000.) << " MB/s\n";
      parse_stream_to_particles(buff, p, header); //in main
    }     
  }
}
  
  
