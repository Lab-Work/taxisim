#!/bin/bash
#SBATCH -J pt_test
#SBATCH -n 32
#SBATCH -t 00:02:00
#SBATCH -p normal


module load intel/14.0.1.106
module load mvapich2/2.0b
module load python/2.7.6
module load mpi4py

cd /home1/03172/dbwork/taxisim



export PATH=$PATH:/opt/apps/intel14/mvapich2_2_0/python/2.7.6/lib/python2.7/site-packages/mpi4py/bin
export MV2_SMP_USE_LIMIC2=0

ibrun -np 23 python-mpi ProcessTree.py &> pt_out.txt

