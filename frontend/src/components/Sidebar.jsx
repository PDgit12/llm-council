import { Plus, Command, Trash2, MessageSquare, History, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import './Sidebar.css';

function Sidebar({ conversations, currentConversationId, onSelectConversation, onNewConversation, onDeleteConversation, onGoHome }) {
  const { currentUser, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Failed to log out:', error);
    }
  };

  return (
    <div className="sidebar glass-panel">
      <div className="sidebar-header">
        <div className="sidebar-brand" onClick={onGoHome} title="Return to Home">
          <div className="brand-icon-wrapper">
            <Command size={18} className="brand-icon" />
          </div>
          <span className="brand-name">Council</span>
        </div>
        <button className="new-btn glass-button" onClick={onNewConversation}>
          <Plus size={16} />
          <span>New Thread</span>
        </button>
      </div>

      <div className="sidebar-conversations">
        {conversations.length > 0 && (
          <div className="conv-section-label">
            <History size={12} />
            <span>History</span>
          </div>
        )}
        <div className="conversations-list">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conv-item ${conv.id === currentConversationId ? 'active' : ''}`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <MessageSquare size={14} className="conv-icon" />
              <span className="conv-title">{conv.title || 'Untitled Thread'}</span>
              <button
                className="conv-delete"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteConversation(conv.id);
                }}
                title="Delete"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="user-profile glass-button">
          <div className="user-avatar">{currentUser?.email?.[0]?.toUpperCase() || 'U'}</div>
          <div className="user-info">
            <div className="user-name">{currentUser?.email?.split('@')[0] || 'User'}</div>
            <div className="user-role">Council Member</div>
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Sign Out">
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
