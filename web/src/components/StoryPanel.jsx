import React, { useEffect, useRef } from 'react';
import { Send } from 'lucide-react';

const StoryPanel = ({ 
  history, 
  onTakeAction, 
  loading, 
  input, 
  setInput 
}) => {
  const historyEndRef = useRef(null);

  const scrollToBottom = () => {
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [history]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onTakeAction(input.trim());
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="story-panel">
      <div className="story-history">
        {history.length === 0 ? (
          <div className="empty-state">
            <h3>Welcome to your story!</h3>
            <p>Start by creating a new session or loading an existing one.</p>
          </div>
        ) : (
          history.map((entry, index) => (
            <div key={index} className={`story-entry ${entry.actor}`}>
              <div className="entry-header">
                <span className="actor">
                  {entry.actor === 'ai' ? '🤖 AI' : '👤 You'}
                </span>
                <span className="timestamp">
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="entry-text">{entry.text}</div>
            </div>
          ))
        )}
        <div ref={historyEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="input-section">
        <input
          type="text"
          placeholder="What do you want to do?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? (
            <div className="spinner" />
          ) : (
            <>
              <Send size={16} />
              Send
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default StoryPanel;

