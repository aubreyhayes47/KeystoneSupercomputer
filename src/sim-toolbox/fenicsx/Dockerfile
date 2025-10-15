# FEniCSx Simulation Toolbox
# Based on the official DOLFINx Docker image for reproducible finite element simulations
# Includes MPI support for distributed parallel computing
# Optimized for minimal layers and fast builds

FROM dolfinx/dolfinx:stable

# Set working directory
WORKDIR /app

# Create standardized data directory and copy files in single layer
RUN mkdir -p /data

# Copy example scripts
COPY *.py /app/

# Set environment variables for optimal performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=1 \
    OMP_PROC_BIND=spread \
    OMP_PLACES=threads

# Default entrypoint - can be overridden to run specific scripts
ENTRYPOINT ["python3"]
CMD ["poisson.py"]
