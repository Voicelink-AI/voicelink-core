# Voicelink Integration Guide

## Repository Architecture

### Core → App Integration
**voicelink-core** provides REST API endpoints that **voicelink-app** consumes:

```typescript
// Frontend API client
const VoicelinkAPI = {
  // Process meeting audio
  processMeeting: async (audioFile: File) => {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    return fetch('/api/process-meeting', { method: 'POST', body: formData });
  },
  
  // Ask questions about meetings
  askQuestion: async (question: string) => {
    return fetch('/api/ask-question', {
      method: 'POST',
      body: JSON.stringify({ question }),
      headers: { 'Content-Type': 'application/json' }
    });
  },
  
  // Get meeting documentation
  getMeetingDocs: async (sessionId: string) => {
    return fetch(`/api/meetings/${sessionId}/docs`);
  }
};
```

### Core → Integrations Connection
**voicelink-core** exposes hooks that **voicelink-integrations** uses:

```python
# Integration webhook example
from voicelink_core.llm_engine.enhanced_pipeline_with_context import process_audio_with_context
from voicelink_core.llm_engine.modules.doc_generator import generate_meeting_documentation

# GitHub integration
def sync_to_github(meeting_results):
    docs = generate_meeting_documentation(meeting_results)
    # Push to GitHub wiki/issues
    
# Discord bot integration  
def handle_discord_meeting(audio_url):
    results = process_audio_with_context(audio_url)
    # Send summary to Discord channel
```

### Core → Bot Integration
**voicelink-core** provides bot SDK:

```python
# Discord bot using core
from voicelink_core.api.main import process_meeting
from voicelink_core.llm_engine.modules.voice_qa import ask_voice_question

@bot.command()
async def analyze_meeting(ctx, audio_attachment):
    results = await process_meeting(audio_attachment)
    await ctx.send(f"Meeting analyzed: {results['documentation']['summary']['meeting_title']}")

@bot.command() 
async def ask(ctx, *, question):
    answer = ask_voice_question(question)
    await ctx.send(f"🤖 {answer['answer']}")
```

### Core → Chain Integration
**voicelink-core** connects to **voicelink-chain**:

```python
# Blockchain integration
from voicelink_chain.contracts.provenance import ProvenanceContract

def anchor_document(meeting_docs):
    contract = ProvenanceContract()
    hash_id = create_meeting_provenance(meeting_docs)
    tx = contract.anchor_document(hash_id, metadata)
    return tx.hash
```
