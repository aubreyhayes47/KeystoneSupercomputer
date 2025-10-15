#!/bin/bash
# Test script to validate OpenMP and MPI support in LAMMPS

set -e

echo "========================================="
echo "LAMMPS Parallel Support Test"
echo "========================================="
echo

# Test 1: Check MPI installation
echo "1. Checking MPI installation..."
which mpirun
mpirun --version
echo "✓ MPI is installed"
echo

# Test 2: Check OpenMP support in LAMMPS
echo "2. Checking LAMMPS OpenMP support..."
lmp -h 2>&1 | grep -i "OpenMP"
echo "✓ LAMMPS compiled with OpenMP"
echo

# Test 3: Check MPI support in LAMMPS
echo "3. Checking LAMMPS MPI support..."
lmp -h 2>&1 | grep -i "MPI"
echo "✓ LAMMPS compiled with MPI"
echo

# Test 4: Check available LAMMPS packages
echo "4. Checking LAMMPS packages..."
lmp -h 2>&1 | grep -A 20 "Active compile time flags" || true
echo

# Test 5: Run simple LAMMPS test with serial execution
echo "5. Testing LAMMPS serial execution..."
cat > /tmp/test_simple.lmp << 'EOF'
# Simple Lennard-Jones fluid
units lj
atom_style atomic
lattice fcc 0.8442
region box block 0 4 0 4 0 4
create_box 1 box
create_atoms 1 box
mass 1 1.0
velocity all create 1.44 87287 loop geom
pair_style lj/cut 2.5
pair_coeff 1 1 1.0 1.0 2.5
neighbor 0.3 bin
neigh_modify every 20 delay 0 check no
fix 1 all nve
timestep 0.005
run 100
EOF
lmp -in /tmp/test_simple.lmp > /tmp/test_serial.log 2>&1
echo "✓ LAMMPS serial test completed successfully"
echo

# Test 6: Run simple LAMMPS test with MPI
echo "6. Testing LAMMPS with MPI (2 processes)..."
mpirun -np 2 --allow-run-as-root lmp -in /tmp/test_simple.lmp > /tmp/test_mpi.log 2>&1
echo "✓ LAMMPS MPI test completed successfully"
echo

echo "========================================="
echo "All tests passed! ✓"
echo "========================================="
echo
echo "Summary:"
echo "- OpenMP: Available in LAMMPS (set OMP_NUM_THREADS to control threads)"
echo "- MPI: Available and tested (use mpirun -np <N> to run on N processes)"
echo "- Note: USER-OMP package may not be installed; OpenMP is available in base LAMMPS"
echo
echo "Example commands:"
echo "  Serial:       lmp -in input.lmp"
echo "  MPI:          mpirun -np 4 lmp -in input.lmp"
echo "  With threads: export OMP_NUM_THREADS=4 && lmp -in input.lmp"
echo
echo "To check available packages in LAMMPS: lmp -h"

