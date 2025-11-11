# LLM Backend Service

This service provides LLM inference capabilities for the conversational AI system.

## Features

- Supports Ollama for local LLM inference
- RESTful API for text generation
- Simulation mode for development without Ollama
- Health check endpoint
- Performance monitoring and latency tracking

## Prerequisites

- Python 3.9+
- Ollama (for local LLM inference)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Service

### With Ollama (Recommended for Local Development)

1. Install Ollama from https://ollama.com/
2. Pull the Llama 3 8B model:
```bash
ollama pull llama3:8b
```
3. Start Ollama service (usually starts automatically after installation)
4. Run the backend with Ollama enabled:
```bash
USE_OLLAMA=true python src/server.py
```

### In Simulation Mode (Without Ollama)

Run the backend in simulation mode:
```bash
python src/server.py
```

## Environment Variables

- `USE_OLLAMA` - Set to "true" to enable Ollama integration (default: "false")
- `OLLAMA_MODEL` - Ollama model to use (default: "llama3:8b")
- `OLLAMA_HOST` - Ollama API host (default: "http://localhost:11434")

## API Endpoints

- `GET /` - Server status and configuration information
- `POST /generate` - Generate text response
- `GET /health` - Health check endpoint

### POST /generate

Request body:
```json
{
  "prompt": "Your prompt here",
  "max_tokens": 100
}
```

Response:
```json
{
  "response": "Generated response",
  "latency": {
    "processing": 1250
  }
}
```

## Testing

You can test the service with curl:

```bash
curl -X POST http://localhost:5002/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, how are you?"}'
```