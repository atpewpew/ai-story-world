import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send } from 'lucide-react';
import { api } from '../../services/api';

export default function DemoModal({ onClose }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    setLoading(true);
    setError('');
    
    try {
      const result = await api.demoAction(input.trim());
      setResponse(result);
      setInput('');
    } catch (err) {
      setError(`Demo failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleOptionClick = async (option) => {
    setLoading(true);
    setError('');
    
    try {
      const result = await api.demoAction(option);
      setResponse(result);
    } catch (err) {
      setError(`Demo failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        className="modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          className="demo-modal"
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="modal-header">
            <h2>🎭 Try AI Story World</h2>
            <button onClick={onClose} className="close-button">
              <X size={20} />
            </button>
          </div>

          <div className="modal-content">
            {!response ? (
              <div className="demo-start">
                <p>Experience the magic of AI storytelling! Type an action to begin your adventure.</p>
                <form onSubmit={handleSubmit} className="demo-form">
                  <input
                    type="text"
                    placeholder="What do you want to do? (e.g., 'Look around', 'Open the door')"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={loading}
                    autoFocus
                  />
                  <button type="submit" disabled={loading || !input.trim()}>
                    {loading ? <div className="spinner" /> : <Send size={16} />}
                    {loading ? 'Generating...' : 'Start Adventure'}
                  </button>
                </form>
              </div>
            ) : (
              <div className="demo-story">
                <div className="story-response">
                  <p>{response.ai_response}</p>
                </div>
                
                {response.options && response.options.length > 0 && (
                  <div className="demo-options">
                    <p>Choose your next action:</p>
                    {response.options.map((option, i) => (
                      <button
                        key={i}
                        className="demo-option-btn"
                        onClick={() => handleOptionClick(option)}
                        disabled={loading}
                      >
                        <span className="option-key">{['A', 'B', 'C'][i]}</span>
                        {option}
                      </button>
                    ))}
                  </div>
                )}
                
                <div className="demo-actions">
                  <button onClick={() => setResponse(null)} className="btn-secondary">
                    Try Again
                  </button>
                  <button onClick={() => window.location.href = '/login'} className="btn-primary">
                    Start Full Adventure
                  </button>
                </div>
              </div>
            )}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
