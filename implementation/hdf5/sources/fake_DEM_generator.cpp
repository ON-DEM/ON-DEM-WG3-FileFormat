// Open file format library - fake "random" DEM data generator sources

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 28.04.2026




#include <random>
#include <thread>
#include <omp.h>

#include "fake_DEM_generator.h"

double get_rand_uniform(double min, double max)
{
    thread_local std::mt19937 mt(
        std::random_device{}() + std::hash<std::thread::id>{}(std::this_thread::get_id())
    );
    std::uniform_real_distribution<double> dist(min, max);
    return dist(mt);
}

double3 gen_rand_vec(double3 min, double3 max)
{
  return make_double3
  (
    get_rand_uniform(min.x, max.x),
    get_rand_uniform(min.y, max.y),
    get_rand_uniform(min.z, max.z)
  );
}

// Generate random unit quaternion
double4 gen_rand_quaternion() 
{
    double u1 = get_rand_uniform(0.0, 1.0);
    double u2 = get_rand_uniform(0.0, 1.0);
    double u3 = get_rand_uniform(0.0, 1.0);

    double sqrt1_minus_u1 = std::sqrt(1 - u1);
    double sqrt_u1 = std::sqrt(u1);

    double theta1 = 2 * M_PI * u2;
    double theta2 = 2 * M_PI * u3;

    double w = sqrt1_minus_u1 * std::sin(theta1);
    double x = sqrt1_minus_u1 * std::cos(theta1);
    double y = sqrt_u1 * std::sin(theta2);
    double z = sqrt_u1 * std::cos(theta2);

    return make_double4(w, x, y, z);
}

// Fill functions per type
void fill_vec_double(std::vector<double>& vec, double min, double max) {
    for (auto& v : vec) v = get_rand_uniform(min, max);
}

void fill_vec_int(std::vector<int>& vec, int min, int max) {
    for (auto& v : vec) v = static_cast<int>(get_rand_uniform(min, max)); // inclusive
}

void fill_vec_double3(std::vector<double3>& vec, const double3& min, const double3& max) {
    for (auto& v : vec) v = gen_rand_vec(min, max);
}

void fill_vec_double4(std::vector<double4>& vec) {
    for (auto& v : vec) v = gen_rand_quaternion();
}

double calc_vol(double r, double rho)
{
  return 4./3.*M_PI*r*r*r; //lets make it sphere
}

// Fake generator - automatically launches threads for all vectors
void fake_DEM_generator(PARTICLES& p, particle_header &header, int n_p) 
{
    p.resize(n_p);

    double min_vel = -1.0; 
    double max_vel = 1.0;
    
    double3 pos_ll=make_double3(-0.02, -0.02, 0.0);
    double3 pos_ur=make_double3(0.2, 0.2, 0.5);

    // Vector to store threads
    std::vector<std::thread> th;

// Launch threads per vector
    
    th.push_back(std::thread(fill_vec_int, std::ref(p.type_id), 0, 1));
   
    th.push_back(std::thread(fill_vec_double, std::ref(p.scale), 1, 1));
    th.push_back(std::thread(fill_vec_double, std::ref(p.radius), 0.001, 0.002));
    th.push_back(std::thread(fill_vec_double, std::ref(p.density), 2000, 2000));
        
    th.push_back(std::thread(fill_vec_double3, std::ref(p.pos_com), pos_ll, pos_ur));
    th.push_back(std::thread(fill_vec_double3, std::ref(p.vel_com), make_double3(min_vel, min_vel, min_vel), make_double3(max_vel, max_vel, max_vel)));
    th.push_back(std::thread(fill_vec_double3, std::ref(p.vel_ang), make_double3(min_vel, min_vel, min_vel), make_double3(max_vel, max_vel, max_vel)));
    
    th.push_back(std::thread(fill_vec_double4, std::ref(p.orient_quart)));
    
    th.push_back(std::thread(fill_vec_double, std::ref(p.temp), 0., 0.));
    th.push_back(std::thread(fill_vec_double, std::ref(p.coh), 0, 1));
    
    for(int i=0; i<n_p; ++i)
      p.id[i]=i;
  
    // Join all threads
    for (auto& t : th) t.join();

#pragma omp parallel for num_threads(16)
    for(int i=0; i<n_p; ++i)
    {
      p.volume[i]=calc_vol(p.radius[i], p.density[i]);
      p.mass[i]=p.volume[i]*p.density[i];
    }
}