// Blaze Data converter - struct.cpp 

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025

#include "structs.h"

double3 make_double3(double a, double b, double c)
{
    double3 t;
    t.x=a;
    t.y=b;
    t.z=c;
    return t;
}

double4 make_double4(double a, double b, double c, double d)
{
    double4 t;
    t.x=a;
    t.y=b;
    t.z=c;
    t.w=d;
    return t;
}


double length(const double3 &t)
{
  return sqrt(t.x*t.x+t.y*t.y+t.z*t.z);  
}

double length2D(const double3 &t)
{
  return sqrt(t.x*t.x+t.y*t.y);  
}

double dist(const double3 &p, const double3 q)
{
    return sqrt(pow(p.x-q.x, 2)+pow(p.y-q.y, 2)+ pow(p.z-q.z, 2));
}

double dist2D(const double3 &p, const double3 q)
{
    return sqrt(pow(p.x-q.x, 2)+pow(p.y-q.y, 2));
}

double dot(double3 a, double3 b)
{
  return a.x*b.x+a.y*b.y+a.z*b.z;
}


std::stringstream& operator >> (std::stringstream& in, double3 &f)
{
    in >> f.x >> f.y >> f.z;
    return in;
}

std::ostream& operator << (std::ostream& out, const double3 &p)
{
    out << p.x <<" "<< p.y << " "<< p.z;
    return out;
}

std::stringstream& operator >> (std::stringstream& in, double4 &f)
{
  in >> f.x >> f.y >> f.z >> f.w;
  return in;
}

std::ostream& operator << (std::ostream& out, const double4 &p)
{
    out << p.x << " "<< p.y << " "<< p.z << " "<< p.w;
    return out;
}

double3 operator - (const double3 &a, const double3 &b)
{
    return double3(a.x-b.x, a.y-b.y, a.z-b.z);
}

double3 operator + (const double3 &a, const double3 &b)
{
    return double3(a.x+b.x, a.y+b.y, a.z+b.z);
}

double3 operator * (const double3 &a, const double &b)
{
  return make_double3(a.x*b, a.y*b, a.z*b);
}

double3 operator * (const double &b, const double3 &a)
{
  return make_double3(a.x*b, a.y*b, a.z*b);
}

double3& operator+=(double3& a, const double3& b) 
{
    a.x += b.x;
    a.y += b.y;
    a.z += b.z;
    return a;
}

double3& operator-=(double3& a, const double3& b) 
{
    a.x -= b.x;
    a.y -= b.y;
    a.z -= b.z;
    return a;
}

void PARTICLES::resize(int n)
{
    if(n<1)
      throw std::invalid_argument("no particles?");
  
    id.resize(n, -1);
    type_id.resize(n, -1);
    scale.resize(n, 0.);
    radius.resize(n, 0.);
    mass.resize(n, 0.);
    volume.resize(n, 0);
    pos_com.resize(n, make_double3(0., 0., 0.));
    vel_com.resize(n, make_double3(0., 0., 0.));
    orient_quart.resize(n, make_double4(0., 0., 0., 0));
    vel_ang.resize(n, make_double3(0., 0., 0.));
    temp.resize(n, 0);
    coh.resize(n, 0); 
    
    density.resize(n, 0);
    
    n_p=n;
    
}


std::stringstream& operator >> (std::stringstream& in, PARTICLES &p) // ver 3.1
{
//  int i=PARTICLES::counter;
    
  int i;
  double d;
  double3 d3;
  double4 d4;
  
  // goes in order <- do not replace it with if/else or switch 
  if(in >> i)
    p.id.push_back(i);
  if(in >> i)
    p.type_id.push_back(i);
  if (in >> d)
    p.scale.push_back(d);
  if(in >> d)
    p.radius.push_back(d);
  if(in >> d)
    p.volume.push_back(d);
  if(in >> d)
    p.mass.push_back(d);
  if(in >> d3)
     p.pos_com.push_back(d3);
  if(in >> d3)
     p.vel_com.push_back(d3);
  if(in >> d4)
     p.orient_quart.push_back(d4);
  if(in >> d3)
     p.vel_ang.push_back(d3);
  if(in >> d)
     p.temp.push_back(d);
  if(in >> d)
     p.coh.push_back(d);
      
  p.density.push_back(p.mass[i]/p.volume[i]);
    
  p.set_size(p.id.size());  
  return in;
}

double vol(double r)
{
    return 4./3.*M_PI*r*r*r;
}


std::ostream& operator << (std::ostream& out, PARTICLES &p)
{
    for(int i=0; i<p.size(); ++i)
    {
      out << p.id[i] << "\t"<< p.type_id[i] << "\t"<< p.scale[i] << "\t"
        << p.radius[i] << "\t"<< p.volume[i] << "\t" <<p.mass[i] << "\t" 
        << p.pos_com[i] << "\t" << p.vel_com[i] << "\t" << p.orient_quart[i] << "\t"<< p.vel_ang[i] << "\t"
        << p.temp[i] << "\t" << p.coh[i] << "\n";
    }
    return out;
}

