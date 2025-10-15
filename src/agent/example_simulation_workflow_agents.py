#!/usr/bin/env python3
"""
Example: Simulation Workflow Agents
====================================

Demonstrates the six specialized agents for complete simulation workflow:
1. RequirementAnalysisAgent
2. PlanningAgent
3. SimulationAgent
4. VisualizationAgent
5. ValidationAgent
6. SummarizationAgent

Run: python3 example_simulation_workflow_agents.py
"""

import sys
from datetime import datetime

from simulation_workflow_agents import (
    WorkflowStage,
    AgentStatus,
    AgentInput,
    AgentOutput,
    RequirementAnalysisAgent,
    PlanningAgent,
    SimulationAgent,
    VisualizationAgent,
    ValidationAgent,
    SummarizationAgent
)


def print_header(title):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_stage(stage_name, status):
    """Print stage status."""
    status_icon = "✓" if status == AgentStatus.COMPLETED else "✗"
    print(f"{status_icon} {stage_name}: {status.value}")


def print_output_summary(output: AgentOutput):
    """Print summary of agent output."""
    print(f"\nStage: {output.stage.value}")
    print(f"Status: {output.status.value}")
    if output.errors:
        print(f"Errors: {output.errors}")
    if output.warnings:
        print(f"Warnings: {output.warnings}")
    print(f"Output keys: {list(output.data.keys())[:5]}")


def example_1_simple_structural_analysis():
    """Example 1: Simple structural analysis workflow."""
    print_header("Example 1: Simple Structural Analysis")
    
    user_request = "Run finite element analysis on a steel beam under 10kN load"
    print(f"\n📝 User Request: {user_request}\n")
    
    # Stage 1: Requirement Analysis
    print("Stage 1: Requirement Analysis")
    req_agent = RequirementAnalysisAgent()
    req_input = AgentInput(
        stage=WorkflowStage.REQUIREMENT_ANALYSIS,
        data={"user_request": user_request}
    )
    req_output = req_agent.process(req_input)
    print_stage("Requirement Analysis", req_output.status)
    print(f"  Simulation Type: {req_output.data['simulation_type']}")
    print(f"  Required Tools: {', '.join(req_output.data['required_tools'])}")
    print(f"  Estimated Resources: {req_output.data['resource_estimate']}")
    
    # Stage 2: Planning
    print("\nStage 2: Planning")
    plan_agent = PlanningAgent()
    plan_input = AgentInput(
        stage=WorkflowStage.PLANNING,
        data={},
        previous_stage_output=req_output.data
    )
    plan_output = plan_agent.process(plan_input)
    print_stage("Planning", plan_output.status)
    print(f"  Plan ID: {plan_output.data['execution_plan']['plan_id']}")
    print(f"  Tasks: {len(plan_output.data['execution_plan']['tasks'])}")
    print(f"  Estimated Duration: {plan_output.data['schedule']['estimated_duration_minutes']} min")
    
    # Stage 3: Simulation
    print("\nStage 3: Simulation")
    sim_agent = SimulationAgent()
    sim_input = AgentInput(
        stage=WorkflowStage.SIMULATION,
        data={},
        previous_stage_output=plan_output.data
    )
    sim_output = sim_agent.process(sim_input)
    print_stage("Simulation", sim_output.status)
    summary = sim_output.data['execution_summary']
    print(f"  Total Tasks: {summary['total_tasks']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")
    
    # Stage 4: Visualization
    print("\nStage 4: Visualization")
    viz_agent = VisualizationAgent()
    viz_input = AgentInput(
        stage=WorkflowStage.VISUALIZATION,
        data={},
        previous_stage_output=sim_output.data
    )
    viz_output = viz_agent.process(viz_input)
    print_stage("Visualization", viz_output.status)
    print(f"  Visualizations Generated: {len(viz_output.data['visualizations'])}")
    
    # Stage 5: Validation
    print("\nStage 5: Validation")
    val_agent = ValidationAgent()
    val_input = AgentInput(
        stage=WorkflowStage.VALIDATION,
        data={},
        previous_stage_output=sim_output.data,
        context={"requirements": req_output.data}
    )
    val_output = val_agent.process(val_input)
    print_stage("Validation", val_output.status)
    print(f"  Validation Status: {val_output.data['validation_status']}")
    print(f"  Quality Score: {val_output.data['quality_score']:.2f}")
    
    # Stage 6: Summarization
    print("\nStage 6: Summarization")
    sum_agent = SummarizationAgent()
    sum_input = AgentInput(
        stage=WorkflowStage.SUMMARIZATION,
        data={
            "requirement_analysis": req_output,
            "planning": plan_output,
            "simulation": sim_output,
            "visualization": viz_output,
            "validation": val_output
        }
    )
    sum_output = sum_agent.process(sum_input)
    print_stage("Summarization", sum_output.status)
    
    # Print Executive Summary
    exec_summary = sum_output.data['executive_summary']
    print(f"\n{'='*70}")
    print(f"Executive Summary")
    print(f"{'='*70}")
    print(f"Title: {exec_summary['title']}")
    print(f"Status: {exec_summary['status']}")
    print(f"Simulation Type: {exec_summary['simulation_type']}")
    print(f"\nKey Findings:")
    for finding in exec_summary['key_findings']:
        print(f"  • {finding}")
    
    print(f"\n✓ Workflow Complete!")


def example_2_multiphysics_simulation():
    """Example 2: Multiphysics simulation with multiple tools."""
    print_header("Example 2: Multiphysics Simulation")
    
    user_request = "Run coupled structural and fluid analysis for wing design"
    print(f"\n📝 User Request: {user_request}\n")
    
    # Run through workflow
    req_agent = RequirementAnalysisAgent()
    req_output = req_agent.process(AgentInput(
        stage=WorkflowStage.REQUIREMENT_ANALYSIS,
        data={"user_request": user_request}
    ))
    
    print(f"✓ Requirements analyzed")
    print(f"  Type: {req_output.data['simulation_type']}")
    print(f"  Tools: {', '.join(req_output.data['required_tools'])}")
    
    plan_agent = PlanningAgent()
    plan_output = plan_agent.process(AgentInput(
        stage=WorkflowStage.PLANNING,
        data={},
        previous_stage_output=req_output.data
    ))
    
    print(f"✓ Plan created")
    print(f"  Tasks: {len(plan_output.data['execution_plan']['tasks'])}")
    
    sim_agent = SimulationAgent()
    sim_output = sim_agent.process(AgentInput(
        stage=WorkflowStage.SIMULATION,
        data={},
        previous_stage_output=plan_output.data
    ))
    
    print(f"✓ Simulation complete")
    print(f"  Results: {len(sim_output.data['results'])} task results")
    
    viz_agent = VisualizationAgent()
    viz_output = viz_agent.process(AgentInput(
        stage=WorkflowStage.VISUALIZATION,
        data={},
        previous_stage_output=sim_output.data
    ))
    
    print(f"✓ Visualizations generated")
    print(f"  Count: {len(viz_output.data['visualizations'])}")
    
    val_agent = ValidationAgent()
    val_output = val_agent.process(AgentInput(
        stage=WorkflowStage.VALIDATION,
        data={},
        previous_stage_output=sim_output.data,
        context={"requirements": req_output.data}
    ))
    
    print(f"✓ Validation complete")
    print(f"  Status: {val_output.data['validation_status']}")
    
    sum_agent = SummarizationAgent()
    sum_output = sum_agent.process(AgentInput(
        stage=WorkflowStage.SUMMARIZATION,
        data={
            "requirement_analysis": req_output,
            "planning": plan_output,
            "simulation": sim_output,
            "visualization": viz_output,
            "validation": val_output
        }
    ))
    
    print(f"✓ Summary generated")
    print(f"\n{'='*70}")
    print(f"Executive Summary: {sum_output.data['executive_summary']['title']}")
    print(f"Status: {sum_output.data['executive_summary']['status']}")
    print(f"{'='*70}")


def example_3_agent_details():
    """Example 3: Detailed agent information and capabilities."""
    print_header("Example 3: Agent Details and Capabilities")
    
    agents = [
        ("RequirementAnalysisAgent", RequirementAnalysisAgent()),
        ("PlanningAgent", PlanningAgent()),
        ("SimulationAgent", SimulationAgent()),
        ("VisualizationAgent", VisualizationAgent()),
        ("ValidationAgent", ValidationAgent()),
        ("SummarizationAgent", SummarizationAgent())
    ]
    
    print("\nAgent Specifications:")
    print("-" * 70)
    
    for name, agent in agents:
        print(f"\n{name}")
        print(f"  Stage: {agent.stage.value}")
        print(f"  Purpose: {agent.__class__.__doc__.split('Purpose:')[1].split('Responsibilities:')[0].strip() if 'Purpose:' in agent.__class__.__doc__ else 'N/A'}")


def example_4_error_handling():
    """Example 4: Demonstrate error handling and warnings."""
    print_header("Example 4: Error Handling and Warnings")
    
    # Empty request
    print("\n1. Empty user request:")
    req_agent = RequirementAnalysisAgent()
    req_output = req_agent.process(AgentInput(
        stage=WorkflowStage.REQUIREMENT_ANALYSIS,
        data={"user_request": ""}
    ))
    print(f"  Status: {req_output.status.value}")
    print(f"  Warnings: {len(req_output.warnings)}")
    
    # Validation with empty results
    print("\n2. Validation with no simulation results:")
    val_agent = ValidationAgent()
    val_output = val_agent.process(AgentInput(
        stage=WorkflowStage.VALIDATION,
        data={},
        previous_stage_output={"results": {}},
        context={"requirements": {}}
    ))
    print(f"  Status: {req_output.status.value}")
    print(f"  Validation Status: {val_output.data['validation_status']}")


def interactive_menu():
    """Interactive menu for running examples."""
    while True:
        print_header("Simulation Workflow Agents - Examples")
        print("\nAvailable Examples:")
        print("  1. Simple Structural Analysis (Full Workflow)")
        print("  2. Multiphysics Simulation")
        print("  3. Agent Details and Capabilities")
        print("  4. Error Handling Demonstration")
        print("  5. Run All Examples")
        print("  0. Exit")
        
        choice = input("\nSelect example (0-5): ").strip()
        
        if choice == "1":
            example_1_simple_structural_analysis()
        elif choice == "2":
            example_2_multiphysics_simulation()
        elif choice == "3":
            example_3_agent_details()
        elif choice == "4":
            example_4_error_handling()
        elif choice == "5":
            example_1_simple_structural_analysis()
            example_2_multiphysics_simulation()
            example_3_agent_details()
            example_4_error_handling()
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("\n⚠ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific example from command line
        example = sys.argv[1]
        if example == "1":
            example_1_simple_structural_analysis()
        elif example == "2":
            example_2_multiphysics_simulation()
        elif example == "3":
            example_3_agent_details()
        elif example == "4":
            example_4_error_handling()
        elif example == "all":
            example_1_simple_structural_analysis()
            example_2_multiphysics_simulation()
            example_3_agent_details()
            example_4_error_handling()
        else:
            print(f"Unknown example: {example}")
            print("Usage: python3 example_simulation_workflow_agents.py [1|2|3|4|all]")
    else:
        # Run interactive menu
        interactive_menu()
