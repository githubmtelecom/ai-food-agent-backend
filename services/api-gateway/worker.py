from celery import Celery
import time
import os
from database import SessionLocal
import models

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(name="build_delivery_cart")
def build_delivery_cart(device_id: str, restaurant_name: str, items: list):
    print(f"[WORKER] Starting cart build for {device_id} at {restaurant_name}...")
    time.sleep(5) 
    deep_link = f"ubereats://checkout?restaurant={restaurant_name.replace(' ', '').lower()}&status=ready"
    print(f"[WORKER] Cart built successfully! Deep link generated: {deep_link}")
    return {"status": "success", "deep_link": deep_link}

@celery_app.task(name="ingest_local_menus")
def ingest_local_menus(lat: float, lon: float):
    """Background task to scrape local restaurants and index them into our DB."""
    print(f"[WORKER] Initiating spatial menu scan around {lat}, {lon}...")
    
    # Simulate the time it takes Playwright to scrape an entire restaurant menu
    time.sleep(3) 
    
    db = SessionLocal()
    try:
        # Create a mock restaurant
        rest = models.Restaurant(name="Luigi's Trattoria", location_lat=lat, location_lon=lon)
        db.add(rest)
        db.commit()
        db.refresh(rest)
        
        # Inject highly detailed, AI-indexed menu items
        item1 = models.MenuItem(
            restaurant_id=rest.id, 
            name="Spicy Arrabbiata", 
            description="Classic pasta with an angry, fiery tomato sauce.", 
            price=18.50, 
            attributes={"spice_level": "extreme", "allergies": ["gluten"], "size": "large"}
        )
        item2 = models.MenuItem(
            restaurant_id=rest.id, 
            name="Vegan Garlic Bread", 
            description="Toasted artisan bread with olive oil and garlic.", 
            price=8.00, 
            attributes={"spice_level": "none", "allergies": ["gluten"], "diet": "vegan"}
        )
        
        db.add_all([item1, item2])
        db.commit()
        print(f"[WORKER] Successfully indexed menu for {rest.name} into database!")
    finally:
        db.close()
        
    return {"status": "success", "scraped_restaurants": 1}
