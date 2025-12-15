// Blaze Data converter - save_restart_vtkhdf.cpp 

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025

#include "save_restart_vtkhdf.h"

#include <vtkSmartPointer.h>
#include <vtkHDFWriter.h>
#include <vtkPolyData.h>
#include <vtkPoints.h>
#include <vtkDoubleArray.h>
#include <vtkIntArray.h>
#include <vtkPointData.h>

//for vtp files if used
#include <vtkXMLPolyDataWriter.h>

template <typename T>
void add_int_array(vtkPolyData* poly,
                      const std::string& name,
                      const std::vector<T>& data)
{
    auto arr = vtkSmartPointer<vtkIntArray>::New();
    arr->SetName(name.c_str());
    arr->SetNumberOfComponents(1);
    arr->SetNumberOfTuples(data.size());

    for (size_t i = 0; i < data.size(); ++i)
        arr->SetValue(i, data[i]);

    poly->GetPointData()->AddArray(arr);
}



template <typename T>
void add_double_array(vtkPolyData* poly,
                      const std::string& name,
                      const std::vector<T>& data)
{
    auto arr = vtkSmartPointer<vtkDoubleArray>::New();
    arr->SetName(name.c_str());
    arr->SetNumberOfComponents(1);
    arr->SetNumberOfTuples(data.size());

    for (size_t i = 0; i < data.size(); ++i)
        arr->SetValue(i, data[i]);

    poly->GetPointData()->AddArray(arr);
}

//supposed to be slightly slower, and only for 3 components vector, would need separate one for double4
//void add_vector3_array(vtkPolyData* poly,
//                       const std::string &name,
//                       const std::vector<double3>& data)
//{
//    auto arr = vtkSmartPointer<vtkDoubleArray>::New();
//    arr->SetName(name.c_str());
//    arr->SetNumberOfComponents(3);
//    arr->SetNumberOfTuples(data.size());
//
//    for (size_t i = 0; i < data.size(); ++i)
//        arr->SetTuple3(i, data[i].x, data[i].y, data[i].z);
//
//    poly->GetPointData()->AddArray(arr);
//}

template <typename Vec>
void add_vec_array(vtkPolyData* poly,
                      const std::string& name,
                      const std::vector<Vec>& data,
                      int ncomp=3)
{
    auto arr = vtkSmartPointer<vtkDoubleArray>::New();
    arr->SetName(name.c_str());
    arr->SetNumberOfComponents(ncomp);
    arr->SetNumberOfTuples(data.size());

    for (size_t i = 0; i < data.size(); ++i)
        arr->SetTuple(i, &data[i].x);

    poly->GetPointData()->AddArray(arr);
}

void save_restart_vtkhdf(PARTICLES &p, particle_header &header, std::string filename)
{
    using namespace std;

    size_t N = p.id.size();
    if (N == 0) return;

    // Create VTK container
    auto poly = vtkSmartPointer<vtkPolyData>::New();

    // ---- Points ----
    auto pts = vtkSmartPointer<vtkPoints>::New();
    pts->SetDataTypeToDouble(); // ensure double precision
    pts->SetNumberOfPoints(N);

    for (size_t i = 0; i < N; i++)
        pts->SetPoint(i, p.pos_com[i].x, p.pos_com[i].y, p.pos_com[i].z);

    poly->SetPoints(pts);


    add_int_array(poly, "id", p.id);
    add_int_array(poly, "type_id", p.type_id);

    add_double_array(poly, "scale", p.scale);
    add_double_array(poly, "radius", p.radius);
    add_double_array(poly, "mass", p.mass);
    add_double_array(poly, "volume", p.volume);
    
    add_vec_array(poly, "pos", p.pos_com);
    add_vec_array(poly, "vel", p.vel_com);
    add_vec_array(poly, "vel_ang", p.vel_ang);
    add_vec_array(poly, "orient_quart", p.orient_quart, 4);
    
    add_double_array(poly, "temp", p.temp);
    add_double_array(poly, "coh", p.coh);
    add_double_array(poly, "density", p.density);

        
    // vtk-hdf 
    auto writer = vtkSmartPointer<vtkHDFWriter>::New();
//    or vtp,
//    auto writer = vtkSmartPointer<vtkXMLPolyDataWriter>::New();
    
    writer->SetFileName(filename.c_str());
    writer->SetInputData(poly);
    writer->Write();

//    std::cout << "Saved " << N << " particles to " << filename << "\n";
}
