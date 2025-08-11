import React, { useState, useEffect, useRef } from 'react';
import styles from './LiteratureReview.module.css';

interface PDFFile {
  file_hash: string;
  filename: string;
  page_count: number;
  upload_timestamp: string;
  text_length: number;
}

interface SearchResult {
  file_hash: string;
  filename: string;
  matches: Array<{
    line_number: number;
    content: string;
    context: string[];
  }>;
}

const LiteratureReview: React.FC = () => {
  const [pdfs, setPdfs] = useState<PDFFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [answerData, setAnswerData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedPdf, setSelectedPdf] = useState<string>('');
  const [showQAModal, setShowQAModal] = useState(false);
  const [selectedPdfName, setSelectedPdfName] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const API_BASE = 'http://localhost:8000/api/v1/literature';

  useEffect(() => {
    loadPDFs();
  }, []);

  const loadPDFs = async () => {
    try {
      const response = await fetch(`${API_BASE}/list-pdfs`);
      const data = await response.json();
      if (data.success) {
        setPdfs(data.pdfs);
      }
    } catch (error) {
      console.error('Error loading PDFs:', error);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
    } else {
      alert('Please select a valid PDF file');
    }
  };

  const uploadPDF = async () => {
    if (!selectedFile) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${API_BASE}/upload-pdf`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      console.log('Upload response:', data); // Debug log
      if (data.success) {
        alert('PDF uploaded successfully!');
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        loadPDFs();
      } else {
        alert('Upload failed: ' + (data.detail || data.message || 'Unknown error'));
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const searchPDFs = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const url = selectedPdf 
        ? `${API_BASE}/search?query=${encodeURIComponent(searchQuery)}&file_hash=${selectedPdf}`
        : `${API_BASE}/search?query=${encodeURIComponent(searchQuery)}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success) {
        setSearchResults(data.results);
      } else {
        alert('Search failed: ' + data.detail);
      }
    } catch (error) {
      console.error('Search error:', error);
      alert('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('question', question);
    if (selectedPdf) {
      formData.append('file_hash', selectedPdf);
    }

    try {
      const response = await fetch(`${API_BASE}/ask-question`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.success) {
        setAnswer(data.answer);
        setAnswerData(data);
      } else {
        alert('Failed to get answer: ' + data.detail);
      }
    } catch (error) {
      console.error('Question error:', error);
      alert('Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const deletePDF = async (fileHash: string) => {
    if (!confirm('Are you sure you want to delete this PDF?')) return;

    try {
      const response = await fetch(`${API_BASE}/delete/${fileHash}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      if (data.success) {
        alert('PDF deleted successfully!');
        loadPDFs();
      } else {
        alert('Delete failed: ' + data.detail);
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Delete failed');
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>📚 Literature Review Assistant</h2>
      
      {/* PDF Upload Section */}
      <div className={styles.section}>
        <h3>📄 Upload PDF</h3>
        <div className={styles.uploadArea}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            className={styles.fileInput}
          />
          <button 
            onClick={uploadPDF}
            disabled={!selectedFile || uploading}
            className={styles.uploadButton}
          >
            {uploading ? 'Uploading...' : 'Upload PDF'}
          </button>
        </div>
        {selectedFile && (
          <p className={styles.fileInfo}>Selected: {selectedFile.name}</p>
        )}
      </div>

      {/* PDF List Section */}
      <div className={styles.section}>
        <h3>📋 Uploaded PDFs</h3>
        <div className={styles.pdfList}>
          {pdfs.length === 0 ? (
            <p className={styles.emptyState}>No PDFs uploaded yet</p>
          ) : (
            pdfs.map((pdf) => (
              <div key={pdf.file_hash} className={styles.pdfItem}>
                <div className={styles.pdfInfo}>
                  <h4>{pdf.filename}</h4>
                  <p>Pages: {pdf.page_count} | Size: {Math.round(pdf.text_length / 1000)}KB</p>
                  <p>Uploaded: {new Date(pdf.upload_timestamp).toLocaleDateString()}</p>
                </div>
                <div className={styles.pdfActions}>
                                     <button
                     onClick={() => {
                       setSelectedPdf(pdf.file_hash);
                       setSelectedPdfName(pdf.filename);
                       setShowQAModal(true);
                     }}
                     className={`${styles.selectButton} ${selectedPdf === pdf.file_hash ? styles.selected : ''}`}
                   >
                     {selectedPdf === pdf.file_hash ? 'Selected' : 'Select'}
                   </button>
                  <button
                    onClick={() => deletePDF(pdf.file_hash)}
                    className={styles.deleteButton}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Search Section */}
      <div className={styles.section}>
        <h3>🔍 Search PDFs</h3>
        <div className={styles.searchArea}>
          <input
            type="text"
            placeholder="Enter search query..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
          <button 
            onClick={searchPDFs}
            disabled={!searchQuery.trim() || loading}
            className={styles.searchButton}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
        
        {searchResults.length > 0 && (
          <div className={styles.searchResults}>
            <h4>Search Results:</h4>
            {searchResults.map((result) => (
              <div key={result.file_hash} className={styles.searchResult}>
                <h5>{result.filename}</h5>
                {result.matches.map((match, index) => (
                  <div key={index} className={styles.match}>
                    <p><strong>Line {match.line_number}:</strong> {match.content}</p>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

             {/* Q&A Modal */}
       {showQAModal && (
         <div className={styles.qaModal}>
           <div className={styles.qaModalContent}>
             <div className={styles.qaModalHeader}>
               <h3 className={styles.qaModalTitle}>❓ Ask Questions about: {selectedPdfName}</h3>
               <button 
                 onClick={() => {
                   setShowQAModal(false);
                   setQuestion('');
                   setAnswer('');
                 }}
                 className={styles.closeButton}
               >
                 ×
               </button>
             </div>
             
             <div className={styles.qaArea}>
               <textarea
                 placeholder="Ask a question about this PDF..."
                 value={question}
                 onChange={(e) => setQuestion(e.target.value)}
                 className={styles.questionInput}
                 rows={4}
               />
               <button 
                 onClick={askQuestion}
                 disabled={!question.trim() || loading}
                 className={styles.askButton}
               >
                 {loading ? 'Thinking...' : 'Ask Question'}
               </button>
             </div>
             
                           {answer && (
                <div className={styles.answerArea}>
                  <h4>Answer:</h4>
                  <div className={styles.answer}>{answer}</div>
                  
                  {answerData && (
                    <div className={styles.answerMetadata}>
                      <div className={styles.confidenceBar}>
                        <span>Confidence: {Math.round(answerData.confidence * 100)}%</span>
                        <div className={styles.confidenceMeter}>
                          <div 
                            className={styles.confidenceFill} 
                            style={{width: `${answerData.confidence * 100}%`}}
                          ></div>
                        </div>
                      </div>
                      
                      {answerData.sources && answerData.sources.length > 0 && (
                        <div className={styles.sourcesSection}>
                          <h5>Sources ({answerData.sources.length}):</h5>
                          {answerData.sources.map((source: any, index: number) => (
                            <div key={index} className={styles.sourceItem}>
                              <div className={styles.sourceHeader}>
                                <span className={styles.pageNumber}>Page {source.page_number}</span>
                                <span className={styles.similarity}>Relevance: {Math.round(source.similarity * 100)}%</span>
                              </div>
                              <div className={styles.sourceContent}>{source.content}</div>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {answerData.processing_info && (
                        <div className={styles.processingInfo}>
                          <small>
                            Model: {answerData.model_used} | 
                            Chunks found: {answerData.processing_info.chunks_found} | 
                            Search method: {answerData.processing_info.search_method}
                          </small>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
           </div>
         </div>
       )}
     </div>
   );
 };

export default LiteratureReview;
