# VoiceLink-Bot Integration

## Core Connection
Bot will use your SDK:

```python
# Bot imports your working functions
from voicelink_sdk import process_meeting, ask_meeting_question

@bot.command()
async def analyze_voice(ctx, attachment):
    # Uses your real pipeline
    result = process_meeting(attachment.url)
    await ctx.send(f"📋 {result['documentation']['summary']['meeting_title']}")

@bot.command()
async def ask(ctx, *, question):
    # Uses your real Q&A
    answer = ask_meeting_question(question)
    await ctx.send(f"🤖 {answer['answer']}")
```

## Demo Impact: VERY HIGH  
Live Discord demo shows real developer workflow
