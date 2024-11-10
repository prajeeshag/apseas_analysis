#!/bin/bash
#SBATCH --nodes=1
#SBATCH -o prepare_data.out
#SBATCH --account=k10023
#SBATCH --ntasks-per-node=192

/scratch/athippp/iops/micromamba/bin/python prepare_data.py
