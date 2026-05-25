# Release Notes - v0.7.0 (Autonomous Fleet Discovery)

## Overview
Upgraded the AI ingestion pipeline from a manual trigger to an autonomous Fan-Out architecture. The backend can now scan a geofenced radius to automatically discover targets and deploy parallel web-scraping workers.

## Features Deployed
* **Google Places Radar:** Integrated the `googlemaps` SDK to query local areas for `restaurant` types based on GPS coordinates.
* **Fan-Out Architecture:** Created a `discover_local_restaurants` master task that dynamically spawns asynchronous `ingest_local_menus` Celery tasks for every valid website discovered.
* **Safety Limiter:** Implemented a strict slice (`[:3]`) to prevent local machine resource exhaustion during parallel headless browser execution.
