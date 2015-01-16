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



def funcA(x):
    print("A " + str(x))

def funcB(x):
    print("B " + str(x))


print("Helloworld! I am process %d of %d on %s.\n" % (rank, size, name))

if(rank==0):
    comm.send(funcA, dest=0)
    comm.send(funcB, dest=1)
    comm.send(funcA, dest=2)
    comm.send(funcB, dest=3)


func = comm.recv(source=0)
func(rank)


