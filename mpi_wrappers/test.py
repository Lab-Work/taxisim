# -*- coding: utf-8 -*-
"""
Created on Wed Jan 14 11:59:53 2015

@author: brian
"""

from mpi4py import MPI
import sys
comm = MPI.COMM_WORLD

size = MPI.COMM_WORLD.Get_size()
rank = MPI.COMM_WORLD.Get_rank()
name = MPI.Get_processor_name()


print("Helloworld! I am process %d of %d on %s.\n" % (rank, size, name))

if(rank==0):
    comm.send("++++", dest=0)
    comm.send("AAAA", dest=1)
    comm.send("BBBB", dest=2)
    comm.send("CCCC", dest=3)


data = comm.recv(source=0)
print("Process " + str(rank) + " received " + data)


