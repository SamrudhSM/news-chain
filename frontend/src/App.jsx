import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import Home from './pages/Home';
import Auth from './pages/Auth';
import './App.css';

function App() {
  const [session, setSession] = useState(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  return (
    <Router>
      <div className="app-container">
        <header className="header animate-in" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 className="gradient-text">NewsChain Intelligence</h1>
            <p>Agentic OSing Geopolitical Graphs in Real-Time</p>
          </div>
          {session && (
            <button 
              onClick={handleLogout}
              className="chip" 
              style={{ padding: '0.4rem 1rem' }}
            >
              Sign Out
            </button>
          )}
        </header>
        
        <main>
          {!session ? (
            <Auth />
          ) : (
            <Routes>
              <Route path="/" element={<Home session={session} />} />
            </Routes>
          )}
        </main>
      </div>
    </Router>
  );
}

export default App;
