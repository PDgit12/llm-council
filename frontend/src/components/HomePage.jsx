import { useState } from 'react';
import './HomePage.css';

function HomePage({ conversations, onNewConversation, onSelectConversation, onExampleClick }) {
    const exampleQueries = [
        {
            icon: '🏢',
            query: 'How to reduce customer churn in SaaS?',
            domain: null,
        },
        {
            icon: '🧠',
            query: 'How to make learning stick in online education?',
            domain: 'Immunology',
        },
        {
            icon: '👥',
            query: 'How to improve team communication in a remote startup?',
            domain: 'Marine Biology',
        },
        {
            icon: '⚡',
            query: 'How to scale a marketplace from 100 to 10,000 users?',
            domain: null,
        },
    ];

    return (
        <div className="homepage-hero-wrapper">
            {/* Animated background orbs */}
            <div className="bg-orb bg-orb-1" />
            <div className="bg-orb bg-orb-2" />
            <div className="bg-orb bg-orb-3" />

            <nav className="landing-nav">
                <div className="nav-brand">⫘ Parallels</div>
                <div className="nav-links">
                    {conversations.length > 0 && (
                        <button className="nav-btn-text" onClick={() => onSelectConversation(conversations[0].id)}>
                            View Results
                        </button>
                    )}
                    <button className="nav-btn-primary" onClick={onNewConversation}>
                        Launch Engine
                    </button>
                </div>
            </nav>

            <div className="homepage-content-centered">
                {/* Hero Section */}
                <div className="hero">
                    <div className="hero-badge">Cross-Domain Analogy Engine</div>
                    <h1 className="hero-title">Parallels</h1>
                    <p className="hero-subtitle">
                        Think outside your industry. Parallels deconstructs your problems and
                        discovers breakthrough solutions in unexpected domains.
                    </p>
                </div>

                {/* How It Works */}
                <div className="pipeline-steps">
                    <div className="pipeline-step">
                        <div className="step-number">1</div>
                        <div className="step-icon">🔬</div>
                        <div className="step-label">Deconstruct</div>
                    </div>
                    <div className="pipeline-connector" />
                    <div className="pipeline-step">
                        <div className="step-number">2</div>
                        <div className="step-icon">🌍</div>
                        <div className="step-label">Explore</div>
                    </div>
                    <div className="pipeline-connector" />
                    <div className="pipeline-step">
                        <div className="step-number">3</div>
                        <div className="step-icon">🔗</div>
                        <div className="step-label">Map</div>
                    </div>
                    <div className="pipeline-connector" />
                    <div className="pipeline-step">
                        <div className="step-number">4</div>
                        <div className="step-icon">✨</div>
                        <div className="step-label">Synthesize</div>
                    </div>
                </div>

                {/* Example Queries */}
                <div className="examples-section">
                    <h3 className="examples-title">Try an exploration</h3>
                    <div className="examples-grid">
                        {exampleQueries.map((example, idx) => (
                            <button
                                key={idx}
                                className="example-card"
                                onClick={() => onExampleClick(example.query)}
                            >
                                <span className="example-icon">{example.icon}</span>
                                <span className="example-query">{example.query}</span>
                                {example.domain && (
                                    <span className="example-domain">→ {example.domain}</span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* CTA */}
                <div className="hero-actions">
                    <button className="cta-button-main" onClick={onNewConversation}>
                        Start Exploring
                    </button>
                </div>

                {/* Recent Explorations */}
                {conversations.length > 0 && (
                    <div className="recent-section-landing">
                        <h3 className="recent-title">Recent Activity</h3>
                        <div className="recent-pills">
                            {conversations.slice(0, 3).map((conv) => (
                                <button
                                    key={conv.id}
                                    className="recent-pill"
                                    onClick={() => onSelectConversation(conv.id)}
                                >
                                    {conv.title || 'Untitled Exploration'}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <footer className="landing-footer">
                Parallels &copy; 2026 • Powered by LLM Council
            </footer>
        </div>
    );
}

export default HomePage;
