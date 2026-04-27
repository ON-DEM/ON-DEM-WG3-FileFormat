// Open file format library - fake "random" DEM data generator

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 28.04.2026




#pragma once

#include "open_file_format.h"
#include "structs.h"

void fake_DEM_generator(PARTICLES& p, particle_header &header, int n_p);