from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
USE_OLLAMA = os.getenv("USE_OLLAMA", "False").lower() == "true"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def generate_with_ollama(prompt, max_tokens=100):
    """Generate text using Ollama API"""
    try:
        import requests
        
        # Ollama API endpoint
        url = f"{OLLAMA_HOST}/api/generate"
        
        # Request payload
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        # Make request to Ollama
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        return result.get("response", "No response generated")
        
    except ImportError:
        logger.error("Requests library not available for Ollama integration")
        return "Error: Requests library not available"
    except Exception as e:
        logger.error(f"Error generating with Ollama: {e}")
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return jsonify({
        "message": "LLM Backend Server Running",
        "use_ollama": USE_OLLAMA,
        "ollama_model": OLLAMA_MODEL if USE_OLLAMA else None
    })

@app.route('/generate', methods=['POST'])
def generate_response():
    start_time = time.time()
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        max_tokens = data.get('max_tokens', 100)
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        # Generate response using Ollama or simulation
        if USE_OLLAMA:
            response_text = generate_with_ollama(prompt, max_tokens)
        else:
            # Simulate more realistic LLM processing time based on prompt length
            # This simulates that longer prompts take more time to process
            base_delay = 0.3  # Base 300ms delay
            prompt_length_factor = min(len(prompt) * 0.005, 0.7)  # Up to 700ms extra for very long prompts
            processing_delay = base_delay + prompt_length_factor
            
            # Add some random variation to simulate real-world variance
            import random
            variation = random.uniform(-0.1, 0.1)  # +/- 100ms variation
            processing_delay = max(0.1, processing_delay + variation)  # Minimum 100ms
            
            time.sleep(processing_delay)
            
            # Simple response for testing
            response_text = "I got it"
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return jsonify({
            "response": response_text,
            "latency": {
                "processing": round(processing_time * 1000)  # Convert to milliseconds
            }
        })
    except Exception as e:
        logger.error(f"Error in generate_response: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    if USE_OLLAMA:
        try:
            import requests
            # Check if Ollama is running
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            ollama_status = "available" if response.status_code == 200 else "unavailable"
        except:
            ollama_status = "unavailable"
    else:
        ollama_status = "not enabled"
    
    return jsonify({
        "status": "healthy",
        "use_ollama": USE_OLLAMA,
        "ollama_status": ollama_status
    })

if __name__ == '__main__':
    logger.info("Starting LLM Backend Server")
    if USE_OLLAMA:
        logger.info(f"Using Ollama with model: {OLLAMA_MODEL}")
        logger.info(f"Ollama host: {OLLAMA_HOST}")
    else:
        logger.info("Running in simulation mode")
    
    app.run(host='0.0.0.0', port=5002, debug=True)