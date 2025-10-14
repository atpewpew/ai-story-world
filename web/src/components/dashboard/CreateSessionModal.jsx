import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Wand2, Rocket, Search, Sparkles } from 'lucide-react';

export default function CreateSessionModal({ onClose, onCreate }) {
  const [sessionName, setSessionName] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [customSeed, setCustomSeed] = useState('');

  const templates = [
    {
      id: 'fantasy',
      name: 'Fantasy Quest',
      description: 'Embark on an epic adventure in a magical realm',
      icon: <Wand2 size={20} />,
      seed: 'You are a brave adventurer in a mystical forest. Ancient magic flows through the trees, and mysterious creatures lurk in the shadows.'
    },
    {
      id: 'scifi',
      name: 'Sci-Fi Adventure',
      description: 'Explore the cosmos and futuristic worlds',
      icon: <Rocket size={20} />,
      seed: 'You are aboard a starship exploring the galaxy. Your mission is to discover new worlds and encounter alien civilizations.'
    },
    {
      id: 'mystery',
      name: 'Mystery Detective',
      description: 'Solve puzzles and uncover hidden secrets',
      icon: <Search size={20} />,
      seed: 'You are a detective investigating a mysterious case. Clues are scattered throughout the city, and time is running out.'
    }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!sessionName.trim()) {
      alert('Please enter a session name');
      return;
    }

    const seedText = selectedTemplate ? 
      templates.find(t => t.id === selectedTemplate)?.seed : 
      customSeed;

    const sessionData = {
      name: sessionName.trim(),
      seedText: seedText && seedText.trim() ? seedText.trim() : undefined
    };

    console.log('CreateSessionModal sending data:', sessionData);
    onCreate(sessionData);
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
          className="create-session-modal"
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="modal-header">
            <h2>🎭 Create New Story</h2>
            <button onClick={onClose} className="close-button">
              <X size={20} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="modal-content">
            <div className="form-group">
              <label htmlFor="sessionName">Session Name</label>
              <input
                id="sessionName"
                type="text"
                placeholder="My Amazing Adventure"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label>Choose a Template (Optional)</label>
              <div className="template-grid">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className={`template-card ${selectedTemplate === template.id ? 'selected' : ''}`}
                    onClick={() => {
                      setSelectedTemplate(template.id);
                      setCustomSeed('');
                    }}
                  >
                    <div className="template-icon">{template.icon}</div>
                    <h4>{template.name}</h4>
                    <p>{template.description}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="customSeed">Custom Story Seed (Optional)</label>
              <textarea
                id="customSeed"
                placeholder="Describe your world, character, or starting situation..."
                value={customSeed}
                onChange={(e) => {
                  setCustomSeed(e.target.value);
                  setSelectedTemplate('');
                }}
                rows={3}
              />
            </div>

            <div className="modal-actions">
              <button type="button" onClick={onClose} className="btn-secondary">
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={!sessionName.trim()}>
                <Sparkles size={16} />
                Create & Begin
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
