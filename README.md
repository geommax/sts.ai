# Conversational AI System (STS-DeepBlue)

A three-tier Conversational AI system with Speech-to-Speech (STS) and Text-to-Text (TTT) capabilities, featuring real-time audio visualization, latency metrics, and responsive design.

## System Architecture

- **Frontend**: HTML/JS with Tailwind CSS - Triple-panel UI (STS, TTT, Latency Metrics)
- **Backend 01**: Python/Flask for Speech-to-Text (STT) and Text-to-Speech (TTS) on port 5001
- **Backend 02**: Python/Flask for Large Language Model (LLM) processing on port 5002

## Key Features

### Voice Chat (Speech-to-Speech)
- Real-time voice recording and playback
- Vosk-based Speech-to-Text transcription
- Piper TTS for natural voice synthesis
- Real-time waveform visualization during AI voice playback
- Stop AI voice button to cancel audio playback

### Text Chat (Text-to-Text)
- Traditional text-based chat interface
- LLM-powered responses
- Chat history export functionality (TXT/JSON)
- Stop generating button to cancel long-running requests

### UI/UX Features
- Responsive design with dark/light mode toggle
- Real-time latency metrics display (STT, LLM, TTS)
- Notification system with color-coded feedback
- Triple-panel dashboard layout (STS, TTT, Metrics)

## Prerequisites

- Python 3.8+
- Node.js and npm
- Ollama (for local LLM inference)
- Vosk (for speech recognition)
- Piper TTS (for text-to-speech)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sts.ai
```

2. Install backend dependencies:
```bash
# For Backend 01 (STT/TTS)
cd backend01-stt-tts
pip install -r requirements.txt

# For Backend 02 (LLM)
cd ../backend02-llm
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd ../frontend-web
npm install
```

4. Set up Ollama:
```bash
# Install Ollama from https://ollama.com/
# Pull the required model
ollama pull llama3.2:latest
```

5. Download Vosk model:
```bash
# Download the appropriate Vosk model from https://alphacephei.com/vosk/models
# Place it in the backend01-stt-tts/models/ directory
```

6. Set up Piper TTS:
```bash
# Download Piper TTS from https://github.com/rhasspy/piper
# Download voice models and place them in the appropriate directory
```

## Running the Application

### Start Backend Services

1. Start Backend 01 (STT/TTS):
```bash
cd backend01-stt-tts
python src/app.py
```

2. Start Backend 02 (LLM):
```bash
cd ../backend02-llm
python src/server.py
```

### Start Frontend

```bash
cd ../frontend-web
npm start
```

### Access the Application

Open your browser and navigate to `http://localhost:8000`

## API Endpoints

### Backend 01 (STT/TTS) - Port 5001
- `POST /voice/process` - Process voice input and generate TTS response
- `GET /tts/<filename>` - Serve generated TTS audio files
- `POST /voice/stop` - Stop current TTS playback
- `POST /text/chat` - Process text input and generate response

### Backend 02 (LLM) - Port 5002
- `POST /generate` - Generate LLM response
- `GET /chat/history` - Retrieve chat history

## Recent Improvements

### Voice Playback Enhancements
- Added real-time waveform visualization during AI voice playback
- Improved stop voice button functionality to properly cancel audio playback
- Text-to-text chat no longer triggers unnecessary TTS generation

### UI/UX Improvements
- Updated notification colors (default: gray, error: red, success: green, warning: yellow)
- Added "Stop Generating" button that toggles with the send button during LLM requests
- Enhanced chat messages to display latency in both milliseconds and seconds

### Voice Chat Features
- Voice chat now displays both the transcribed input text and AI response text
- Improved error handling and user feedback for all voice interactions

### Performance & Reliability
- Implemented request cancellation for long-running LLM queries
- Added proper cleanup of audio resources and visualization elements
- Enhanced error handling throughout the application