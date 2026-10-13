import { NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth.jsx'

const LINKS_BY_ROLE = {
  analyst: [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/analyst', label: 'Contracts' },
  ],
  approver: [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/approver', label: 'Approvals' },
  ],
  admin: [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/admin', label: 'Users' },
  ],
}

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const links = [
    ...(LINKS_BY_ROLE[user?.role] ?? [{ to: '/dashboard', label: 'Dashboard' }]),
    // Every role can open their own account page.
    { to: '/profile', label: 'Profile' },
  ]

  function onLogout() {
    logout()
    navigate('/')
  }

  return (
    <nav className="navbar">
      <span className="navbar-brand">ContractOps</span>
      <div className="navbar-links">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to}>
            {link.label}
          </NavLink>
        ))}
        <button className="nav-logout" type="button" onClick={onLogout}>
          Logout
        </button>
      </div>
    </nav>
  )
}
