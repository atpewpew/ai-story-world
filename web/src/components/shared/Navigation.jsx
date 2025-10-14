import { LogOut, User } from 'lucide-react';

export default function Navigation({ token, onLogout }) {
  const handleLogout = () => {
    localStorage.removeItem('api_token');
    window.location.href = '/';
  };

  return (
    <nav className="navigation">
      <div className="nav-logo">
        🎭 AI Story World
      </div>
      
      <div className="nav-actions">
        <div className="user-info">
          <User size={16} />
          <span>Connected</span>
        </div>
        <button onClick={handleLogout} className="logout-button">
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </nav>
  );
}
