import React from 'react';
import { Play, RotateCcw, LogOut } from 'lucide-react';

const Header = ({ 
  sessionId, 
  sessionName, 
  onCreateSession, 
  onNewStory, 
  onLogout,
  loading 
}) => {
  return (
    <header className="header">
      <h1>🎭 AI Story World</h1>
      <div className="header-controls">
        {!sessionId ? (
          <div className="create-session">
            <input
              type="text"
              placeholder="Session name..."
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !loading) {
                  onCreateSession(e.target.value);
                }
              }}
              disabled={loading}
            />
            <button 
              onClick={(e) => {
                const input = e.target.previousElementSibling;
                onCreateSession(input.value);
              }} 
              disabled={loading}
            >
              <Play size={16} />
              Start Story
            </button>
          </div>
        ) : (
          <div className="session-info">
            <span>Session: {sessionName || sessionId}</span>
            <button onClick={onNewStory} disabled={loading}>
              <RotateCcw size={16} />
              New Story
            </button>
          </div>
        )}
        
        <button onClick={onLogout} className="logout-button" disabled={loading}>
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </header>
  );
};

export default Header;

