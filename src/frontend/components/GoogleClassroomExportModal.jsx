import React, { useState, useEffect } from 'react';

/**
 * GoogleClassroomExportModal component.
 * Allows teachers to select a Google Classroom course, specify assignment details,
 * and publish decodable reading assignments directly to classroom.google.com.
 */
export default function GoogleClassroomExportModal({ isOpen, onClose, initialTitle = '', initialContent = '' }) {
  const [token, setToken] = useState(localStorage.getItem('gc_access_token') || '');
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [title, setTitle] = useState(initialTitle);
  const [description, setDescription] = useState(initialContent);
  const [points, setPoints] = useState(100);
  const [loading, setLoading] = useState(false);
  const [publishedUrl, setPublishedUrl] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setTitle(initialTitle);
      setDescription(initialContent);
      fetchCourses();
    }
  }, [isOpen, initialTitle, initialContent]);

  const fetchCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch('/api/v1/google-classroom/courses', { headers });
      const data = await res.json();
      if (data.courses) {
        setCourses(data.courses);
        if (data.courses.length > 0) {
          setSelectedCourse(data.courses[0].id);
        }
      }
    } catch (err) {
      setError('Failed to load courses: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setPublishedUrl(null);

    try {
      const payload = {
        course_id: selectedCourse,
        title: title,
        description: description,
        points: Number(points),
        access_token: token
      };

      const res = await fetch('/api/v1/google-classroom/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok || data.error) {
        throw new Error(data.detail || 'Publishing failed');
      }

      setPublishedUrl(data.alternateLink || 'https://classroom.google.com');
      if (token) {
        localStorage.setItem('gc_access_token', token);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={modalBackdropStyle}>
      <div style={modalCardStyle}>
        <div style={modalHeaderStyle}>
          <h3 style={{ margin: 0, color: '#6750A4', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            🎓 Export Assignment to Google Classroom
          </h3>
          <button onClick={onClose} style={closeBtnStyle}>✕</button>
        </div>

        {publishedUrl ? (
          <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
            <div style={{ fontSize: '3rem', marginBottom: '0.8rem' }}>🎉</div>
            <h4 style={{ color: '#2E7D32', marginBottom: '0.5rem' }}>Successfully Published!</h4>
            <p style={{ fontSize: '0.9rem', color: '#555', marginBottom: '1.2rem' }}>
              Your decodable reading assignment is now live for your students in Google Classroom.
            </p>
            <a href={publishedUrl} target="_blank" rel="noopener noreferrer" style={actionBtnStyle}>
              🔗 View Assignment in Google Classroom
            </a>
          </div>
        ) : (
          <form onSubmit={handlePublish}>
            <div style={formGroupStyle}>
              <label style={labelStyle}>Google OAuth Access Token (Optional for Demo Mode)</label>
              <input
                type="password"
                placeholder="Paste Bearer Token or leave blank for demo"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                style={inputStyle}
              />
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Select Target Classroom Course</label>
              <select
                value={selectedCourse}
                onChange={(e) => setSelectedCourse(e.target.value)}
                style={inputStyle}
                disabled={loading}
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} {c.section ? `(${c.section})` : ''}
                  </option>
                ))}
              </select>
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Assignment Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={inputStyle}
                required
              />
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Instructions / Decodable Text Content</label>
              <textarea
                rows={5}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                style={inputStyle}
                required
              />
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Points</label>
              <input
                type="number"
                value={points}
                onChange={(e) => setPoints(e.target.value)}
                style={inputStyle}
              />
            </div>

            {error && <div style={errorStyle}>⚠️ {error}</div>}

            <div style={{ display: 'flex', gap: '0.8rem', marginTop: '1.2rem' }}>
              <button type="button" onClick={onClose} style={secondaryBtnStyle}>
                Cancel
              </button>
              <button type="submit" disabled={loading} style={primaryBtnStyle}>
                {loading ? 'Publishing...' : '🎓 Publish Assignment'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

const modalBackdropStyle = {
  position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 2000,
  display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem'
};
const modalCardStyle = {
  backgroundColor: '#fff', borderRadius: '16px', maxWidth: '550px', width: '100%',
  padding: '1.8rem', boxShadow: '0 8px 32px rgba(0,0,0,0.2)'
};
const modalHeaderStyle = {
  display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.2rem'
};
const closeBtnStyle = { background: 'none', border: 'none', fontSize: '1.3rem', cursor: 'pointer' };
const formGroupStyle = { marginBottom: '1rem' };
const labelStyle = { display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: '#1C1B1F' };
const inputStyle = { width: '100%', padding: '0.65rem 0.85rem', borderRadius: '8px', border: '1px solid #79747E', fontSize: '0.9rem' };
const errorStyle = { color: '#B00020', fontSize: '0.85rem', marginTop: '0.5rem' };
const actionBtnStyle = {
  display: 'inline-block', backgroundColor: '#6750A4', color: '#fff', padding: '0.75rem 1.4rem',
  borderRadius: '24px', textDecoration: 'none', fontWeight: 700, fontSize: '0.9rem'
};
const primaryBtnStyle = {
  flex: 1, backgroundColor: '#6750A4', color: '#fff', border: 'none', padding: '0.75rem',
  borderRadius: '24px', fontWeight: 700, cursor: 'pointer'
};
const secondaryBtnStyle = {
  backgroundColor: '#E8DEF8', color: '#1D192B', border: 'none', padding: '0.75rem 1.2rem',
  borderRadius: '24px', fontWeight: 700, cursor: 'pointer'
};
