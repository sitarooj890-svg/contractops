import { useEffect, useState } from 'react'

import {
  addObligation,
  createContract,
  getContract,
  listContracts,
  uploadContractFile,
} from '../contractsApi.js'

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString() : '—'
}

export default function AnalystPortal() {
  const [contracts, setContracts] = useState([])
  const [loading, setLoading] = useState(true)
  const [listError, setListError] = useState(null)

  // New contract form
  const [title, setTitle] = useState('')
  const [sourceId, setSourceId] = useState('')
  const [partiesText, setPartiesText] = useState('')
  const [contractError, setContractError] = useState(null)
  const [contractSuccess, setContractSuccess] = useState(null)
  const [savingContract, setSavingContract] = useState(false)

  // Manual obligation form
  const [obligationContractId, setObligationContractId] = useState('')
  const [description, setDescription] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [obligationError, setObligationError] = useState(null)
  const [obligationSuccess, setObligationSuccess] = useState(null)
  const [savingObligation, setSavingObligation] = useState(false)

  // File uploads (per contract id)
  const [uploadingId, setUploadingId] = useState(null)
  const [uploadNotices, setUploadNotices] = useState({})

  async function refresh() {
    try {
      const list = await listContracts()
      // The list endpoint only has counts; details carry the file versions.
      const details = await Promise.all(list.map((c) => getContract(c.id)))
      setContracts(details)
      setListError(null)
    } catch (err) {
      setListError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  // Default the obligation form to the newest contract until the user picks one.
  useEffect(() => {
    if (!obligationContractId && contracts.length > 0) {
      setObligationContractId(String(contracts[0].id))
    }
  }, [contracts, obligationContractId])

  async function onCreateContract(event) {
    event.preventDefault()
    setContractError(null)
    setContractSuccess(null)
    setSavingContract(true)
    try {
      const parties = partiesText
        .split(',')
        .map((name) => name.trim())
        .filter(Boolean)
      const contract = await createContract({
        title: title.trim(),
        source_id: sourceId.trim() || null,
        parties,
      })
      setContractSuccess(`Contract #${contract.id} created.`)
      setTitle('')
      setSourceId('')
      setPartiesText('')
      await refresh()
      setObligationContractId(String(contract.id))
    } catch (err) {
      setContractError(err.message)
    } finally {
      setSavingContract(false)
    }
  }

  async function onAddObligation(event) {
    event.preventDefault()
    setObligationError(null)
    setObligationSuccess(null)
    setSavingObligation(true)
    try {
      const obligation = await addObligation(obligationContractId, {
        description: description.trim(),
        due_date: dueDate || null,
      })
      setObligationSuccess(
        `Obligation #${obligation.id} added to contract #${obligationContractId}.`,
      )
      setDescription('')
      setDueDate('')
      await refresh()
    } catch (err) {
      setObligationError(err.message)
    } finally {
      setSavingObligation(false)
    }
  }

  async function onUpload(event, contractId) {
    event.preventDefault()
    const form = event.currentTarget
    const file = form.elements.file.files[0]
    setUploadNotices((prev) => ({ ...prev, [contractId]: null }))
    if (!file) {
      setUploadNotices((prev) => ({
        ...prev,
        [contractId]: { type: 'error', text: 'Choose a file to upload.' },
      }))
      return
    }
    setUploadingId(contractId)
    try {
      const version = await uploadContractFile(contractId, file)
      setUploadNotices((prev) => ({
        ...prev,
        [contractId]: {
          type: 'success',
          text: `Uploaded ${version.file_name} as v${version.version_number}.`,
        },
      }))
      form.reset()
      await refresh()
    } catch (err) {
      setUploadNotices((prev) => ({
        ...prev,
        [contractId]: { type: 'error', text: err.message },
      }))
    } finally {
      setUploadingId(null)
    }
  }

  return (
    <main className="page page-wide">
      <h2>Analyst Portal</h2>

      <div className="card-grid">
        <section className="card">
          <h3>Create Contract</h3>
          {contractError && <p className="error">{contractError}</p>}
          {contractSuccess && <p className="success">{contractSuccess}</p>}
          <form className="form" onSubmit={onCreateContract}>
            <label>
              Title
              <input
                type="text"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                required
                maxLength={500}
                placeholder="MSA with Acme Corp"
              />
            </label>
            <label>
              Source ID
              <input
                type="text"
                value={sourceId}
                onChange={(event) => setSourceId(event.target.value)}
                maxLength={255}
                placeholder="Optional — e.g. SRC-001"
              />
            </label>
            <label>
              Parties
              <input
                type="text"
                value={partiesText}
                onChange={(event) => setPartiesText(event.target.value)}
                placeholder="Comma-separated names"
              />
            </label>
            <button className="btn btn-primary" type="submit" disabled={savingContract}>
              {savingContract ? 'Creating…' : 'Create Contract'}
            </button>
          </form>
        </section>

        <section className="card">
          <h3>Add Manual Obligation</h3>
          {obligationError && <p className="error">{obligationError}</p>}
          {obligationSuccess && <p className="success">{obligationSuccess}</p>}
          <form className="form" onSubmit={onAddObligation}>
            <label>
              Contract
              <select
                value={obligationContractId}
                onChange={(event) => setObligationContractId(event.target.value)}
                disabled={contracts.length === 0}
              >
                {contracts.length === 0 && <option value="">No contracts yet</option>}
                {contracts.map((contract) => (
                  <option key={contract.id} value={contract.id}>
                    #{contract.id} — {contract.title}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Description
              <input
                type="text"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                required
                maxLength={5000}
                placeholder="Send quarterly report"
              />
            </label>
            <label>
              Due date
              <input
                type="date"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
              />
            </label>
            <button
              className="btn btn-primary"
              type="submit"
              disabled={savingObligation || contracts.length === 0}
            >
              {savingObligation ? 'Adding…' : 'Add Obligation'}
            </button>
          </form>
        </section>
      </div>

      <section className="card portal-section">
        <h3>Your Contracts</h3>
        {listError && <p className="error">{listError}</p>}
        {loading && <p className="loading">Loading contracts…</p>}
        {!loading && !listError && contracts.length === 0 && (
          <p className="muted">No contracts yet. Create your first contract above.</p>
        )}
        {!loading && contracts.length > 0 && (
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Parties</th>
                  <th>Obligations</th>
                  <th>Document</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {contracts.map((contract) => {
                  const notice = uploadNotices[contract.id]
                  return (
                    <tr key={contract.id}>
                      <td>{contract.id}</td>
                      <td>
                        <strong>{contract.title}</strong>
                        {contract.source_id && (
                          <div className="muted">{contract.source_id}</div>
                        )}
                      </td>
                      <td>
                        {contract.parties.map((p) => p.name).join(', ') || '—'}
                      </td>
                      <td>{contract.obligation_count}</td>
                      <td className="doc-cell">
                        <form
                          className="upload-form"
                          onSubmit={(event) => onUpload(event, contract.id)}
                        >
                          <input
                            type="file"
                            name="file"
                            accept=".pdf,.doc,.docx"
                            required
                            disabled={uploadingId === contract.id}
                          />
                          <button
                            className="btn btn-secondary btn-small"
                            type="submit"
                            disabled={uploadingId === contract.id}
                          >
                            {uploadingId === contract.id
                              ? 'Uploading…'
                              : 'Upload'}
                          </button>
                        </form>
                        {notice && (
                          <p className={notice.type}>{notice.text}</p>
                        )}
                        {contract.document_versions.length === 0 ? (
                          <p className="muted">No versions yet</p>
                        ) : (
                          <ul className="version-list">
                            {contract.document_versions.map((version) => (
                              <li key={version.id}>
                                v{version.version_number} — {version.file_name}
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>
                      <td>{formatDate(contract.created_at)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  )
}
