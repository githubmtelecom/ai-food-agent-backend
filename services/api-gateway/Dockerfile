# Use Microsoft's official pre-built image (Chromium is already installed!)
FROM mcr.microsoft.com/playwright/python:jammy

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install FastAPI, Celery, LangChain, etc.
RUN pip install --no-cache-dir -r requirements.txt

# Notice we completely DELETED the 'RUN playwright install' step!

# Copy the rest of our application code
COPY . .
