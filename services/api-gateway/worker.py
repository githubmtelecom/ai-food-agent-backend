from celery import Celery
import time
import os
from database import SessionLocal
import models
from sentence_transformers import SentenceTransformer
from playwright.sync_api import sync_playwright
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field
import googlemaps

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

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
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=30000)
            raw_text = page.inner_text("body")
        except Exception as e:
            print(f"[WORKER] Scraping failed: {e}")
            browser.close()
            return {"status": "error", "message": str(e)}
        browser.close()

    print("[WORKER] Website scraped. Passing raw text to Claude for JSON extraction...")
    
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
    structured_llm = llm.with_structured_output(ScrapedMenu)
    
    prompt = f"Extract the restaurant name and menu items from this raw website text. Do your best to infer spice level and allergies from the descriptions.\n\nWebsite Text:\n{raw_text[:50000]}"
    
    extracted_data = structured_llm.invoke(prompt)
    print(f"[WORKER] Claude extracted {len(extracted_data.items)} items for {extracted_data.restaurant_name}!")

    db = SessionLocal()
    try:
        rest = models.Restaurant(name=extracted_data.restaurant_name, location_lat=lat, location_lon=lon)
        db.add(rest)
        db.commit()
        db.refresh(rest)
        
        db_items = []
        for item in extracted_data.items:
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

@celery_app.task(name="discover_local_restaurants")
def discover_local_restaurants(lat: float, lon: float, radius: int):
    if not GOOGLE_API_KEY:
        print("[COMMANDER] Error: GOOGLE_PLACES_API_KEY is missing.")
        return {"status": "error", "message": "Missing API Key"}

    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    print(f"[COMMANDER] Sweeping {radius}m radius around ({lat}, {lon}) via Google Places...")

    places_result = gmaps.places_nearby(location=(lat, lon), radius=radius, type='restaurant')
    places = places_result.get('results', [])
    
    print(f"[COMMANDER] Radar hit: Found {len(places)} restaurants. Filtering for websites...")

    dispatched = 0
    # SAFETY LIMITER: We slice the array to only process the first 3 results so your machine doesn't crash!
    for place in places[:3]:
        place_id = place.get('place_id')
        details = gmaps.place(place_id, fields=['name', 'website'])
        
        result = details.get('result', {})
        website = result.get('website')
        name = result.get('name')

        if website and "grubhub" not in website and "doordash" not in website:
            print(f"[COMMANDER] Dispatched scraper drone to: {name} ({website})")
            # FAN-OUT: Trigger the web scraper task asynchronously
            ingest_local_menus.delay(lat, lon, website)
            dispatched += 1

    return {"status": "success", "targets_acquired": len(places), "scrapers_dispatched": dispatched}
