import { useEffect, useState } from 'react'

import { getContract, listContracts } from '../contractsApi.js'

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString() : '—'
}

export default function ApproverPortal() {
  const [contracts, setContracts] = useState([])
  const [pendingObligations, setPendingObligations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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
              Draft obligations waiting for confirm, correct or reject.
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
                    </tr>
                  </thead>
                  <tbody>
                    {pendingObligations.map((obligation) => (
                      <tr key={obligation.id}>
                        <td>#{obligation.contract_id} {obligation.contract_title}</td>
                        <td>{obligation.description}</td>
                        <td>{formatDate(obligation.due_date)}</td>
                        <td>
                          <span className="badge badge-draft">
                            {obligation.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </main>
  )
}
