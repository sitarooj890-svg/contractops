import { Navigate } from 'react-router-dom'

import { useAuth } from '../auth.jsx'

// Wraps pages that need a logged-in user. Unauthenticated visitors are
// redirected to /login; while the startup /auth/me check runs we show a
// loading message instead of flashing a redirect.
export default function ProtectedRoute({ children }) {
  const { token, user, loading } = useAuth()

  if (loading) {
    return (
      <main className="page">
        <p className="loading">Checking your session…</p>
      </main>
    )
  }

  if (!token || !user) {
    return <Navigate to="/login" replace />
  }

  return children
}
