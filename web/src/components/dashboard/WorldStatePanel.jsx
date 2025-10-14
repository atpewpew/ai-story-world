import { useState } from 'react';
import { Users, Package, MapPin, Network } from 'lucide-react';
import KnowledgeGraph from './KnowledgeGraph';

export default function WorldStatePanel({ world, sessionId }) {
  const [activeTab, setActiveTab] = useState('world');

  const characters = world?.characters || {};
  const items = world?.items || {};
  const locations = world?.locations || {};

  const hasData = Object.keys(characters).length > 0 || 
                  Object.keys(items).length > 0 || 
                  Object.keys(locations).length > 0;

  return (
    <div className="world-panel">
      <div className="panel-tabs">
        <button 
          className={`tab ${activeTab === 'world' ? 'active' : ''}`}
          onClick={() => setActiveTab('world')}
        >
          🌍 World State
        </button>
        <button 
          className={`tab ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveTab('graph')}
        >
          <Network size={16} />
          Knowledge Graph
        </button>
      </div>

      {activeTab === 'world' && (
        <div className="world-content">
          {!hasData ? (
            <div className="empty-state">
              <p>No world data yet. Start playing to see characters, items, and locations!</p>
            </div>
          ) : (
            <>
              {Object.keys(characters).length > 0 && (
                <div className="world-section">
                  <h4>
                    <Users size={16} />
                    Characters
                  </h4>
                  <div className="world-items">
                    {Object.entries(characters).map(([name, char]) => (
                      <div key={name} className="world-item">
                        <strong>{name}</strong>
                        {char.location && (
                          <div>📍 {char.location}</div>
                        )}
                        {char.items && char.items.length > 0 && (
                          <div>🎒 {char.items.join(', ')}</div>
                        )}
                        {char.description && (
                          <div className="description">{char.description}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {Object.keys(items).length > 0 && (
                <div className="world-section">
                  <h4>
                    <Package size={16} />
                    Items
                  </h4>
                  <div className="world-items">
                    {Object.entries(items).map(([name, item]) => (
                      <div key={name} className="world-item">
                        <strong>{name}</strong>
                        {item.owner && (
                          <div>👤 {item.owner}</div>
                        )}
                        {item.location && (
                          <div>📍 {item.location}</div>
                        )}
                        {item.description && (
                          <div className="description">{item.description}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {Object.keys(locations).length > 0 && (
                <div className="world-section">
                  <h4>
                    <MapPin size={16} />
                    Locations
                  </h4>
                  <div className="world-items">
                    {Object.entries(locations).map(([name, location]) => (
                      <div key={name} className="world-item">
                        <strong>{name}</strong>
                        {location.occupants && location.occupants.length > 0 && (
                          <div>👥 {location.occupants.join(', ')}</div>
                        )}
                        {location.items && location.items.length > 0 && (
                          <div>🎒 {location.items.join(', ')}</div>
                        )}
                        {location.description && (
                          <div className="description">{location.description}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'graph' && (
        <KnowledgeGraph sessionId={sessionId} world={world} />
      )}
    </div>
  );
}
