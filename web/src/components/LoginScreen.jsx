import React, { useState } from 'react';
import { Key, AlertCircle, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

const LoginScreen = ({ onLogin }) => {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token.trim()) {
      setError('Please enter an API token');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const isValid = await api.validateToken(token.trim());
      if (isValid) {
        setSuccess('Token validated successfully!');
        localStorage.setItem('api_token', token.trim());
        setTimeout(() => {
          onLogin(token.trim());
        }, 1000);
      } else {
        setError('Invalid API token. Please check your token and try again.');
      }
    } catch (err) {
      setError(`Connection failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleSubmit(e);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>🎭 AI Story World</h1>
          <p>Enter your API token to begin your adventure</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label htmlFor="token">
              <Key size={16} />
              API Token
            </label>
            <input
              id="token"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter your API token..."
              disabled={loading}
              autoFocus
            />
          </div>

          {error && (
            <div className="error-message">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              <CheckCircle size={16} />
              {success}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !token.trim()}
            className="login-button"
          >
            {loading ? (
              <>
                <div className="spinner" />
                Connecting...
              </>
            ) : (
              <>
                <Key size={16} />
                Connect
              </>
            )}
          </button>
        </form>

        <div className="login-help">
          <p>
            <strong>Need an API token?</strong>
          </p>
          <p>
            Contact your administrator or check your environment configuration.
            The token should be set in your <code>API_TOKEN</code> environment variable.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;

