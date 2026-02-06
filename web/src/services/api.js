const API_BASE =
  import.meta.env?.VITE_API_BASE ??
  (typeof process !== 'undefined' ? process.env?.REACT_APP_API_BASE : undefined) ??
  '/api';

console.log('🚀 API_BASE configured as:', API_BASE);

class ApiError extends Error {
  constructor(message, status, response) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.response = response;
  }
}

async function request(path, options = {}) {
  const { token, headers, body, ...rest } = options;
  const payload =
    body && typeof body === 'object' && !(body instanceof FormData)
      ? JSON.stringify(body)
      : body;

  const finalHeaders = {
    Accept: 'application/json',
    ...(payload ? { 'Content-Type': 'application/json' } : {}),
    ...headers,
  };

  const response = await fetch(`${API_BASE}${path}`, {
    method: payload ? 'POST' : 'GET',
    ...rest,
    body: payload,
    headers: finalHeaders,
  });

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      (isJson && data?.detail && JSON.stringify(data.detail)) ||
      (isJson && (data?.error || data?.message)) ||
      (typeof data === 'string' ? data : 'Request failed');
    throw new ApiError(message, response.status, data);
  }

  return data;
}

export async function listSessions({ token }) {
  return request('/list_sessions', { method: 'GET', token });
}

export async function createSession({ token, session_name, seed_text = '', settings = {} }) {
  return request('/create_session', {
    method: 'POST',
    token,
    body: { session_name, seed_text, settings },
  });
}

export async function getSession({ token, session_id }) {
  return request(`/get_session?session_id=${encodeURIComponent(session_id)}`, {
    method: 'GET',
    token,
  });
}

export async function takeAction({ token, session_id, player_action, options = {} }) {
  return request('/take_action', {
    method: 'POST',
    token,
    body: { session_id, player_action, options },
  });
}

export async function startStory({ token, session_id, seed_action = 'Start the story' }) {
  return request('/start_story', {
    method: 'POST',
    token,
    body: { session_id, seed_action },
  });
}

export async function demoAction(player_action) {
  return request('/demo_action', {
    method: 'POST',
    body: { player_action },
  });
}

export async function healthCheck() {
  return request('/health', { method: 'GET' });
}

export async function validateToken(token) {
  try {
    await healthCheck();
    await listSessions({ token });
    return true;
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return false;
    }
    return true;
  }
}

export const api = {
  healthCheck,
  validateToken,
  async createSession(token, sessionName, seedText = '', settings = {}) {
    const data = await createSession({ token, session_name: sessionName, seed_text: seedText, settings });
    if (data?.session) {
      return data.session;
    }
    return data;
  },
  async listSessions(token) {
    return listSessions({ token });
  },
  async getSession(token, sessionId) {
    return getSession({ token, session_id: sessionId });
  },
  async takeAction(token, sessionId, playerAction, options = {}) {
    return takeAction({
      token,
      session_id: sessionId,
      player_action: playerAction,
      options,
    });
  },
  async deleteSession(token, sessionId) {
    return request(`/delete_session?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
      token,
    });
  },
  startStory,
  demoAction,
};

export { ApiError };

