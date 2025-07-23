"""
Simple on-chain provenance for Voicelink docs
"""
import hashlib
import json
from datetime import datetime
from typing import Dict, Any

class SimpleProvenance:
    """Basic provenance system for demo"""
    
    def __init__(self):
        print("⛓️  Simple Provenance initialized (demo mode)")
    
    def create_document_hash(self, documentation: Dict[str, Any]) -> str:
        """Create a hash of the documentation for provenance"""
        doc_string = json.dumps(documentation, sort_keys=True)
        return hashlib.sha256(doc_string.encode()).hexdigest()
    
    def create_provenance_record(self, voicelink_results: Dict[str, Any], documentation: Dict[str, Any]) -> Dict[str, Any]:
        """Create a provenance record (demo version)"""
        doc_hash = self.create_document_hash(documentation)
        
        record = {
            "document_hash": doc_hash,
            "timestamp": datetime.now().isoformat(),
            "audio_duration": voicelink_results.get("summary", {}).get("total_duration", 0),
            "speakers_count": voicelink_results.get("summary", {}).get("speakers_detected", 0),
            "transcripts_count": voicelink_results.get("summary", {}).get("transcribed_segments", 0),
            "blockchain_status": "demo_mode",
            "provenance_id": f"voicelink_{int(datetime.now().timestamp())}"
        }
        
        print(f"⛓️  Created provenance record: {record['provenance_id']}")
        print(f"📋 Document hash: {doc_hash[:16]}...")
        
        return record

# Global instance
provenance = SimpleProvenance()

def create_meeting_provenance(voicelink_results: Dict[str, Any], documentation: Dict[str, Any]) -> Dict[str, Any]:
    """Create provenance record for meeting"""
    return provenance.create_provenance_record(voicelink_results, documentation)
