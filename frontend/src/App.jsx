import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { useAuth } from './auth.jsx'
import NavBar from './components/NavBar.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import AdminPortal from './pages/AdminPortal.jsx'
import AnalystPortal from './pages/AnalystPortal.jsx'
import ApproverPortal from './pages/ApproverPortal.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import ForbiddenPage from './pages/ForbiddenPage.jsx'
import LandingPage from './pages/LandingPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import SignupPage from './pages/SignupPage.jsx'

// Auth gate + nav bar for every logged-in page.
function Protected({ children }) {
  return (
    <ProtectedRoute>
      <NavBar />
      {children}
    </ProtectedRoute>
  )
}

// Renders the portal only for the matching role, otherwise the 403 page.
function RequireRole({ role, children }) {
  const { user } = useAuth()
  if (user && user.role !== role) {
    return <ForbiddenPage />
  }
  return children
}

function Placeholder({ title }) {
  return (
    <main className="page">
      <h2>{title}</h2>
      <p className="muted">Coming soon.</p>
    </main>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/dashboard"
          element={
            <Protected>
              <DashboardPage />
            </Protected>
          }
        />

        {/* Any authenticated role may view their own account. */}
        <Route
          path="/profile"
          element={
            <Protected>
              <ProfilePage />
            </Protected>
          }
        />

        <Route
          path="/analyst"
          element={
            <Protected>
              <RequireRole role="analyst">
                <AnalystPortal />
              </RequireRole>
            </Protected>
          }
        />

        <Route
          path="/approver"
          element={
            <Protected>
              <RequireRole role="approver">
                <ApproverPortal />
              </RequireRole>
            </Protected>
          }
        />

        <Route
          path="/admin"
          element={
            <Protected>
              <RequireRole role="admin">
                <AdminPortal />
              </RequireRole>
            </Protected>
          }
        />

        <Route path="*" element={<Placeholder title="Page not found" />} />
      </Routes>
    </BrowserRouter>
  )
}
