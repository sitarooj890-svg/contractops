import { Link } from 'react-router-dom'

export default function LandingPage() {
  return (
    <div className="landing">
      <h1>ContractOps</h1>
      <p className="tagline">
        Contract obligation, renewal and deadline workspace. Track obligations,
        collect approvals and never miss a renewal date — with Analyst,
        Approver and Admin roles.
      </p>
      <div className="landing-actions">
        <Link className="btn btn-primary" to="/signup">
          Sign Up
        </Link>
        <Link className="btn btn-secondary" to="/login">
          Log In
        </Link>
      </div>
    </div>
  )
}
