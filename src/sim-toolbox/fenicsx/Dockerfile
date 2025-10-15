# FEniCSx Simulation Toolbox
# Based on the official DOLFINx Docker image for reproducible finite element simulations
# Includes MPI support for distributed parallel computing

FROM dolfinx/dolfinx:stable

# Set working directory
WORKDIR /app

# Create standardized data directory for inputs and outputs
RUN mkdir -p /data

# Copy example scripts
COPY *.py /app/

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Set OpenMP environment variables for optimal multi-core performance
# Note: FEniCSx uses MPI for parallelism by default
ENV OMP_NUM_THREADS=1
ENV OMP_PROC_BIND=spread
ENV OMP_PLACES=threads

# Copy test script
COPY test_parallel.py /app/test_parallel.py

# Default entrypoint - can be overridden to run specific scripts
ENTRYPOINT ["python3"]
CMD ["poisson.py"]
