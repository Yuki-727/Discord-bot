# Use a slim Python image to keep the size minimal
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies (if any) and clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final stage
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy the source code
COPY . .

# Create a directory for persistent data
RUN mkdir -p /app/data

# NOTE: Railway bans the 'VOLUME' keyword in Dockerfiles.
# You must manually attach a Volume to '/app/data' in the Railway Volume settings.

# Environment variables (to be provided at runtime)
# DISCORD_TOKEN
# AI_API_KEY (Groq)
# VOYAGE_API_KEY

# Run the bot
CMD ["python", "main.py"]
