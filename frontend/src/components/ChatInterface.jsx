import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import FileUploader from './FileUploader';
import { api } from '../api';
import './ChatInterface.css';

function ChatInterface({ conversation, onSendMessage, isLoading }) {
  const [input, setInput] = useState('');
  const [files, setFiles] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages]);

  const handleFileSelect = async (file) => {
    try {
      // Upload to backend to get a path/url
      // OR convert to base64 to send in message payload.
      // Given council.py structure, sending base64 in payload is cleaner for the "stateless" orchestrator,
      // but main.py has an /api/upload endpoint.
      // Let's use the /api/upload endpoint for better performance (not bloating JSON).

      const result = await api.uploadFile(file);
      // Result should be { path: "/uploads/...", filename: "...", ... }
      setFiles(prev => [...prev, result]);
    } catch (err) {
      console.error("Upload failed", err);
      alert("Failed to upload file.");
    }
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if ((!input.trim() && files.length === 0) || isLoading) return;

    // Pass input AND attachments
    // We expect onSendMessage to handle the payload construction
    // OR we modify onSendMessage signature.
    // Looking at App.jsx (likely parent), it calls api.sendMessageStream.
    // We should pass an object or arguments. 
    // Let's assume onSendMessage takes (text, attachments).

    const attachments = files.map(f => ({
      path: f.path,
      content_type: f.content_type,
      name: f.filename
    }));

    onSendMessage(input, attachments);

    setInput('');
    setFiles([]);
  };

  const handleExampleClick = (text) => {
    setInput(text);
    // Optional: Auto-send or just populate
    // onSendMessage(text, []); 
  };

  if (!conversation) return <div className="chat-loading">Loading...</div>;

  const isEmpty = conversation.messages?.length === 0;

  // Helper to determine the loading text based on active stage
  const getLoadingText = (loadingState) => {
    if (!loadingState) return "Thinking...";
    if (loadingState.stage1) return "Deconstructing query...";
    if (loadingState.stage2) return "Exploring cross-domain analogies...";
    if (loadingState.stage3) return "Mapping structural similarities...";
    if (loadingState.stage4) return "Synthesizing insights...";
    return "Thinking...";
  };

  return (
    <div className="chat-interface">
      <div className="messages-area">
        {isEmpty && (
          <div className="empty-state">
            <div className="empty-content">
              <div className="empty-icon">⌘</div>
              <h2 className="empty-title">Parallels</h2>
              <p className="empty-subtitle">Unlock breakthrough insights with cross-domain thinking.</p>
            </div>

            <div className="example-cards">
              <div className="example-card" onClick={() => handleExampleClick("Analyze these quarterly reports for trends")}>
                <div className="card-icon">📊</div>
                <div className="card-title">Analyze quarterly reports</div>
              </div>
              <div className="example-card" onClick={() => handleExampleClick("Debug this React component performance issue")}>
                <div className="card-icon">🐞</div>
                <div className="card-title">Debug React performance</div>
              </div>
              <div className="example-card" onClick={() => handleExampleClick("Compare marketing strategies for a SaaS launch")}>
                <div className="card-icon">🚀</div>
                <div className="card-title">SaaS launch strategies</div>
              </div>
              <div className="example-card" onClick={() => handleExampleClick("Explain quantum entanglement to a 5 year old")}>
                <div className="card-icon">⚛️</div>
                <div className="card-title">Explain quantum physics</div>
              </div>
            </div>
          </div>
        )}

        {conversation.messages?.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.role === 'user' ? (
              <div className="user-bubble">
                {msg.attachments && msg.attachments.length > 0 && (
                  <div className="message-attachments">
                    {msg.attachments.map((att, i) => (
                      <div key={i} className="attachment-chip">
                        📎 {att.name || 'File'}
                      </div>
                    ))}
                  </div>
                )}
                <div>{msg.content}</div>
              </div>
            ) : (
              <div className="assistant-response">
                {/* Only show the final answer or a clean loading state */}
                {msg.final_answer ? (
                  <div className="markdown-content">
                    <ReactMarkdown>{msg.final_answer}</ReactMarkdown>
                  </div>
                ) : (
                  /* Robust loading text if no final answer yet */
                  <div className="processing-indicator">
                    <span className="stage-spinner" />
                    <span className="processing-text">{getLoadingText(msg.loading)}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Floating Input Area */}
      <div className="input-area">
        <form className="input-wrapper" onSubmit={handleSubmit}>
          {/* Top: Text Input */}
          <div className="input-top">
            <input
              type="text"
              className="message-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything..."
              disabled={isLoading}
              autoFocus
            />
          </div>

          {/* Middle: File Chips (if any) */}
          {files.length > 0 && (
            <div className="file-chips">
              {files.map((file, i) => (
                <div key={i} className="file-chip">
                  <span className="file-icon">📄</span>
                  <span className="file-name">{file.filename.substring(0, 15)}...</span>
                  <button type="button" className="remove-file" onClick={() => removeFile(i)}>×</button>
                </div>
              ))}
            </div>
          )}

          {/* Bottom: Tools & Send */}
          <div className="input-bottom">
            <div className="input-tools">
              <FileUploader onFileSelect={handleFileSelect} disabled={isLoading} />
              {/* Mock focus selector */}
              <button type="button" className="tool-btn" title="Search Mode">
                <span>Writing Styles</span>
                <svg width="10" height="6" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                <div style={{ width: '24px', height: '14px', background: '#8b5cf6', borderRadius: '10px', position: 'relative' }}>
                  <div style={{ width: '10px', height: '10px', background: 'white', borderRadius: '50%', position: 'absolute', right: '2px', top: '2px' }}></div>
                </div>
                <span>Citation</span>
              </div>
            </div>

            <button
              type="submit"
              className="send-btn"
              disabled={(!input.trim() && files.length === 0) || isLoading}
            >
              {isLoading ? (
                <span className="send-spinner">⟳</span>
              ) : (
                '↑'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ChatInterface;
