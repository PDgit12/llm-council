import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage1.css';

function Stage1({ explorations }) {
  const [expandedIdx, setExpandedIdx] = useState(null);

  if (!explorations || explorations.length === 0) return null;

  const domainColors = ['domain-color-1', 'domain-color-2', 'domain-color-3', 'domain-color-4'];

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
              <div className="exploration-model">{exp.model?.split('/').pop()?.replace(':free', '')}</div>
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
