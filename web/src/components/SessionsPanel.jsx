import React from 'react';
import { Trash2, Calendar, MessageSquare } from 'lucide-react';

const SessionsPanel = ({ 
  sessions, 
  onLoadSession, 
  onDeleteSession, 
  currentSessionId,
  loading 
}) => {
  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this session?')) {
      await onDeleteSession(sessionId);
    }
  };

  if (sessions.length === 0) {
    return (
      <div className="sessions-panel">
        <h3>📚 Saved Sessions</h3>
        <div className="empty-state">
          <p>No saved sessions yet. Create your first story to get started!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="sessions-panel">
      <h3>📚 Saved Sessions</h3>
      <div className="sessions-list">
        {sessions.map((session) => (
          <div 
            key={session.session_id} 
            className={`session-item ${session.session_id === currentSessionId ? 'active' : ''}`}
            onClick={() => !loading && onLoadSession(session.session_id)}
          >
            <div className="session-header">
              <div className="session-name">{session.session_name}</div>
              <button
                className="delete-button"
                onClick={(e) => handleDeleteSession(e, session.session_id)}
                disabled={loading}
                title="Delete session"
              >
                <Trash2 size={14} />
              </button>
            </div>
            
            <div className="session-meta">
              <div className="session-date">
                <Calendar size={12} />
                {new Date(session.created_at).toLocaleDateString()}
              </div>
              <div className="session-turns">
                <MessageSquare size={12} />
                {session.history_count} turns
              </div>
            </div>
            
            {session.last_modified && (
              <div className="session-modified">
                Modified: {new Date(session.last_modified).toLocaleDateString()}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SessionsPanel;

