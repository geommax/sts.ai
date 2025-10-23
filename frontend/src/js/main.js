// Main JavaScript logic for the Conversational AI frontend

// DOM Elements - Speech to Speech
const speechToggleBtn = document.getElementById('speech-toggle-btn');
const stopAiVoiceBtn = document.getElementById('stop-ai-voice-btn');
const userWaveformSvg = document.getElementById('user-waveform-svg');
const assistantWaveformSvg = document.getElementById('assistant-waveform-svg');
const userAudioLevel = document.getElementById('user-audio-level');
const assistantAudioLevel = document.getElementById('assistant-audio-level');
const sttStatus = document.getElementById('stt-status');

// DOM Elements - Chat
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-btn');

// DOM Elements - Export
const exportBtn = document.getElementById('export-btn');
const exportModal = document.getElementById('export-modal');
const cancelExport = document.getElementById('cancel-export');
const confirmExport = document.getElementById('confirm-export');

// DOM Elements - Notification and Latency
const notificationBar = document.getElementById('notification-bar');
const totalLatency = document.getElementById('total-latency');
const sttLatency = document.getElementById('stt-latency');
const llmLatency = document.getElementById('llm-latency');
const ttsLatency = document.getElementById('tts-latency');
const totalLatencyBar = document.getElementById('total-latency-bar');
const sttLatencyBar = document.getElementById('stt-latency-bar');
const llmLatencyBar = document.getElementById('llm-latency-bar');
const ttsLatencyBar = document.getElementById('tts-latency-bar');

// Backend service URLs (hardcoded)
const STT_TTS_BACKEND_URL = 'http://localhost:5001';
const LLM_BACKEND_URL = 'http://localhost:5002';

// Voice recording variables
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let userId = 'user-' + Date.now(); // Simple user ID generation

// Audio visualization variables
let audioContext = null;
let userAnalyser = null;
let microphone = null;
let userAnimationFrameId = null;
let isSpeaking = false;

// Media stream variables
let mediaStream = null;

// Latency tracking variables
let interactionStartTime = 0;
let sttStartTime = 0;
let llmStartTime = 0;
let ttsStartTime = 0;

// Conversation history
let conversationHistory = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Add event listeners
    addEventListeners();
    
    // Show welcome message
    setTimeout(() => {
        addMessage("Hello! I'm your AI assistant. Type a message or click the mic to speak.");
    }, 500);
});

// Add all event listeners
function addEventListeners() {
    // Speech to Speech events
    speechToggleBtn.addEventListener('click', toggleRecording);
    stopAiVoiceBtn.addEventListener('click', stopAiVoice);
    
    // Chat events
    sendBtn.addEventListener('click', handleTextMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleTextMessage();
        }
    });
    clearBtn.addEventListener('click', clearChat);
    
    // Export events
    exportBtn.addEventListener('click', () => {
        exportModal.classList.remove('hidden');
    });
    cancelExport.addEventListener('click', () => {
        exportModal.classList.add('hidden');
    });
    confirmExport.addEventListener('click', exportChat);
    
    // Close modals when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === exportModal) {
            exportModal.classList.add('hidden');
        }
    });
}

// Format time in milliseconds to appropriate units (ms, s, or m)
function formatTime(ms) {
    if (ms < 1000) {
        return `${Math.round(ms)}ms`;
    } else if (ms < 60000) {
        return `${(ms / 1000).toFixed(2)}s`;
    } else {
        return `${(ms / 60000).toFixed(2)}m`;
    }
}

// Update progress bar width based on latency value
function updateProgressBar(barElement, value, maxValue = 5000) {
    // Cap the value at maxValue for visualization purposes
    const percentage = Math.min(100, (value / maxValue) * 100);
    barElement.style.width = `${percentage}%`;
}

// Show notification in the notification bar
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `mb-2 p-3 rounded-lg shadow-lg transform transition-all duration-300 ease-in-out opacity-0 translate-y-2`;
    
    // Set colors based on type
    switch (type) {
        case 'success':
            notification.classList.add('bg-green-100', 'text-green-800', 'dark:bg-green-900', 'dark:text-green-200');
            break;
        case 'error':
            notification.classList.add('bg-red-100', 'text-red-800', 'dark:bg-red-900', 'dark:text-red-200');
            break;
        case 'warning':
            notification.classList.add('bg-yellow-100', 'text-yellow-800', 'dark:bg-yellow-900', 'dark:text-yellow-200');
            break;
        default:
            notification.classList.add('bg-blue-100', 'text-blue-800', 'dark:bg-blue-900', 'dark:text-blue-200');
    }
    
    notification.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0 mr-2 mt-1">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'}"></i>
            </div>
            <div class="text-sm">${message}</div>
        </div>
    `;
    
    // Add to notification bar
    notificationBar.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('opacity-0', 'translate-y-2');
    }, 10);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Update latency display with formatted times and progress bars
function updateLatencyDisplay(totalTime = 0, sttTime = 0, llmTime = 0, ttsTime = 0) {
    totalLatency.textContent = totalTime > 0 ? formatTime(totalTime) : '0ms';
    sttLatency.textContent = sttTime > 0 ? formatTime(sttTime) : '0ms';
    llmLatency.textContent = llmTime > 0 ? formatTime(llmTime) : '0ms';
    ttsLatency.textContent = ttsTime > 0 ? formatTime(ttsTime) : '0ms';
    
    // Update progress bars
    updateProgressBar(totalLatencyBar, totalTime, 10000); // Max 10 seconds
    updateProgressBar(sttLatencyBar, sttTime, 2000);    // Max 2 seconds
    updateProgressBar(llmLatencyBar, llmTime, 5000);    // Max 5 seconds
    updateProgressBar(ttsLatencyBar, ttsTime, 2000);    // Max 2 seconds
}

// Add a message to the chat container
function addMessage(text, isUser = false, llmTime = 0, timestamp = null) {
    // Remove the placeholder message if it's the first message
    const placeholder = chatContainer.querySelector('.text-gray-500');
    if (placeholder) {
        placeholder.remove();
    }
    
    // Use current time if no timestamp provided
    const messageTimestamp = timestamp || new Date();
    
    // Format timestamp for display
    const formattedTime = messageTimestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    // Create message content with timing information
    let messageContent = `<div class="${isUser ? 'text-blue-700 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}">${text}</div>`;
    
    // Add timing information for user messages (send time) and assistant messages (response time and inference duration)
    if (isUser) {
        messageContent += `
        <div class="text-xs mt-1 ${isUser ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'}">
            Sent at ${formattedTime}
        </div>`;
    } else {
        // For assistant messages, include response time and inference duration
        messageContent += `
        <div class="text-xs mt-1 ${isUser ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'}">
            Responded at ${formattedTime}`;
        
        if (llmTime > 0) {
            messageContent += ` • Inference: ${formatTime(llmTime)}`;
        }
        messageContent += `
        </div>`;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-animation mb-3 p-3 rounded-lg ${isUser ? 'bg-blue-100 dark:bg-blue-900 ml-4' : 'bg-gray-100 dark:bg-gray-700 mr-4'}`;
    messageDiv.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0 mr-2 mt-1">
                <i class="fas ${isUser ? 'fa-user text-blue-600' : 'fa-robot text-green-600'}"></i>
            </div>
            <div>
                <div class="font-medium text-sm ${isUser ? 'text-blue-800 dark:text-blue-200' : 'text-gray-800 dark:text-gray-200'}">
                    ${isUser ? 'You' : 'Assistant'}
                </div>
                ${messageContent}
            </div>
        </div>
    `;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Add to conversation history
    conversationHistory.push({
        role: isUser ? 'user' : 'assistant',
        content: text,
        timestamp: messageTimestamp.toISOString(),
        llmTime: llmTime
    });
}

// Send text message to LLM backend
async function sendToLLM(text) {
    try {
        // Start LLM timing
        llmStartTime = Date.now();
        
        // Send to backend01-stt-tts instead of directly to backend02-llm
        console.log('Sending request to backend01-stt-tts');
        const response = await fetch(`${STT_TTS_BACKEND_URL}/chat/text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: text,
                user_id: userId
            })
        });
        
        console.log('Received response from backend01-stt-tts:', response);
        const data = await response.json();
        console.log('Parsed JSON data:', data);
        
        // Calculate LLM latency
        const llmTime = Date.now() - llmStartTime;
        
        let actualLlmTime = 0;
        // Update latency from backend if provided
        if (data.latency && data.latency.processing) {
            actualLlmTime = data.latency.processing;
            updateLatencyDisplay(0, 0, data.latency.processing, 0);
        } else {
            actualLlmTime = llmTime;
            updateLatencyDisplay(0, 0, llmTime, 0);
        }
        
        return { response: data.response, llmTime: actualLlmTime };
    } catch (error) {
        console.error('Error sending to LLM:', error);
        return { response: "Sorry, I encountered an error processing your request.", llmTime: 0 };
    }
}

// Handle text message submission
async function handleTextMessage() {
    // Start total interaction timing
    interactionStartTime = Date.now();
    
    const text = userInput.value.trim();
    if (!text) return;
    
    // Add user message to chat with timestamp
    addMessage(text, true, 0, new Date());
    userInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Get response from LLM
    const result = await sendToLLM(text);
    
    // Calculate total interaction time
    const totalTime = Date.now() - interactionStartTime;
    updateLatencyDisplay(totalTime, 0, result.llmTime, 0);
    
    // Remove typing indicator and add AI response with timing info
    removeTypingIndicator();
    addMessage(result.response, false, result.llmTime);
}

// Show typing indicator
function showTypingIndicator() {
    // Remove existing typing indicator if any
    removeTypingIndicator();
    
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'message-animation mb-3 p-3 rounded-lg bg-gray-100 dark:bg-gray-700 mr-4';
    typingDiv.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0 mr-2 mt-1">
                <i class="fas fa-robot text-green-600"></i>
            </div>
            <div>
                <div class="font-medium text-sm text-gray-800 dark:text-gray-200">Assistant</div>
                <div class="flex space-x-1">
                    <div class="typing-dot w-2 h-2 bg-gray-500 rounded-full"></div>
                    <div class="typing-dot w-2 h-2 bg-gray-500 rounded-full"></div>
                    <div class="typing-dot w-2 h-2 bg-gray-500 rounded-full"></div>
                </div>
            </div>
        </div>
    `;
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Clear chat history
function clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        chatContainer.innerHTML = '<div class="text-gray-500 dark:text-gray-400 text-center text-sm py-4">Messages will appear here</div>';
        conversationHistory = [];
    }
}

// Export chat history
function exportChat() {
    const format = document.querySelector('input[name="export-format"]:checked').value;
    let content, filename, mimeType;
    
    if (format === 'json') {
        content = JSON.stringify(conversationHistory, null, 2);
        filename = 'chat-history.json';
        mimeType = 'application/json';
    } else {
        let textContent = 'Chat History\n=============\n\n';
        conversationHistory.forEach(msg => {
            const role = msg.role === 'user' ? 'You' : 'Assistant';
            const timestamp = new Date(msg.timestamp).toLocaleString();
            
            // Add timing information
            if (msg.role === 'user') {
                textContent += `[${timestamp}] ${role}: ${msg.content}\n`;
            } else {
                // For assistant messages, include inference time if available
                const inferenceInfo = msg.llmTime ? ` (Inference: ${formatTime(msg.llmTime)})` : '';
                textContent += `[${timestamp}] ${role}: ${msg.content}${inferenceInfo}\n`;
            }
            textContent += '\n';
        });
        content = textContent;
        filename = 'chat-history.txt';
        mimeType = 'text/plain';
    }
    
    // Create download link
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    // Close export modal
    exportModal.classList.add('hidden');
}

// Initialize Audio Context and Analyser
function setupAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    if (!userAnalyser) {
        userAnalyser = audioContext.createAnalyser();
        userAnalyser.fftSize = 1024;
        userAnalyser.smoothingTimeConstant = 0.6;
    }
    
    return audioContext.state === 'running';
}

// Request microphone access
async function requestMicrophoneAccess() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaStream = stream; // Store the media stream reference
        
        if (!audioContext) {
            setupAudioContext();
        } else if (audioContext.state !== 'running') {
            await audioContext.resume();
        }
        
        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(userAnalyser);
        
        return true;
    } catch (error) {
        console.error('Error accessing microphone:', error);
        sttStatus.textContent = 'Microphone access denied';
        sttStatus.classList.remove('text-success');
        sttStatus.classList.add('text-danger');
        showNotification("Unable to access microphone. Please grant permission and try again.", 'error');
        return false;
    }
}

// Create waveform path for SVG
function createWaveformPath(dataArray, bufferLength) {
    const height = 20;
    const width = 100;
    const middleY = height / 2;
    
    let path = `M0,${middleY} `;
    const sliceWidth = width / bufferLength;
    
    for (let i = 0; i < bufferLength; i++) {
        const value = dataArray[i] / 128.0;
        const y = value * middleY;
        const x = i * sliceWidth;
        
        path += `L${x},${middleY + y - middleY} `;
    }
    
    path += `L${width},${middleY}`;
    return path;
}

// Start user speech visualization
function startUserSpeechVisualization() {
    if (!userAnalyser) return;
    
    const bufferLength = userAnalyser.fftSize;
    const dataArray = new Uint8Array(bufferLength);
    
    function updateWaveform() {
        userAnalyser.getByteTimeDomainData(dataArray);
        
        // Calculate audio activity level
        let sum = 0;
        let count = 0;
        
        for (let i = 0; i < bufferLength; i++) {
            const deviation = Math.abs(dataArray[i] - 128);
            if (deviation > 2) { // Ignore minimal noise
                sum += deviation;
                count++;
            }
        }
        
        const averageDeviation = count ? sum / count : 0;
        const activity = Math.min(100, Math.max(0, averageDeviation * 2)); // Scale to 0-100%
        
        // Update waveform path
        const userPath = userWaveformSvg.querySelector('path');
        userPath.setAttribute('d', createWaveformPath(dataArray, bufferLength));
        
        // Update activity level and color based on intensity
        if (activity > 30) {
            userPath.setAttribute('stroke', '#2b5dbd');
            userPath.setAttribute('stroke-width', '2');
            userPath.setAttribute('opacity', '1');
            userAudioLevel.textContent = 'Active';
            userAudioLevel.classList.add('text-primary');
            userAudioLevel.classList.remove('opacity-60');
        } else if (activity > 5) {
            userPath.setAttribute('stroke', '#2b5dbd');
            userPath.setAttribute('stroke-width', '1.5');
            userPath.setAttribute('opacity', '0.8');
            userAudioLevel.textContent = 'Low';
            userAudioLevel.classList.add('text-primary');
            userAudioLevel.classList.remove('opacity-60');
        } else {
            userPath.setAttribute('stroke', '#2b5dbd');
            userPath.setAttribute('stroke-width', '1');
            userPath.setAttribute('opacity', '0.5');
            userPath.setAttribute('d', 'M0,10 L100,10'); // Flat line when silent
            userAudioLevel.textContent = 'Silent';
            userAudioLevel.classList.remove('text-primary');
            userAudioLevel.classList.add('opacity-60');
        }
        
        // Continue animation if still speaking
        if (isSpeaking) {
            userAnimationFrameId = requestAnimationFrame(updateWaveform);
        }
    }
    
    isSpeaking = true;
    userAnimationFrameId = requestAnimationFrame(updateWaveform);
}

// Stop user speech visualization
function stopUserSpeechVisualization() {
    isSpeaking = false;
    if (userAnimationFrameId) {
        cancelAnimationFrame(userAnimationFrameId);
        userAnimationFrameId = null;
    }
    
    // Reset waveform to flat line
    const userPath = userWaveformSvg.querySelector('path');
    userPath.setAttribute('d', 'M0,10 L100,10');
    userPath.setAttribute('stroke', '#2b5dbd');
    userPath.setAttribute('stroke-width', '1');
    userPath.setAttribute('opacity', '0.5');
    userAudioLevel.textContent = 'Idle';
    userAudioLevel.classList.remove('text-primary');
    userAudioLevel.classList.add('opacity-60');
}

// Permanently stop the microphone
function permanentlyStopMicrophone() {
    // Stop all tracks in the media stream
    if (mediaStream) {
        const tracks = mediaStream.getTracks();
        tracks.forEach(track => {
            track.stop();
        });
        mediaStream = null;
    }
    
    // Disconnect the microphone source
    if (microphone) {
        microphone.disconnect();
        microphone = null;
    }
    
    // Stop audio context
    if (audioContext && audioContext.state !== 'closed') {
        audioContext.close();
        audioContext = null;
    }
    
    // Stop visualization
    stopUserSpeechVisualization();
    
    // Reset recording state
    isRecording = false;
    mediaRecorder = null;
    audioChunks = [];
}

// Start voice recording
async function startRecording() {
    try {
        // Start total interaction timing
        interactionStartTime = Date.now();
        
        // Request microphone access
        const micAccess = await requestMicrophoneAccess();
        if (!micAccess) return;
        
        // Start audio visualization
        startUserSpeechVisualization();
        
        // Start recording
        const stream = microphone.mediaStream;
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await sendAudioToBackend(audioBlob);
            stopUserSpeechVisualization();
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        speechToggleBtn.classList.remove('bg-primary', 'hover:bg-blue-700');
        speechToggleBtn.classList.add('bg-danger', 'hover:bg-red-700');
        speechToggleBtn.innerHTML = '<i class="fas fa-stop mr-1"></i><span class="text-sm">Stop STS</span>';
        sttStatus.textContent = 'Listening';
        sttStatus.classList.remove('text-success');
        sttStatus.classList.add('text-danger');
        
        // Show notification instead of chat message
        showNotification("🎙️ Recording... Click 'Stop STS' to finish", 'info');
    } catch (error) {
        console.error('Error starting recording:', error);
        showNotification("Microphone access denied. Please enable microphone permissions.", 'error');
        stopUserSpeechVisualization();
    }
}

// Stop voice recording
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // Update UI
        speechToggleBtn.classList.remove('bg-danger', 'hover:bg-red-700');
        speechToggleBtn.classList.add('bg-primary', 'hover:bg-blue-700');
        speechToggleBtn.innerHTML = '<i class="fas fa-microphone mr-1"></i><span class="text-sm">Start STS</span>';
        sttStatus.textContent = 'Processing';
        sttStatus.classList.remove('text-danger');
        sttStatus.classList.add('text-warning');
        
        // Show notification
        showNotification("Processing your voice message...", 'info');
    }
}

// Toggle recording state
function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

// Send audio blob to backend
async function sendAudioToBackend(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('user_id', userId);
    
    try {
        // Start STT timing
        sttStartTime = Date.now();
        
        const response = await fetch(`${STT_TTS_BACKEND_URL}/chat/voice`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Calculate STT latency
        const sttTime = Date.now() - sttStartTime;
        
        // Calculate total interaction time
        const totalTime = Date.now() - interactionStartTime;
        
        // Update latency from backend if provided
        if (data.latency) {
            const sttLatency = data.latency.stt || 0;
            const ttsLatency = data.latency.tts || 0;
            updateLatencyDisplay(totalTime, sttLatency, 0, ttsLatency);
        } else {
            updateLatencyDisplay(totalTime, sttTime, 0, 0);
        }
        
        if (data.status === 'success') {
            // Add transcribed text to chat
            addMessage(`🎤 You said: ${data.transcription}`, true);
            
            // Add AI response to chat
            addMessage(data.response, false);
            
            // Update status
            sttStatus.textContent = 'Ready';
            sttStatus.classList.remove('text-warning');
            sttStatus.classList.add('text-success');
        } else {
            showNotification(`Error: ${data.error || 'Failed to process voice message'}`, 'error');
            sttStatus.textContent = 'Error';
            sttStatus.classList.remove('text-warning');
            sttStatus.classList.add('text-danger');
        }
    } catch (error) {
        console.error('Error sending audio to backend:', error);
        showNotification("Failed to send voice message. Please try again.", 'error');
        sttStatus.textContent = 'Error';
        sttStatus.classList.remove('text-warning');
        sttStatus.classList.add('text-danger');
    }
}

// Stop AI voice and permanently stop microphone
function stopAiVoice() {
    showNotification("🔇 AI voice output stopped", 'info');
    
    // Permanently stop the microphone
    permanentlyStopMicrophone();
    
    // Reset UI elements
    speechToggleBtn.classList.remove('bg-danger', 'hover:bg-red-700');
    speechToggleBtn.classList.add('bg-primary', 'hover:bg-blue-700');
    speechToggleBtn.innerHTML = '<i class="fas fa-microphone mr-1"></i><span class="text-sm">Start STS</span>';
    sttStatus.textContent = 'Ready';
    sttStatus.classList.remove('text-danger', 'text-warning');
    sttStatus.classList.add('text-success');
    
    // Enable the stop AI voice button
    stopAiVoiceBtn.disabled = false;
    stopAiVoiceBtn.classList.remove('opacity-50');
    
    // In a real implementation, you would send a request to the backend
    // to stop the current TTS playback
    /*
    fetch(`${STT_TTS_BACKEND_URL}/voice/stop`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification("🔇 AI voice output stopped", 'info');
        } else {
            showNotification(`Error: ${data.error || 'Failed to stop AI voice'}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error stopping AI voice:', error);
        showNotification("Failed to stop AI voice. Please try again.", 'error');
    });
    */
}