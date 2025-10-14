from typing import TypedDict, List, Dict, Annotated
from langchain_core.messages import AnyMessage
import operator

class AgentState(TypedDict):
    # The history of messages in the conversation
    messages: Annotated[List[AnyMessage], operator.add]
    # Parsed parameters for the current simulation task
    simulation_params: Dict
    # File paths to generated artifacts (e.g., mesh files, result plots)
    artifact_paths: List[str]
