import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth.jsx'

const ROLE_OPTIONS = ['analyst', 'approver']

export default function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    email: '',
    password: '',
    full_name: '',
    organization_name: '',
    role: 'analyst',
  })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const update = (field) => (event) =>
    setForm({ ...form, [field]: event.target.value })

  async function onSubmit(event) {
    event.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await signup(form)
      navigate('/login', {
        state: { message: 'Account created. Please log in.' },
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h2>Sign up</h2>
      <p className="muted">
        Already have an account?{' '}
        <Link to="/login">Log in</Link>
      </p>

      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">Creating your account…</p>}

      <form className="form" onSubmit={onSubmit}>
        <label>
          Email
          <input
            type="email"
            value={form.email}
            onChange={update('email')}
            required
            autoComplete="email"
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={form.password}
            onChange={update('password')}
            required
            minLength={8}
            maxLength={72}
            autoComplete="new-password"
            placeholder="At least 8 characters"
          />
        </label>

        <label>
          Full Name
          <input
            type="text"
            value={form.full_name}
            onChange={update('full_name')}
            required
            autoComplete="name"
          />
        </label>

        <label>
          Organization Name
          <input
            type="text"
            value={form.organization_name}
            onChange={update('organization_name')}
            required
          />
        </label>

        <label>
          Role
          <select value={form.role} onChange={update('role')}>
            {ROLE_OPTIONS.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </label>

        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? 'Signing up…' : 'Sign Up'}
        </button>
      </form>
    </div>
  )
}
