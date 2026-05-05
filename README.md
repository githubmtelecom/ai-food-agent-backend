# AI Food Agent Backend
This repository contains the microservices and Infrastructure as Code (IaC) for the AI Food Agent mobile application.

## Architecture Principles
- **Cloud-Agnostic:** Infrastructure is deployed via Kubernetes and managed by Terraform.
- **Event-Driven:** Asynchronous tasks (like headless browser cart building) are handled via message queues.
- **Containerized:** All services are packaged as Docker containers.

## Tech Stack
- **API/Backend:** Python (FastAPI)
- **AI Framework:** LangChain
- **Workers:** Playwright (Headless Browser)
- **Infrastructure:** Terraform, Docker, Kubernetes
