import { Trash2, Calendar, MessageSquare, Plus } from 'lucide-react';
import { api } from '../../services/api';

export default function SessionsList({ 
  sessions, 
  onSelectSession, 
  onDeleteSession, 
  currentSessionId,
  loading,
  onCreateSession,
  onShowCreateModal
}) {

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this session?')) {
      try {
        await api.deleteSession(sessionId);
        if (onDeleteSession) {
          await onDeleteSession(sessionId);
        }
        if (onCreateSession) {
          onCreateSession();
        }
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    }
  };


  return (
    <div className="sessions-panel">
      <div className="sessions-header">
        <h3>📚 Saved Sessions</h3>
        <button 
          onClick={onShowCreateModal}
          className="create-session-btn"
          disabled={loading}
        >
          <Plus size={16} />
          New
        </button>
      </div>
      
      <div className="sessions-list">
        {sessions.length === 0 ? (
          <div className="empty-state">
            <p>No saved sessions yet. Create your first story to get started!</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div 
              key={session.session_id} 
              className={`session-item ${session.session_id === currentSessionId ? 'active' : ''}`}
              onClick={() => !loading && onSelectSession && onSelectSession(session.session_id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if ((e.key === 'Enter' || e.key === ' ') && !loading) {
                  e.preventDefault();
                  onSelectSession && onSelectSession(session.session_id);
                }
              }}
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
          ))
        )}
      </div>
    </div>
  );
}
