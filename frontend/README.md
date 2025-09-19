# CSRD RAG System Frontend

A React TypeScript application for managing sustainability reporting documents with AI-powered search and report generation capabilities.

## Features

- **Document Management**: Upload and organize CSRD, ESRS, and UK SRD documents
- **Intelligent Search**: Semantic search through document repository
- **RAG Query Interface**: AI-powered question answering with multiple model support
- **Report Generation**: Automated sustainability report creation from client requirements
- **Schema Management**: Support for EU ESRS/CSRD and UK SRD reporting standards
- **Responsive Design**: Mobile-friendly interface with Material-UI components

## Technology Stack

- **React 18** with TypeScript for type safety
- **Material-UI (MUI)** for consistent, professional UI components
- **React Router** for client-side routing
- **Axios** for API communication
- **Jest & React Testing Library** for unit and integration testing

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API server running (see backend README)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment configuration:
```bash
cp .env.example .env
```

3. Update `.env` with your API endpoint:
```
REACT_APP_API_URL=http://localhost:8000/api
```

### Development

Start the development server:
```bash
npm start
```

The application will open at `http://localhost:3000`.

### Testing

Run the test suite:
```bash
npm test
```

Run tests with coverage:
```bash
npm test -- --coverage
```

### Building for Production

Create a production build:
```bash
npm run build
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Layout/         # Main application layout
├── pages/              # Page components
│   ├── Dashboard.tsx   # System overview and statistics
│   ├── Documents.tsx   # Document repository management
│   ├── Search.tsx      # Semantic search interface
│   ├── RAG.tsx         # AI question answering
│   ├── Reports.tsx     # Report generation workflow
│   └── Schemas.tsx     # Reporting schema reference
├── services/           # API service layers
│   ├── api.ts          # Base API configuration
│   ├── documentService.ts
│   ├── searchService.ts
│   └── ragService.ts
└── utils/              # Utility functions
```

## Key Components

### Layout Component
- Responsive navigation with drawer for mobile
- Consistent header and sidebar across all pages
- Material-UI theming and accessibility support

### Document Management
- File upload with drag-and-drop support
- Remote directory synchronization
- Document metadata display and filtering
- Processing status tracking

### Search Interface
- Natural language query input
- Relevance-scored results with source attribution
- Schema element filtering and highlighting

### RAG Query System
- Multiple AI model selection (GPT-4, Claude, Llama)
- Confidence scoring and source citations
- Query history and response rating

### Report Generation
- Step-by-step wizard interface
- Client requirements upload and processing
- Schema mapping visualization
- PDF report download

## Accessibility Features

- ARIA labels and roles for screen readers
- Keyboard navigation support
- High contrast color schemes
- Responsive design for various screen sizes
- Focus management for modal dialogs

## Testing Strategy

- **Unit Tests**: Component logic and rendering
- **Integration Tests**: API service interactions
- **Accessibility Tests**: ARIA compliance and keyboard navigation
- **Responsive Tests**: Mobile and desktop layouts

## Environment Variables

- `REACT_APP_API_URL`: Backend API base URL
- `REACT_APP_VERSION`: Application version (optional)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Follow TypeScript strict mode guidelines
2. Use Material-UI components consistently
3. Write tests for new components and features
4. Follow accessibility best practices
5. Ensure responsive design compatibility