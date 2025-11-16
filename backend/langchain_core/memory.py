from langchain.memory import ConversationBufferMemory

def get_memory():
    """Returns a simple conversation memory buffer."""
    return ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
