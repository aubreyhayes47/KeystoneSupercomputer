import click
from agent_state import AgentState
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

llm = ChatOllama(
    model="llama3:8b",  # Change to the model you have pulled in Ollama
    base_url="http://127.0.0.1:11434"
)

@click.group()
def cli():
    pass

@cli.command()
@click.argument('message')
def ask(message):
    """Send a message to the agent and receive a response."""
    state = AgentState(
        messages=[HumanMessage(content=message)],
        simulation_params={},
        artifact_paths=[]
    )
    click.echo(f"User: {message}")
    # Get LLM response
    response = llm.invoke(message)
    click.echo(f"Agent: {response.content}")

if __name__ == '__main__':
    cli()
