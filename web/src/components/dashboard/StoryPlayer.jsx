import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send } from 'lucide-react';
import { api } from '../../services/api';

export default function StoryPlayer({ session, token, onSessionUpdate }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const historyEndRef = useRef(null);
  
  useEffect(() => {
    if (session) {
      setHistory(session.history || []);
    }
  }, [session]);
  
  useEffect(() => {
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);
  
  const handleAction = async (action) => {
    if (!session || loading) return;
    
    setLoading(true);
    try {
      const result = await api.takeAction(token, session.session_id, action);
      
      // Add player and AI entries
      setHistory(prev => [
        ...prev,
        { actor: 'player', text: action, timestamp: new Date().toISOString() },
        { 
          actor: 'ai', 
          text: result.ai_response, 
          options: result.options,
          timestamp: new Date().toISOString() 
        }
      ]);
      
      setInput('');
      
      // Update session data
      if (onSessionUpdate) {
        onSessionUpdate();
      }
    } catch (error) {
      console.error('Action failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAction(input);
    }
    // Keyboard shortcuts for options
    if (e.key === 'a' || e.key === 'b' || e.key === 'c') {
      const lastEntry = history[history.length - 1];
      if (lastEntry?.options) {
        const index = { a: 0, b: 1, c: 2 }[e.key];
        if (lastEntry.options[index]) {
          handleAction(lastEntry.options[index]);
        }
      }
    }
  };
  
  return (
    <div className="story-player">
      <div className="story-history">
        {history.length === 0 ? (
          <div className="empty-state">
            <h3>Welcome to your story!</h3>
            <p>Start by creating a new session or loading an existing one from the left panel.</p>
          </div>
        ) : (
          <AnimatePresence>
            {history.map((entry, index) => (
              <motion.div
                key={index}
                className={`story-entry ${entry.actor}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <div className="entry-header">
                  <span className="actor">
                    {entry.actor === 'ai' ? '🤖 AI' : '👤 You'}
                  </span>
                  <span className="timestamp">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="entry-text">{entry.text}</div>
                
                {entry.options && entry.options.length > 0 && (
                  <div className="action-options">
                    {entry.options.map((option, i) => (
                      <button
                        key={i}
                        className="option-btn"
                        onClick={() => handleAction(option)}
                        disabled={loading}
                      >
                        <span className="option-key">{['A', 'B', 'C'][i]}</span>
                        {option}
                      </button>
                    ))}
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        )}
        <div ref={historyEndRef} />
      </div>
      
      {session && (
        <div className="story-input">
          <input
            type="text"
            placeholder="Type your action or press A/B/C..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <button onClick={() => handleAction(input)} disabled={loading || !input.trim()}>
            {loading ? <div className="spinner" /> : <Send size={20} />}
          </button>
        </div>
      )}
    </div>
  );
}
