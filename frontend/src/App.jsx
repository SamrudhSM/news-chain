import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <header className="header animate-in">
          <h1 className="gradient-text">NewsChain Intelligence</h1>
          <p>Agentic OSing Geopolitical Graphs in Real-Time</p>
        </header>
        
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
