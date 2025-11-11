#!/usr/bin/env python3
"""
Test script to verify Ollama integration
"""

import os
import requests
import json

def test_ollama_connection():
    """Test connection to Ollama service"""
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    try:
        # Test if Ollama is running
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama service is running")
            models = response.json()
            print(f"  Available models: {[model['name'] for model in models.get('models', [])]}")
            return True
        else:
            print("✗ Ollama service returned unexpected status code")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Ollama service. Make sure Ollama is running.")
        return False
    except Exception as e:
        print(f"✗ Error connecting to Ollama: {e}")
        return False

def test_model_generation():
    """Test text generation with Ollama"""
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3:8b")
    
    try:
        # Test generation
        payload = {
            "model": model,
            "prompt": "Hello, how are you?",
            "stream": False,
            "options": {
                "num_predict": 50,
                "temperature": 0.7
            }
        }
        
        response = requests.post(f"{ollama_host}/api/generate", json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✓ Text generation successful")
            print(f"  Response: {result.get('response', 'No response')}")
            return True
        else:
            print(f"✗ Text generation failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error during text generation: {e}")
        return False

def main():
    print("Testing Ollama Integration")
    print("=" * 30)
    
    # Test connection
    if test_ollama_connection():
        print()
        # Test generation
        test_model_generation()
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()