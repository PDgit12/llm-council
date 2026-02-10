import { useState } from 'react';
import './TestCaseManager.css';

export default function TestCaseManager({ conversation, onAddTestCase, onDeleteTestCase }) {
    const [input, setInput] = useState('');
    const [expected, setExpected] = useState('');
    const [isAdding, setIsAdding] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!input || !expected) return;
        onAddTestCase(input, expected);
        setInput('');
        setExpected('');
        setIsAdding(false);
    };

    if (!conversation) return null;

    return (
        <div className="test-case-manager">
            <div className="section-header">
                <h3>Test Cases</h3>
                <button
                    className="btn-add"
                    onClick={() => setIsAdding(!isAdding)}
                >
                    {isAdding ? 'Cancel' : '+ Add Test Case'}
                </button>
            </div>

            {isAdding && (
                <form className="add-test-case-form" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Test Input</label>
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="e.g., 'Extract date from: Meeting on Jan 5th'"
                            rows={2}
                        />
                    </div>
                    <div className="form-group">
                        <label>Expected Output</label>
                        <textarea
                            value={expected}
                            onChange={(e) => setExpected(e.target.value)}
                            placeholder="e.g., '2026-01-05'"
                            rows={2}
                        />
                    </div>
                    <button type="submit" className="btn-save">Save Test Case</button>
                </form>
            )}

            <div className="test-cases-list">
                {!conversation.test_cases || conversation.test_cases.length === 0 ? (
                    <p className="empty-msg">No test cases yet. Add some to enable Prompt Optimization mode.</p>
                ) : (
                    conversation.test_cases.map((tc) => (
                        <div key={tc.id} className="test-case-item">
                            <div className="tc-content">
                                <div className="tc-label">Input:</div>
                                <div className="tc-value">{tc.input}</div>
                                <div className="tc-label">Expected:</div>
                                <div className="tc-value">{tc.expected}</div>
                            </div>
                            <button
                                className="btn-delete"
                                onClick={() => onDeleteTestCase(tc.id)}
                                title="Delete Test Case"
                            >
                                ×
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
