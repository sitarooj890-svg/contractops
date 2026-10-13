import { useState } from 'react'

import { useAuth } from '../auth.jsx'

// Account page: shows the logged-in user as returned by GET /auth/me
// (the auth context stores that exact payload after every login/refresh).
export default function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const [refreshing, setRefreshing] = useState(false)
  const [notice, setNotice] = useState(null)

  if (!user) {
    return null
  }

  async function onRefresh() {
    setNotice(null)
    setRefreshing(true)
    try {
      await refreshUser()
      setNotice({ type: 'success', text: 'Profile refreshed via /auth/me.' })
    } catch (err) {
      setNotice({ type: 'error', text: err.message })
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <main className="page">
      <h2>Profile</h2>

      <section className="card">
        <h3>Account</h3>
        <dl className="detail-list">
          <dt>Full name</dt>
          <dd>{user.full_name}</dd>

          <dt>Email</dt>
          <dd>{user.email}</dd>

          <dt>Role</dt>
          <dd>
            <span className={`badge badge-${user.role}`}>{user.role}</span>
          </dd>

          <dt>Organization</dt>
          <dd>
            {user.organization_name ? (
              <>
                {user.organization_name}
                <span className="muted"> (ID {user.organization_id})</span>
              </>
            ) : (
              <span className="muted">No organization membership</span>
            )}
          </dd>

          <dt>User ID</dt>
          <dd>{user.id}</dd>
        </dl>

        <div className="profile-actions">
          <button
            className="btn btn-secondary btn-small"
            type="button"
            disabled={refreshing}
            onClick={onRefresh}
          >
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
          {notice && <p className={notice.type}>{notice.text}</p>}
        </div>
      </section>
    </main>
  )
}
