import React, { useState } from 'react';

export default function SearchBar({ onSearch, isLoading }) {
  const [query, setQuery] = useState('');

  // Example chips provided by spec
  const examples = [
    "US trade restrictions on Chinese tech",
    "How is the Iran conflict affecting oil prices?",
    "Impact of AI regulations in Europe",
    "Taiwan semiconductor supply chain risks"
  ];

  const handleChipClick = (text) => {
    setQuery(text);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query);
    }
  };

  return (
    <div className="search-container animate-in">
      <form className="search-input-wrapper" onSubmit={handleSubmit}>
        <input 
          type="text" 
          className="search-input"
          placeholder="> Enter geopolitical query or entity to analyze..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
        />
        <button 
          className="search-button" 
          type="submit" 
          disabled={!query.trim() || isLoading}
        >
          {isLoading ? 'Processing' : 'Analyze'}
        </button>
      </form>

      {!isLoading && (
        <div className="query-chips">
          {examples.map((ex, i) => (
            <div key={i} className="chip" onClick={() => handleChipClick(ex)}>
              {ex}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
