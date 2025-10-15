# OpenFOAM Simulation Toolbox Dockerfile
# Provides a containerized environment for computational fluid dynamics (CFD) simulations
# with standardized /data mount points for input/output transfer
# Includes OpenMP and MPI support for parallel computing

FROM openfoam/openfoam11-paraview510:latest

# Switch to root to install packages and create directories
USER root

# Create standardized data mount points
RUN mkdir -p /data/input /data/output && \
    chown -R openfoam:openfoam /data

# Install Python for scripting and automation
# Note: OpenFOAM base image includes OpenMPI and OpenMP support
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy example scripts
COPY example_cavity.py /workspace/example_cavity.py
COPY README.md /workspace/README.md
COPY test_parallel.sh /workspace/test_parallel.sh
RUN chmod +x /workspace/test_parallel.sh

# Set environment variables
ENV FOAM_RUN=/workspace/foam-run
ENV DATA_INPUT=/data/input
ENV DATA_OUTPUT=/data/output

# Set OpenMP environment variables for optimal multi-core performance
ENV OMP_NUM_THREADS=1
ENV OMP_PROC_BIND=spread
ENV OMP_PLACES=threads

# Create foam run directory
RUN mkdir -p $FOAM_RUN && \
    chown -R openfoam:openfoam /workspace

# Switch back to openfoam user
USER openfoam

# Default entrypoint sources OpenFOAM environment
ENTRYPOINT ["/bin/bash", "-c", "source /opt/openfoam11/etc/bashrc && exec \"$@\"", "--"]

# Default command shows help
CMD ["echo", "OpenFOAM toolbox ready. Mount /data/input and /data/output volumes. Run example: python3 /workspace/example_cavity.py"]
