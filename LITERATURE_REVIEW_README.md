# 📚 Literature Review Feature

## Overview

The Literature Review feature allows users to upload PDF documents and interact with them through an AI-powered Q&A system. This is perfect for researchers, students, and professionals who need to analyze and extract insights from research papers, reports, and other PDF documents.

## 🚀 Features

### 📄 PDF Upload & Processing
- **Drag & Drop Upload**: Easy PDF file upload with drag-and-drop interface
- **Text Extraction**: Automatic extraction of text content from PDFs
- **Metadata Storage**: Stores file information, page count, and processing timestamps
- **Duplicate Detection**: Prevents processing the same file multiple times

### 🔍 Advanced Search
- **Full-Text Search**: Search across all uploaded PDFs
- **Targeted Search**: Search within specific PDF files
- **Context-Aware Results**: Shows surrounding text for better context
- **Line-by-Line Matching**: Precise location of search terms

### ❓ AI-Powered Q&A
- **Natural Language Questions**: Ask questions in plain English
- **Document-Specific Answers**: Get answers based on uploaded content
- **Multi-Document Analysis**: Ask questions across multiple PDFs
- **Intelligent Summarization**: Get document summaries and key insights

### 📋 Document Management
- **File Organization**: View all uploaded PDFs with metadata
- **Selective Analysis**: Choose specific documents for focused analysis
- **File Deletion**: Remove documents when no longer needed
- **Storage Optimization**: Efficient text storage and retrieval

## 🛠️ Technical Implementation

### Backend Architecture

#### Core Components
- **`LiteratureReviewTools`**: Main class handling PDF processing and analysis
- **`literature_router.py`**: FastAPI endpoints for all literature review operations
- **PDF Processing**: Uses PyMuPDF for reliable text extraction
- **File Management**: Secure file storage with hash-based identification

#### API Endpoints
```
POST /api/v1/literature/upload-pdf     # Upload and process PDF
GET  /api/v1/literature/list-pdfs      # List all uploaded PDFs
GET  /api/v1/literature/search         # Search PDF content
GET  /api/v1/literature/summary/{hash} # Get PDF summary
POST /api/v1/literature/ask-question   # AI Q&A functionality
DELETE /api/v1/literature/delete/{hash} # Delete PDF
```

### Frontend Components

#### React Components
- **`LiteratureReview.tsx`**: Main component with all functionality
- **`LiteratureReview.module.css`**: Modern, responsive styling
- **Navigation Integration**: Seamless integration with existing sidebar

#### User Interface Features
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Feedback**: Loading states and progress indicators
- **Error Handling**: User-friendly error messages
- **Accessibility**: Keyboard navigation and screen reader support

## 📖 Usage Guide

### Getting Started

1. **Access the Feature**
   - Start the application: `docker-compose up --build`
   - Open your browser: `http://localhost:2025`
   - Click on "📚 Literature Review" in the sidebar

2. **Upload Your First PDF**
   - Click "Choose File" or drag a PDF into the upload area
   - Click "Upload PDF" to process the document
   - Wait for the processing to complete

3. **Search Your Documents**
   - Enter your search query in the search box
   - Choose to search all PDFs or a specific document
   - Click "Search" to find relevant content
   - Review the highlighted results with context

4. **Ask Questions**
   - Type your question in the Q&A section
   - Optionally select a specific PDF to focus on
   - Click "Ask Question" to get an AI-generated answer
   - Review the detailed response based on your documents

### Advanced Usage

#### Batch Processing
- Upload multiple PDFs for comprehensive analysis
- Use the "Select" button to focus on specific documents
- Search across all documents simultaneously

#### Research Workflow
1. **Upload Research Papers**: Add all relevant PDFs to your collection
2. **Initial Search**: Use search to find specific topics or keywords
3. **Deep Analysis**: Ask detailed questions about findings and conclusions
4. **Document Management**: Organize and clean up your collection as needed

#### Collaboration Tips
- Share document collections by exporting file lists
- Use consistent naming conventions for uploaded files
- Regularly clean up old or irrelevant documents

## 🔧 Configuration

### Environment Variables
```bash
# PDF Processing
MAX_FILE_SIZE=50MB          # Maximum PDF file size
ALLOWED_EXTENSIONS=pdf      # Allowed file types
UPLOAD_DIR=data/uploads     # Upload directory

# AI Integration (Future)
AI_MODEL=gpt-4             # AI model for Q&A
AI_TEMPERATURE=0.7         # Response creativity
```

### Docker Configuration
The feature is fully integrated with the existing Docker setup:
- **Volume Mounting**: `./data:/app/data` ensures file persistence
- **Upload Directory**: Automatically created at `data/uploads/`
- **File Permissions**: Proper read/write access for file operations

## 🧪 Testing

### Manual Testing
```bash
# Test the API endpoints
python test_literature_review.py

# Test with sample PDFs
# 1. Upload a research paper
# 2. Search for key terms
# 3. Ask questions about the content
# 4. Verify responses are accurate
```

### Automated Testing
```bash
# Run backend tests
poetry run pytest tests/test_literature_review.py

# Run frontend tests
cd frontend && npm test
```

## 🚀 Future Enhancements

### Planned Features
- **AI-Powered Summarization**: Automatic document summaries
- **Citation Extraction**: Identify and extract references
- **Figure Analysis**: Process charts, graphs, and images
- **Collaborative Annotations**: Share notes and highlights
- **Export Functionality**: Export analysis results to various formats

### AI Integration Roadmap
1. **Basic Q&A**: Simple question-answering (Current)
2. **Context-Aware Responses**: Better understanding of document context
3. **Multi-Modal Analysis**: Text, tables, and figure understanding
4. **Research Synthesis**: Automatic literature review generation
5. **Citation Management**: Integration with reference managers

## 🐛 Troubleshooting

### Common Issues

#### Upload Problems
- **File Too Large**: Check file size limits in configuration
- **Invalid Format**: Ensure file is a valid PDF
- **Permission Errors**: Verify upload directory permissions

#### Search Issues
- **No Results**: Check if PDF text was extracted properly
- **Slow Performance**: Large documents may take time to process
- **Encoding Problems**: Some PDFs may have text encoding issues

#### AI Q&A Problems
- **Generic Responses**: AI model may need fine-tuning for specific domains
- **Context Issues**: Ensure relevant documents are selected
- **API Limits**: Check AI service quotas and limits

### Debug Mode
Enable debug logging for detailed troubleshooting:
```python
# In app/config/settings.py
DEBUG = True
LOG_LEVEL = "DEBUG"
```

## 📊 Performance Considerations

### Optimization Tips
- **File Size**: Keep PDFs under 50MB for optimal performance
- **Text Quality**: High-quality PDFs with selectable text work best
- **Batch Processing**: Upload multiple files during off-peak hours
- **Regular Cleanup**: Remove unused documents to free up space

### Scalability
- **Horizontal Scaling**: Multiple backend instances can share file storage
- **Caching**: Implement Redis caching for frequently accessed content
- **CDN Integration**: Use CDN for static file serving
- **Database Optimization**: Index metadata for faster searches

## 🤝 Contributing

### Development Setup
1. **Clone the repository**
2. **Install dependencies**: `poetry install`
3. **Set up environment**: Copy `env.example` to `.env`
4. **Run tests**: `poetry run pytest`
5. **Start development**: `poetry run python main.py`

### Code Standards
- **Python**: Follow PEP 8 and use type hints
- **React**: Use TypeScript and functional components
- **Testing**: Maintain >80% code coverage
- **Documentation**: Update docs for all new features

## 📄 License

This feature is part of the Docugent project and follows the same MIT license.

---

**Happy Researching! 📚✨**

For support and questions, please refer to the main project documentation or create an issue in the repository.
