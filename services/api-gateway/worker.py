from celery import Celery
import time

# Initialize Celery and tell it to use our Docker Redis container as the message broker
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task(name="build_delivery_cart")
def build_delivery_cart(device_id: str, restaurant_name: str, items: list):
    """
    This is the background task. 
    In production, this will use Playwright to open an invisible browser.
    For our MVP test, we will simulate the delay of browser automation.
    """
    print(f"[WORKER] Starting cart build for {device_id} at {restaurant_name}...")
    
    # Simulate a bot navigating a website (takes 5 seconds)
    time.sleep(5) 
    
    # Simulate generating the deep link payload
    deep_link = f"ubereats://checkout?restaurant={restaurant_name.replace(' ', '').lower()}&status=ready"
    
    print(f"[WORKER] Cart built successfully! Deep link generated: {deep_link}")
    
    # Later, we will use WebSockets to push this link back to the mobile app
    return {"status": "success", "deep_link": deep_link}
