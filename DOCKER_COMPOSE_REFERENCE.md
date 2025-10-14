# Docker Compose Quick Reference

Quick reference guide for common Docker Compose operations in Keystone Supercomputer.

## Essential Commands

### Service Management

```bash
# Start Redis service (default)
docker compose up -d redis

# Start all services including simulation tools
docker compose --profile simulation up -d

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v

# Restart a specific service
docker compose restart redis

# View running services
docker compose ps

# View logs
docker compose logs redis
docker compose logs -f redis  # Follow logs
```

### Building Images

```bash
# Build all images
docker compose build

# Build a specific image
docker compose build fenicsx

# Build with no cache (clean build)
docker compose build --no-cache

# Pull latest base images before building
docker compose build --pull
```

### Running Simulations

```bash
# FEniCSx - Run default Poisson solver
docker compose run --rm fenicsx poisson.py

# LAMMPS - Run Lennard-Jones simulation
docker compose run --rm lammps lmp -in /data/example.lammps

# OpenFOAM - Run cavity flow
docker compose run --rm openfoam python3 /workspace/example_cavity.py

# Interactive shell for debugging
docker compose run --rm fenicsx bash
docker compose run --rm lammps bash
docker compose run --rm openfoam bash
```

## Common Workflows

### Initial Setup

```bash
# 1. Run quick start script
./docker-compose-quickstart.sh

# 2. Build simulation images
docker compose build

# 3. Verify everything works
docker compose ps
docker compose exec redis redis-cli ping
```

### Running Integration Tests

```bash
# Start Redis (if needed)
docker compose up -d redis

# Run integration test
cd src/sim-toolbox
python3 integration_test.py --build

# View results
ls integration_test_output/
cat integration_test_report.md
```

### Development Workflow

```bash
# Start Redis for background queue
docker compose up -d redis

# Edit code in your favorite editor
vim src/sim-toolbox/fenicsx/poisson.py

# Test changes immediately
docker compose run --rm fenicsx python3 poisson.py

# Check outputs
ls data/fenicsx/output/

# Stop services when done
docker compose down
```

### Batch Simulations

```bash
# Prepare input files
mkdir -p data/fenicsx/input
for i in {1..5}; do
  echo "# Simulation $i" > data/fenicsx/input/sim_$i.py
done

# Run batch
for i in {1..5}; do
  docker compose run --rm fenicsx python3 /data/input/sim_$i.py
done

# Collect results
tar -czf results.tar.gz data/fenicsx/output/
```

## Maintenance

### Cleanup

```bash
# Remove stopped containers
docker compose rm

# Remove unused images
docker image prune

# Remove unused volumes (WARNING: deletes data)
docker volume prune

# Full cleanup (WARNING: deletes everything)
docker system prune -a
```

### Monitoring

```bash
# View resource usage
docker stats keystone-redis
docker stats --no-stream

# Check disk usage
docker system df

# View network details
docker network inspect keystone-network

# Check volume usage
docker volume ls
docker volume inspect keystone-redis-data
```

### Troubleshooting

```bash
# View logs for a service
docker compose logs redis
docker compose logs --tail=100 redis

# Check service health
docker compose ps
docker inspect keystone-redis --format='{{.State.Health.Status}}'

# Test Redis connection
docker compose exec redis redis-cli ping

# Rebuild a problematic service
docker compose build --no-cache fenicsx
docker compose up -d --force-recreate fenicsx

# Check configuration
docker compose config
docker compose config --services
```

## Data Management

### Volume Mounts

```bash
# List data directories
tree data/ -L 2

# Copy input files
cp my_script.py data/fenicsx/input/

# Archive outputs
tar -czf outputs_$(date +%Y%m%d).tar.gz data/*/output/

# Clean output directories
rm -rf data/*/output/*
```

### Backup and Restore

```bash
# Backup Redis data
docker compose exec redis redis-cli BGSAVE
docker cp keystone-redis:/data/dump.rdb ./backup/

# Backup all simulation data
tar -czf keystone_backup_$(date +%Y%m%d).tar.gz data/

# Restore Redis data
docker cp ./backup/dump.rdb keystone-redis:/data/
docker compose restart redis

# Restore simulation data
tar -xzf keystone_backup_20251014.tar.gz
```

## Environment Configuration

### Using .env File

```bash
# Create .env from template
cp .env.example .env

# Edit configuration
nano .env

# Restart services to apply changes
docker compose down
docker compose up -d
```

### Override Configuration

```bash
# Create override file (already in .gitignore)
cat > docker-compose.override.yml << 'EOF'
services:
  redis:
    ports:
      - "6380:6379"  # Use different host port
EOF

# Verify merged configuration
docker compose config

# Start with override
docker compose up -d
```

## Advanced Usage

### Resource Limits

```bash
# Run with memory limit
docker compose run --rm -m 4g fenicsx python3 poisson.py

# Run with CPU limit
docker compose run --rm --cpus="2.0" lammps lmp -in /data/input/example.lammps
```

### Custom Commands

```bash
# Run custom Python script
docker compose run --rm fenicsx python3 -c "import dolfinx; print(dolfinx.__version__)"

# Run shell command
docker compose run --rm lammps bash -c "lmp -h | head -20"

# Mount additional volume
docker compose run --rm -v $(pwd)/my_data:/data/custom fenicsx bash
```

### Network Debugging

```bash
# Test connectivity between containers
docker compose run --rm fenicsx ping redis
docker compose run --rm fenicsx curl http://redis:6379

# Check network configuration
docker network inspect keystone-network

# View container IPs
docker compose exec redis hostname -i
```

## Integration with Python Adapters

```bash
# Ensure adapters can use the services
cd src/sim-toolbox/fenicsx

# Run adapter with Docker Compose images
python3 fenicsx_adapter.py --output-dir ../../../data/fenicsx/output

# Test all adapters
cd ../
python3 validate_adapters.py
```

## Tips and Best Practices

1. **Always use `--rm` flag** when running one-off simulations to auto-remove containers
2. **Use profiles** to avoid starting simulation services unnecessarily
3. **Check logs** if a service fails to start: `docker compose logs <service>`
4. **Build regularly** to ensure you have the latest code: `docker compose build`
5. **Monitor resources** to prevent system overload: `docker stats`
6. **Backup data** before major changes: `tar -czf backup.tar.gz data/`
7. **Use .env file** for configuration instead of editing docker-compose.yml
8. **Keep images updated** by rebuilding periodically: `docker compose build --pull`

## Getting Help

```bash
# View Docker Compose help
docker compose --help
docker compose run --help

# View service-specific help
docker compose run --rm fenicsx python3 --help
docker compose run --rm lammps lmp -h
docker compose run --rm openfoam bash -c "source /opt/openfoam11/etc/bashrc && icoFoam -help"

# Read documentation
less DOCKER_COMPOSE.md
less src/sim-toolbox/ADAPTERS.md
```

## References

- [DOCKER_COMPOSE.md](DOCKER_COMPOSE.md) - Full documentation
- [Docker Compose CLI Reference](https://docs.docker.com/compose/reference/)
- [Simulation Adapters](src/sim-toolbox/ADAPTERS.md)
- [Integration Tests](src/sim-toolbox/INTEGRATION_TEST.md)

---

**Last Updated:** 2025-10-14  
**Maintainer:** Keystone Supercomputer Project
