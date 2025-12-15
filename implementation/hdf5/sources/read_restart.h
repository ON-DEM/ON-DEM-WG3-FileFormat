// Blaze Data converter - read_restart.h

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025

#ifndef rrestart__
#define rrestart__


#include<fstream>
#include<filesystem>

#include"structs.h"


void read_restart_file(const std::filesystem::directory_entry &f, PARTICLES &p, particle_header &header);

void get_file_list(const char *path, std::vector<std::filesystem::directory_entry> &file_list, std::vector<double> &t_step_list, double t_min=-1e6, double t_max=1e6);

double extract_timestep(const std::string &filename);

#endif
