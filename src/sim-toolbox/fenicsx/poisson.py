#!/usr/bin/env python3
"""
Minimal FEniCSx Example: Poisson Equation
==========================================

Solves the 2D Poisson equation:
    -∇²u = f  in Ω = [0,1] × [0,1]
    u = 0     on ∂Ω

with f = 10*exp(-((x-0.5)² + (y-0.5)²)/0.02)

This demonstrates basic FEniCSx finite element simulation capabilities.
Results are written to /data for standardized output.
"""

import numpy as np
from mpi4py import MPI
from dolfinx import mesh, fem, io
from dolfinx.fem.petsc import LinearProblem
import ufl

def main():
    print("=" * 60)
    print("FEniCSx Poisson Equation Solver")
    print("=" * 60)
    
    # Create mesh: unit square with 32x32 elements
    domain = mesh.create_unit_square(MPI.COMM_WORLD, 32, 32, mesh.CellType.triangle)
    print(f"Mesh created: {domain.topology.index_map(domain.topology.dim).size_global} cells")
    
    # Define function space (piecewise linear elements)
    V = fem.functionspace(domain, ("Lagrange", 1))
    print(f"Function space dimension: {V.dofmap.index_map.size_global}")
    
    # Define boundary condition: u = 0 on boundary
    facets = mesh.locate_entities_boundary(
        domain, 
        domain.topology.dim - 1,
        lambda x: np.full(x.shape[1], True, dtype=bool)
    )
    dofs = fem.locate_dofs_topological(V, domain.topology.dim - 1, facets)
    bc = fem.dirichletbc(np.float64(0.0), dofs, V)
    
    # Define variational problem
    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)
    x = ufl.SpatialCoordinate(domain)
    
    # Source term: Gaussian centered at (0.5, 0.5)
    f = 10 * ufl.exp(-((x[0] - 0.5)**2 + (x[1] - 0.5)**2) / 0.02)
    
    # Bilinear and linear forms
    a = ufl.dot(ufl.grad(u), ufl.grad(v)) * ufl.dx
    L = f * v * ufl.dx
    
    print("\nSolving linear system...")
    # Solve the problem
    problem = LinearProblem(a, L, bcs=[bc], petsc_options={"ksp_type": "preonly", "pc_type": "lu"})
    uh = problem.solve()
    print("Solution computed successfully!")
    
    # Compute solution statistics
    u_values = uh.x.array
    print(f"\nSolution statistics:")
    print(f"  Min value: {u_values.min():.6f}")
    print(f"  Max value: {u_values.max():.6f}")
    print(f"  Mean value: {u_values.mean():.6f}")
    
    # Save solution to /data directory
    try:
        with io.XDMFFile(domain.comm, "/data/poisson_solution.xdmf", "w") as xdmf:
            xdmf.write_mesh(domain)
            xdmf.write_function(uh)
        print("\n✓ Solution saved to /data/poisson_solution.xdmf")
        print("  (Can be visualized with ParaView)")
    except Exception as e:
        print(f"\nNote: Could not write to /data (mount may not be configured): {e}")
        print("This is expected when running without a volume mount.")
    
    print("\n" + "=" * 60)
    print("Simulation completed successfully!")
    print("=" * 60)
    
    return uh

if __name__ == "__main__":
    main()
