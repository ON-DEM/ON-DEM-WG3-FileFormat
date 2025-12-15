// Blaze Data converter - tools.h 

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025

#ifndef tools__
#define tools__


#include"structs.h"

#include<chrono>


std::pair<double, double> get_average(std::vector<std::pair<std::chrono::milliseconds, double>> &t);

std::string gen_stats(std::vector<std::pair<std::chrono::milliseconds, double>> &t);
#endif
