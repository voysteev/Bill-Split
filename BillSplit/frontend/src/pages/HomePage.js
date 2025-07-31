import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

function HomePage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="container home-page">
      <h1>Welcome to BillSplit!</h1>
      <p>Manage shared expenses with friends and family effortlessly.</p>
      
      {!isAuthenticated ? (
        <div className="auth-links">
          <Link to="/login" className="button primary">Login</Link>
          <Link to="/signup" className="button secondary">Sign Up</Link>
        </div>
      ) : (
        <div className="dashboard-link">
          <p>You're logged in!</p>
          <Link to="/dashboard" className="button primary">Go to Dashboard</Link>
        </div>
      )}

      <section className="features-section">
        <h2>Key Features:</h2>
        <ul>
          <li>Create and manage groups for any occasion.</li>
          <li>Easily add expenses, specifying who paid and who's involved.</li>
          <li>Smart settlement calculations to minimize transactions.</li>
          <li>View "who owes whom" and track personal balances.</li>
        </ul>
      </section>

      <section className="about-us-section">
        <h2>About BillSplit</h2>
        <p>
          BillSplit is designed to take the hassle out of group expenses. 
          Whether it's a trip, a dinner, or recurring household bills, 
          we make sure everyone pays their fair share with clarity and simplicity.
        </p>
      </section>
    </div>
  );
}

export default HomePage;