# An example showing how to integrate and use the Open file format shared library in external python code.

# created by Rafal Kobylka 
# rkobylka@ipan.lublin.pl


# This code is provided 'as is,' and the author 
# assumes no responsibility for any errors, inaccuracies, 
# or faulty results arising from its use. 
# Users are advised to employ it at their own risk.

# last modified 28.04.2026

# copy this file to Your build directory

import sys
from py_open_file_format_lib import PARTICLES, particle_header, fake_DEM_generator, save_restart_hdf5, read_restart_hdf5, save_restart_vtkhdf, read_restart_vtkhdf

def main():
    if len(sys.argv) != 4:
        raise ValueError("Invalid number of arguments. Usage:\n python script.py out_dir num_particles n_files")

    out_dir = sys.argv[1]
    n_p = int(sys.argv[2])
    n_files = int(sys.argv[3])

    for i in range(n_files):
        particles = PARTICLES()
        header = particle_header()

        # Fill particles with fake data
        fake_DEM_generator(particles, header, n_p)

        # Build output file name
        file_name = f"{out_dir}/restart_{i}.h5"

        # Save HDF5
        save_restart_hdf5(particles, header, file_name)
        
        p_hdf5 = PARTICLES()
        read_restart_hdf5(p_hdf5, header, file_name);
        
        file_name = f"{out_dir}/restart_{i}.vtkhdf"
        
        save_restart_vtkhdf(particles, header, file_name)
        p_hdfvtk = PARTICLES()
        read_restart_vtkhdf(p_hdfvtk, header, file_name);


if __name__ == "__main__":
    main()
