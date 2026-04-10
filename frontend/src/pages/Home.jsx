import React, { useState, useEffect } from 'react';
import axios from 'axios';
import SearchBar from '../components/SearchBar';
import BriefCard from '../components/BriefCard';
import GraphVisualization from '../components/GraphVisualization';

const API_BASE_URL = 'https://newschain-backend.agreeablesmoke-eff19f0c.centralindia.azurecontainerapps.io';

const LOADING_PHASES = [
  "Fetching news streams...",
  "Running LangGraph Agents...",
  "Extracting Intelligence Details...",
  "Building Causal Knowledge Graph...",
  "Finalizing Output..."
];

export default function Home({ session }) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const [activeTab, setActiveTab] = useState('brief'); // 'brief' | 'graph'
  
  const [result, setResult] = useState(null);
  const [graphData, setGraphData] = useState(null);

  // Cycling loading text effect
  useEffect(() => {
    let interval;
    if (isAnalyzing) {
      setLoadingPhase(0);
      interval = setInterval(() => {
        setLoadingPhase(prev => (prev < LOADING_PHASES.length - 1 ? prev + 1 : prev));
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isAnalyzing]);

  const handleSearch = async (query) => {
    setIsAnalyzing(true);
    setResult(null);
    setGraphData(null);
    setActiveTab('brief'); // Reset tab on new search
    
    try {
      const config = {
        headers: {
          Authorization: `Bearer ${session?.access_token}`
        }
      };

      // 1. Run Pipeline
      const { data } = await axios.post(`${API_BASE_URL}/query`, { query: query, dry_run: false }, config);
      setResult(data);
      
      // 2. Fetch Graph
      const eventId = data.brief?.event?.id;
      if (eventId) {
        try {
          // Give Neo4j a brief moment
          await new Promise(r => setTimeout(r, 1000));
          const graphRes = await axios.get(`${API_BASE_URL}/graph/event/${encodeURIComponent(eventId)}`, config);
          setGraphData(graphRes.data);
        } catch (err) {
          console.error("Graph fetch error:", err);
        }
      }
    } catch (error) {
      console.error("Pipeline failure:", error);
      alert("Failed to analyze query. Is backend running?");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div>
      <SearchBar onSearch={handleSearch} isLoading={isAnalyzing} />

      {/* Loading State */}
      {isAnalyzing && (
        <div className="loader-wrapper animate-in">
          <div className="spinner"></div>
          <h3 className="mono multi-phase-text">
            {LOADING_PHASES[loadingPhase]}
          </h3>
        </div>
      )}

      {/* Results View */}
      {result && !isAnalyzing && (
        <div className="results-container animate-in">
          
          <div className="tabs-container">
            <button 
              className={`tab-button ${activeTab === 'brief' ? 'active' : ''}`}
              onClick={() => setActiveTab('brief')}
            >
              Intelligence Brief
            </button>
            <button 
              className={`tab-button ${activeTab === 'graph' ? 'active' : ''}`}
              onClick={() => setActiveTab('graph')}
            >
              Causal Graph
            </button>
          </div>

          <div className="tab-content" style={{ minHeight: '600px' }}>
            {activeTab === 'brief' && <BriefCard brief={result.brief} />}
            {activeTab === 'graph' && <GraphVisualization graphData={graphData} />}
          </div>

        </div>
      )}
    </div>
  );
}
