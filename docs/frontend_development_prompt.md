# Voicelink Frontend Development Prompt

Use this comprehensive prompt to guide AI agent development of the Voicelink React frontend.

---

# Build Voicelink Frontend: AI-Powered Voice Documentation Platform

## 🎯 Project Overview

**Voicelink** is a revolutionary AI-powered platform that transforms developer meetings into structured, code-aware documentation with voice Q&A and blockchain provenance. Think "Notion meets GitHub Copilot meets Google Docs, powered by voice and AI."

## 🏗️ Frontend Requirements

### **Technology Stack:**
- **React 18+ with TypeScript**
- **Modern UI Framework:** Tailwind CSS + Headless UI or Chakra UI
- **State Management:** Zustand or Redux Toolkit
- **API Client:** Axios with React Query
- **Audio Handling:** Web Audio API + MediaRecorder
- **File Upload:** React Dropzone
- **Charts/Visualizations:** Recharts or Chart.js
- **Icons:** Heroicons or Lucide React

### **Backend Integration:**
- **API Base URL:** `http://localhost:8000`
- **Key Endpoints:**
  - `POST /process-meeting` - Upload and process audio
  - `POST /ask-question` - Interactive Q&A
  - `GET /health` - System health check
  - `GET /capabilities` - System capabilities

## 🎨 Core Features to Implement

### **1. Audio Upload & Processing Interface**
```typescript
// Key functionality:
- Drag-and-drop audio file upload (.wav, .mp3, .m4a, .flac)
- Real-time upload progress
- File validation (format, size limits)
- Processing status indicators
- Support for live microphone recording
```

### **2. Meeting Dashboard**
```typescript
// Display components:
- Meeting list with search/filter
- Processing status cards
- Audio duration and participant count
- Meeting type badges (sprint, review, standup)
- Quick actions (reprocess, share, delete)
```

### **3. Real-time Documentation Viewer**
```typescript
// Generated content display:
- Meeting title and summary
- Participant list with roles
- Timestamped transcript segments
- Action items with assignees
- Technical decisions and key points
- Code references and GitHub links
- Collapsible sections for organization
```

### **4. Interactive Voice Q&A Chat**
```typescript
// Chat interface features:
- Text input for questions
- Voice recording button (future enhancement)
- AI response display with confidence scores
- Source citations linking to transcript segments
- Chat history persistence
- Quick question suggestions
```

### **5. Code Context Visualization**
```typescript
// Technical context display:
- GitHub references (issues, PRs) as clickable badges
- File mentions with syntax highlighting previews
- Technical terms glossary
- Code snippet embeddings
- Repository connection status
```

### **6. Blockchain Provenance Panel**
```typescript
// Trust and verification features:
- Document hash display
- Timestamp verification
- Authorship proof
- Blockchain transaction links
- Verification status indicators
- Download signed documents
```

## 📱 UI/UX Design Guidelines

### **Design System:**
- **Primary Colors:** Blue (#3B82F6) for trust, Green (#10B981) for success
- **Typography:** Inter or System fonts for readability
- **Layout:** Sidebar navigation + main content area
- **Responsive:** Mobile-first approach
- **Accessibility:** WCAG 2.1 AA compliance

### **Component Hierarchy:**
```
App
├── Layout
│   ├── Sidebar (Navigation)
│   ├── Header (User, Search)
│   └── Main Content
├── Pages
│   ├── Dashboard (Meeting list)
│   ├── Upload (Audio processing)
│   ├── Meeting Detail (Full analysis)
│   └── Settings (Configuration)
└── Components
    ├── AudioUploader
    ├── MeetingCard
    ├── TranscriptViewer
    ├── ChatInterface
    ├── CodeContextPanel
    └── ProvenanceDisplay
```

## 🔌 API Integration Patterns

### **Example API Calls:**
```typescript
// Process meeting audio
const processMeeting = async (audioFile: File) => {
  const formData = new FormData();
  formData.append('audio_file', audioFile);
  
  const response = await fetch('http://localhost:8000/process-meeting', {
    method: 'POST',
    body: formData
  });
  
  return response.json();
};

// Ask questions about meetings
const askQuestion = async (question: string) => {
  const response = await fetch('http://localhost:8000/ask-question', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  
  return response.json();
};
```

### **Expected API Response Formats:**
```typescript
// Meeting processing response
interface MeetingResult {
  status: 'success' | 'error';
  voicelink_analysis: {
    summary: {
      total_duration: number;
      speakers_detected: number;
      transcribed_segments: number;
    };
    transcripts: Array<{
      text: string;
      speaker_id: number;
      start_time: number;
      end_time: number;
    }>;
    code_context: {
      github_references: Array<{
        type: 'issue' | 'pr';
        value: string;
        full_match: string;
      }>;
      technical_terms: string[];
      file_mentions: string[];
    };
  };
  documentation: {
    summary: {
      meeting_title: string;
      participants: string[];
      action_items: string[];
      key_topics: string[];
    };
    markdown: string;
  };
  provenance: {
    document_hash: string;
    timestamp: string;
    provenance_id: string;
  };
}
```

## 🎯 Priority Implementation Order

### **Phase 1: Core Upload & Display (Week 1)**
1. Basic React app structure with TypeScript
2. Audio file upload component with validation
3. API integration for meeting processing
4. Simple results display (transcripts, summary)

### **Phase 2: Enhanced UI & Interactions (Week 2)**
1. Professional dashboard with meeting cards
2. Detailed meeting view with organized sections
3. Real-time processing status updates
4. Basic Q&A chat interface

### **Phase 3: Advanced Features (Week 3)**
1. Code context visualization
2. Blockchain provenance display
3. Search and filtering capabilities
4. Export functionality (PDF, Markdown)

### **Phase 4: Polish & Performance (Week 4)**
1. Responsive design optimization
2. Loading states and error handling
3. Accessibility improvements
4. Performance optimization

## 🛠️ Development Guidelines

### **Code Quality:**
- Use TypeScript strictly (no `any` types)
- Implement proper error boundaries
- Add loading states for all async operations
- Follow React best practices (hooks, functional components)
- Write comprehensive PropTypes/interfaces

### **State Management:**
- Use React Query for server state
- Zustand for client state (UI, settings)
- Local state for component-specific data
- Proper error and loading state handling

### **Performance:**
- Implement code splitting for routes
- Lazy load heavy components
- Optimize bundle size
- Use React.memo for expensive renders
- Implement virtual scrolling for large lists

### **Testing:**
- Unit tests for utility functions
- Component tests for key interactions
- Integration tests for API calls
- E2E tests for critical user flows

## 📋 Specific Component Requirements

### **AudioUploader Component:**
```typescript
interface AudioUploaderProps {
  onUpload: (file: File) => Promise<void>;
  acceptedFormats: string[];
  maxSize: number;
  isProcessing: boolean;
}
```

### **MeetingCard Component:**
```typescript
interface MeetingCardProps {
  meeting: {
    id: string;
    title: string;
    duration: number;
    participants: string[];
    status: 'processing' | 'completed' | 'failed';
    createdAt: string;
  };
  onView: (id: string) => void;
  onDelete: (id: string) => void;
}
```

### **ChatInterface Component:**
```typescript
interface ChatInterfaceProps {
  meetingId: string;
  onAskQuestion: (question: string) => Promise<any>;
  chatHistory: Array<{
    question: string;
    answer: string;
    confidence: number;
    sources: string[];
  }>;
}
```

## 🚀 Success Criteria

### **Functional Requirements:**
- ✅ Users can upload audio files and see processing results
- ✅ Clean, intuitive interface showing meeting summaries
- ✅ Interactive Q&A works with confidence scores
- ✅ Code context is clearly displayed with GitHub links
- ✅ Blockchain provenance information is accessible

### **Technical Requirements:**
- ✅ TypeScript with strict mode enabled
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Fast loading times (<3s initial load)
- ✅ Proper error handling and user feedback
- ✅ Accessibility compliance (keyboard navigation, screen readers)

### **User Experience:**
- ✅ Professional, developer-focused design
- ✅ Clear visual hierarchy and information architecture
- ✅ Smooth animations and transitions
- ✅ Intuitive navigation and discoverability
- ✅ Helpful loading states and progress indicators

## 🎨 Design References

**Inspiration from:**
- GitHub's clean, developer-focused interface
- Notion's organized content layout
- Discord's chat interface design
- Figma's collaborative features
- Linear's modern, fast UI

**Key Design Principles:**
- **Clarity:** Information is easy to find and understand
- **Efficiency:** Common tasks are quick to complete
- **Trust:** Professional appearance builds confidence
- **Accessibility:** Usable by developers with different abilities
- **Scalability:** Interface works with 1 or 1000 meetings

---

## 🏁 Getting Started

1. **Initialize React TypeScript project with Vite**
2. **Set up Tailwind CSS and UI component library**
3. **Create basic routing structure**
4. **Implement audio upload component first**
5. **Test API integration with backend**
6. **Build iteratively with frequent testing**

**Remember:** The goal is creating a professional tool that developers love using for their meeting documentation needs. Focus on clarity, performance, and the unique value proposition of code-aware AI analysis.

Good luck building the future of developer collaboration! 🚀
