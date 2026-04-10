import React, { useState } from 'react';
import { supabase } from '../supabaseClient';
import '../App.css';

export default function Auth() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isLogin, setIsLogin] = useState(true);

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setMessage('Registration successful! Check your email or sign in.');
      }
    } catch (error) {
      setMessage(error.message || 'An error occurred during authentication.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <div className="glass-panel animate-in" style={{ padding: '3rem', width: '100%', maxWidth: '450px' }}>
        <div className="header" style={{ marginBottom: '2rem' }}>
          <h2 style={{ color: 'var(--accent-color)' }}>{isLogin ? 'Mission Login' : 'Agent Registration'}</h2>
          <p style={{ color: 'var(--text-secondary)' }}>
            {isLogin ? 'Enter your credentials to access the intelligence graph.' : 'Register to begin tracking causal chains.'}
          </p>
        </div>

        <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div>
            <input
              type="email"
              placeholder="Agent Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="search-input"
              style={{ padding: '1rem', width: '100%', marginBottom: '0' }}
              required
            />
          </div>
          <div>
            <input
              type="password"
              placeholder="Access Code"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="search-input"
              style={{ padding: '1rem', width: '100%', marginBottom: '0' }}
              required
            />
          </div>

          <button
            type="submit"
            className="search-button"
            disabled={loading}
            style={{ position: 'relative', right: '0', top: '0', bottom: '0', width: '100%', padding: '1rem' }}
          >
            {loading ? 'Processing...' : isLogin ? 'Authenticate' : 'Register'}
          </button>
        </form>

        {message && (
          <div style={{ marginTop: '1.5rem', textAlign: 'center', color: message.includes('error') ? 'var(--risk-high)' : 'var(--risk-low)' }}>
            <p>{message}</p>
          </div>
        )}

        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', textDecoration: 'underline' }}
          >
            {isLogin ? 'Need clearance? Register here.' : 'Already have clearance? Login.'}
          </button>
        </div>
      </div>
    </div>
  );
}
