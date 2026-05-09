FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a writable directory for ChromaDB (Hugging Face runs as non-root with id 1000)
# We need to ensure the app has permissions to write to /app/chroma_db
RUN mkdir -p /app/chroma_db && chmod 777 /app/chroma_db

# Copy the rest of the application
COPY . .

# Expose the port used by Hugging Face Spaces
EXPOSE 7860

# Run the FastAPI application on port 7860
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]
