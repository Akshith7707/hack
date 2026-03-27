import { useState } from 'react';
import { submitFeedback } from '../api';

export default function FeedbackButtons({ runId, onFeedbackSubmitted, disabled }) {
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [feedbackType, setFeedbackType] = useState(null);

  const handleFeedback = async (action) => {
    setLoading(true);
    setFeedbackType(action);
    
    try {
      const result = await submitFeedback(runId, action);
      setSubmitted(true);
      onFeedbackSubmitted(result.weights);
    } catch (err) {
      console.error('Feedback failed:', err);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="feedback-buttons fade-in">
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 'var(--space-md)',
          padding: 'var(--space-md) var(--space-xl)',
          background: feedbackType === 'accept' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          borderRadius: 'var(--radius-lg)'
        }}>
          <span style={{ fontSize: '1.5rem' }}>
            {feedbackType === 'accept' ? '✅' : '❌'}
          </span>
          <span style={{ color: 'var(--text-secondary)' }}>
            Feedback recorded! Agent weights updated.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-buttons">
      <button
        className="btn btn-success feedback-btn"
        onClick={() => handleFeedback('accept')}
        disabled={disabled || loading}
      >
        {loading && feedbackType === 'accept' ? (
          <span className="loading-spinner" />
        ) : (
          '👍 Accept'
        )}
      </button>
      
      <button
        className="btn btn-danger feedback-btn"
        onClick={() => handleFeedback('reject')}
        disabled={disabled || loading}
      >
        {loading && feedbackType === 'reject' ? (
          <span className="loading-spinner" />
        ) : (
          '👎 Reject'
        )}
      </button>
    </div>
  );
}
