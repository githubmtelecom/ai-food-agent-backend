from celery import Celery
import time
import os
from database import SessionLocal
import models
from sentence_transformers import SentenceTransformer

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

# Load the local, free embedding model (downloads automatically on first run)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

@celery_app.task(name="build_delivery_cart")
def build_delivery_cart(device_id: str, restaurant_name: str, items: list):
    time.sleep(5) 
    deep_link = f"ubereats://checkout?restaurant={restaurant_name.replace(' ', '').lower()}&status=ready"
    return {"status": "success", "deep_link": deep_link}

@celery_app.task(name="ingest_local_menus")
def ingest_local_menus(lat: float, lon: float):
    print(f"[WORKER] Initiating spatial menu scan around {lat}, {lon}...")
    time.sleep(3) 
    
    db = SessionLocal()
    try:
        rest = models.Restaurant(name="Luigi's Trattoria", location_lat=lat, location_lon=lon)
        db.add(rest)
        db.commit()
        db.refresh(rest)
        
        # Define the items
        desc1 = "Classic pasta with an angry, fiery tomato sauce. Very greasy and heavy."
        desc2 = "Toasted artisan bread with olive oil and garlic. Light and healthy."
        
        # Calculate the mathematical vectors
        emb1 = embedding_model.encode(desc1).tolist()
        emb2 = embedding_model.encode(desc2).tolist()
        
        item1 = models.MenuItem(
            restaurant_id=rest.id, name="Spicy Arrabbiata", description=desc1, price=18.50, 
            attributes={"spice_level": "extreme", "allergies": ["gluten"]}, embedding=emb1
        )
        item2 = models.MenuItem(
            restaurant_id=rest.id, name="Vegan Garlic Bread", description=desc2, price=8.00, 
            attributes={"diet": "vegan"}, embedding=emb2
        )
        
        db.add_all([item1, item2])
        db.commit()
        print(f"[WORKER] Menus embedded and indexed!")
    finally:
        db.close()
        
    return {"status": "success"}
