# CSRD RAG System - Simple Frontend

A lightweight, vanilla TypeScript frontend for the CSRD RAG System using Vite as the build tool.

## Features

- **Vanilla TypeScript**: No heavy frameworks, just clean TypeScript code
- **Vite Build Tool**: Fast development and optimized builds
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean, professional interface with CSS Grid and Flexbox
- **Full API Integration**: Complete integration with the backend API

## Pages

1. **Dashboard**: Overview with system statistics
2. **Documents**: Upload and manage documents with drag-and-drop
3. **Search**: Semantic search through document content
4. **RAG Query**: AI-powered question answering with multiple model support
5. **Reports**: Generate and download compliance reports
6. **Schemas**: View available regulatory schemas

## Getting Started

### Prerequisites

- Node.js 18+ (for Vite)
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development

The development server runs on http://localhost:3000 with automatic proxy to the backend API.

### API Integration

The frontend automatically proxies `/api/*` requests to the backend server. All API calls include:

- Automatic loading states
- Error handling
- Request/response interceptors
- TypeScript interfaces for type safety

## Architecture

- **src/main.ts**: Main application class with navigation and event handling
- **src/services/api.ts**: API client with TypeScript interfaces
- **src/styles/main.css**: Responsive CSS with modern design
- **index.html**: Single-page application entry point
- **vite.config.ts**: Vite configuration with API proxy

## Browser Support

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+

## Advantages over React Setup

1. **Faster startup**: No complex build process or large dependencies
2. **Smaller bundle**: Minimal JavaScript footprint
3. **Direct control**: No framework abstractions
4. **Better performance**: Native DOM manipulation
5. **Easier debugging**: Straightforward code flow
6. **No version conflicts**: Fewer dependencies to manage

This simple frontend provides all the functionality of the React version while being more lightweight and easier to maintain.