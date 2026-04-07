import React from 'react';

export default function BriefCard({ brief }) {
  if (!brief || !brief.event) return null;

  const { event, intelligence_brief, watch_points, topics_impacted, entities, causal_chain } = brief;

  const getRiskClass = (score) => {
    if (score >= 8) return 'c-high';
    if (score >= 5) return 'c-med';
    return 'c-low';
  };

  const getEntityStyle = (type) => {
    const t = (type || '').toLowerCase();
    if (t === 'country') return 'e-country';
    if (t === 'organization') return 'e-org';
    if (t === 'person') return 'e-person';
    if (t === 'commodity') return 'e-commodity';
    return 'e-unknown';
  };

  return (
    <div className="brief-card glass-panel animate-in">
      <div className="brief-header">
        <div>
          <span className="category-badge">{event.category || 'EVENT'}</span>
          <br /><br />
          <h2 className="title-highlight brief-title">{event.title}</h2>
          <div className="mono" style={{ color: 'var(--text-secondary)' }}>
            DETECTED: {new Date(event.date).toLocaleDateString()}
          </div>
        </div>
        
        <div className="risk-circle-container">
          <div className={`risk-circle ${getRiskClass(event.risk_score)}`}>
            {event.risk_score}
          </div>
          <div className="risk-label">Risk Score</div>
        </div>
      </div>

      <div className="brief-section">
        <h3>Intelligence Summary</h3>
        <div className="brief-summary">
          {intelligence_brief || event.summary}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div className="brief-section">
          <h3>Key Actors</h3>
          <div className="tag-list">
            {entities && entities.map((e, i) => (
              <span key={i} className={`entity-tag ${getEntityStyle(e.type)}`}>
                {e.name}
              </span>
            ))}
          </div>
        </div>

        <div className="brief-section">
          <h3>Sectors Impacted</h3>
          <div className="tag-list">
            {topics_impacted && topics_impacted.map((t, i) => (
              <span key={i} className={`entity-tag ${t.impact === 'negative' ? 't-negative' : 't-positive'}`}>
                {t.name}
              </span>
            ))}
          </div>
        </div>
      </div>

      {causal_chain && causal_chain.length > 0 && (
        <div className="brief-section" style={{ marginTop: '1rem', borderTop: '1px solid var(--border-light)', paddingTop: '1.5rem' }}>
          <h3>Causal Chain Analysis</h3>
          {causal_chain.map((link, i) => (
            <div key={i} className="causal-item">
              <div className="chain-flow">
                <span className="chain-cause">{link.from_event}</span>
                <span className="chain-arrow">→</span>
                <span className="chain-effect">{link.to_event}</span>
                <span className="chain-conf mono">{(link.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="chain-desc">{link.explanation}</div>
            </div>
          ))}
        </div>
      )}

      {watch_points && watch_points.length > 0 && (
         <div className="brief-section">
          <h3>Watch Points</h3>
          <ul className="watch-list">
            {watch_points.map((wp, i) => (
              <li key={i}>{wp}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
