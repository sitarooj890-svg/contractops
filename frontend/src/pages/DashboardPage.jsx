import { useAuth } from '../auth.jsx'

export default function DashboardPage() {
  const { user } = useAuth()

  if (!user) {
    return null
  }

  return (
    <main className="page">
      <h2>Dashboard</h2>
      <dl className="detail-list">
        <dt>Name</dt>
        <dd>{user.full_name}</dd>

        <dt>Email</dt>
        <dd>{user.email}</dd>

        <dt>Role</dt>
        <dd>
          <span className={`badge badge-${user.role}`}>{user.role}</span>
        </dd>
      </dl>
    </main>
  )
}
