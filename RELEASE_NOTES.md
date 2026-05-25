# Release Notes - v0.5.0 (Live Web Scraping & AI Data Extraction)

## Overview
Replaced the mocked ingestion logic with a live, autonomous web scraper. The background worker now physically navigates to target URLs, extracts raw website text, and leverages Claude's Structured Outputs to parse messy HTML into clean, strictly-typed JSON before embedding it into the Vector Database.

## Features Deployed
* **Headless Browsing (Playwright):** Integrated Microsoft Playwright to spin up headless Chromium instances inside the Docker network, bypassing basic static-scraping limitations.
* **LLM Structured Extraction:** Upgraded the data pipeline to use Claude 4.5 Haiku to process up to 50,000 characters of raw website text, dynamically inferring missing attributes like "spice level" and "allergies" based on menu item descriptions.
* **Dynamic API Endpoints:** Upgraded the `POST /restaurants/scan` endpoint to accept dynamic `url` payloads for targeted restaurant indexing.
* **DevOps & Containerization:** Pinned the API Gateway Dockerfile to `mcr.microsoft.com/playwright/python:v1.59.0-jammy` to ensure strict binary compatibility between the Python runtime and the headless browser executables.
