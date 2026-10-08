import { Link } from 'react-router-dom'

const FEATURES = [
  {
    icon: '📋',
    title: 'Track obligations',
    text: 'Every obligation from your contracts in one organized, searchable workspace.',
  },
  {
    icon: '⏰',
    title: 'Never miss a renewal date',
    text: 'Renewals and due dates surfaced early, so nothing slips through the cracks.',
  },
  {
    icon: '✅',
    title: 'Human approval with a clear history',
    text: 'Approvers confirm, correct or reject — every decision is recorded and auditable.',
  },
]

export default function LandingPage() {
  return (
    <div className="landing">
      <header className="topbar">
        <span className="topbar-brand">ContractOps</span>
        <div className="topbar-actions">
          <Link className="btn btn-secondary" to="/login">
            Log In
          </Link>
          <Link className="btn btn-primary" to="/signup">
            Sign Up
          </Link>
        </div>
      </header>

      <section className="hero">
        <div className="hero-inner">
          <h1>Never miss a contract deadline again.</h1>
          <p className="hero-sub">
            ContractOps keeps obligations, renewals and approvals moving — one
            workspace for Analysts, Approvers and Admins.
          </p>
          <div className="hero-actions">
            <Link className="btn-hero btn-hero-primary" to="/signup">
              Get started
            </Link>
          </div>
        </div>
      </section>

      <section className="features">
        <div className="card-grid">
          {FEATURES.map((feature) => (
            <section className="card feature-card" key={feature.title}>
              <span className="feature-icon" aria-hidden="true">
                {feature.icon}
              </span>
              <h3>{feature.title}</h3>
              <p className="muted">{feature.text}</p>
            </section>
          ))}
        </div>
      </section>

      <footer className="footer">
        <span className="footer-brand">ContractOps</span>
        <span className="muted">
          Contract obligation, renewal and deadline workspace.
        </span>
      </footer>
    </div>
  )
}
