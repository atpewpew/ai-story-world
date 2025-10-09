import React, { useState, useEffect } from 'react';
import { Play, Save, RotateCcw, Users, MapPin, Package } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [sessionName, setSessionName] = useState('');
  const [history, setHistory] = useState([]);
  const [world, setWorld] = useState({ characters: {}, items: {}, locations: {} });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      // This would be a real endpoint to list sessions
      const response = await fetch(`${API_BASE}/list_sessions`);
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const createSession = async () => {
    if (!sessionName.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/create_session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_name: sessionName })
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        setHistory([{ turn_id: 0, actor: 'ai', text: 'Welcome to your story!', timestamp: new Date().toISOString() }]);
        setWorld({ characters: {}, items: {}, locations: {} });
        loadSessions();
      }
    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSession = async (id) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/get_session?session_id=${id}`);
      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        setHistory(data.history || []);
        setWorld(data.world || { characters: {}, items: {}, locations: {} });
      }
    } catch (error) {
      console.error('Failed to load session:', error);
    } finally {
      setLoading(false);
    }
  };

  const takeAction = async () => {
    if (!input.trim() || !sessionId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/take_action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          player_action: input,
          options: { use_rag: true }
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setHistory(prev => [...prev, 
          { turn_id: data.turn_id, actor: 'ai', text: data.ai_response, timestamp: new Date().toISOString() }
        ]);
        setInput('');
        // Reload session to get updated world state
        loadSession(sessionId);
      }
    } catch (error) {
      console.error('Failed to take action:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      takeAction();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎭 AI Story World</h1>
        <div className="header-controls">
          {!sessionId ? (
            <div className="create-session">
              <input
                type="text"
                placeholder="Session name..."
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <button onClick={createSession} disabled={loading || !sessionName.trim()}>
                <Play size={16} />
                Start Story
              </button>
            </div>
          ) : (
            <div className="session-info">
              <span>Session: {sessionId}</span>
              <button onClick={() => setSessionId(null)}>
                <RotateCcw size={16} />
                New Story
              </button>
            </div>
          )}
        </div>
      </header>

      <div className="main-content">
        <div className="story-panel">
          <div className="story-history">
            {history.map((entry, index) => (
              <div key={index} className={`story-entry ${entry.actor}`}>
                <div className="entry-header">
                  <span className="actor">{entry.actor === 'ai' ? '🤖 AI' : '👤 You'}</span>
                  <span className="timestamp">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                </div>
                <div className="entry-text">{entry.text}</div>
              </div>
            ))}
          </div>
          
          {sessionId && (
            <div className="input-section">
              <input
                type="text"
                placeholder="What do you want to do?"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={loading}
              />
              <button onClick={takeAction} disabled={loading || !input.trim()}>
                {loading ? '...' : 'Send'}
              </button>
            </div>
          )}
        </div>

        <div className="world-panel">
          <h3>🌍 World State</h3>
          
          <div className="world-section">
            <h4><Users size={16} /> Characters</h4>
            <div className="world-items">
              {Object.entries(world.characters || {}).map(([name, char]) => (
                <div key={name} className="world-item">
                  <strong>{name}</strong>
                  {char.location && <div>📍 {char.location}</div>}
                  {char.items && char.items.length > 0 && (
                    <div>🎒 {char.items.join(', ')}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="world-section">
            <h4><Package size={16} /> Items</h4>
            <div className="world-items">
              {Object.entries(world.items || {}).map(([name, item]) => (
                <div key={name} className="world-item">
                  <strong>{name}</strong>
                  {item.owner && <div>👤 {item.owner}</div>}
                </div>
              ))}
            </div>
          </div>

          <div className="world-section">
            <h4><MapPin size={16} /> Locations</h4>
            <div className="world-items">
              {Object.entries(world.locations || {}).map(([name, location]) => (
                <div key={name} className="world-item">
                  <strong>{name}</strong>
                  {location.occupants && location.occupants.length > 0 && (
                    <div>👥 {location.occupants.join(', ')}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="sessions-panel">
        <h3>📚 Saved Sessions</h3>
        <div className="sessions-list">
          {sessions.map((session) => (
            <div key={session.id} className="session-item" onClick={() => loadSession(session.id)}>
              <div className="session-name">{session.name}</div>
              <div className="session-date">{new Date(session.created_at).toLocaleDateString()}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
