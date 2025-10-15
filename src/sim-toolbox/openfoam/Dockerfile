# OpenFOAM Simulation Toolbox Dockerfile
# Provides a containerized environment for computational fluid dynamics (CFD) simulations
# with standardized /data mount points for input/output transfer
# Includes OpenMP and MPI support for parallel computing
# Optimized for minimal layers and fast builds

FROM openfoam/openfoam11-paraview510:latest

# Switch to root to install packages and create directories
USER root

# Install Python and create directories in a single layer
# Note: OpenFOAM base image includes OpenMPI and OpenMP support
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && mkdir -p /data/input /data/output /workspace $FOAM_RUN \
    && chown -R openfoam:openfoam /data /workspace

# Set working directory
WORKDIR /workspace

# Copy example scripts
COPY example_cavity.py /workspace/example_cavity.py
COPY README.md /workspace/README.md
COPY test_parallel.sh /workspace/test_parallel.sh
RUN chmod +x /workspace/test_parallel.sh

# Set environment variables for optimal performance
ENV FOAM_RUN=/workspace/foam-run \
    DATA_INPUT=/data/input \
    DATA_OUTPUT=/data/output \
    OMP_NUM_THREADS=1 \
    OMP_PROC_BIND=spread \
    OMP_PLACES=threads

# Switch back to openfoam user
USER openfoam

# Default entrypoint sources OpenFOAM environment
ENTRYPOINT ["/bin/bash", "-c", "source /opt/openfoam11/etc/bashrc && exec \"$@\"", "--"]

# Default command shows help
CMD ["echo", "OpenFOAM toolbox ready. Mount /data/input and /data/output volumes. Run example: python3 /workspace/example_cavity.py"]
