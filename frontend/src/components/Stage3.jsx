import ReactMarkdown from 'react-markdown';
import './Stage3.css';

function Stage3({ synthesis }) {
  if (!synthesis?.content) return null;

  return (
    <div className="synthesis-report">
      <div className="synthesis-content markdown-content">
        <ReactMarkdown>{synthesis.content}</ReactMarkdown>
      </div>
    </div>
  );
}

export default Stage3;
