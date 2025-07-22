#!/usr/bin/env python3
"""
VoiceLink Orchestration Pipeline

This is the main orchestration layer that coordinates the entire AI-powered
documentation pipeline for VoiceLink.

Pipeline Flow:
1. Audio Processing (C++ audio_engine + Python wrappers)
2. Speaker Diarization (pyannote.audio)
3. Speech-to-Text (Whisper/Vosk/ElevenLabs)
4. Code Context Extraction (C++ code_context + Python)
5. LLM Processing (Summarization, Q&A, Documentation)
6. Integration & Storage (Discord, GitHub, Notion, Blockchain)

Author: VoiceLink Team
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# Core imports
from api.config import Config
from llm_engine.pipeline import LLMPipeline
from audio_engine.python.audio_processor import AudioProcessor
from integrations.manager import IntegrationManager
from persistence.models import DocumentSession, AudioTranscript
from persistence.database_service import get_database_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class VoiceLinkSession:
    """Represents a single VoiceLink processing session"""
    session_id: str
    audio_file: Path
    participants: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing results
    vad_segments: List[Dict] = field(default_factory=list)
    diarization_results: Dict = field(default_factory=dict)
    transcriptions: List[Dict] = field(default_factory=list)
    code_context: Dict = field(default_factory=dict)
    llm_outputs: Dict = field(default_factory=dict)


class VoiceLinkOrchestrator:
    """
    Main orchestration class for the VoiceLink pipeline
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.audio_processor = AudioProcessor()
        self.llm_pipeline = LLMPipeline(config)
        self.integration_manager = IntegrationManager(config)
        self.db_service = get_database_service()
        
        logger.info("VoiceLink Orchestrator initialized")
    
    async def process_audio_session(
        self,
        audio_file: Path,
        session_id: str = None,
        participants: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> VoiceLinkSession:
        """
        Process a complete audio session through the VoiceLink pipeline
        """
        if session_id is None:
            session_id = f"session_{int(time.time())}"
        
        # Create meeting record in database
        meeting_data = {
            'title': metadata.get('title', f'Meeting {session_id}'),
            'description': metadata.get('description'),
            'participants': participants or [],
            'metadata': metadata or {},
            'audio_file_path': str(audio_file)
        }
        
        meeting_id = self.db_service.create_meeting(meeting_data)
        logger.info(f"Created meeting record: {meeting_id}")
        
        session = VoiceLinkSession(
            session_id=session_id,
            audio_file=audio_file,
            participants=participants or [],
            metadata=metadata or {}
        )
        session.meeting_id = meeting_id  # Store meeting ID in session
        
        logger.info(f"Starting processing for session {session_id}")
        
        try:
            # Update meeting status
            self.db_service.update_meeting_status(meeting_id, 'processing')
            
            # Step 1: Audio preprocessing and VAD
            logger.info("Step 1: Audio preprocessing and VAD")
            session.vad_segments = await self._process_audio_vad(session)
            
            # Step 2: Speaker diarization
            logger.info("Step 2: Speaker diarization")
            session.diarization_results = await self._process_speaker_diarization(session)
            
            # Step 3: Speech-to-text transcription
            logger.info("Step 3: Speech-to-text transcription")
            session.transcriptions = await self._process_transcription(session)
            
            # Save transcripts to database
            if session.transcriptions:
                transcript_data = [
                    {
                        'speaker': t.get('speaker'),
                        'text': t.get('text', ''),
                        'confidence': t.get('confidence'),
                        'start_time': t.get('start_time'),
                        'end_time': t.get('end_time'),
                        'speaker_id': t.get('speaker_id'),
                        'processing_method': t.get('method', 'whisper')
                    }
                    for t in session.transcriptions
                ]
                self.db_service.save_transcripts(meeting_id, transcript_data)
            
            # Step 4: Code context extraction
            logger.info("Step 4: Code context extraction")
            session.code_context = await self._extract_code_context(session)
            
            # Step 5: LLM processing
            logger.info("Step 5: LLM processing")
            session.llm_outputs = await self._process_llm_pipeline(session)
            
            # Save LLM analysis to database
            if session.llm_outputs:
                self.db_service.save_meeting_analysis(meeting_id, session.llm_outputs)
            
            # Step 6: Integration and storage
            logger.info("Step 6: Integration and storage")
            await self._handle_integrations_and_storage(session)
            
            # Update meeting status to completed
            self.db_service.update_meeting_status(meeting_id, 'completed')
            
            logger.info(f"Successfully processed session {session_id}")
            return session
            
        except Exception as e:
            # Update meeting status to failed
            self.db_service.update_meeting_status(meeting_id, 'failed')
            logger.error(f"Error processing session {session_id}: {str(e)}")
            raise
    
    async def _process_audio_vad(self, session: VoiceLinkSession) -> List[Dict]:
        """Process audio file with Voice Activity Detection using C++ audio engine"""
        try:
            logger.info(f"Processing VAD for {session.audio_file}")
            
            # Use audio processor for VAD
            audio_data = self.audio_processor.load_audio(session.audio_file)
            vad_segments = self.audio_processor.run_vad(audio_data)
            
            logger.info(f"Found {len(vad_segments)} speech segments")
            return vad_segments
            
        except Exception as e:
            logger.error(f"VAD processing failed: {str(e)}")
            raise
    
    async def _process_speaker_diarization(self, session: VoiceLinkSession) -> Dict:
        """Process speaker diarization using pyannote.audio"""
        try:
            logger.info(f"Processing speaker diarization for {session.audio_file}")
            
            # Mock diarization results - would use actual pyannote.audio
            diarization_results = {
                "speakers": ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"],
                "segments": [
                    {"start": 0.0, "end": 5.2, "speaker": "SPEAKER_00"},
                    {"start": 6.1, "end": 12.3, "speaker": "SPEAKER_01"},
                    {"start": 15.0, "end": 28.7, "speaker": "SPEAKER_02"},
                ]
            }
            
            logger.info(f"Identified {len(diarization_results['speakers'])} speakers")
            return diarization_results
            
        except Exception as e:
            logger.error(f"Speaker diarization failed: {str(e)}")
            raise
    
    async def _process_transcription(self, session: VoiceLinkSession) -> List[Dict]:
        """Process speech-to-text transcription using Whisper/Vosk/ElevenLabs"""
        try:
            logger.info("Processing speech-to-text transcription")
            
            # Mock transcription results - replace with actual ASR
            transcriptions = [
                {
                    "start_time": 0.0,
                    "end_time": 5.2,
                    "speaker_id": "SPEAKER_00",
                    "text": "Let's start the sprint planning meeting. We need to discuss the API redesign.",
                    "confidence": 0.94
                },
                {
                    "start_time": 6.1,
                    "end_time": 12.3,
                    "speaker_id": "SPEAKER_01",
                    "text": "I think we should focus on the authentication middleware first. The PR #234 has some issues.",
                    "confidence": 0.87
                },
                {
                    "start_time": 15.0,
                    "end_time": 28.7,
                    "speaker_id": "SPEAKER_02",
                    "text": "Good point. Let's also review the database migrations in the user_service.py file.",
                    "confidence": 0.91
                }
            ]
            
            logger.info(f"Generated {len(transcriptions)} transcript segments")
            return transcriptions
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    async def _extract_code_context(self, session: VoiceLinkSession) -> Dict:
        """Extract code context using C++ code context engine"""
        try:
            logger.info("Extracting code context from transcription")
            
            # Mock code context extraction - would use C++ code parser
            code_context = {
                "file_references": ["user_service.py", "auth_middleware.py"],
                "pr_references": ["#234"],
                "issue_references": [],
                "functions_mentioned": ["authenticate_user", "migrate_database"],
                "code_snippets": []
            }
            
            logger.info(f"Extracted code context: {len(code_context['file_references'])} files, {len(code_context['pr_references'])} PRs")
            return code_context
            
        except Exception as e:
            logger.error(f"Code context extraction failed: {str(e)}")
            raise
    
    async def _process_llm_pipeline(self, session: VoiceLinkSession) -> Dict:
        """Process transcriptions through LLM pipeline for documentation generation"""
        try:
            logger.info("Processing through LLM pipeline")
            
            # Use the LLM pipeline to generate summaries, action items, etc.
            llm_results = await self.llm_pipeline.process_meeting(
                transcripts=session.transcriptions,
                code_context=session.code_context,
                participants=session.participants,
                metadata=session.metadata
            )
            
            logger.info("LLM processing completed")
            return llm_results
            
        except Exception as e:
            logger.error(f"LLM pipeline failed: {str(e)}")
            raise
    
    async def _handle_integrations_and_storage(self, session: VoiceLinkSession):
        """Handle integrations (Discord, GitHub, Notion) and storage"""
        try:
            logger.info("Handling integrations and storage")
            
            # Store session data
            await self._store_session_data(session)
            
            # Handle integrations
            await self.integration_manager.process_session_results(session)
            
            logger.info("Integrations and storage completed")
            
        except Exception as e:
            logger.error(f"Integration/storage failed: {str(e)}")
            raise
    
    async def _store_session_data(self, session: VoiceLinkSession):
        """Store session data in persistent storage"""
        logger.info(f"Storing session data for {session.session_id}")
        # Would store in actual database
        pass


async def main():
    """Main entry point for the VoiceLink orchestrator"""
    # Initialize configuration
    config = Config()
    
    # Create orchestrator
    orchestrator = VoiceLinkOrchestrator(config)
    
    # Example usage
    audio_file = Path("example_meeting.wav")
    if audio_file.exists():
        session = await orchestrator.process_audio_session(
            audio_file=audio_file,
            participants=["Alice", "Bob", "Charlie"],
            metadata={"meeting_type": "sprint_planning", "project": "voicelink"}
        )
        
        print(f"Session {session.session_id} processed successfully!")
        print(f"Generated {len(session.transcriptions)} transcript segments")
        print(f"LLM outputs: {list(session.llm_outputs.keys())}")
    else:
        logger.warning(f"Audio file {audio_file} not found. Running demo mode.")
        
        # Demo with mock data
        session = await orchestrator.process_audio_session(
            audio_file=Path("demo.wav"),
            participants=["Alice", "Bob"],
            metadata={"meeting_type": "demo", "project": "voicelink"}
        )
        
        print(f"Demo session {session.session_id} completed!")


if __name__ == "__main__":
    asyncio.run(main())
