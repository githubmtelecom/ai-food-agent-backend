import os
import json
import redis
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from worker import build_delivery_cart
from database import SessionLocal
import models
from sentence_transformers import SentenceTransformer

load_dotenv()

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.2, max_tokens=500)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

@tool
def dispatch_order_bot(device_id: str, restaurant_name: str, items: list) -> str:
    """Use this tool ONLY when the user explicitly confirms they want to place an order."""
    build_delivery_cart.delay(device_id, restaurant_name, items)
    return "Bot dispatched successfully."

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
    messages = [SystemMessage(content=system_prompt)]
    
    # 1. Fetch text history
    history_key = f"chat_history:{device_id}"
    history_data = redis_client.get(history_key)
    history = json.loads(history_data) if history_data else []
    
    for msg in history:
        # DATA SANITIZATION: Force any list/dict from cache into a clean string
        raw_content = msg.get("content", "")
        if isinstance(raw_content, list):
            clean_content = " ".join([str(c.get("text", c)) if isinstance(c, dict) else str(c) for c in raw_content])
        else:
            clean_content = str(raw_content)
            
        if msg["role"] == "user":
            messages.append(HumanMessage(content=clean_content))
        elif clean_content.strip(): 
            messages.append(AIMessage(content=clean_content))
            
    messages.append(HumanMessage(content=user_input))
    
    # 2. Robust Tool Execution Loop
    for _ in range(3):
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)
        
        if hasattr(ai_msg, "tool_calls") and len(ai_msg.tool_calls) > 0:
            for tool_call in ai_msg.tool_calls:
                try:
                    if tool_call["name"] == "dispatch_order_bot":
                        dispatch_order_bot.invoke(tool_call["args"])
                        result_content = "Bot dispatched successfully."
                    elif tool_call["name"] == "search_local_menus":
                        result_content = search_local_menus.invoke(tool_call["args"])
                    else:
                        result_content = f"Error: Tool {tool_call['name']} not supported."
                except Exception as e:
                    result_content = f"Error executing tool: {str(e)}"
                    
                messages.append(ToolMessage(
                    content=str(result_content), 
                    name=tool_call["name"], 
                    tool_call_id=tool_call["id"]
                ))
        else:
            break 
            
    # 3. Extract final string safely
    final_msg = messages[-1]
    raw_final = final_msg.content
    if isinstance(raw_final, list):
        final_text = " ".join([str(b.get("text", b)) if isinstance(b, dict) else str(b) for b in raw_final])
    else:
        final_text = str(raw_final)
        
    if not final_text.strip():
        final_text = "I have completed the task."
        
    # 4. Save clean string history to Redis
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": final_text})
    
    redis_client.setex(history_key, 3600, json.dumps(history[-10:]))
    
    return final_text
