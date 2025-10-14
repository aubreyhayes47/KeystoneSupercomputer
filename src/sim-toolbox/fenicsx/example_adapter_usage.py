#!/usr/bin/env python3
"""
Example Usage: FEniCSx Adapter
================================

This script demonstrates how to use the FEniCSx adapter to run
containerized finite element simulations.
"""

import sys
from pathlib import Path

# Add adapter to path
adapter_dir = Path(__file__).parent
sys.path.insert(0, str(adapter_dir))

from fenicsx_adapter import FEniCSxAdapter


def example_basic_usage():
    """Example 1: Basic usage with default Poisson solver."""
    print("="*60)
    print("Example 1: Running default Poisson solver")
    print("="*60 + "\n")
    
    # Create adapter
    adapter = FEniCSxAdapter(
        image_name="fenicsx-toolbox",
        output_dir="./output/fenicsx_basic"
    )
    
    # Check if image is available
    if not adapter.check_image_available():
        print("Docker image not available. Please build it first:")
        print("  cd src/sim-toolbox/fenicsx")
        print("  docker build -t fenicsx-toolbox .")
        return
    
    # Run simulation with default script
    result = adapter.run_simulation()
    
    # Save results
    adapter.save_result_json()
    
    # Print results
    print("\nResults:")
    print(f"  Success: {result['success']}")
    print(f"  Output files: {result['output_files']}")
    if result['metadata']:
        print(f"  Solution min: {result['metadata'].get('min_value', 'N/A')}")
        print(f"  Solution max: {result['metadata'].get('max_value', 'N/A')}")


def example_custom_script():
    """Example 2: Running with a custom Python script."""
    print("\n" + "="*60)
    print("Example 2: Running with custom script content")
    print("="*60 + "\n")
    
    # Define a custom FEniCSx script
    custom_script = """
import numpy as np
from mpi4py import MPI
from dolfinx import mesh, fem, io
from dolfinx.fem.petsc import LinearProblem
import ufl

# Create a finer mesh
domain = mesh.create_unit_square(MPI.COMM_WORLD, 64, 64, mesh.CellType.triangle)
print(f"Custom mesh: {domain.topology.index_map(domain.topology.dim).size_global} cells")

# Define function space
V = fem.functionspace(domain, ("Lagrange", 1))

# Define boundary condition
facets = mesh.locate_entities_boundary(
    domain, domain.topology.dim - 1,
    lambda x: np.full(x.shape[1], True, dtype=bool)
)
dofs = fem.locate_dofs_topological(V, domain.topology.dim - 1, facets)
bc = fem.dirichletbc(np.float64(0.0), dofs, V)

# Variational problem
u = ufl.TrialFunction(V)
v = ufl.TestFunction(V)
f = fem.Constant(domain, np.float64(1.0))  # Unit source

a = ufl.dot(ufl.grad(u), ufl.grad(v)) * ufl.dx
L = f * v * ufl.dx

# Solve
problem = LinearProblem(a, L, bcs=[bc])
uh = problem.solve()

# Save
with io.XDMFFile(domain.comm, "/data/custom_solution.xdmf", "w") as xdmf:
    xdmf.write_mesh(domain)
    xdmf.write_function(uh)

print(f"Solution range: [{uh.x.array.min():.6f}, {uh.x.array.max():.6f}]")
"""
    
    # Create adapter
    adapter = FEniCSxAdapter(
        image_name="fenicsx-toolbox",
        output_dir="./output/fenicsx_custom"
    )
    
    # Run with custom script
    result = adapter.run_simulation(script_content=custom_script)
    
    if result['success']:
        print(f"\n✓ Custom script executed successfully!")
        print(f"✓ Output files: {result['output_files']}")


def example_external_script():
    """Example 3: Running with an external script file."""
    print("\n" + "="*60)
    print("Example 3: Running with external script file")
    print("="*60 + "\n")
    
    # Use the existing poisson.py from the toolbox directory
    script_path = adapter_dir / "poisson.py"
    
    if not script_path.exists():
        print(f"Script not found: {script_path}")
        return
    
    # Create adapter
    adapter = FEniCSxAdapter(
        image_name="fenicsx-toolbox",
        output_dir="./output/fenicsx_external"
    )
    
    # Run with external script
    result = adapter.run_simulation(script_path=str(script_path))
    
    if result['success']:
        print(f"\n✓ External script executed successfully!")
        print(f"✓ Mesh cells: {result['metadata'].get('mesh_cells', 'N/A')}")
        print(f"✓ DOF count: {result['metadata'].get('dof_count', 'N/A')}")


def main():
    """Run all examples."""
    print("FEniCSx Adapter Examples")
    print("=" * 60)
    
    # Example 1: Basic usage
    example_basic_usage()
    
    # Example 2: Custom script content
    # example_custom_script()
    
    # Example 3: External script
    # example_external_script()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
