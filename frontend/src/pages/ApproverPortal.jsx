import { useEffect, useMemo, useState } from 'react'

import {
  getContract,
  listContracts,
  updateObligationStatus,
} from '../contractsApi.js'

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString() : '—'
}

const DEADLINE_WINDOW_DAYS = 30
const SOON_DAYS = 7

// "YYYY-MM-DD" as a local date so day math never shifts across time zones.
function parseDateOnly(value) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function todayLocal() {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), now.getDate())
}

// Highlight classes: overdue (red), due within SOON_DAYS (accent).
function daysLeftLabel(value) {
  const days = Math.round((parseDateOnly(value) - todayLocal()) / 86_400_000)
  const plural = (n) => (n === 1 ? '' : 's')
  if (days < 0) {
    return { text: `${-days} day${plural(-days)} overdue`, cls: 'deadline-overdue' }
  }
  if (days === 0) {
    return { text: 'Due today', cls: 'deadline-soon' }
  }
  if (days <= SOON_DAYS) {
    return { text: `Due in ${days} day${plural(days)}`, cls: 'deadline-soon' }
  }
  return { text: `Due in ${days} days`, cls: '' }
}

export default function ApproverPortal() {
  const [contracts, setContracts] = useState([])
  const [pendingObligations, setPendingObligations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  // Approve/Reject in flight (obligation id) + per-row result notices.
  const [actingId, setActingId] = useState(null)
  const [rowNotices, setRowNotices] = useState({})

  // Upcoming deadlines: pending (draft) obligations with a due date inside
  // the window, earliest first — overdue rows sort to the top naturally.
  // Derived from the same queue state, so live approve/reject updates it too.
  const upcoming = useMemo(() => {
    const horizon = todayLocal()
    horizon.setDate(horizon.getDate() + DEADLINE_WINDOW_DAYS)
    return pendingObligations
      .filter((o) => o.status === 'draft' && o.due_date)
      .filter((o) => parseDateOnly(o.due_date) <= horizon)
      .sort((a, b) => a.due_date.localeCompare(b.due_date) || a.id - b.id)
  }, [pendingObligations])

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const list = await listContracts()
        // The list endpoint only has counts; fetch details for the obligations.
        const details = await Promise.all(list.map((c) => getContract(c.id)))
        if (cancelled) return

        const drafts = []
        for (const detail of details) {
          for (const obligation of detail.obligations) {
            if (obligation.status === 'draft') {
              drafts.push({ ...obligation, contract_title: detail.title })
            }
          }
        }
        // Earliest due date first; obligations without a date come last.
        drafts.sort((a, b) => {
          if (a.due_date && b.due_date) return a.due_date.localeCompare(b.due_date)
          if (a.due_date) return -1
          if (b.due_date) return 1
          return a.id - b.id
        })

        setContracts(list)
        setPendingObligations(drafts)
        setError(null)
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  async function onDecide(obligation, status) {
    setRowNotices((prev) => ({ ...prev, [obligation.id]: null }))
    setActingId(obligation.id)
    try {
      const updated = await updateObligationStatus(obligation.id, status)
      // Live badge update: keep the row in the queue with its new status.
      setPendingObligations((rows) =>
        rows.map((row) =>
          row.id === updated.id ? { ...row, status: updated.status } : row,
        ),
      )
      setRowNotices((prev) => ({
        ...prev,
        [obligation.id]: {
          type: 'success',
          text: `Obligation marked ${updated.status}.`,
        },
      }))
    } catch (err) {
      setRowNotices((prev) => ({
        ...prev,
        [obligation.id]: { type: 'error', text: err.message },
      }))
    } finally {
      setActingId(null)
    }
  }

  return (
    <main className="page page-wide">
      <h2>Approver Portal</h2>

      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">Loading review queue…</p>}

      {!loading && !error && (
        <>
          <section className="card portal-section">
            <h3>Pending Contracts</h3>
            <p className="muted">
              Contracts submitted by analysts in your organization.
            </p>
            {contracts.length === 0 ? (
              <p className="muted">No contracts awaiting review.</p>
            ) : (
              <div className="table-scroll">
                <table className="table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Title</th>
                      <th>Parties</th>
                      <th>Obligations</th>
                      <th>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {contracts.map((contract) => (
                      <tr key={contract.id}>
                        <td>{contract.id}</td>
                        <td>
                          <strong>{contract.title}</strong>
                        </td>
                        <td>
                          {contract.parties.map((p) => p.name).join(', ') || '—'}
                        </td>
                        <td>{contract.obligation_count}</td>
                        <td>{formatDate(contract.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="card portal-section">
            <h3>Obligations Awaiting Approval</h3>
            <p className="muted">
              Draft obligations waiting for your approve or reject decision.
            </p>
            {pendingObligations.length === 0 ? (
              <p className="muted">All caught up — nothing to review.</p>
            ) : (
              <div className="table-scroll">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Contract</th>
                      <th>Obligation</th>
                      <th>Due date</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingObligations.map((obligation) => {
                      const notice = rowNotices[obligation.id]
                      const busy = actingId === obligation.id
                      return (
                        <tr key={obligation.id}>
                          <td>
                            #{obligation.contract_id} {obligation.contract_title}
                          </td>
                          <td>{obligation.description}</td>
                          <td>{formatDate(obligation.due_date)}</td>
                          <td>
                            <span className={`badge badge-${obligation.status}`}>
                              {obligation.status}
                            </span>
                          </td>
                          <td className="queue-actions">
                            {obligation.status === 'draft' ? (
                              <>
                                <button
                                  className="btn btn-primary btn-small"
                                  type="button"
                                  disabled={busy}
                                  onClick={() => onDecide(obligation, 'approved')}
                                >
                                  {busy ? 'Saving…' : 'Approve'}
                                </button>
                                <button
                                  className="btn btn-danger btn-small"
                                  type="button"
                                  disabled={busy}
                                  onClick={() => onDecide(obligation, 'rejected')}
                                >
                                  {busy ? 'Saving…' : 'Reject'}
                                </button>
                              </>
                            ) : (
                              <span className="muted">Reviewed</span>
                            )}
                            {notice && <p className={notice.type}>{notice.text}</p>}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}

      {/* Rendered while the queue loads too, so the section has its own
          loading and empty states instead of vanishing. */}
      {!error && (
        <section className="card portal-section">
          <h3>Upcoming Deadlines</h3>
          <p className="muted">
            Pending obligations due in the next {DEADLINE_WINDOW_DAYS} days;
            overdue items appear first.
          </p>
          {loading ? (
            <p className="loading">Loading deadlines…</p>
          ) : upcoming.length === 0 ? (
            <p className="muted">
              No pending obligations are due in the next {DEADLINE_WINDOW_DAYS}{' '}
              days.
            </p>
          ) : (
            <div className="table-scroll">
              <table className="table">
                <thead>
                  <tr>
                    <th>Due date</th>
                    <th>Days left</th>
                    <th>Contract</th>
                    <th>Obligation</th>
                  </tr>
                </thead>
                <tbody>
                  {upcoming.map((obligation) => {
                    const label = daysLeftLabel(obligation.due_date)
                    return (
                      <tr key={obligation.id}>
                        <td>{formatDate(obligation.due_date)}</td>
                        <td className={label.cls}>{label.text}</td>
                        <td>
                          #{obligation.contract_id} {obligation.contract_title}
                        </td>
                        <td>{obligation.description}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </main>
  )
}
