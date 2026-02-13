import ReactMarkdown from 'react-markdown';
import './Stage2.css';

function Stage2({ evaluation }) {
  if (!evaluation?.content) return null;

  return (
    <div className="evaluation-section">
      <details>
        <summary className="eval-summary">View analogy rankings</summary>
        <div className="evaluation-content markdown-content">
          <ReactMarkdown>{evaluation.content}</ReactMarkdown>
        </div>
      </details>
    </div>
  );
}

export default Stage2;
