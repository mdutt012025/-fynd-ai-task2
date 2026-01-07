// frontend-user/src/App.jsx
import { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [rating, setRating] = useState(5);
  const [review, setReview] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [hoveredStar, setHoveredStar] = useState(0);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setAiResponse(null);

    if (!review.trim()) {
      setError('Please write a review');
      return;
    }

    if (review.trim().length < 5) {
      setError('Review must be at least 5 characters');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/reviews`, {
        rating: parseInt(rating),
        user_review: review.trim()
      });

      setAiResponse(response.data);
      setSuccess(true);
      setSubmitted(true);
      setReview('');
      setRating(5);

      setTimeout(() => setSuccess(false), 5000);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to submit review. Please try again.';
      setError(errorMsg);
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRatingEmoji = (r) => {
    if (r >= 5) return '🤩';
    if (r >= 4) return '😊';
    if (r >= 3) return '😐';
    if (r >= 2) return '😕';
    return '😠';
  };

  const getRatingText = (r) => {
    if (r >= 5) return 'Excellent!';
    if (r >= 4) return 'Good!';
    if (r >= 3) return 'Average';
    if (r >= 2) return 'Poor';
    return 'Terrible';
  };

  return (
    <div className="app-container">
      {/* Animated Background */}
      <div className="animated-bg">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
        <div className="blob blob-3"></div>
      </div>

      {/* Main Card */}
      <div className="main-card">
        {/* Header Section */}
        <div className="header-section">
          <h1 className="main-title">✨ Share Your Feedback</h1>
          <p className="subtitle">Help us create amazing experiences</p>
        </div>

        {/* Alerts */}
        {success && (
          <div className="alert alert-success fade-in">
            <div className="alert-icon">✓</div>
            <div className="alert-content">
              <strong>Thank you!</strong>
              <p>Your review has been submitted successfully</p>
            </div>
          </div>
        )}

        {error && (
          <div className="alert alert-error fade-in">
            <div className="alert-icon">✕</div>
            <div className="alert-content">
              <strong>Oops!</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* Form Section */}
        <form onSubmit={handleSubmit} className="form-section">
          {/* Rating Section */}
          <div className="form-group">
            <div className="rating-header">
              <label>How would you rate us?</label>
              <span className="rating-emoji">{getRatingEmoji(hoveredStar || rating)}</span>
            </div>

            <div className="star-container">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  className={`star-btn ${star <= (hoveredStar || rating) ? 'active' : ''}`}
                  onClick={() => setRating(star)}
                  onMouseEnter={() => setHoveredStar(star)}
                  onMouseLeave={() => setHoveredStar(0)}
                >
                  ★
                </button>
              ))}
            </div>

            <div className="rating-display">
              <span className="rating-number">{hoveredStar || rating}</span>
              <span className="rating-label">{getRatingText(hoveredStar || rating)}</span>
            </div>
          </div>

          {/* Review Textarea */}
          <div className="form-group">
            <label htmlFor="review" className="textarea-label">
              Your Experience
              <span className="label-hint">(Be detailed and honest)</span>
            </label>
            <div className="textarea-wrapper">
              <textarea
                id="review"
                value={review}
                onChange={(e) => setReview(e.target.value.slice(0, 1000))}
                placeholder="Tell us what made your experience special... (minimum 5 characters)"
                rows="6"
                disabled={loading}
                className="review-textarea"
              />
              <div className="char-counter">
                <span className={review.length > 800 ? 'warning' : ''}>
                  {review.length}
                </span>
                <span className="char-max">/1000</span>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !review.trim()}
            className={`submit-btn ${loading ? 'loading' : ''}`}
          >
            <span className="btn-icon">📤</span>
            <span>{loading ? 'Submitting...' : 'Submit Review'}</span>
            {!loading && <span className="btn-arrow">→</span>}
          </button>
        </form>

        {/* AI Response Section */}
        {aiResponse && (
          <div className="response-section fade-in">
            <div className="response-header">
              <h3>💬 Response from Our Team</h3>
            </div>
            <div className="response-card">
              <p className="response-text">{aiResponse.ai_response}</p>
              <div className="response-meta">
                <span className="meta-label">Submitted:</span>
                <time dateTime={aiResponse.created_at}>
                  {new Date(aiResponse.created_at).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </time>
              </div>
            </div>
          </div>
        )}

        {/* Tips Section */}
        {!submitted && (
          <div className="tips-section">
            <h4>💡 Tips for Great Feedback</h4>
            <ul className="tips-list">
              <li><span className="tip-icon">✓</span> Be specific about what you liked or didn't like</li>
              <li><span className="tip-icon">✓</span> Share your honest experience</li>
              <li><span className="tip-icon">✓</span> Help us improve for everyone</li>
            </ul>
          </div>
        )}
      </div>

      {/* Floating Elements */}
      <div className="floating-elements">
        <div className="float float-1">⭐</div>
        <div className="float float-2">💬</div>
        <div className="float float-3">✨</div>
      </div>
    </div>
  );
}

export default App;