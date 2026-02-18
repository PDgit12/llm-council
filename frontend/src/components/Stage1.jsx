import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage1.css';

function Stage1({ explorations }) {
  const [expandedIdx, setExpandedIdx] = useState(null);

  if (!explorations || explorations.length === 0) return null;

  const domainColors = ['domain-color-1', 'domain-color-2', 'domain-color-3', 'domain-color-4'];

  // Map model IDs to Council Roles
  const getModelDisplay = (modelId) => {
    if (!modelId) return 'Unknown Model';
    const id = modelId.toLowerCase();

    if (id.includes('llama-3.3')) return '🏛️ The Architect';
    if (id.includes('gemini-2.0-flash-thinking')) return '🔎 The Strategist';
    if (id.includes('qwen')) return '⚙️ The Engineer';
    if (id.includes('hermes')) return '✨ The Polymath';
    if (id.includes('solar')) return '☀️ The Illuminator';
    if (id.includes('glm-4.5')) return '📜 The Scholar';
    if (id.includes('deepseek-r1')) return '🧊 The Deep Thinker';
    if (id.includes('gemma-3')) return '🧠 The Mastermind';
    if (id.includes('nemotron')) return '⚡ The Speedster';
    if (id.includes('step-3.5')) return '🎨 The Visionary';
    if (id.includes('trinity')) return '🛡️ The Guardian';

    return modelId.split('/').pop()?.replace(':free', '');
  };

  return (
    <div className="explorations-grid">
      {explorations.map((exp, idx) => (
        <div
          key={idx}
          className={`exploration-card ${domainColors[idx % 4]} ${expandedIdx === idx ? 'expanded' : ''}`}
          onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
        >
          <div className="exploration-header">
            <span className="exploration-icon">{exp.icon || '🔬'}</span>
            <div className="exploration-meta">
              <div className="exploration-domain">{exp.domain}</div>
              <div className="exploration-model">{getModelDisplay(exp.model)}</div>
            </div>
            <span className="expand-arrow">{expandedIdx === idx ? '▼' : '▶'}</span>
          </div>
          {expandedIdx === idx && exp.content && (
            <div className="exploration-body markdown-content">
              <ReactMarkdown>{exp.content}</ReactMarkdown>
            </div>
          )}
          {exp.error && (
            <div className="exploration-error">{exp.error}</div>
          )}
        </div>
      ))}
    </div>
  );
}

export default Stage1;
