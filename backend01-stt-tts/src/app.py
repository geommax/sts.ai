from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from datetime import datetime
import time
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory storage for chat history (in production, use a database)
chat_history = {}

@app.route('/')
def index():
    return jsonify({"message": "STT/TTS Backend Server Running", "version": "1.0"})

@app.route('/chat/text', methods=['POST'])
def handle_text_chat():
    """Handle text chat input from frontend"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'anonymous')
        message = data.get('message', '')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
            
        # Forward text to LLM backend (backend02-llm)
        llm_latency = 0
        try:
            llm_response = requests.post('http://localhost:5002/generate', 
                                       json={'prompt': message}, 
                                       timeout=30)
            
            if llm_response.status_code == 200:
                llm_data = llm_response.json()
                response_text = llm_data.get('response', '')
                # Extract latency information from LLM response
                if 'latency' in llm_data and 'processing' in llm_data['latency']:
                    llm_latency = llm_data['latency']['processing']
            else:
                # If LLM backend returns an error, we still want to show a response
                response_text = "Error: Unable to get response from LLM backend"
        except Exception as e:
            print(f"Error calling LLM backend: {e}")
            # If there's a network error, we still want to show a response
            response_text = "Error: Unable to connect to LLM backend"
        
        # Store in chat history
        store_chat_message(user_id, "user", message)
        store_chat_message(user_id, "ai", response_text)
        
        return jsonify({
            "status": "success",
            "response": response_text,
            "timestamp": datetime.now().isoformat(),
            "latency": {
                "processing": llm_latency
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat/voice', methods=['POST'])
def handle_voice_chat():
    """Handle voice chat audio POST"""
    start_time = time.time()
    
    try:
        # Check if audio file is present in request
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
            
        audio_file = request.files['audio']
        user_id = request.form.get('user_id', 'anonymous')
        
        if audio_file.filename == '':
            return jsonify({"error": "No audio file selected"}), 400
            
        # Process audio file (placeholder for actual STT implementation)
        # In a real implementation, you would:
        # 1. Save the audio file temporarily
        # 2. Process it with a speech recognition service
        # 3. Convert speech to text
        
        # Simulate STT processing time
        time.sleep(0.3)  # Simulate 300ms STT processing
        stt_end_time = time.time()
        stt_time = stt_end_time - start_time
        
        # Placeholder STT result
        transcribed_text = "This is a placeholder transcription of your voice message"
        
        # Store in chat history
        store_chat_message(user_id, "user_voice", transcribed_text)
        
        # Process the transcribed text (placeholder)
        response_text = f"I heard: {transcribed_text}"
        store_chat_message(user_id, "ai", response_text)
        
        # Simulate TTS processing time
        time.sleep(0.2)  # Simulate 200ms TTS processing
        tts_time = time.time() - stt_end_time
        
        return jsonify({
            "status": "success",
            "transcription": transcribed_text,
            "response": response_text,
            "timestamp": datetime.now().isoformat(),
            "latency": {
                "stt": round(stt_time * 1000),  # Convert to milliseconds
                "tts": round(tts_time * 1000)   # Convert to milliseconds
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/voice/stop', methods=['POST'])
def stop_ai_voice():
    """Handle AI voice stop command"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'anonymous')
        
        # Process voice stop command (placeholder for actual implementation)
        # In a real implementation, you would:
        # 1. Send a signal to stop current TTS playback
        # 2. Update any relevant state
        
        return jsonify({
            "status": "success",
            "message": "AI voice output stopped",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat/history/<user_id>', methods=['GET'])
def get_chat_history(user_id):
    """Retrieve chat history for a specific user"""
    try:
        history = chat_history.get(user_id, [])
        return jsonify({
            "status": "success",
            "user_id": user_id,
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat/history/<user_id>', methods=['DELETE'])
def clear_chat_history(user_id):
    """Clear chat history for a specific user"""
    try:
        if user_id in chat_history:
            del chat_history[user_id]
        return jsonify({
            "status": "success",
            "message": f"Chat history cleared for user {user_id}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def store_chat_message(user_id, message_type, content):
    """Helper function to store chat messages in memory"""
    if user_id not in chat_history:
        chat_history[user_id] = []
        
    message_entry = {
        "id": str(uuid.uuid4()),
        "type": message_type,  # user, ai, user_voice
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    
    chat_history[user_id].append(message_entry)
    
    # Keep only the last 100 messages per user to prevent memory issues
    if len(chat_history[user_id]) > 100:
        chat_history[user_id] = chat_history[user_id][-100:]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)