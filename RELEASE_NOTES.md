# Release Notes - v0.2.0 (Spatial Menu Ingestion)

## Features Deployed
* **Data Layer:** Expanded PostgreSQL schema to include `Restaurant` and `MenuItem` models with JSON indexing for complex food attributes (spice level, allergens).
* **Ingestion Engine:** Implemented `POST /restaurants/scan` endpoint. Dispatches Celery tasks to asynchronously mock-scrape geolocation-based menus.
* **Retrieval-Augmented Generation (RAG):** Upgraded Claude Agent with the `search_local_menus` tool. The AI now natively reads the PostgreSQL database and filters real-world restaurant data against the user's dietary Persona.
