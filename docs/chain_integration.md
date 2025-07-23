# VoiceLink-Chain Integration

## Purpose
Cryptographic proof of meeting documentation:

```solidity
// Smart contract for document provenance
contract VoiceLinkProvenance {
    struct DocumentProof {
        bytes32 contentHash;
        uint256 timestamp;
        address author;
        string metadataURI;
    }
    
    mapping(bytes32 => DocumentProof) public documents;
    
    function anchorDocument(bytes32 hash, string calldata metadata) external {
        documents[hash] = DocumentProof(hash, block.timestamp, msg.sender, metadata);
    }
}
```

## Core Integration
Your existing provenance system will call this:

```python
# Your core already has this placeholder
from blockchain.simple_provenance import create_meeting_provenance

# Will become:
from voicelink_chain.contracts import anchor_document_onchain
```

## Business Value
- 🔒 IP protection for enterprises
- ⚖️ Legal compliance (SOX, GDPR)
- 🎯 Differentiator vs competitors

## When to Build: Month 6+ or for enterprise deals
