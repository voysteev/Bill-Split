import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import './Header.css'; // Create this CSS file for header styling

function Header() {
  const { isAuthenticated, logout, appUser } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    const { success } = await logout();
    if (success) {
      navigate('/login');
    }
  };

  return (
    <header className="app-header">
      <div className="header-content">
        <Link to={isAuthenticated ? "/dashboard" : "/"} className="logo">
          Bill Split
        </Link>
        <nav>
          {isAuthenticated ? (
            <ul className="nav-links">
              <li>Welcome, {appUser?.username || appUser?.email}!</li>
              <li><Link to="/dashboard">Dashboard</Link></li>
              <li><button onClick={handleLogout} className="button logout-button">Logout</button></li>
            </ul>
          ) : (
            <ul className="nav-links">
              <li><Link to="/login">Login</Link></li>
              <li><Link to="/signup">Sign Up</Link></li>
            </ul>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;