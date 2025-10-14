import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import LoginScreen from './components/LoginScreen';
import './App.css';

function App() {
  const [token, setToken] = useState(null);
  
  useEffect(() => {
    const savedToken = localStorage.getItem('api_token');
    if (savedToken) setToken(savedToken);
  }, []);
  
  const handleLogin = (newToken) => {
    setToken(newToken);
    localStorage.setItem('api_token', newToken);
  };
  
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route 
          path="/login" 
          element={token ? <Navigate to="/dashboard" /> : <LoginScreen onLogin={handleLogin} />} 
        />
        <Route 
          path="/dashboard" 
          element={token ? <Dashboard token={token} /> : <Navigate to="/login" />} 
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
