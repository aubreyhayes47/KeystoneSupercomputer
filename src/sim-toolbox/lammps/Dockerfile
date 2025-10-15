# LAMMPS Simulation Toolbox Dockerfile
# Provides a containerized LAMMPS environment for molecular dynamics simulations

FROM ubuntu:22.04

LABEL maintainer="Keystone Supercomputer"
LABEL description="LAMMPS molecular dynamics simulation environment with OpenMP and MPI support"

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install LAMMPS, OpenMP, MPI libraries, and utilities
# Note: LAMMPS package includes OpenMPI and OpenMP support by default
RUN apt-get update && apt-get install -y \
    lammps \
    libopenmpi-dev \
    openmpi-bin \
    python3 \
    python3-pip \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set OpenMP environment variables for optimal multi-core performance
ENV OMP_NUM_THREADS=1
ENV OMP_PROC_BIND=spread
ENV OMP_PLACES=threads

# Copy test scripts
COPY test_parallel.sh /app/test_parallel.sh
RUN chmod +x /app/test_parallel.sh

# Create standard data mount point
RUN mkdir -p /data/input /data/output

# Set working directory
WORKDIR /data

# Default command: run LAMMPS with help
CMD ["lmp", "-h"]
