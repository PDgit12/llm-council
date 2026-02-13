import './Sidebar.css';

import './Sidebar.css';

function Sidebar({ conversations, currentConversationId, onSelectConversation, onNewConversation, onDeleteConversation, onGoHome }) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand" onClick={onGoHome} title="Return to Home">
          <span className="brand-icon">⌘</span>
          <span className="brand-name">Council</span>
        </div>
        <button className="new-btn" onClick={onNewConversation}>
          New Thread
        </button>
      </div>

      <div className="sidebar-conversations">
        {conversations.length > 0 && <div className="conv-section-label">History</div>}
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`conv-item ${conv.id === currentConversationId ? 'active' : ''}`}
            onClick={() => onSelectConversation(conv.id)}
          >
            <span className="conv-title">{conv.title || 'Untitled Thread'}</span>
            <button
              className="conv-delete"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteConversation(conv.id);
              }}
              title="Delete"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">J</div>
          <div className="user-name">Jason</div>
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
