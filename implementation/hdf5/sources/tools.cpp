// Blaze Data converter - tools.cpp 

// created by Rafal Kobylka 
// rkobylka@ipan.lublin.pl


// This library is provided 'as is,' and the author 
// assumes no responsibility for any errors, inaccuracies, 
// or faulty results arising from its use. 
// Users are advised to employ it at their own risk.

// last modified 20.11.2025

#include"tools.h"

#include<algorithm>



std::pair<double, double> get_average(std::vector<std::pair<std::chrono::milliseconds, double>> &t)
{
  size_t N = t.size();
  
    // --- Extract mean ---
  double sum = 0.;
  
  for (const auto& entry : t)
    sum += entry.first.count();

  double mean = sum / N;

    // --- Variance / Standard deviation ---
  double variance = 0.0;
  for (const auto& entry : t) 
  {
    double diff = entry.first.count() - mean;
    variance += diff * diff;
  }
  variance /= N;             // population variance

  double stddev = std::sqrt(variance);
  double stderr = stddev / std::sqrt(N);


  return std::make_pair(mean, stddev);
    
}

std::string gen_stats(std::vector<std::pair<std::chrono::milliseconds, double>> &save)
{
  std::stringstream ss;
  int i=0;
  for( auto &t : save)
    ss << "file " << i++ << " - " << t.first.count()/1000. << " s, \t" << t.second/1024/1024<< " MB\t" << t.second/1024/1024/double(t.first.count()/1000.) << " MB/s\n";
  
  auto q=get_average(save);
  
  ss << "avg " << " - " << q.first/1000. << " s, \t" ;
  ss << "stderr " << " - " << q.second/1000. << " s \t avg - "<< save[0].second/1024/1024/double(q.first/1000.) << " MB/s \n";
  
  return ss.str();
}
