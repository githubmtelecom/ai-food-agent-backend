from celery import Celery
import time
import os
from database import SessionLocal
import models
from sentence_transformers import SentenceTransformer
from playwright.sync_api import sync_playwright
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

# 1. Setup Connections
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Define the exact JSON structure we want Claude to extract from the messy website
class ScrapedMenuItem(BaseModel):
    name: str = Field(description="Name of the dish")
    description: str = Field(description="Description of the dish. If none, summarize based on name.")
    price: float = Field(description="Price as a float. If none found, use 0.0")
    spice_level: str = Field(description="e.g., none, mild, medium, extreme")
    allergies: list[str] = Field(description="List of potential allergens based on description")

class ScrapedMenu(BaseModel):
    restaurant_name: str
    items: list[ScrapedMenuItem]

@celery_app.task(name="build_delivery_cart")
def build_delivery_cart(device_id: str, restaurant_name: str, items: list):
    time.sleep(5) 
    deep_link = f"ubereats://checkout?restaurant={restaurant_name.replace(' ', '').lower()}&status=ready"
    return {"status": "success", "deep_link": deep_link}

@celery_app.task(name="ingest_local_menus")
def ingest_local_menus(lat: float, lon: float, url: str):
    print(f"[WORKER] Launching headless browser to scrape: {url}")
    
    # 3. Physically scrape the website text using Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=30000)
            # Grab all the visible text on the page
            raw_text = page.inner_text("body")
        except Exception as e:
            print(f"[WORKER] Scraping failed: {e}")
            browser.close()
            return {"status": "error", "message": str(e)}
        browser.close()

    print("[WORKER] Website scraped. Passing raw text to Claude for JSON extraction...")
    
    # 4. Use Claude to parse the messy text into our strict JSON Schema
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
    structured_llm = llm.with_structured_output(ScrapedMenu)
    
    prompt = f"Extract the restaurant name and menu items from this raw website text. Do your best to infer spice level and allergies from the descriptions.\n\nWebsite Text:\n{raw_text[:50000]}"
    
    extracted_data = structured_llm.invoke(prompt)
    print(f"[WORKER] Claude extracted {len(extracted_data.items)} items for {extracted_data.restaurant_name}!")

    # 5. Save the real data to the Vector Database
    db = SessionLocal()
    try:
        rest = models.Restaurant(name=extracted_data.restaurant_name, location_lat=lat, location_lon=lon)
        db.add(rest)
        db.commit()
        db.refresh(rest)
        
        db_items = []
        for item in extracted_data.items:
            # Embed the real description!
            emb = embedding_model.encode(item.description).tolist()
            
            db_item = models.MenuItem(
                restaurant_id=rest.id, 
                name=item.name, 
                description=item.description, 
                price=item.price, 
                attributes={"spice_level": item.spice_level, "allergies": item.allergies}, 
                embedding=emb
            )
            db_items.append(db_item)
            
        db.add_all(db_items)
        db.commit()
        print(f"[WORKER] Live menu successfully embedded and indexed into pgvector!")
    finally:
        db.close()
        
    return {"status": "success", "restaurant": extracted_data.restaurant_name, "items_indexed": len(extracted_data.items)}
