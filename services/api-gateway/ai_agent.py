import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from worker import build_delivery_cart
from database import SessionLocal
import models

load_dotenv()

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0.2, 
    max_tokens=500
)

@tool
def dispatch_order_bot(device_id: str, restaurant_name: str, items: list) -> str:
    """Use this tool ONLY when the user explicitly confirms they want to place an order."""
    build_delivery_cart.delay(device_id, restaurant_name, items)
    return "Bot dispatched."

@tool
def search_local_menus() -> str:
    """Use this tool to search the database for available restaurants and food items in the user's area."""
    db = SessionLocal()
    try:
        restaurants = db.query(models.Restaurant).all()
        if not restaurants:
            return "No restaurants have been scanned in your area yet. Ask the system to scan your location."
        
        menu_text = "AVAILABLE LOCAL RESTAURANTS & MENUS:\n"
        for rest in restaurants:
            menu_text += f"\n--- {rest.name} ---\n"
            for item in rest.items:
                menu_text += f"- {item.name} (${item.price}): {item.description} (Attributes: {item.attributes})\n"
        return menu_text
    finally:
        db.close()

# Give Claude access to BOTH tools now
tools = [dispatch_order_bot, search_local_menus]
llm_with_tools = llm.bind_tools(tools)

def process_user_intent(user_input: str, persona: dict, device_id: str) -> str:
    persona_str = "\n".join([f"- {k}: {v}" for k, v in persona.items()]) if persona else "No specific preferences recorded."
    
    system_prompt = f"""You are a highly capable AI Personal Butler specializing in food delivery.

CRITICAL USER PERSONA:
{persona_str}

RULES:
1. ALWAYS use the `search_local_menus` tool first to see what food is available before recommending anything.
2. Filter the menu results strictly against the User Persona (e.g., do not recommend spicy food to someone who hates spice).
3. If the user CONFIRMS an order, use the `dispatch_order_bot` tool. (Device ID: {device_id})
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    
    ai_msg = llm_with_tools.invoke(messages)
    
    if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
        print(f"[SYSTEM] Intercepted tool call from Claude: {ai_msg.tool_calls}")
        
        for tool_call in ai_msg.tool_calls:
            if tool_call["name"] == "dispatch_order_bot":
                dispatch_order_bot.invoke(tool_call["args"])
                return "I've dispatched the bot to build your cart!"
            
            elif tool_call["name"] == "search_local_menus":
                # Claude requested the menu! We fetch it and send it BACK to Claude to generate a natural response.
                menu_data = search_local_menus.invoke({})
                messages.append(ai_msg) # Append Claude's request
                messages.append(HumanMessage(content=f"Tool result: {menu_data}")) # Append our DB data
                final_response = llm_with_tools.invoke(messages) # Ask Claude to summarize it for the user
                return final_response.content
                
    return ai_msg.content
