# OpenAgentRAG Frontend

Modern Next.js 14 frontend for the OpenAgentRAG platform, built with React 18, TypeScript, and TailwindCSS.

## Features

- **Chat Interface**: Interactive chat with the RAG system, displaying answers with source citations
- **Document Management**: Upload files (PDF, DOCX, XLSX, TXT) or ingest from URLs
- **Settings Panel**: Configure Ollama and ChromaDB connections with live status monitoring
- **Dark Theme**: Professional dark UI similar to ChatGPT/Perplexity
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5
- **Styling**: TailwindCSS 3
- **UI Components**: Custom components with Lucide React icons
- **Markdown**: react-markdown with syntax highlighting
- **API**: REST API calls to backend at http://localhost:8000

## Getting Started

### Prerequisites

- Node.js 20 or higher
- npm or yarn
- Backend API running at http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update `.env` if your backend runs on a different URL:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

Build for production:
```bash
npm run build
npm start
```

### Docker

Build and run with Docker:
```bash
docker build -t open-agent-rag-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://backend:8000 open-agent-rag-frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── chat/              # Chat interface
│   │   ├── documents/         # Document management
│   │   ├── settings/          # Settings panel
│   │   ├── layout.tsx         # Root layout with sidebar
│   │   └── page.tsx           # Redirect to /chat
│   ├── components/            # Reusable React components
│   │   ├── ChatMessage.tsx    # Message bubble with markdown
│   │   ├── SourceCard.tsx     # Expandable source citation
│   │   ├── FileUpload.tsx     # Drag-and-drop file upload
│   │   ├── StatusBadge.tsx    # Service status indicator
│   │   └── Sidebar.tsx        # Navigation sidebar
│   └── lib/
│       └── api.ts             # API client functions
├── public/                    # Static assets
├── Dockerfile                 # Production container
├── next.config.js            # Next.js configuration
├── tailwind.config.ts        # TailwindCSS configuration
└── tsconfig.json             # TypeScript configuration
```

## API Integration

The frontend communicates with the backend via REST API:

### Chat Endpoints
- `POST /api/chat/query` - Send query and get response with sources
- `GET /api/chat/history/{session_id}` - Retrieve chat history

### Document Endpoints
- `GET /api/documents` - List all documents
- `POST /api/documents/upload` - Upload file (multipart/form-data)
- `POST /api/documents/ingest-url` - Ingest document from URL
- `DELETE /api/documents/{id}` - Delete document

### Settings Endpoints
- `GET /api/settings` - Get current configuration
- `PUT /api/settings` - Update configuration
- `GET /api/settings/status` - Check service status

## Components

### ChatMessage
Renders user and assistant messages with markdown support and syntax highlighting. Assistant messages include expandable source citations.

### SourceCard
Displays document sources with relevance scores. Click to expand and view the full chunk content.

### FileUpload
Drag-and-drop or click-to-browse file upload with progress indicators. Supports PDF, DOCX, XLSX, and TXT files.

### StatusBadge
Shows online/offline status with colored indicators for Ollama, ChromaDB, and overall system health.

## Styling

The app uses a custom dark theme with:
- Background: `slate-900`
- Cards: `slate-800`
- Primary: `blue-600`
- Custom scrollbar styling
- Responsive design with Tailwind utilities

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

Part of the OpenAgentRAG project.
