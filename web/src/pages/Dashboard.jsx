import { useCallback, useEffect, useState } from 'react';
import Navigation from '../components/shared/Navigation';
import SessionsList from '../components/dashboard/SessionsList';
import StoryView from '../components/StoryView';
import WorldStatePanel from '../components/dashboard/WorldStatePanel';
import CreateSessionModal from '../components/dashboard/CreateSessionModal';
import { createSession, listSessions } from '../services/api';

export default function Dashboard({ token }) {
  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const loadSessions = useCallback(async () => {
    if (!token) {
      return;
    }
    setLoading(true);
    try {
      const data = await listSessions({ token });
      const items = data.sessions || data || [];
      setSessions(items);
      if (selectedSessionId) {
        const stillExists = items.some((session) => session.session_id === selectedSessionId);
        if (!stillExists) {
          setSelectedSessionId(null);
          setActiveSession(null);
        }
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  }, [token, selectedSessionId]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleSelectSession = useCallback((sessionId) => {
    setSelectedSessionId(sessionId);
    setActiveSession(null);
  }, []);

  const handleCreateSession = async (sessionData) => {
    try {
      if (!sessionData.name || !sessionData.name.trim()) {
        alert('Session name is required');
        return;
      }

      const sessionName = sessionData.name.trim();
      const seedText = sessionData.seedText && sessionData.seedText.trim() ? sessionData.seedText.trim() : '';

      const data = await createSession({ token, session_name: sessionName, seed_text: seedText });
      const session = data.session || data;

      await loadSessions();
      setShowCreateModal(false);
      if (session?.session_id) {
        setSelectedSessionId(session.session_id);
        setActiveSession(session);
      }

      alert(`Session "${sessionName}" created successfully!`);
    } catch (error) {
      console.error('Failed to create session:', error);
      const message = error?.message || 'Failed to create session';
      alert(`Failed to create session: ${message}`);
    }
  };

  const handleSessionUpdated = useCallback(
    (id, session) => {
      if (id && id === selectedSessionId && session) {
        setActiveSession(session);
      }
      loadSessions();
    },
    [loadSessions, selectedSessionId]
  );

  return (
    <div className="dashboard">
      <Navigation token={token} />

      <div className="dashboard-grid">
        <SessionsList
          sessions={sessions}
          currentSessionId={selectedSessionId}
          onSelectSession={handleSelectSession}
          onCreateSession={loadSessions}
          onShowCreateModal={() => setShowCreateModal(true)}
          token={token}
          loading={loading}
        />

        <StoryView
          sessionId={selectedSessionId}
          token={token}
          onSessionUpdated={handleSessionUpdated}
        />

        <WorldStatePanel
          world={activeSession?.world}
          sessionId={selectedSessionId}
        />
      </div>

      {showCreateModal && (
        <CreateSessionModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateSession}
        />
      )}
    </div>
  );
}
