import { Link } from 'react-router-dom'

export default function ForbiddenPage() {
  return (
    <main className="page">
      <h2>403 — Permission Denied</h2>
      <p className="error">
        Your role does not allow access to this page. Ask an admin if you
        think this is a mistake.
      </p>
      <p>
        <Link className="btn btn-secondary" to="/dashboard">
          Back to Dashboard
        </Link>
      </p>
    </main>
  )
}
