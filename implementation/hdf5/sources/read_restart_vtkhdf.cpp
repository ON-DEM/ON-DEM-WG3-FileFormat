// Blaze Data converter - read_restart_vtkhdf.cpp 

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025



#include "read_restart_vtkhdf.h"

#include <vtkSmartPointer.h>
#include <vtkHDFReader.h>
#include <vtkPolyData.h>
#include <vtkPointData.h>
#include <vtkIntArray.h>
#include <vtkDoubleArray.h>

//for vtp if used
#include <vtkXMLPolyDataReader.h>



void read_restart_vtkhdf(PARTICLES &p, particle_header &header, std::string filename)
{

  auto reader = vtkSmartPointer<vtkHDFReader>::New();  // .hdf
//  auto reader = vtkSmartPointer<vtkXMLPolyDataReader>::New();  // .vtp

  reader->SetFileName(filename.c_str());
  reader->Update(); // read the dataset
    
  vtkPolyData* poly = vtkPolyData::SafeDownCast(reader->GetOutput());
  if (!poly)
    throw std::runtime_error("sth went wrong, file does not contain vtkPolyData");

  auto pd = poly->GetPointData();
  const size_t N = poly->GetNumberOfPoints();
    
  p.resize(N);
    
  if (auto arr = vtkIntArray::SafeDownCast(pd->GetArray("id"))) 
  {
    for (size_t i = 0; i < N; i++)
      p.id[i] = arr->GetValue(i);
  }  
 
  if (auto arr = vtkIntArray::SafeDownCast(pd->GetArray("type_id"))) 
  {
    for (size_t i = 0; i < N; i++)
      p.type_id[i] = arr->GetValue(i);
  }  

  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("scale"))) 
  {
    for (size_t i = 0; i < N; i++)
      p.scale[i] = arr->GetValue(i);
  }  
  
  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("radius"))) 
  {
    for (size_t i = 0; i < N; i++)
      p.radius[i] = arr->GetValue(i);
  }  
  
  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("mass"))) 
  {
    for (size_t i = 0; i < N; i++)
      p.mass[i] = arr->GetValue(i);
  }  
  
  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("volume"))) 
  {
    for (size_t i = 0; i < N; i++)
      p.volume[i] = arr->GetValue(i);
  }  
  
  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("temp"))) 
  {
    for (size_t i = 0; i < N; i++)
      p.temp[i] = arr->GetValue(i);
  }  
  
  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("coh"))) 
  {
    for (size_t i = 0; i < N; i++)
      p.coh[i] = arr->GetValue(i);
  }  
  
  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("density"))) 
  {
    for (size_t i = 0; i < N; i++)
      p.density[i] = arr->GetValue(i);
  }  
  
  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("pos"))) 
  {
    for (size_t i = 0; i < N; i++) 
    {
      double t[3];
      arr->GetTuple(i, t);
      p.pos_com[i] = make_double3(t[0], t[1], t[2]);
    }
  }
  
  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("vel"))) 
  {
    for (size_t i = 0; i < N; i++) 
    {
      double t[3];
      arr->GetTuple(i, t);
      p.vel_com[i] = make_double3(t[0], t[1], t[2]);
    }
  }
  
  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("vel_ang"))) 
  {
    for (size_t i = 0; i < N; i++) 
    {
      double t[3];
      arr->GetTuple(i, t);
      p.vel_ang[i] = make_double3(t[0], t[1], t[2]);
    }
  }
  
  if (auto arr = vtkDoubleArray::SafeDownCast(pd->GetArray("orient_quart"))) 
  {
    for (size_t i = 0; i < N; i++) 
    {
      double t[4];
      arr->GetTuple(i, t);
      p.orient_quart[i] = make_double4(t[0], t[1], t[2], t[3]);
    }
  }
  
}


