# OpenFOAM Simulation Toolbox Dockerfile
# Provides a containerized environment for computational fluid dynamics (CFD) simulations
# with standardized /data mount points for input/output transfer

FROM openfoam/openfoam11-paraview510:latest

# Set working directory
WORKDIR /workspace

# Create standardized data mount points
RUN mkdir -p /data/input /data/output

# Install Python for scripting and automation
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Copy example scripts
COPY example_cavity.py /workspace/example_cavity.py
COPY README.md /workspace/README.md

# Set environment variables
ENV FOAM_RUN=/workspace/foam-run
ENV DATA_INPUT=/data/input
ENV DATA_OUTPUT=/data/output

# Create foam run directory
RUN mkdir -p $FOAM_RUN

# Default entrypoint sources OpenFOAM environment
ENTRYPOINT ["/bin/bash", "-c", "source /opt/openfoam11/etc/bashrc && exec \"$@\"", "--"]

# Default command shows help
CMD ["echo", "OpenFOAM toolbox ready. Mount /data/input and /data/output volumes. Run example: python3 /workspace/example_cavity.py"]
