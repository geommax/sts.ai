from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from datetime import datetime
import time
import requests
import json
import logging
import sys
import subprocess

# Import Vosk components at the top level
from vosk import Model, KaldiRecognizer
import wave

# Set up logging with configurable level
def setup_logging(debug_level=0):
    """Set up logging with configurable verbosity level"""
    # Convert debug level to logging level
    if debug_level >= 2:
        log_level = logging.DEBUG
    elif debug_level == 1:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# Get debug level from environment variable or default to 0
DEBUG_LEVEL = int(os.getenv('DEBUG_LEVEL', '0'))
logger = setup_logging(DEBUG_LEVEL)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory storage for chat history (in production, use a database)
chat_history = {}

# Piper TTS configuration
PIPER_AVAILABLE = False
PIPER_MODEL_PATH = os.path.expanduser("/app/piper_models/en_US-lessac-medium.onnx")
PIPER_MODEL_CONFIG = os.path.expanduser("/app/piper_models/en_US-lessac-medium.onnx.json")

# Check if Piper is available
try:
    subprocess.run(["piper", "--help"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(PIPER_MODEL_PATH) and os.path.exists(PIPER_MODEL_CONFIG):
        PIPER_AVAILABLE = True
        logger.info("Piper TTS initialized successfully")
    else:
        logger.warning("Piper TTS installed but model files not found")
except (subprocess.CalledProcessError, FileNotFoundError):
    logger.warning("Piper TTS not available")

# Initialize Vosk model
VOSK_MODEL_PATH = None
try:
    VOSK_MODEL_PATH = Model(lang="en-us")
    logger.info("Vosk model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Vosk model: {e}")
    VOSK_MODEL_PATH = None

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
        
        # Convert LLM response to speech using Piper TTS for text chat as well
        tts_file_path = None
        tts_time = 0
        if PIPER_AVAILABLE:
            tts_start_time = time.time()
            tts_file_path = text_to_speech(response_text, user_id)
            tts_time = time.time() - tts_start_time
        
        response_data = {
            "status": "success",
            "response": response_text,
            "timestamp": datetime.now().isoformat(),
            "latency": {
                "processing": llm_latency,
                "tts": round(tts_time * 1000) if tts_time > 0 else 0
            }
        }
        
        # Include TTS file path if available
        if tts_file_path and os.path.exists(tts_file_path):
            response_data["tts_file"] = f"/tts/{os.path.basename(tts_file_path)}"
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat/voice', methods=['POST'])
def handle_voice_chat():
    """Handle voice chat audio POST"""
    logger.info("[API CALL] POST /chat/voice - Processing voice chat")
    start_time = time.time()
    
    try:
        # Check if audio file is present in request
        if 'audio' not in request.files:
            logger.warning("[VALIDATION] No audio file provided in voice chat request")
            return jsonify({"error": "No audio file provided"}), 400
            
        audio_file = request.files['audio']
        user_id = request.form.get('user_id', 'anonymous')
        
        if audio_file.filename == '':
            logger.warning("[VALIDATION] No audio file selected in voice chat request")
            return jsonify({"error": "No audio file selected"}), 400
            
        logger.debug(f"[WORKFLOW] Voice chat - User ID: {user_id}, Audio filename: {audio_file.filename}")
            
        # Save the audio file temporarily
        temp_audio_path = f"/tmp/temp_audio_{user_id}.webm"
        audio_file.save(temp_audio_path)
        logger.debug(f"[WORKFLOW] Audio file saved to {temp_audio_path}")
        
        # Process audio file with Vosk STT
        if VOSK_MODEL_PATH:
            logger.debug("[WORKFLOW] Processing audio with Vosk STT")
            transcribed_text = transcribe_with_vosk(temp_audio_path)
        else:
            # Fallback to simulation if Vosk model is not available
            logger.debug("[WORKFLOW] Vosk not available, using simulation")
            time.sleep(0.3)  # Simulate 300ms STT processing
            transcribed_text = "This is a placeholder transcription of your voice message"
            # Clean up temp file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
        
        stt_end_time = time.time()
        stt_time = stt_end_time - start_time
        logger.debug(f"[WORKFLOW] STT completed - Time: {stt_time*1000:.2f}ms, Transcription: {transcribed_text[:50]}...")
        
        # Store in chat history
        store_chat_message(user_id, "user_voice", transcribed_text)
        
        # Forward transcribed text to LLM backend (backend02-llm)
        llm_latency = 0
        try:
            logger.debug("[WORKFLOW] Forwarding transcription to LLM backend")
            llm_response = requests.post('http://localhost:5002/generate', 
                                       json={'prompt': transcribed_text}, 
                                       timeout=30)
            
            if llm_response.status_code == 200:
                llm_data = llm_response.json()
                response_text = llm_data.get('response', '')
                # Extract latency information from LLM response
                if 'latency' in llm_data and 'processing' in llm_data['latency']:
                    llm_latency = llm_data['latency']['processing']
                logger.debug(f"[WORKFLOW] LLM response received - Latency: {llm_latency}ms")
            else:
                # If LLM backend returns an error, we still want to show a response
                response_text = "Error: Unable to get response from LLM backend"
                logger.warning(f"[WORKFLOW] LLM backend returned error status: {llm_response.status_code}")
        except Exception as e:
            logger.error(f"[WORKFLOW] Error calling LLM backend: {e}")
            # If there's a network error, we still want to show a response
            response_text = "Error: Unable to connect to LLM backend"
        
        store_chat_message(user_id, "ai", response_text)
        
        # Convert LLM response to speech using Piper TTS
        tts_file_path = None
        if PIPER_AVAILABLE:
            logger.debug("[WORKFLOW] Converting response to speech with Piper TTS")
            tts_file_path = text_to_speech(response_text, user_id)
            tts_time = time.time() - stt_end_time
            logger.debug(f"[WORKFLOW] TTS completed - Time: {tts_time*1000:.2f}ms")
        else:
            # Simulate TTS processing time
            time.sleep(0.2)  # Simulate 200ms TTS processing
            tts_time = 0.2
            logger.debug("[WORKFLOW] Piper TTS not available, using simulation")
        
        total_time = time.time() - start_time
        logger.info(f"[API CALL] Completed /chat/voice - Total time: {total_time*1000:.2f}ms")
        
        response_data = {
            "status": "success",
            "transcription": transcribed_text,
            "response": response_text,
            "timestamp": datetime.now().isoformat(),
            "latency": {
                "stt": round(stt_time * 1000),  # Convert to milliseconds
                "llm": llm_latency,
                "tts": round(tts_time * 1000) if tts_time > 0 else 200  # Convert to milliseconds
            }
        }
        
        # Include TTS file path if available
        if tts_file_path and os.path.exists(tts_file_path):
            response_data["tts_file"] = f"/tts/{os.path.basename(tts_file_path)}"
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"[ERROR] Exception in /chat/voice: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/tts/<filename>')
def serve_tts_file(filename):
    """Serve TTS audio files"""
    logger.info(f"[API CALL] GET /tts/{filename} - Serving TTS file")
    try:
        from flask import send_file, make_response
        file_path = f"/tmp/{filename}"
        if os.path.exists(file_path):
            logger.debug(f"[WORKFLOW] Serving TTS file: {file_path}")
            response = make_response(send_file(file_path))
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Content-Type'] = 'audio/wav'
            return response
        else:
            logger.warning(f"[WORKFLOW] TTS file not found: {file_path}")
            return jsonify({"error": "TTS file not found"}), 404
    except Exception as e:
        logger.error(f"[ERROR] Exception in /tts/{filename}: {e}")
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

def transcribe_with_vosk(audio_path):
    """Transcribe audio file using Vosk STT"""
    wav_path = None
    try:
        # Convert webm to wav using ffmpeg
        wav_path = audio_path.replace('.webm', '.wav')
        subprocess.run([
            'ffmpeg', '-y', '-i', audio_path, '-acodec', 'pcm_s16le', 
            '-ac', '1', '-ar', '16000', wav_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Open the wave file
        wf = wave.open(wav_path, "rb")
        
        # Check if wave file is valid
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            raise ValueError("Audio file must be WAV format mono PCM.")
        
        # Initialize Vosk recognizer with pre-loaded model
        rec = KaldiRecognizer(VOSK_MODEL_PATH, wf.getframerate())
        
        # Process audio
        results = []
        chunk_size = 4000
        while True:
            data = wf.readframes(chunk_size)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                results.append(result.get("text", ""))
        
        # Get final result
        final_result = json.loads(rec.FinalResult())
        results.append(final_result.get("text", ""))
        
        # Combine all results
        transcription = " ".join(results).strip()
        
        # Clean up temporary files
        cleanup_files(audio_path, wav_path)
        
        return transcription if transcription else "Could not transcribe audio"
        
    except subprocess.CalledProcessError as e:
        # Clean up temporary files
        cleanup_files(audio_path, wav_path)
        raise Exception(f"Failed to convert audio file: {str(e)}")
    except Exception as e:
        # Clean up temporary files
        cleanup_files(audio_path, wav_path)
        raise e

def text_to_speech(text, user_id):
    """Convert text to speech using Piper TTS"""
    if not PIPER_AVAILABLE:
        return None
    
    try:
        # Create output file path
        tts_file_path = f"/tmp/tts_output_{user_id}_{int(time.time())}.wav"
        logger.debug(f"[WORKFLOW] Generating TTS output: {tts_file_path}")
        
        # Run Piper TTS command
        cmd = [
            "piper",
            "--model", PIPER_MODEL_PATH,
            "--output_file", tts_file_path
        ]
        
        # Execute Piper with text input
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(input=text.encode())
        
        if process.returncode != 0:
            logger.error(f"[ERROR] Piper TTS failed: {stderr.decode()}")
            if os.path.exists(tts_file_path):
                os.remove(tts_file_path)
            return None
            
        logger.debug(f"[WORKFLOW] TTS file generated successfully: {tts_file_path}")
        
        # Clean up old TTS files (keep only the most recent 10)
        try:
            tts_files = [f for f in os.listdir("/tmp") if f.startswith("tts_output_") and f.endswith(".wav")]
            if len(tts_files) > 10:
                tts_files.sort(key=lambda x: os.path.getmtime(os.path.join("/tmp", x)))
                for old_file in tts_files[:-10]:  # Keep the 10 most recent files
                    old_file_path = os.path.join("/tmp", old_file)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                        logger.debug(f"[WORKFLOW] Cleaned up old TTS file: {old_file_path}")
        except Exception as e:
            logger.warning(f"[WORKFLOW] Failed to clean up old TTS files: {e}")
        
        return tts_file_path
        
    except Exception as e:
        logger.error(f"[ERROR] Exception in text_to_speech: {e}")
        return None

def cleanup_files(*file_paths):
    """Safely remove temporary files"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass  # Ignore errors during cleanup

if __name__ == '__main__':
    # Get debug level from command line argument
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug-level', type=int, default=DEBUG_LEVEL, help='Debug level (0=warnings only, 1=info, 2=debug)')
    args = parser.parse_args()
    
    # Reconfigure logging with command line debug level
    logger = setup_logging(args.debug_level)
    
    logger.info(f"Starting STT/TTS Backend Server with debug level {args.debug_level}")
    if VOSK_MODEL_PATH:
        logger.info("Using Vosk for speech recognition")
    else:
        logger.warning("Vosk not available, using simulation mode")
        
    if PIPER_AVAILABLE:
        logger.info("Using Piper for text-to-speech")
    else:
        logger.warning("Piper TTS not available, using simulation mode")
    
    app.run(host='0.0.0.0', port=5001, debug=True)