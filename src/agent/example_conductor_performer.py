"""
Example: Using the Conductor-Performer Graph for Simulation Workflows
====================================================================

This script demonstrates various use cases of the LangGraph Conductor-Performer
pattern for orchestrating multi-agent simulation workflows.

Examples:
1. Single-tool structural analysis
2. Multi-physics coupled simulation
3. Parameter sweep workflow
4. Error recovery with refinement
5. Custom workflow configuration
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from conductor_performer_graph import (
    ConductorPerformerGraph,
    EXAMPLE_WORKFLOWS
)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(result: dict):
    """Print workflow execution result in a readable format."""
    print(f"\n✅ Workflow Status: {result['status']}")
    print(f"🔄 Iterations: {result['iterations']}")
    
    if result.get('result'):
        final_result = result['result']
        print(f"\n📊 Results:")
        print(f"  - Workflow ID: {final_result.get('workflow_id', 'N/A')}")
        print(f"  - Status: {final_result.get('status', 'N/A')}")
        
        if 'performer_results' in final_result:
            print(f"  - Performers executed: {len(final_result['performer_results'])}")
            for task_id, task_result in final_result['performer_results'].items():
                print(f"    • {task_id}: {task_result.get('performer', 'unknown')} "
                      f"({task_result.get('status', 'unknown')})")
        
        if 'validation' in final_result:
            validation = final_result['validation']
            print(f"  - Validation: {'✅ Passed' if validation.get('validation_passed') else '❌ Failed'}")
    
    print(f"\n💬 Message Log:")
    for i, msg in enumerate(result.get('messages', []), 1):
        print(f"  {i}. {msg}")


def example_1_structural_analysis():
    """Example 1: Single-tool structural analysis."""
    print_section("Example 1: Structural Analysis with FEniCSx")
    
    print("\n📖 Scenario:")
    print("Run finite element structural analysis on a steel beam")
    print("using the FEniCSx simulation tool.")
    
    # Initialize graph
    graph = ConductorPerformerGraph()
    
    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = graph.execute_workflow(
        user_request="Run structural finite element analysis for steel beam under load with mesh size 64"
    )
    
    # Display results
    print_result(result)
    
    # Explain what happened
    print("\n📝 What happened:")
    print("1. Conductor analyzed the request and identified FEniCSx task")
    print("2. Conductor delegated the task to FEniCSx Performer")
    print("3. FEniCSx Performer executed the finite element simulation")
    print("4. Validator checked the results for completeness")
    print("5. Conductor aggregated the results and returned final output")


def example_2_multiphysics():
    """Example 2: Multi-physics coupled simulation."""
    print_section("Example 2: Multi-Physics Coupled Simulation")
    
    print("\n📖 Scenario:")
    print("Run a coupled structural and fluid dynamics analysis")
    print("combining FEniCSx and OpenFOAM simulations.")
    
    # Initialize graph
    graph = ConductorPerformerGraph()
    
    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = graph.execute_workflow(
        user_request="Perform coupled structural and fluid dynamics analysis"
    )
    
    # Display results
    print_result(result)
    
    # Explain what happened
    print("\n📝 What happened:")
    print("1. Conductor created a sequential execution plan")
    print("2. FEniCSx Performer executed structural analysis")
    print("3. Results were passed to OpenFOAM Performer for fluid dynamics")
    print("4. Validator ensured coupling consistency")
    print("5. Conductor aggregated multi-physics results")


def example_3_molecular_dynamics():
    """Example 3: Molecular dynamics parameter sweep."""
    print_section("Example 3: Molecular Dynamics Parameter Sweep")
    
    print("\n📖 Scenario:")
    print("Run LAMMPS molecular dynamics simulation with")
    print("parameter sweep across multiple configurations.")
    
    # Initialize graph
    graph = ConductorPerformerGraph()
    
    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = graph.execute_workflow(
        user_request="Run molecular dynamics simulation with parameter sweep"
    )
    
    # Display results
    print_result(result)
    
    # Explain what happened
    print("\n📝 What happened:")
    print("1. Conductor identified parameter sweep pattern")
    print("2. LAMMPS Performer executed multiple configurations")
    print("3. Validator checked all runs completed successfully")
    print("4. Conductor aggregated statistical analysis results")


def example_4_error_recovery():
    """Example 4: Error recovery with refinement."""
    print_section("Example 4: Error Recovery with Mesh Refinement")
    
    print("\n📖 Scenario:")
    print("Run CFD simulation with automatic mesh refinement")
    print("if convergence issues are detected.")
    
    # Initialize graph
    graph = ConductorPerformerGraph()
    
    # Execute workflow with higher max iterations
    print("\n🚀 Executing workflow...")
    result = graph.execute_workflow(
        user_request="Run CFD fluid analysis with automatic mesh refinement if needed",
        max_iterations=5
    )
    
    # Display results
    print_result(result)
    
    # Explain what happened
    print("\n📝 What happened:")
    print("1. Conductor delegated to OpenFOAM Performer")
    print("2. Simulation may detect convergence issues")
    print("3. Validator provides refinement feedback")
    print("4. Conductor triggers mesh refinement iteration if needed")
    print("5. Workflow continues until success or max iterations")


def example_5_graph_visualization():
    """Example 5: Visualize the workflow graph structure."""
    print_section("Example 5: Workflow Graph Visualization")
    
    print("\n📖 Scenario:")
    print("Display the structure of the Conductor-Performer workflow graph")
    print("showing all nodes, edges, and decision points.")
    
    # Initialize graph
    graph = ConductorPerformerGraph()
    
    # Get visualization
    print("\n🌐 Graph Structure:")
    print(graph.get_graph_visualization())


def example_6_all_example_workflows():
    """Example 6: Display all predefined example workflows."""
    print_section("Example 6: Predefined Example Workflows")
    
    print("\n📖 Available Example Workflows:")
    
    for workflow_name, workflow_config in EXAMPLE_WORKFLOWS.items():
        print(f"\n{'─' * 70}")
        print(f"🔹 {workflow_name.replace('_', ' ').title()}")
        print(f"{'─' * 70}")
        print(f"Description: {workflow_config['description']}")
        print(f"\nRequest: \"{workflow_config['request']}\"")
        print(f"\nExpected Performers: {', '.join(workflow_config['expected_performers'])}")
        print(f"\nExecution Steps:")
        for i, step in enumerate(workflow_config['steps'], 1):
            print(f"  {i}. {step}")


def example_7_custom_configuration():
    """Example 7: Custom workflow configuration."""
    print_section("Example 7: Custom Workflow Configuration")
    
    print("\n📖 Scenario:")
    print("Execute a workflow with custom maximum iterations")
    print("and monitor the refinement process.")
    
    # Initialize graph
    graph = ConductorPerformerGraph()
    
    # Custom configuration
    custom_request = "Run complex simulation requiring multiple refinement iterations"
    max_iterations = 3
    
    print(f"\n⚙️  Configuration:")
    print(f"  - Request: {custom_request}")
    print(f"  - Max Iterations: {max_iterations}")
    
    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = graph.execute_workflow(
        user_request=custom_request,
        max_iterations=max_iterations
    )
    
    # Display results
    print_result(result)
    
    # Show iteration details
    print(f"\n🔄 Iteration Details:")
    if result['iterations'] > 0:
        print(f"  - Workflow required {result['iterations']} refinement iteration(s)")
        print(f"  - Maximum allowed: {max_iterations}")
    else:
        print(f"  - Workflow completed successfully on first attempt")


def interactive_demo():
    """Interactive demo allowing user to input custom requests."""
    print_section("Interactive Demo: Custom Workflow Execution")
    
    print("\n📖 This interactive demo allows you to input custom simulation requests")
    print("and see how the Conductor-Performer graph processes them.")
    
    # Initialize graph
    graph = ConductorPerformerGraph()
    
    print("\n💡 Example requests you can try:")
    print("  - 'Run structural analysis on aluminum component'")
    print("  - 'Perform molecular dynamics simulation'")
    print("  - 'Execute CFD analysis for turbulent flow'")
    print("  - 'Run coupled structural and fluid simulation'")
    
    while True:
        print("\n" + "─" * 70)
        user_input = input("\n🎯 Enter your simulation request (or 'quit' to exit): ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Exiting interactive demo. Goodbye!")
            break
        
        if not user_input:
            print("❌ Please enter a valid request.")
            continue
        
        # Execute workflow
        print(f"\n🚀 Executing workflow for: \"{user_input}\"")
        result = graph.execute_workflow(user_request=user_input)
        
        # Display results
        print_result(result)
        
        # Ask if user wants to continue
        continue_input = input("\n❓ Try another request? (yes/no): ").strip().lower()
        if continue_input not in ['yes', 'y', '']:
            print("\n👋 Exiting interactive demo. Goodbye!")
            break


def main():
    """Main function to run all examples."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  Conductor-Performer Graph - Example Demonstrations".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    
    print("\n📚 This script demonstrates the LangGraph Conductor-Performer pattern")
    print("for orchestrating multi-agent simulation workflows.")
    
    # Show menu
    print("\n📋 Available Examples:")
    print("  1. Structural Analysis (Single Tool)")
    print("  2. Multi-Physics Coupled Simulation")
    print("  3. Molecular Dynamics Parameter Sweep")
    print("  4. Error Recovery with Refinement")
    print("  5. Workflow Graph Visualization")
    print("  6. View All Example Workflows")
    print("  7. Custom Workflow Configuration")
    print("  8. Interactive Demo (Custom Requests)")
    print("  9. Run All Examples")
    print("  0. Exit")
    
    while True:
        print("\n" + "─" * 70)
        choice = input("\n🎯 Select an example (0-9): ").strip()
        
        if choice == '1':
            example_1_structural_analysis()
        elif choice == '2':
            example_2_multiphysics()
        elif choice == '3':
            example_3_molecular_dynamics()
        elif choice == '4':
            example_4_error_recovery()
        elif choice == '5':
            example_5_graph_visualization()
        elif choice == '6':
            example_6_all_example_workflows()
        elif choice == '7':
            example_7_custom_configuration()
        elif choice == '8':
            interactive_demo()
        elif choice == '9':
            print("\n🚀 Running all examples...")
            example_1_structural_analysis()
            example_2_multiphysics()
            example_3_molecular_dynamics()
            example_4_error_recovery()
            example_5_graph_visualization()
            example_6_all_example_workflows()
            example_7_custom_configuration()
            print("\n✅ All examples completed!")
        elif choice == '0':
            print("\n👋 Exiting. Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 0-9.")
        
        # Ask if user wants to continue
        if choice != '0':
            continue_input = input("\n❓ Run another example? (yes/no): ").strip().lower()
            if continue_input not in ['yes', 'y', '']:
                print("\n👋 Exiting. Goodbye!")
                break


if __name__ == "__main__":
    main()
