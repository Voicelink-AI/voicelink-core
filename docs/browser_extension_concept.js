// Browser Extension for Live Meeting Capture

// Content script for Google Meet/Zoom web
class VoicelinkExtension {
    constructor() {
        this.isRecording = false;
        this.audioStream = null;
        this.voicelinkAPI = 'http://localhost:8000';
    }
    
    async startRecording() {
        try {
            // Capture tab audio
            this.audioStream = await navigator.mediaDevices.getDisplayMedia({
                video: false,
                audio: {
                    echoCancellation: false,
                    noiseSuppression: false,
                    sampleRate: 44100
                }
            });
            
            // Set up MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.audioStream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.processMeeting();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            console.log('🎙️ Voicelink recording started');
            
        } catch (error) {
            console.error('Recording failed:', error);
        }
    }
    
    async processMeeting() {
        // Create audio blob
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        
        // Send to Voicelink API
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'meeting.wav');
        
        const response = await fetch(`${this.voicelinkAPI}/process-meeting`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        // Display results in browser
        this.displayMeetingSummary(result);
    }
    
    displayMeetingSummary(result) {
        // Inject summary UI into the meeting page
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'voicelink-summary';
        summaryDiv.innerHTML = `
            <h3>🎙️ Voicelink Meeting Summary</h3>
            <p><strong>Title:</strong> ${result.documentation.summary.meeting_title}</p>
            <p><strong>Participants:</strong> ${result.documentation.summary.participants.join(', ')}</p>
            <div><strong>Action Items:</strong>
                <ul>
                    ${result.documentation.summary.action_items.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
        
        document.body.appendChild(summaryDiv);
    }
}

// Initialize extension
const voicelinkExt = new VoicelinkExtension();

// Add UI button to start recording
const recordButton = document.createElement('button');
recordButton.textContent = '🎙️ Start Voicelink';
recordButton.onclick = () => voicelinkExt.startRecording();
document.body.appendChild(recordButton);
