import asyncio
import json
from app.api.chat import chat_support
from app.models.user import User

async def test_chat():
    # Mock user
    user = User(id=1, email="test@example.com", company_id=1)
    
    # Simulate the chat_support call
    # Note: chat_support is an async function returning a StreamingResponse
    # We need to manually call the event_generator inside it
    try:
        # We can't easily call the route because it depends on DB and Auth
        # But we can test the LLM and the logic separately
        from app.agent.nodes import llm, groq_llm
        from langchain_core.messages import HumanMessage, SystemMessage
        
        print("Testing Gemini astream...")
        async for chunk in llm.astream([HumanMessage(content="Hello")]):
            print(f"Gemini: {chunk.content}")
            
        print("\nTesting Groq astream...")
        async for chunk in groq_llm.astream([HumanMessage(content="Hello")]):
            print(f"Groq: {chunk.content}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
