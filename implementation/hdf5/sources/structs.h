// Blaze Data converter - struct.h 

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 04.12.2025

#ifndef structs__
#define structs__

#include <iostream>
#include <sstream>
#include <math.h>
#include <vector>
#include <unordered_map>



#include<string>
#include<math.h>

#include<algorithm>


class double3
{
public:
    double x, y, z;
    double3(double x_, double y_, double z_):x(x_), y(y_), z(z_){}
    double3():x(0), y(0), z(0){}

};

double3 make_double3(double a, double b, double c);

double length(const double3 &t);
double dist(const double3 &p, const double3 q);
double dist2D(const double3 &p, const double3 q);


class double4:public double3
{
public:
  double w;
  double4(double x_, double y_, double z_, double w_):double3(x_,y_,z_), w(w_){}
  double4():double3(), w(0){};
};

double4 make_double4(double a, double b, double c, double d);

std::stringstream& operator >> (std::stringstream& in, double3 &f);
std::ostream& operator << (std::ostream& out, const double3 &p);

std::stringstream& operator >> (std::stringstream& in, double4 &f);
std::ostream& operator << (std::ostream& out, const double4 &p);


double3 operator - (const double3 &a, const double3 &b);
double3 operator + (const double3 &a, const double3 &b);
double3& operator += (double3 &a, const double3 &b);
double3& operator -= (double3 &a, const double3 &b);

double length2D(const double3 &t);
double dot(double3 a, double3 b);
double3 operator * (const double3 &a, const double &b);
double3 operator * (const double &a, const double3 &b);

// ------------------------------------------
// container for Particles


class PARTICLES
{
public:
    std::vector<int> id;
    std::vector<int> type_id;
    std::vector<double> scale;
    std::vector<double> radius;
    std::vector<double> mass;
    std::vector<double> volume;
    std::vector<double3> pos_com;
    std::vector<double3> vel_com;
    std::vector<double4> orient_quart;
    std::vector<double3> vel_ang;
    std::vector<double> temp;
    std::vector<double> coh; 
    
    std::vector<double> density;
    
    PARTICLES() = default;
    void resize(int n);
    inline size_t size(){return n_p;}
    inline void set_size(int n){n_p=n;}

    inline size_t get_size()
    {
      return 2*n_p*sizeof(int) + 7*n_p*sizeof(double) + 3*n_p*sizeof(double3) + n_p*sizeof(double4);
    }
private:
    size_t n_p;
    
};


std::stringstream& operator >> (std::stringstream& in, PARTICLES &p);
std::ostream& operator << (std::ostream& out, PARTICLES &p);

// ------------------------------------------
// container for header in restart files

class P_LINE
{
public:
    std::string name, shape, type;
    int number;
    double volume;
    P_LINE(std::string n, double v, int nu, std::string s, std::string t):name(n), shape(s), type(t), number(nu), volume(v){};
};

class particle_header
{
public:
    std::string VER;
    double time;
    int n_DEM;
    int n_Fluid;
    int numPTypes;
    std::vector<P_LINE> ptype;

};


#endif
