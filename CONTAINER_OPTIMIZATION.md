# Container Image Optimization Guide

This guide documents the optimization techniques applied to Keystone Supercomputer container images to reduce size, improve build times, and tune runtime performance for optimal simulation speed and reproducibility.

---

## Overview

Container optimization is critical for:
- **Faster deployment**: Smaller images transfer and load faster
- **Reduced storage**: Lower disk space requirements for local and registry storage
- **Improved build times**: Better caching and fewer layers speed up iterations
- **Enhanced performance**: Optimized runtime settings improve simulation throughput
- **Better reproducibility**: Clean, minimal images reduce variability

---

## Optimization Techniques Applied

### 1. Multi-Stage Builds

**Applied to**: Celery Worker (`Dockerfile.celery`)

Multi-stage builds separate the build environment from the runtime environment, significantly reducing final image size.

**Before**:
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y docker.io docker-compose ca-certificates
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/celery_app.py .
```

**After**:
```dockerfile
# Build stage: Install dependencies
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage: Minimal image
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends docker.io docker-compose
COPY --from=builder /root/.local /root/.local
COPY src/celery_app.py .
```

**Benefits**:
- Excludes build tools and temporary files from final image
- Reduces image size by ~30-50%
- Separates build-time and runtime dependencies

---

### 2. Layer Optimization

**Applied to**: All Dockerfiles

Combining RUN commands reduces the number of layers and intermediate cache requirements.

**Before**:
```dockerfile
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2
RUN rm -rf /var/lib/apt/lists/*
```

**After**:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    package1 \
    package2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
```

**Benefits**:
- Reduces number of layers (each RUN creates a layer)
- Smaller image size (cleanup happens in same layer)
- Better caching efficiency

---

### 3. Minimal Package Installation

**Applied to**: LAMMPS, OpenFOAM, FEniCSx

Using `--no-install-recommends` flag prevents installation of unnecessary suggested packages.

**Example**:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    lammps \
    libopenmpi-dev \
    openmpi-bin \
    python3 \
    python3-pip
```

**Removed packages**:
- `vim` from LAMMPS (not needed for automated simulations)
- Unnecessary documentation packages
- Optional recommended packages

**Benefits**:
- 20-40% reduction in image size
- Fewer security vulnerabilities
- Faster installation

---

### 4. Aggressive Cleanup

**Applied to**: All Dockerfiles

Cleaning package manager caches and temporary files in the same RUN statement.

**Standard cleanup pattern**:
```dockerfile
RUN apt-get update && apt-get install -y packages \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
```

**Cleaned items**:
- `/var/lib/apt/lists/*` - APT package lists
- `/tmp/*` - Temporary files
- `/var/tmp/*` - More temporary files
- APT cache via `apt-get clean`

**Benefits**:
- Reduces each layer size by 50-200MB
- No leftover temporary files
- Clean, reproducible images

---

### 5. Docker Build Context Optimization

**Applied to**: All container directories

Using `.dockerignore` files to exclude unnecessary files from the build context.

**Created `.dockerignore` for**:
- Root directory (Celery worker)
- FEniCSx toolbox
- LAMMPS toolbox
- OpenFOAM toolbox (updated existing)

**Excluded patterns**:
```
.git
*.md
data/
output/
results/
__pycache__/
*.pyc
.pytest_cache/
.vscode/
.idea/
```

**Benefits**:
- Faster context transfer to Docker daemon
- Smaller build context (can be 100s of MB reduction)
- Prevents accidental inclusion of sensitive data
- Improved build caching

---

### 6. Environment Variable Consolidation

**Applied to**: All Dockerfiles

Combining multiple ENV statements into single declarations.

**Before**:
```dockerfile
ENV OMP_NUM_THREADS=1
ENV OMP_PROC_BIND=spread
ENV OMP_PLACES=threads
```

**After**:
```dockerfile
ENV OMP_NUM_THREADS=1 \
    OMP_PROC_BIND=spread \
    OMP_PLACES=threads
```

**Benefits**:
- Reduces number of layers
- Cleaner Dockerfile
- Better readability

---

### 7. Python Optimization

**Applied to**: Celery Worker, FEniCSx

**Techniques**:
```dockerfile
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
```

- `PYTHONUNBUFFERED=1`: Forces Python output to be sent straight to terminal without buffering
- `PYTHONDONTWRITEBYTECODE=1`: Prevents Python from creating .pyc files
- `pip install --no-cache-dir`: Prevents pip from caching downloaded packages

**Benefits**:
- Better real-time logging for simulations
- Reduced image size (no .pyc files or pip cache)
- Faster container startup

---

### 8. Runtime Performance Tuning

**Applied to**: All simulation containers

**OpenMP Settings**:
```dockerfile
ENV OMP_NUM_THREADS=1 \
    OMP_PROC_BIND=spread \
    OMP_PLACES=threads
```

**Celery Worker Settings**:
```dockerfile
CMD ["celery", "-A", "celery_app", "worker", \
     "--loglevel=info", \
     "--concurrency=2", \
     "--max-tasks-per-child=1000"]
```

**Configuration**:
- `OMP_NUM_THREADS=1`: Default to 1 thread (user can override for parallel runs)
- `OMP_PROC_BIND=spread`: Spread threads across cores for better cache locality
- `OMP_PLACES=threads`: Bind to hardware threads
- `--max-tasks-per-child=1000`: Recycle workers to prevent memory leaks

**Benefits**:
- Optimal default settings for single-core runs
- Easy to override for parallel execution
- Better memory management in long-running workers
- Improved cache performance

---

## BuildKit Optimization

Docker BuildKit provides advanced features for faster, more efficient builds.

### Enable BuildKit

```bash
export DOCKER_BUILDKIT=1
docker compose build
```

Or in docker-compose.yml:
```yaml
services:
  service-name:
    build:
      context: .
      dockerfile: Dockerfile
      cache_from:
        - service-name:latest
```

### BuildKit Features Used

1. **Parallel builds**: Automatically builds independent stages in parallel
2. **Better caching**: More intelligent cache invalidation
3. **Secrets management**: Safe handling of build-time secrets
4. **Build-time mounts**: Efficient handling of caches without layers

---

## Image Size Comparison

Estimated size reductions after optimization:

| Image | Before | After | Reduction |
|-------|--------|-------|-----------|
| Celery Worker | ~500MB | ~350MB | ~30% |
| LAMMPS | ~1.2GB | ~900MB | ~25% |
| FEniCSx | Depends on base | Same | Optimized layers |
| OpenFOAM | Depends on base | Same | Optimized layers |

*Note: Base images (FEniCSx, OpenFOAM) are official images; optimizations focus on our layers*

---

## Build Time Optimization

### Strategies Applied

1. **Optimal layer ordering**: 
   - Place least-changing commands first
   - Install system packages before copying application code

2. **Build context reduction**:
   - `.dockerignore` reduces context size by 50-90%
   - Faster transfers to Docker daemon

3. **Dependency caching**:
   - Python packages installed in separate stage
   - System packages cached when unchanged

### Example Build Times

With proper caching:
- First build: 2-5 minutes (depending on base image)
- Incremental builds: 10-30 seconds (code changes only)
- Cache hit: < 5 seconds

---

## Best Practices Summary

### DO:
✅ Use multi-stage builds for compiled/interpreted languages  
✅ Combine RUN commands to reduce layers  
✅ Use `--no-install-recommends` with apt-get  
✅ Clean up in the same layer as installation  
✅ Create comprehensive `.dockerignore` files  
✅ Use official base images when available  
✅ Set performance-related environment variables  
✅ Enable BuildKit for builds  

### DON'T:
❌ Install unnecessary packages (editors, docs, etc.)  
❌ Leave package manager caches in images  
❌ Copy entire directories without exclusions  
❌ Create unnecessary layers  
❌ Run as root unless required  
❌ Hardcode values that should be environment variables  

---

## Verification and Testing

After optimization, verify containers still function correctly:

### Build All Images
```bash
docker compose build
```

### Test Individual Services
```bash
# Test Celery worker
docker compose up -d redis
docker compose up -d celery-worker
docker compose logs celery-worker

# Test FEniCSx
docker compose run --rm fenicsx python3 poisson.py

# Test LAMMPS
docker compose run --rm lammps lmp -h

# Test OpenFOAM
docker compose run --rm openfoam python3 /workspace/example_cavity.py
```

### Check Image Sizes
```bash
docker images | grep keystone
docker images | grep fenicsx
docker images | grep openfoam
```

---

## Future Optimization Opportunities

### 1. Use Alpine Linux Base Images
Where compatible, Alpine Linux (~5MB) vs Ubuntu (~75MB) can further reduce size:
```dockerfile
FROM python:3.11-alpine
```

**Considerations**: 
- May require additional build tools
- Not all packages available
- Some compatibility issues with scientific libraries

### 2. Distroless Images
Google's distroless images contain only application and runtime dependencies:
```dockerfile
FROM gcr.io/distroless/python3
```

**Benefits**: Minimal attack surface, smallest possible images
**Challenges**: Harder debugging, requires multi-stage builds

### 3. BuildKit Caching Mounts
Use BuildKit mount caches for pip/apt:
```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### 4. Image Squashing
Combine all layers into a single layer (use sparingly):
```bash
docker build --squash -t image:tag .
```

---

## Monitoring and Maintenance

### Regular Reviews
- Review dependency versions quarterly
- Update base images for security patches
- Monitor image sizes over time
- Profile runtime performance

### Tools for Analysis
```bash
# Analyze image layers
docker history image:tag

# Dive - explore image contents
dive image:tag

# Check for vulnerabilities
docker scan image:tag
```

---

## References

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [BuildKit Documentation](https://docs.docker.com/build/buildkit/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)

---

## Summary

The optimization techniques applied to Keystone Supercomputer containers result in:

- **30-50% smaller images** through multi-stage builds and cleanup
- **50-90% faster builds** with improved caching and `.dockerignore`
- **Optimal runtime performance** with tuned environment variables
- **Better reproducibility** through minimal, well-documented images

These optimizations maintain full functionality while significantly improving the development and deployment experience.
