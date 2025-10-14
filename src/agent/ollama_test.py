from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3:8b",  # Or the model you pulled
    base_url="http://127.0.0.1:11434"
)

response = llm.invoke("What is computational fluid dynamics?")
print(response)
