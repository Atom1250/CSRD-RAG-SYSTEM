# 🚀 CSRD RAG System - User Guide

## 📱 **Accessing the System**

- **Frontend**: http://localhost:62646
- **Backend API**: http://localhost:50222
- **System Management**: `./manage.sh status`

## 🎯 **Key Features**

### 1. **📊 Dashboard**
- Real-time system status monitoring
- Connection status for all services
- Quick system health overview

### 2. **📄 Document Management**
- **Upload Documents**: Drag & drop or select PDF, DOCX, TXT files
- **View Library**: See all uploaded documents with metadata
- **Processing Status**: Track document processing progress
- **File Support**: PDF, DOCX, TXT with automatic text extraction

### 3. **🔍 Document Search**
- **Semantic Search**: Natural language queries
- **Smart Results**: Relevance scoring and source citations
- **Context-Aware**: Understands CSRD, climate, governance topics
- **Keyboard Shortcut**: Press Enter to search

**Example Queries:**
- "CSRD reporting requirements"
- "Scope 3 emissions calculation"
- "governance structures sustainability"

### 4. **🤖 RAG Question Answering**
- **AI Models**: OpenAI GPT-4, Anthropic Claude, Local models
- **Comprehensive Responses**: Detailed answers with sources
- **Topic Expertise**: CSRD, climate, ESG, governance
- **Keyboard Shortcut**: Ctrl/Cmd + Enter to submit

**Example Questions:**
- "What are the CSRD reporting requirements?"
- "How do I calculate Scope 3 emissions?"
- "What governance structures are needed for sustainability?"

### 5. **📋 Report Generation**
- **Templates**: EU ESRS/CSRD, UK SRD compliance reports
- **Automated Generation**: Professional PDF reports
- **Section Breakdown**: Comprehensive report structure
- **Download Ready**: Direct PDF download links

### 6. **🧪 System Testing**
- **Connection Tests**: Database, Redis, OpenAI API
- **Health Monitoring**: Real-time service status
- **Performance Metrics**: Response times and system load

## ⌨️ **Keyboard Shortcuts**

- **Enter**: Submit search queries
- **Ctrl/Cmd + Enter**: Submit RAG questions
- **Escape**: Clear all results

## 🎨 **User Interface Features**

- **Auto-Detection**: Automatically finds backend on startup
- **Loading States**: Visual feedback during operations
- **Hover Effects**: Interactive elements with visual feedback
- **Responsive Design**: Works on desktop and mobile
- **Error Handling**: Clear error messages with suggestions

## 📊 **Sample Data**

The system includes rich sample data for demonstration:

- **Documents**: EU ESRS Guidelines, Sustainability Reports
- **Search Results**: Context-aware responses with relevance scoring
- **RAG Responses**: Comprehensive CSRD and climate guidance
- **Reports**: Professional compliance report templates

## 🔧 **System Management**

```bash
# Start the system
./manage.sh start

# Check status
./manage.sh status

# Stop the system
./manage.sh stop

# View logs
./manage.sh logs

# Restart everything
./manage.sh restart
```

## 🎯 **Best Practices**

### **Document Upload**
- Use descriptive filenames
- Supported formats: PDF, DOCX, TXT
- Maximum file size: 50MB per file
- Multiple files can be uploaded simultaneously

### **Search Queries**
- Use natural language
- Be specific about topics (CSRD, climate, governance)
- Try different keyword combinations
- Use quotes for exact phrases

### **RAG Questions**
- Ask specific, focused questions
- Reference specific frameworks (CSRD, ESRS, TCFD)
- Include context in your questions
- Try follow-up questions for deeper insights

### **Report Generation**
- Choose appropriate template for your needs
- EU ESRS/CSRD for European compliance
- UK SRD for UK sustainability reporting

## 🚀 **Advanced Features**

- **Real-time Processing**: Documents processed immediately upon upload
- **Vector Search**: Semantic similarity matching
- **Multi-model AI**: Support for multiple AI providers
- **Source Citations**: All responses include source references
- **Performance Monitoring**: Built-in system performance tracking

## 🆘 **Troubleshooting**

### **Backend Not Found**
- Check if backend is running: `./manage.sh status`
- Restart system: `./manage.sh restart`
- Check logs: `./manage.sh logs`

### **Upload Failures**
- Check file format (PDF, DOCX, TXT only)
- Verify file size (under 50MB)
- Ensure backend is running

### **Search/RAG Not Working**
- Verify backend connection
- Check API key configuration
- Try simpler queries first

### **Performance Issues**
- Check system resources: `./manage.sh status`
- Restart services: `./manage.sh restart`
- Monitor logs for errors

---

**🎉 The CSRD RAG System is now fully functional with comprehensive document management, intelligent search, AI-powered question answering, and automated report generation!**