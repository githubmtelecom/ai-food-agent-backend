import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from worker import build_delivery_cart

# Load environment variables
load_dotenv()

# Initialize Claude 4.5 Haiku - The current generation fast model
llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0.2, 
    max_tokens=500
)

# 1. Define the Tool (The "Hands")
@tool
def dispatch_order_bot(device_id: str, restaurant_name: str, items: list) -> str:
    """Use this tool ONLY when the user explicitly confirms they want to place an order."""
    print(f"[AI AGENT] Autonomous decision made: Triggering bot for {restaurant_name}")
    # Trigger the Celery worker!
    build_delivery_cart.delay(device_id, restaurant_name, items)
    return "Bot dispatched."

# 2. Bind the tool to the LLM so Claude knows it exists
tools = [dispatch_order_bot]
llm_with_tools = llm.bind_tools(tools)

def process_user_intent(user_input: str, persona: dict, device_id: str) -> str:
    """Passes text to Claude, checks if Claude wanted to use a tool, and executes it manually."""
    
    persona_str = "\n".join([f"- {k}: {v}" for k, v in persona.items()]) if persona else "No specific preferences recorded."
    
    # 3. Build the System Prompt explicitly
    system_prompt = f"""You are a highly capable, protective, and conversational AI Personal Butler specializing in food delivery.

CRITICAL USER PERSONA:
{persona_str}

RULES:
1. Help the user decide what to eat. Keep responses concise for voice output.
2. Check dietary restrictions against the persona. Argue politely if they violate them.
3. If the user CONFIRMS what they want to order, you MUST use the `dispatch_order_bot` tool to place the order.
4. When using the tool, ensure you pass the exact device_id: {device_id}.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    
    # 4. Ask Claude what to do
    ai_msg = llm_with_tools.invoke(messages)
    
    # 5. Intercept the response: Did Claude decide to use a tool?
    if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
        print(f"[SYSTEM] Intercepted tool call from Claude: {ai_msg.tool_calls}")
        for tool_call in ai_msg.tool_calls:
            if tool_call["name"] == "dispatch_order_bot":
                # Extract the exact arguments Claude generated and trigger our Python function
                args = tool_call["args"]
                dispatch_order_bot.invoke(args)
                
        return "I've dispatched the bot to get that order added to your cart right away!"
        
    # 6. If no tool was used, just return Claude's conversational text
    return ai_msg.content
