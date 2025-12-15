// Blaze Data converter - read_restart_vtkhdf.h 

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025

#ifndef __DEM_VTKHDF__READ__
#define __DEM_VTKHDF__READ__

#include "structs.h"

void read_restart_vtkhdf(PARTICLES &p, particle_header &header, std::string filename);

#endif
