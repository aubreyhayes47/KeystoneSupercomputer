#!/usr/bin/env python3
"""
Test script to validate MPI support in FEniCSx
FEniCSx uses MPI for parallel computing
"""

import sys
from mpi4py import MPI
import dolfinx

def test_mpi():
    """Test MPI functionality"""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    print(f"Process {rank} of {size} reporting")
    
    if rank == 0:
        print("\n" + "="*50)
        print("FEniCSx MPI Test")
        print("="*50)
        print(f"\nMPI World Size: {size}")
        print(f"FEniCSx version: {dolfinx.__version__}")
        print("\n✓ MPI is working correctly!")
        
        if size == 1:
            print("\nNote: Running with 1 process.")
            print("To test parallel execution, run with:")
            print("  mpirun -np 4 python3 test_parallel.py")
        else:
            print(f"\n✓ Successfully running on {size} parallel processes")
        
        print("\n" + "="*50)
        print("MPI Test Completed Successfully!")
        print("="*50)

if __name__ == "__main__":
    test_mpi()
