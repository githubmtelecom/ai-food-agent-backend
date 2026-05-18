import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from worker import build_delivery_cart
from database import SessionLocal
import models
from sentence_transformers import SentenceTransformer

load_dotenv()

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.2, max_tokens=500)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

@tool
def dispatch_order_bot(device_id: str, restaurant_name: str, items: list) -> str:
    """Use this tool ONLY when the user explicitly confirms they want to place an order."""
    build_delivery_cart.delay(device_id, restaurant_name, items)
    return "Bot dispatched."

@tool
def search_local_menus(semantic_query: str) -> str:
    """Use this tool to search the menu database using semantic meaning, vibes, or cravings."""
    print(f"[SYSTEM] Performing Semantic Search for: '{semantic_query}'")
    query_vector = embedding_model.encode(semantic_query).tolist()
    
    db = SessionLocal()
    try:
        results = db.query(models.MenuItem).order_by(
            models.MenuItem.embedding.l2_distance(query_vector)
        ).limit(3).all()
        
        if not results:
            return "No items found."
            
        menu_text = f"TOP MATCHES FOR '{semantic_query}':\n"
        for item in results:
            menu_text += f"- {item.name} from {item.restaurant.name} (${item.price}): {item.description}\n"
        return menu_text
    finally:
        db.close()

tools = [dispatch_order_bot, search_local_menus]
llm_with_tools = llm.bind_tools(tools)

def process_user_intent(user_input: str, persona: dict, device_id: str) -> str:
    persona_str = "\n".join([f"- {k}: {v}" for k, v in persona.items()]) if persona else "No preferences."
    
    system_prompt = f"""You are a highly capable AI Personal Butler specializing in food delivery.
CRITICAL USER PERSONA:
{persona_str}
RULES:
1. When a user asks for food or expresses a craving, use `search_local_menus` passing their craving as the `semantic_query`.
2. Filter the results against the User Persona.
3. If they CONFIRM an order, use `dispatch_order_bot`. (Device ID: {device_id})
"""
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_input)]
    ai_msg = llm_with_tools.invoke(messages)
    
    if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            if tool_call["name"] == "dispatch_order_bot":
                dispatch_order_bot.invoke(tool_call["args"])
                return "I've dispatched the bot to build your cart!"
            
            elif tool_call["name"] == "search_local_menus":
                # We fetch the menu data
                menu_data = search_local_menus.invoke(tool_call["args"])
                
                # We append Claude's original tool call
                messages.append(ai_msg)
                
                # THE FIX: We append the exact ToolMessage block matching the ID
                messages.append(ToolMessage(content=menu_data, tool_call_id=tool_call["id"]))
                
                return llm_with_tools.invoke(messages).content
                
    return ai_msg.content
