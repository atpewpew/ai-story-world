import { useCallback, useEffect, useMemo, useState } from 'react';
import { getSession as getSessionApi, startStory, takeAction as takeActionApi } from '../services/api';

export default function StoryView({ sessionId, token, onSessionUpdated }) {
  const [session, setSession] = useState(null);
  const [loadingSession, setLoadingSession] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [input, setInput] = useState('');
  const [error, setError] = useState(null);

  const history = useMemo(() => session?.history || [], [session]);

  const loadSession = useCallback(
    async (id = sessionId) => {
      if (!id || !token) {
        return;
      }
      setLoadingSession(true);
      setError(null);
      try {
        const data = await getSessionApi({ token, session_id: id });
        const resolved = data.session || data;
        setSession(resolved);
        setInput('');
        if (onSessionUpdated) {
          onSessionUpdated(id, resolved);
        }
      } catch (err) {
        const message = err?.message || 'Failed to load session';
        setError(message);
      } finally {
        setLoadingSession(false);
      }
    },
    [onSessionUpdated, sessionId, token]
  );

  useEffect(() => {
    if (!sessionId) {
      setSession(null);
      setError(null);
      return;
    }
    loadSession(sessionId);
  }, [loadSession, sessionId]);

  const performAction = useCallback(
    async (actionText, useStartEndpoint = false) => {
      if (!sessionId || !token) {
        return;
      }
      const trimmed = (actionText || '').trim();
      if (!trimmed) {
        setError('Action cannot be empty');
        return;
      }
      setSubmitting(true);
      setError(null);
      try {
        if (useStartEndpoint) {
          await startStory({ token, session_id: sessionId, seed_action: trimmed });
        } else {
          await takeActionApi({
            token,
            session_id: sessionId,
            player_action: trimmed,
            options: { use_rag: true },
          });
        }
        await loadSession(sessionId);
      } catch (err) {
        const message = err?.message || 'Failed to advance the story';
        setError(message);
      } finally {
        setSubmitting(false);
      }
    },
    [loadSession, sessionId, token]
  );

  const handleSendAction = useCallback(() => {
    performAction(input, false);
  }, [input, performAction]);

  const handleOptionClick = useCallback(
    (option) => {
      performAction(option, false);
    },
    [performAction]
  );

  const handleStartContinue = useCallback(() => {
    const shouldUseStart = !history.length;
    const action = shouldUseStart ? 'Start the story' : 'Continue the story';
    performAction(action, shouldUseStart);
  }, [history.length, performAction]);

  if (!sessionId) {
    return <div className="storyview storyview-empty">Select a session to begin.</div>;
  }

  if (loadingSession && !session) {
    return <div className="storyview">Loading session...</div>;
  }

  return (
    <div className="storyview">
      <div className="storyview-header">
        <h3>{session?.session_name || 'Story Session'}</h3>
        <button
          type="button"
          className="storyview-start"
          onClick={handleStartContinue}
          disabled={submitting}
        >
          Start / Continue
        </button>
      </div>

      <div className="storyview-history">
        {history.length === 0 && !loadingSession && (
          <div className="storyview-empty">No history yet — press Start to begin the adventure.</div>
        )}
        {history.map((entry) => (
          <div key={`${entry.turn_id}-${entry.actor}`} className={`storyview-turn storyview-${entry.actor}`}>
            <div className="storyview-turn-meta">
              <strong>{entry.actor === 'player' ? 'You' : 'AI'}</strong>
              <span>{entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : ''}</span>
            </div>
            <div className="storyview-turn-text">{entry.text}</div>
            {entry.options && entry.options.length > 0 && (
              <div className="storyview-options">
                {entry.options.map((option, idx) => (
                  <button
                    key={`${entry.turn_id}-opt-${idx}`}
                    type="button"
                    onClick={() => handleOptionClick(option)}
                    disabled={submitting}
                  >
                    {option}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="storyview-action">
        <input
          type="text"
          placeholder="Type your action (e.g., 'Open the door')"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              handleSendAction();
            }
          }}
          disabled={submitting}
        />
        <button type="button" onClick={handleSendAction} disabled={submitting || !input.trim()}>
          Send
        </button>
      </div>

      {error && <div className="storyview-error">{error}</div>}
    </div>
  );
}
