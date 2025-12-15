// Blaze Data converter - save_restart.cpp 

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025

#include "save_restart.h"

#include <fstream>

void save_restart_BlazeDEM(PARTICLES &p, particle_header &header, std::string filename)
{
  std::stringstream ss;
  ss << "VER:\t3.1\n";
  ss << "TimeStamp:\t" << header.time << "\tNumDEMParticles:\t "<< header.n_DEM << "\tNumFluidParticles:\t" << header.n_Fluid << "\n";
  ss << "NumPTypes:	" << header.numPTypes << "\n";
//  double vol=4./3.*M_PI*p[0].radius*p[0].radius*p[0].radius;
  for(int i=0; i<header.numPTypes; ++i)
  {
    ss << "Name:\t" << header.ptype[i].name << "\tVolume:\t" << header.ptype[i].volume << "\tNumber:\t" << header.ptype[i].number << "\tShape:\t" << header.ptype[i].shape << "\tType:\t" << header.ptype[i].type << "\n";
  }
  ss << "\n";
  ss << "PID	PTypeID	PScale	PBRadius	PVol	PMass	PosCOM_x	PosCOM_y	PosCOM_z	VelCOM_x	VelCOM_y	VelCOM_z	PosAngQuart_w	PosAngQuart_x	PosAngQuart_y	PosAngQuart_z	VelAng_x	VelAng_y	VelAng_z	Temp	Coh\n";
  ss << "\n";
  
  ss << p;
 
  
  ss << "\n\n";

  
  std::ofstream of;
  of.open(filename);
  of << ss.str();
  of.flush();
  of.close();
  
}
