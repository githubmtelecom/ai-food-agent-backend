# Release Notes - v0.4.0 (Conversational Memory & Agentic Loops)

## Overview
Upgraded the AI Agent from a linear script to a true Agentic Loop capable of short-term memory, data sanitization, and handling simultaneous tool calls autonomously.

## Features Deployed
* **Short-Term Memory:** Integrated Redis to cache conversational context with a 1-hour Time-To-Live (TTL), allowing the AI to remember pronouns (e.g., "it") and previous dietary requests.
* **Agentic Loop:** Implemented a multi-turn `while`/`for` execution loop. Claude can now trigger multiple tools simultaneously, review the data, and trigger follow-up tools before responding to the user.
* **Data Sanitization:** Built a robust data parsing pipeline to intercept and sanitize raw JSON/Lists from the LangChain tool outputs before they enter the Redis memory cache.
* **Infrastructure Fixes:** Resolved Docker networking issues to ensure the Celery background worker successfully routes data to the `pgvector` container.
