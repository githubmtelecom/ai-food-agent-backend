# Release Notes - v0.3.0 (Semantic RAG Search)

## Overview
Upgraded the database layer to utilize `pgvector`, enabling true semantic search and Retrieval-Augmented Generation (RAG) for the AI Food Agent. The AI can now recommend food based on cravings, vibes, and concepts rather than strict keyword matching.

## Features Deployed
* **Infrastructure:** Migrated local Docker environment to the `pgvector` PostgreSQL image.
* **Data Layer:** Added a 384-dimensional `Vector` column to the `MenuItem` SQLAlchemy model.
* **Ingestion Engine:** Integrated `sentence-transformers` (`all-MiniLM-L6-v2`) into the Celery worker to mathematically embed menu descriptions during background scraping.
* **AI Orchestrator:** Upgraded Claude's `search_local_menus` tool to perform L2 distance calculations directly in the database.
* **Bug Fixes:** Resolved Anthropic API strict `tool_result` formatting requirements via LangChain `ToolMessage` objects.
