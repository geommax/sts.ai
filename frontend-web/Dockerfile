FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy all frontend files
COPY . .

# Expose port 8000
EXPOSE 8000

# Start the frontend server
CMD ["python3", "-m", "http.server", "8000"]