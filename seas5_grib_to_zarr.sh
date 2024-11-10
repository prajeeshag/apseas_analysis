#!/bin/bash
#SBATCH --nodes=1
###SBATCH --ntasks-per-node=100
#SBATCH --account=k10035
#SBATCH -o apseas5_grib_to_zarr.out

export CDO=/scratch/athippp/iops/micromamba/bin/cdo

/scratch/athippp/iops/micromamba/bin/python apseas5_grib_to_zarr.py
