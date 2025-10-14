# LAMMPS Simulation Toolbox Dockerfile
# Provides a containerized LAMMPS environment for molecular dynamics simulations

FROM ubuntu:22.04

LABEL maintainer="Keystone Supercomputer"
LABEL description="LAMMPS molecular dynamics simulation environment"

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install LAMMPS and utilities
RUN apt-get update && apt-get install -y \
    lammps \
    python3 \
    python3-pip \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Create standard data mount point
RUN mkdir -p /data/input /data/output

# Set working directory
WORKDIR /data

# Default command: run LAMMPS with help
CMD ["lmp", "-h"]
