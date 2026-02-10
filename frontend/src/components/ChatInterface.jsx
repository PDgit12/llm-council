import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { api, API_BASE_URL } from '../api';
import FileUploader from './FileUploader';
import TestCaseManager from './TestCaseManager';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import './ChatInterface.css';

export default function ChatInterface({
  conversation,
  onSendMessage,
  onAddTestCase,
  onDeleteTestCase,
  isLoading,
}) {
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleFileSelect = async (file) => {
    try {
      // Optimistic UI could be added here
      const uploaded = await api.uploadFile(file);
      setAttachments(prev => [...prev, uploaded]);
    } catch (err) {
      console.error("Upload failed", err);
      alert("Failed to upload file");
    }
  };

  const removeAttachment = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if ((input.trim() || attachments.length > 0) && !isLoading) {
      onSendMessage(input, attachments);
      setInput('');
      setAttachments([]);
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="empty-state">
          <h2>Welcome to LLM Council</h2>
          <p>Create a new conversation to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      <div className="messages-container">
        <TestCaseManager
          conversation={conversation}
          onAddTestCase={onAddTestCase}
          onDeleteTestCase={onDeleteTestCase}
        />

        {conversation.messages.length === 0 ? (
          <div className="empty-state">
            <h2>{conversation?.test_cases?.length > 0 ? "Prompt Optimization Lab" : "Welcome to LLM Council"}</h2>
            <p>
              {conversation?.test_cases?.length > 0
                ? "Enter your task below to generate optimized prompts vetted against your test cases."
                : "Ask a question and get a peer-reviewed answer from the council."}
            </p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === 'user' ? (
                <div className="user-message">
                  <div className="message-label">You</div>
                  <div className="message-content">
                    {msg.attachments && msg.attachments.length > 0 && (
                      <div className="message-attachments">
                        {msg.attachments.map((att, i) => (
                          <div key={i} className="attachment-preview">
                            {att.content_type?.startsWith('image/') ? (
                              <img src={`${API_BASE_URL}${att.path}`} alt={att.filename} />
                            ) : (
                              <div className="file-icon">📄 {att.filename}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="markdown-content">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="assistant-message">
                  <div className="message-label">LLM Council</div>

                  {/* Stage 1 */}
                  {msg.loading?.stage1 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 1: Collecting individual responses...</span>
                    </div>
                  )}
                  {msg.stage1 && <Stage1 responses={msg.stage1} />}

                  {/* Stage 2 */}
                  {msg.loading?.stage2 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 2: Peer rankings...</span>
                    </div>
                  )}
                  {msg.stage2 && (
                    <Stage2
                      rankings={msg.stage2}
                      labelToModel={msg.metadata?.label_to_model}
                      aggregateRankings={msg.metadata?.aggregate_rankings}
                    />
                  )}

                  {/* Stage 3 */}
                  {msg.loading?.stage3 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 3: Final synthesis...</span>
                    </div>
                  )}
                  {msg.stage3 && <Stage3 finalResponse={msg.stage3} />}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Consulting the council...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        {attachments.length > 0 && (
          <div className="input-attachments">
            {attachments.map((att, i) => (
              <div key={i} className="attachment-chip">
                <span>{att.filename}</span>
                <button type="button" onClick={() => removeAttachment(i)}>×</button>
              </div>
            ))}
          </div>
        )}
        <div className="input-wrapper">
          <FileUploader onFileSelect={handleFileSelect} disabled={isLoading} />
          <textarea
            className="message-input"
            placeholder={conversation?.test_cases?.length > 0 ? "Describe the task to optimize..." : "Ask your question... (Shift+Enter for new line, Enter to send)"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={3}
          />
        </div>
        <button
          type="submit"
          className="send-button"
          disabled={(!input.trim() && attachments.length === 0) || isLoading}
        >
          Send
        </button>
      </form>
    </div >
  );
}
