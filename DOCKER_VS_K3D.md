# Docker Compose vs k3d: When to Use Each

Both Docker Compose and k3d are available for orchestrating Keystone Supercomputer services. This guide helps you choose the right tool for your needs.

## Quick Comparison

| Aspect | Docker Compose | k3d Kubernetes |
|--------|---------------|----------------|
| **Setup Time** | ~1 minute | ~5 minutes |
| **Complexity** | Simple | Moderate |
| **Learning Curve** | Easy | Steeper |
| **Multi-Node** | No (single machine) | Yes (5 nodes) |
| **Scaling** | Manual restart needed | Dynamic, on-demand |
| **Load Balancing** | No | Yes, automatic |
| **Self-Healing** | No | Yes, automatic |
| **Resource Usage** | Low (~500MB RAM) | Higher (~2GB RAM) |
| **Production-Like** | No | Yes |
| **Best For** | Development, testing | Learning K8s, production testing |

## Use Docker Compose When:

✅ **Quick Development and Testing**
- You need to test a quick change
- You're developing locally
- You want immediate feedback

✅ **Simple Workflows**
- Running a single simulation
- Testing one service at a time
- No need for scaling

✅ **Resource Constrained**
- Limited RAM or CPU
- Running on older hardware
- Battery-powered laptop

✅ **Learning the Basics**
- New to containerization
- First time with the project
- Don't need Kubernetes features

### Docker Compose Commands

```bash
# Quick start
./docker-compose-quickstart.sh

# Run a simulation
docker compose run --rm fenicsx poisson.py

# Start services
docker compose up -d redis celery-worker

# View logs
docker compose logs -f celery-worker

# Stop everything
docker compose down
```

## Use k3d When:

✅ **Production-Like Environment**
- Testing deployment strategies
- Validating production configurations
- Need high availability

✅ **Multi-Node Scenarios**
- Testing distributed workloads
- Load balancing across nodes
- Simulating real cluster behavior

✅ **Advanced Orchestration**
- Automatic scaling needed
- Self-healing desired
- Complex service dependencies

✅ **Learning Kubernetes**
- Preparing for cloud deployment
- Learning K8s concepts
- Testing Helm charts

✅ **Large-Scale Simulations**
- Running many parallel simulations
- Need to scale workers dynamically
- Resource isolation important

### k3d Commands

```bash
# Initial setup
./k3d-setup.sh

# Run a simulation
./k3d-manage.sh run-simulation fenicsx poisson.py

# Scale workers
./k3d-manage.sh scale celery-worker 5

# View logs
./k3d-manage.sh logs celery-worker

# Stop cluster
./k3d-manage.sh stop
```

## Detailed Scenarios

### Scenario 1: Quick Single Simulation

**Recommendation: Docker Compose**

If you just need to run one simulation quickly:

```bash
# Docker Compose approach (faster)
docker compose build fenicsx
docker compose run --rm fenicsx poisson.py
# Result in ~30 seconds
```

vs

```bash
# k3d approach (more overhead)
./k3d-setup.sh           # If not already running
./k3d-manage.sh run-simulation fenicsx poisson.py
# Result in ~2 minutes (including setup)
```

### Scenario 2: Running Multiple Parallel Simulations

**Recommendation: k3d**

If you need to run 10+ simulations in parallel:

```bash
# k3d automatically distributes across nodes
for i in {1..20}; do
  ./k3d-manage.sh run-simulation fenicsx poisson.py &
done
# k3d handles scheduling, load balancing automatically
```

vs

```bash
# Docker Compose would need manual orchestration
# All run on single machine, no load balancing
```

### Scenario 3: Development with Frequent Changes

**Recommendation: Docker Compose**

If you're actively developing and testing changes:

```bash
# Quick iteration cycle with Docker Compose
vim src/sim-toolbox/fenicsx/poisson.py
docker compose run --rm fenicsx poisson.py
# Repeat...
```

### Scenario 4: Preparing for Cloud Deployment

**Recommendation: k3d**

If you'll eventually deploy to AWS/GCP/Azure:

```bash
# k3d provides production-like Kubernetes experience
./k3d-setup.sh
# Test with same kubectl commands you'll use in production
kubectl apply -f k8s/manifests/
```

### Scenario 5: Learning Kubernetes

**Recommendation: k3d**

If you want to learn Kubernetes:

```bash
# k3d is perfect for learning K8s locally
./k3d-setup.sh
kubectl get nodes
kubectl get pods -n keystone
# Practice with real Kubernetes
```

### Scenario 6: Limited Resources (4GB RAM)

**Recommendation: Docker Compose**

If you have limited system resources:

```bash
# Docker Compose uses minimal resources
docker compose up -d redis celery-worker
# Uses ~500MB RAM
```

vs

```bash
# k3d cluster uses more resources
./k3d-setup.sh
# Uses ~2GB RAM for cluster + pods
```

## Migration Path

You can use both! Start with Docker Compose and migrate to k3d as needed:

### Phase 1: Start with Docker Compose
```bash
# Learn the basics
./docker-compose-quickstart.sh
docker compose run --rm fenicsx poisson.py
```

### Phase 2: Move to k3d for Scaling
```bash
# When you need more power
./k3d-setup.sh
./k3d-manage.sh import-images  # Reuse Docker images!
```

### Phase 3: Use Both
```bash
# Docker Compose for development
docker compose run --rm fenicsx poisson.py

# k3d for production testing
./k3d-manage.sh run-simulation fenicsx poisson.py
```

## Feature Availability

| Feature | Docker Compose | k3d |
|---------|---------------|-----|
| Redis Message Broker | ✅ | ✅ |
| Celery Workers | ✅ | ✅ |
| FEniCSx Simulations | ✅ | ✅ |
| LAMMPS Simulations | ✅ | ✅ |
| OpenFOAM Simulations | ✅ | ✅ |
| Task Pipeline | ✅ | ✅ |
| Automatic Scaling | ❌ | ✅ |
| Load Balancing | ❌ | ✅ |
| Self-Healing | ❌ | ✅ |
| Multi-Node | ❌ | ✅ |
| High Availability | ❌ | ✅ |
| Rolling Updates | ❌ | ✅ |
| Resource Limits | ✅ | ✅ |
| Health Checks | ✅ | ✅ |

## Decision Tree

```
Do you need Kubernetes features (scaling, load balancing, HA)?
│
├─ Yes → Use k3d
│  └─ Do you have 4GB+ RAM available?
│     ├─ Yes → Perfect! Use k3d
│     └─ No → Consider Docker Compose or add RAM
│
└─ No → Are you just testing/developing?
   ├─ Yes → Use Docker Compose
   │  └─ Fast, simple, efficient
   │
   └─ No → Do you want to learn Kubernetes?
      ├─ Yes → Use k3d
      └─ No → Use Docker Compose
```

## Recommendation by User Type

### For Students/Learners
**Start with Docker Compose**, move to k3d when comfortable.

### For Developers
**Use Docker Compose** for daily work, k3d for integration testing.

### For DevOps Engineers
**Use k3d** to match production Kubernetes environments.

### For Researchers
**Use Docker Compose** for quick experiments, k3d for large-scale studies.

### For Production Deployments
**Use k3d** locally, then real Kubernetes (EKS/GKE/AKS) in cloud.

## Switching Between Them

You can easily switch:

```bash
# Stop Docker Compose
docker compose down

# Start k3d
./k3d-setup.sh

# Or vice versa
./k3d-manage.sh stop
docker compose up -d
```

## Conclusion

**Default Recommendation**: Start with Docker Compose for simplicity, use k3d when you need Kubernetes features.

- **Docker Compose**: Fast, simple, efficient for development
- **k3d**: Powerful, scalable, production-like for advanced use

Both tools work with the same container images and share the same data directory, so you can switch between them seamlessly!

## See Also

- [DOCKER_COMPOSE.md](DOCKER_COMPOSE.md) - Docker Compose documentation
- [K3D.md](K3D.md) - k3d documentation
- [K3D_EXAMPLES.md](K3D_EXAMPLES.md) - k3d usage examples
