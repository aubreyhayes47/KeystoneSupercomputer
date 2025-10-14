from agent_state import AgentState
from langchain_core.messages import HumanMessage

# Example: initializing agent state
initial_state = AgentState(
    messages=[HumanMessage(content="Hello, Keystone Supercomputer!")],
    simulation_params={},
    artifact_paths=[],
)

# Print initial state for debugging
print("Initial Agent State:", initial_state)
