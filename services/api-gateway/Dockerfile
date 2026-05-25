# Use Microsoft's official pre-built image pinned to the exact version Playwright wants!
FROM mcr.microsoft.com/playwright/python:v1.59.0-jammy

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our application code
COPY . .
