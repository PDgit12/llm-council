import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Paperclip, X, FileText, Sparkles, Zap, Brain, Globe, Search, ArrowUp, CheckCircle, Loader2 } from 'lucide-react';
import { api } from '../api';
import './ChatInterface.css';

// Import Stages
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';

function ChatInterface({ conversation, onSendMessage, isLoading }) {
  const [input, setInput] = useState('');
  const [files, setFiles] = useState([]);
  const [activeModels, setActiveModels] = useState({});
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages]);

  const handleFileSelect = async (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length === 0) return;

    try {
      // Upload each file
      const uploadPromises = selectedFiles.map(file => api.uploadFile(file));
      const results = await Promise.all(uploadPromises);

      setFiles(prev => [...prev, ...results]);
    } catch (err) {
      console.error("Upload failed", err);
    }
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if ((!input.trim() && files.length === 0) || isLoading) return;

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
  };

  if (!conversation && isLoading) return (
    <div className="chat-loading">
      <div className="loading-spinner"></div>
      <p>Consulting history...</p>
    </div>
  );

  if (!conversation) return (
    <div className="chat-loading inactive">
      <div className="empty-content">
        <h2 className="empty-title">Welcome, Council Member</h2>
        <p className="empty-subtitle">Select a thread from the sidebar or start a new one to begin.</p>
      </div>
    </div>
  );

  const isEmpty = conversation.messages?.length === 0;

  return (
    <div className="chat-interface">
      <div className="messages-area">
        {isEmpty && (
          <div className="empty-state animate-fade-in">
            <div className="empty-content">
              <div className="empty-icon-wrapper">
                <Sparkles size={32} className="empty-icon-main" />
              </div>
              <h2 className="empty-title">Good Afternoon</h2>
              <p className="empty-subtitle">Ready to convene the Council?</p>
            </div>

            <div className="example-cards">
              <div className="example-card glass-panel" onClick={() => handleExampleClick("Analyze these quarterly reports for trends")}>
                <div className="card-icon"><Zap size={20} /></div>
                <div className="card-content">
                  <div className="card-title">Analyze quarterly reports</div>
                  <div className="card-desc">Identify key trends & anomalies</div>
                </div>
              </div>
              <div className="example-card glass-panel" onClick={() => handleExampleClick("Debug this React component performance issue")}>
                <div className="card-icon"><Zap size={20} /></div>
                <div className="card-content">
                  <div className="card-title">Debug React performance</div>
                  <div className="card-desc">Optimize render cycles</div>
                </div>
              </div>
              <div className="example-card glass-panel" onClick={() => handleExampleClick("Compare marketing strategies for a SaaS launch")}>
                <div className="card-icon"><Globe size={20} /></div>
                <div className="card-content">
                  <div className="card-title">SaaS launch strategies</div>
                  <div className="card-desc">Market analysis & growth</div>
                </div>
              </div>
              <div className="example-card glass-panel" onClick={() => handleExampleClick("Explain quantum entanglement to a 5 year old")}>
                <div className="card-icon"><Brain size={20} /></div>
                <div className="card-content">
                  <div className="card-title">Explain quantum physics</div>
                  <div className="card-desc">Simplify complex topics</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {conversation.messages?.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role} animate-fade-in`}>
            {msg.role === 'user' ? (
              <div className="user-bubble glass-panel">
                {msg.attachments && msg.attachments.length > 0 && (
                  <div className="message-attachments">
                    {msg.attachments.map((att, i) => (
                      <div key={i} className="attachment-chip">
                        <Paperclip size={12} /> {att.name || 'File'}
                      </div>
                    ))}
                  </div>
                )}
                <div className="message-text">{msg.content}</div>
              </div>
            ) : (
              <div className="assistant-response">
                <div className="response-header">
                  <div className="assistant-avatar">
                    <div className="avatar-icon">⌘</div>
                  </div>
                  <span className="assistant-name">Council</span>
                </div>

                {/* COUNCIL MONITOR: Real-time Multi-Agent Activity */}
                <CouncilMonitor activeModels={msg.model_activity || activeModels} isProcessing={msg.isProcessing} />

                {/* Deliberation Stages (Visible while thinking) */}
                <div className="deliberation-stages">
                  {/* Stage 1: Exploration */}
                  {msg.stage1 && (
                    <div className="deliberation-block">
                      <div className="deliberation-label">
                        <CheckCircle size={14} className="success-icon" /> Stage 1: Exploration
                      </div>
                      <Stage1 explorations={Object.entries(msg.stage1).map(([model, result]) => ({
                        model,
                        content: result?.content,
                        domain: 'Research Angle',
                        icon: '🔬'
                      }))} />
                    </div>
                  )}

                  {/* Stage 2: Grounding */}
                  {msg.stage2 && (
                    <div className="deliberation-block">
                      <div className="deliberation-label">
                        <CheckCircle size={14} className="success-icon" /> Stage 2: Grounding & Verification
                      </div>
                      {Object.values(msg.stage2).map((eval_data, i2) => (
                        <Stage2 key={i2} evaluation={eval_data} />
                      ))}
                    </div>
                  )}

                  {/* Stage 3: Technical Tasking */}
                  {msg.stage3 && Object.keys(msg.stage3).length > 0 && (
                    <div className="deliberation-block">
                      <div className="deliberation-label">
                        <CheckCircle size={14} className="success-icon" /> Stage 3: Technical Specifications
                      </div>
                      <Stage3 result={msg.stage3} />
                    </div>
                  )}

                  {/* Active Loading Indicator */}
                  {!msg.final_answer && (
                    <div className="processing-indicator">
                      <Loader2 size={16} className="animate-spin" />
                      <span className="thinking-text">
                        {msg.loading?.stage1 ? "Exploring angles..." :
                          msg.loading?.stage2 ? "Verifying claims..." :
                            msg.loading?.stage3 ? "Generating specs..." :
                              msg.loading?.stage4 ? "Cross-pollinating ideas..." :
                                msg.loading?.stage5 ? "Council debating..." : "Finalizing consensus..."}
                      </span>
                    </div>
                  )}
                </div>

                {/* Final Answer */}
                {msg.final_answer && (
                  <div className="markdown-content final-consens-bubble">
                    <ReactMarkdown>{msg.final_answer}</ReactMarkdown>
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
        <form className="input-wrapper glass-panel" onSubmit={handleSubmit}>
          <div className="input-top">
            <input
              type="text"
              className="message-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask the Council..."
              disabled={isLoading}
              autoFocus
            />
          </div>

          {files.length > 0 && (
            <div className="file-chips animate-fade-in">
              {files.map((file, i) => {
                const isPdf = file.content_type === 'application/pdf';
                return (
                  <div key={i} className="file-chip glass-button">
                    {isPdf ? (
                      <div className="pdf-icon-wrapper">
                        <span className="pdf-ext">PDF</span>
                      </div>
                    ) : (
                      <FileText size={14} className="file-icon" />
                    )}
                    <span className="file-name" title={file.filename}>
                      {file.filename.length > 15 ? file.filename.substring(0, 15) + '...' : file.filename}
                    </span>
                    <button type="button" className="remove-file" onClick={() => removeFile(i)}>
                      <X size={12} />
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          <div className="input-bottom">
            <div className="input-tools">
              <input
                type="file"
                multiple
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={handleFileSelect}
                disabled={isLoading}
              />
              <button
                type="button"
                className="tool-btn"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
                title="Attach files"
              >
                <Paperclip size={18} />
              </button>
              <button type="button" className="tool-btn" title="Search Mode">
                <Search size={18} />
              </button>
            </div>

            <button
              type="submit"
              className={`send-btn ${input.trim() || files.length > 0 ? 'ready' : ''}`}
              disabled={(!input.trim() && files.length === 0) || isLoading}
            >
              {isLoading ? (
                <span className="send-spinner"></span>
              ) : (
                <ArrowUp size={20} />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const CouncilMonitor = ({ activeModels, isProcessing }) => {
  if (!activeModels || Object.keys(activeModels).length === 0) return null;

  return (
    <div className="council-monitor glass-panel animate-fade-in">
      <div className="monitor-header">
        <div className="monitor-title">
          <Brain size={16} className="monitor-icon" />
          <span>MISSION CONTROL</span>
        </div>
        <div className="monitor-status">
          <span className="pulse-dot"></span>
          LIVE ORACLE LATTICE
        </div>
      </div>

      <div className="agent-grid">
        {Object.entries(activeModels).map(([model, status]) => {
          const isThinking = status === "started";
          const isComplete = status === "completed";
          const hasFailed = status === "failed";

          // Clean up model name for display
          const shortName = model.split('/').pop()
            .replace('deepseek-r1', 'DeepSeek R1')
            .replace('gemini-2.0-flash-thinking-exp:free', 'Gemini 2.0 Flash')
            .replace('gemini-2.0-flash-exp:free', 'Gemini 2.0')
            .replace('step-3.5-flash:free', 'StepFun 3.5')
            .replace('qwen-2.5-coder-32b-instruct:free', 'Qwen Coder')
            .replace('meta-llama-3.3-70b-instruct:free', 'Llama 3.3')
            .replace(':free', '');

          // Assign icons based on model family
          let AgentIcon = Zap;
          if (model.includes('deepseek')) AgentIcon = Brain;
          if (model.includes('gemini')) AgentIcon = Sparkles;
          if (model.includes('qwen')) AgentIcon = FileText;
          if (model.includes('llama')) AgentIcon = Globe;

          return (
            <div key={model} className={`agent-card ${status} ${isThinking ? 'thinking' : ''}`}>
              <div className="agent-header">
                <AgentIcon size={14} className="agent-icon" />
                <span className="agent-name">{shortName}</span>
              </div>
              <div className="agent-status-line">
                {isThinking && (
                  <div className="status-badge thinking">
                    <Loader2 size={10} className="animate-spin" />
                    <span>Processing</span>
                  </div>
                )}
                {isComplete && (
                  <div className="status-badge complete">
                    <CheckCircle size={10} />
                    <span>Complete</span>
                  </div>
                )}
                {hasFailed && (
                  <div className="status-badge failed">
                    <X size={10} />
                    <span>Failed</span>
                  </div>
                )}
              </div>
              {isThinking && <div className="pulse-ring"></div>}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ChatInterface;
