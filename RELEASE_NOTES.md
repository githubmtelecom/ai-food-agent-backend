# Release Notes - v0.1.0 (Sprint 0 MVP)

## Overview
This is the foundational release of the AI Food Agent Backend. It establishes a cloud-agnostic, event-driven microservices architecture featuring an AI orchestrator capable of autonomous tool-calling and background task delegation.

## Features Deployed
* **API Gateway (`main.py`):** * Deployed FastAPI server with bi-directional WebSocket support.
  * Implemented REST endpoints for user registration and chat interface.
* **Data Layer (`models.py`, `database.py`):** * Integrated PostgreSQL via SQLAlchemy ORM.
  * Implemented stateful User Personas (JSON) for active/passive memory injection.
* **AI Orchestrator (`ai_agent.py`):** * Integrated Anthropic's Claude 4.5 Haiku model.
  * Implemented custom Agentic Tool Calling logic (bypassing unstable LangChain wrappers).
  * Enforced strictly formatted system prompts for protective, conversational persona management.
* **Handoff Engine (`worker.py`):** * Deployed asynchronous task queue using Celery and Redis.
  * Built non-blocking background workers to simulate headless browser cart generation (Playwright scaffolding).

## Infrastructure Setup
* Established local containerized environment via `docker-compose.yml` (Postgres, Redis).
* Initialized Terraform scaffolding for future declarative cloud deployments.
