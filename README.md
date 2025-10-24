# Three-Tier Conversational AI System

This project implements a three-tier Conversational AI system with:
- Frontend: HTML/JS with Tailwind CSS
- Backend 01: Python/Flask for STT/TTS
- Backend 02: LLM Server

## Project Structure

```
.
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── js/
│   │   │   └── main.js
│   │   └── css/
│   │       └── style.css
│   └── package.json
├── backend01-stt-tts/
│   ├── src/
│   │   └── app.py
│   └── requirements.txt
└── backend02-llm/
    ├── src/
    │   └── server.py
    └── requirements.txt
```

## Components

### Frontend
- Built with HTML, JavaScript, and Tailwind CSS
- Features a triple-panel interface with Speech-to-Speech (STS), Text-to-Text (TTT), and Latency Metrics widgets
- Real-time audio visualization with waveform displays
- Chat history with export functionality
- Responsive design for different screen sizes

### Backend 01 (STT/TTS)
- Python/Flask application
- Handles Speech-to-Text and Text-to-Speech conversion
- API endpoints for text chat, voice chat, voice stop command, and chat history
- Runs on port 5001

### Backend 02 (LLM)
- Python/Flask application
- Handles language model processing
- Runs on port 5002
- Supports Ollama for local LLM inference
- Simulation mode for development
- Health check and monitoring endpoints

## Frontend Features

### Speech-to-Speech (STS) Widget
- Real-time audio visualization with waveform displays for user and assistant
- Start/Stop recording functionality with visual feedback
- Status indicators for microphone and API connection
- Stop AI voice playback button

### Text-to-Text (TTT) Widget
- Chat interface with message history
- Text input with send button
- Clear chat history functionality
- Export chat history in TXT or JSON format
- Typing indicators for AI responses

### Latency Metrics Widget
- Static panel positioned like other widgets (no auto-hide/show)
- Real-time display of all latency metrics:
  - Total Response Time
  - ASR/STT Time
  - sLLM Inference
  - sTTS Start Delay
- Visual progress bars for quick assessment
- Intelligent time formatting (ms, s, m)

### UI/UX Features
- Dark/light mode support
- Responsive design for mobile and desktop
- Smooth animations and transitions
- Intuitive icon-based interface
- Real-time audio level visualization

## Backend 01 API Endpoints

### Text Chat
- **POST** `/chat/text`
  - Accepts JSON with `user_id` and `message`
  - Returns processed response

### Voice Chat
- **POST** `/chat/voice`
  - Accepts audio file upload with `user_id`
  - Returns transcription and AI response

### Stop AI Voice
- **POST** `/voice/stop`
  - Accepts JSON with `user_id`
  - Stops current AI voice output

### Chat History
- **GET** `/chat/history/<user_id>`
  - Retrieves chat history for specified user
- **DELETE** `/chat/history/<user_id>`
  - Clears chat history for specified user

## Testing the Project

For detailed testing instructions, please refer to the [TESTING_GUIDE.md](file:///Users/kyawswartun/Dev/proj/sts.ai/TESTING_GUIDE.md) file which provides comprehensive steps to test each component of the system.

### Quick Test Commands

You can quickly test the system with these curl commands:

**Test Text Chat:**
```bash
curl -X POST http://localhost:5001/chat/text \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_user", "message": "Hello, how are you?"}'
```

**Test LLM Backend:**
```bash
curl -X POST http://localhost:5002/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, how are you?"}'
```

**Test Chat History:**
```bash
curl http://localhost:5001/chat/history/test_user
```

## Next Steps

- Implement actual STT/TTS functionality in backend01
- Complete Ollama integration in backend02
- Add authentication and security features
- Implement real-time audio processing
- Add more API providers and services