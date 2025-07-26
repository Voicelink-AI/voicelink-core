# Live Audio Capture for Voicelink Bots

## Discord Bot Integration

### Method 1: Voice Channel Recording
```python
import discord
from discord.ext import commands
import asyncio
import io

class VoicelinkDiscordBot(commands.Bot):
    async def record_voice_channel(self, voice_channel):
        """Record audio from Discord voice channel"""
        
        # Connect to voice channel
        voice_client = await voice_channel.connect()
        
        # Set up audio sink to capture all participants
        audio_sink = AudioSink()
        voice_client.start_recording(
            audio_sink,
            self.after_recording,
            sync_mode=False
        )
        
        print(f"🎙️ Recording started in {voice_channel.name}")
        return voice_client
    
    def after_recording(self, sink, channel, *args):
        """Process recorded audio"""
        for user_id, audio_data in sink.audio_data.items():
            # Send to Voicelink pipeline
            self.process_user_audio(user_id, audio_data)

# Bot commands
@bot.command()
async def start_meeting(ctx):
    """Start recording the current voice channel"""
    if ctx.author.voice:
        voice_client = await record_voice_channel(ctx.author.voice.channel)
        await ctx.send("🎙️ Meeting recording started!")
    else:
        await ctx.send("❌ You need to be in a voice channel!")
```

### Method 2: Real-time Audio Streaming
```python
class LiveTranscriptionBot:
    def __init__(self):
        self.voicelink_sdk = VoicelinkSDK()
        self.audio_buffer = []
    
    async def on_voice_data(self, user, audio_chunk):
        """Handle incoming voice data in real-time"""
        
        # Buffer audio chunks
        self.audio_buffer.append({
            'user': user,
            'audio': audio_chunk,
            'timestamp': time.time()
        })
        
        # Process when buffer reaches threshold (e.g., 30 seconds)
        if len(self.audio_buffer) >= 30:
            await self.process_audio_buffer()
    
    async def process_audio_buffer(self):
        """Process buffered audio through Voicelink"""
        
        # Combine audio chunks
        combined_audio = self.combine_audio_chunks(self.audio_buffer)
        
        # Send to Voicelink API
        result = await self.voicelink_sdk.process_meeting_stream(combined_audio)
        
        # Post real-time summary
        await self.post_live_summary(result)
        
        # Clear buffer
        self.audio_buffer = []
