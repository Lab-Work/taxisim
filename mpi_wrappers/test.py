# -*- coding: utf-8 -*-
"""
Created on Wed Jan 14 11:59:53 2015

@author: brian
"""

from mpi4py import MPI
import sys

size = MPI.COMM_WORLD.Get_size()
rank = MPI.COMM_WORLD.Get_rank()
name = MPI.Get_processor_name()


print("Helloworld! I am process %d of %d on %s.\n" % (rank, size, name))