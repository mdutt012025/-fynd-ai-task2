// frontend-admin/src/App.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [stats, setStats] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterRating, setFilterRating] = useState(0);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [expandedReview, setExpandedReview] = useState(null);

  const fetchData = async () => {
    try {
      const [statsRes, reviewsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/admin/stats`),
        axios.get(`${API_BASE_URL}/api/reviews?limit=50`)
      ]);

      setStats(statsRes.data);
      setReviews(reviewsRes.data.data || []);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load data. Retrying...');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredReviews = filterRating === 0
    ? reviews
    : reviews.filter(r => r.rating === filterRating);

  const getRatingColor = (rating) => {
    if (rating >= 5) return '#4caf50';
    if (rating >= 4) return '#8bc34a';
    if (rating === 3) return '#ffc107';
    if (rating === 2) return '#ff9800';
    return '#f44336';
  };

  const getRatingGradient = (rating) => {
    const colors = {
      5: 'linear-gradient(135deg, #4caf50 0%, #45a049 100%)',
      4: 'linear-gradient(135deg, #8bc34a 0%, #7cb342 100%)',
      3: 'linear-gradient(135deg, #ffc107 0%, #ffb300 100%)',
      2: 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)',
      1: 'linear-gradient(135deg, #f44336 0%, #e53935 100%)',
    };
    return colors[rating] || colors[1];
  };

  const RatingBadge = ({ rating }) => (
    <span
      className="rating-badge"
      style={{ background: getRatingGradient(rating) }}
    >
      {'★'.repeat(rating)}
    </span>
  );

  if (loading && !stats) {
    return (
      <div className="admin-container">
        <div className="loading-screen">
          <div className="loader"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-container">
      {/* Animated Background */}
      <div className="admin-bg">
        <div className="gradient-1"></div>
        <div className="gradient-2"></div>
      </div>

      {/* Header */}
      <header className="admin-header">
        <div className="header-content">
          <h1>📊 Admin Dashboard</h1>
          <p className="header-subtitle">Real-time feedback management</p>
        </div>
        <div className="header-actions">
          <button className="refresh-btn" onClick={fetchData}>
            <span className="refresh-icon">⟳</span> Refresh
          </button>
          <span className="last-update">
            🕐 {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </header>

      {error && (
        <div className="alert alert-error">
          ⚠️ {error}
        </div>
      )}

      {stats && (
        <>
          {/* Stats Grid */}
          <div className="stats-grid">
            <div className="stat-card total">
              <div className="stat-icon">📝</div>
              <div className="stat-content">
                <div className="stat-label">Total Reviews</div>
                <div className="stat-value">{stats.total_reviews}</div>
              </div>
            </div>

            <div className="stat-card average">
              <div className="stat-icon">⭐</div>
              <div className="stat-content">
                <div className="stat-label">Average Rating</div>
                <div className="stat-value">{stats.avg_rating.toFixed(2)}</div>
                <div className="stat-subtext">/5.0</div>
              </div>
            </div>

            <div className="stat-card excellent">
              <div className="stat-icon">😍</div>
              <div className="stat-content">
                <div className="stat-label">5 Star</div>
                <div className="stat-value">{stats.rating_distribution[5]}</div>
              </div>
            </div>

            <div className="stat-card good">
              <div className="stat-icon">😊</div>
              <div className="stat-content">
                <div className="stat-label">4 Star</div>
                <div className="stat-value">{stats.rating_distribution[4]}</div>
              </div>
            </div>

            <div className="stat-card neutral">
              <div className="stat-icon">😐</div>
              <div className="stat-content">
                <div className="stat-label">3 Star</div>
                <div className="stat-value">{stats.rating_distribution[3]}</div>
              </div>
            </div>

            <div className="stat-card negative">
              <div className="stat-icon">😞</div>
              <div className="stat-content">
                <div className="stat-label">1-2 Star</div>
                <div className="stat-value">{stats.rating_distribution[1] + stats.rating_distribution[2]}</div>
              </div>
            </div>
          </div>

          {/* Reviews Section */}
          <div className="reviews-section">
            <div className="section-header">
              <h2>📋 Recent Reviews</h2>
              <div className="filter-buttons">
                <button
                  className={`filter-btn ${filterRating === 0 ? 'active' : ''}`}
                  onClick={() => setFilterRating(0)}
                >
                  All <span className="count">({reviews.length})</span>
                </button>
                {[5, 4, 3, 2, 1].map((rating) => (
                  <button
                    key={rating}
                    className={`filter-btn ${filterRating === rating ? 'active' : ''}`}
                    onClick={() => setFilterRating(rating)}
                  >
                    {rating}★ <span className="count">({stats.rating_distribution[rating]})</span>
                  </button>
                ))}
              </div>
            </div>

            {filteredReviews.length === 0 ? (
              <div className="no-reviews">
                <div className="empty-icon">📭</div>
                <p>No reviews found</p>
                <span className="empty-hint">Reviews will appear here when users submit feedback</span>
              </div>
            ) : (
              <div className="reviews-list">
                {filteredReviews.map((review, idx) => (
                  <div
                    key={review.id}
                    className={`review-card ${expandedReview === review.id ? 'expanded' : ''}`}
                    onClick={() => setExpandedReview(expandedReview === review.id ? null : review.id)}
                  >
                    <div className="review-header">
                      <div className="review-meta">
                        <RatingBadge rating={review.rating} />
                        <span className="review-number">#{reviews.length - idx}</span>
                      </div>
                      <span className="review-time">
                        {new Date(review.created_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>

                    {expandedReview === review.id && (
                      <div className="review-expanded">
                        <div className="review-section user-review">
                          <h4>👤 User Review</h4>
                          <p>{review.user_review}</p>
                        </div>

                        <div className="review-section ai-summary">
                          <h4>🎯 AI Summary</h4>
                          <p>{review.ai_summary}</p>
                        </div>

                        <div className="review-section ai-response">
                          <h4>💬 AI Response</h4>
                          <p>{review.ai_response}</p>
                        </div>

                        <div className="review-section recommended">
                          <h4>⚡ Recommended Actions</h4>
                          <p>{review.recommended_actions}</p>
                        </div>
                      </div>
                    )}

                    {expandedReview !== review.id && (
                      <div className="review-preview">
                        <div className="preview-item">
                          <strong>Review:</strong> {review.user_review.substring(0, 60)}...
                        </div>
                        <div className="preview-item">
                          <strong>Summary:</strong> {review.ai_summary.substring(0, 60)}...
                        </div>
                      </div>
                    )}

                    <div className="review-footer">
                      <span className="expand-hint">
                        {expandedReview === review.id ? '▼ Click to collapse' : '▶ Click to expand'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default App;