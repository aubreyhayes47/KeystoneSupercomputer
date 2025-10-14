# FEniCSx Simulation Toolbox
# Based on the official DOLFINx Docker image for reproducible finite element simulations

FROM dolfinx/dolfinx:stable

# Set working directory
WORKDIR /app

# Create standardized data directory for inputs and outputs
RUN mkdir -p /data

# Copy example scripts
COPY *.py /app/

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Default entrypoint - can be overridden to run specific scripts
ENTRYPOINT ["python3"]
CMD ["poisson.py"]
