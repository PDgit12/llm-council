import React from 'react';
import { Sparkles, Globe, Brain, Zap, ArrowRight, Layers, Search, Command } from 'lucide-react';
import './HomePage.css';

function HomePage({ conversations, onNewConversation, onSelectConversation, onExampleClick }) {
    const exampleQueries = [
        {
            icon: <Zap size={20} />,
            query: 'How to reduce customer churn in SaaS?',
            domain: null,
        },
        {
            icon: <Brain size={20} />,
            query: 'How to make learning stick in online education?',
            domain: 'Immunology',
        },
        {
            icon: <Globe size={20} />,
            query: 'How to improve team communication?',
            domain: 'Marine Biology',
        },
        {
            icon: <Sparkles size={20} />,
            query: 'How to scale a marketplace from 100 to 10k users?',
            domain: null,
        },
    ];

    return (
        <div className="homepage-hero-wrapper">
            {/* Animated background orbs */}
            <div className="bg-orb bg-orb-1" />
            <div className="bg-orb bg-orb-2" />
            <div className="bg-orb bg-orb-3" />

            <nav className="landing-nav glass-panel">
                <div className="nav-brand">
                    <Command size={20} className="nav-logo-icon" />
                    <span>Council</span>
                </div>
                <div className="nav-links">
                    {conversations && conversations.length > 0 && (
                        <button className="nav-btn-text" onClick={() => onSelectConversation(conversations[0].id)}>
                            History
                        </button>
                    )}
                    <button className="nav-btn-primary" onClick={onNewConversation}>
                        Launch Engine
                    </button>
                </div>
            </nav>

            <div className="homepage-content-centered">
                {/* Hero Section */}
                <div className="hero animate-fade-in">
                    <div className="hero-badge">
                        <Sparkles size={12} />
                        <span>Cross-Domain Analogy Engine</span>
                    </div>
                    <h1 className="hero-title">
                        Parallels
                        <span className="hero-title-gradient">Council</span>
                    </h1>
                    <p className="hero-subtitle">
                        Think outside your industry. The Council deconstructs your problems and
                        discovers breakthrough solutions in unexpected domains.
                    </p>

                    <div className="hero-actions">
                        <button className="cta-button-main" onClick={onNewConversation}>
                            Start Exploring <ArrowRight size={18} />
                        </button>
                        <button className="cta-button-secondary" onClick={onNewConversation}>
                            Log In
                        </button>
                    </div>
                </div>

                {/* How It Works */}
                <div className="pipeline-steps animate-fade-in" style={{ animationDelay: '0.1s' }}>
                    <div className="pipeline-step">
                        <div className="step-icon-wrapper"><Search size={24} /></div>
                        <div className="step-label">Deconstruct</div>
                    </div>
                    <div className="pipeline-connector" />
                    <div className="pipeline-step">
                        <div className="step-icon-wrapper"><Globe size={24} /></div>
                        <div className="step-label">Explore</div>
                    </div>
                    <div className="pipeline-connector" />
                    <div className="pipeline-step">
                        <div className="step-icon-wrapper"><Layers size={24} /></div>
                        <div className="step-label">Map</div>
                    </div>
                    <div className="pipeline-connector" />
                    <div className="pipeline-step">
                        <div className="step-icon-wrapper"><Sparkles size={24} /></div>
                        <div className="step-label">Synthesize</div>
                    </div>
                </div>

                {/* Example Queries */}
                <div className="examples-section animate-fade-in" style={{ animationDelay: '0.2s' }}>
                    <h3 className="examples-title">Try an exploration</h3>
                    <div className="examples-grid">
                        {exampleQueries.map((example, idx) => (
                            <button
                                key={idx}
                                className="example-card glass-panel"
                                onClick={() => onExampleClick(example.query)}
                            >
                                <span className="example-icon-wrapper">{example.icon}</span>
                                <div className="example-text">
                                    <span className="example-query">{example.query}</span>
                                    {example.domain && (
                                        <span className="example-domain">→ {example.domain}</span>
                                    )}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Recent Explorations */}
                {conversations && conversations.length > 0 && (
                    <div className="recent-section-landing animate-fade-in" style={{ animationDelay: '0.3s' }}>
                        <h3 className="recent-title">Recent Activity</h3>
                        <div className="recent-pills">
                            {conversations.slice(0, 3).map((conv) => (
                                <button
                                    key={conv.id}
                                    className="recent-pill glass-button"
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
                <span className="footer-text">Powered by LLM Council</span>
                <span className="footer-dot">•</span>
                <span className="footer-ver">v2.0 Premium</span>
            </footer>
        </div>
    );
}

export default HomePage;
