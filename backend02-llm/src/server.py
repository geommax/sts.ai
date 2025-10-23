from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return jsonify({"message": "LLM Backend Server Running"})

@app.route('/generate', methods=['POST'])
def generate_response():
    start_time = time.time()
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
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
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Simple response for testing
        response_text = "I got it"
        
        return jsonify({
            "response": response_text,
            "latency": {
                "processing": round(processing_time * 1000)  # Convert to milliseconds
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)