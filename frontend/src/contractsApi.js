// ContractOps contracts API helpers, built on the shared api() wrapper.
// All calls require a Bearer token; role rules are enforced by the backend
// (writes: analyst, reads: analyst/approver/admin).
import { api } from './api.js'

export function listContracts() {
  return api('/contracts')
}

export function getContract(id) {
  return api(`/contracts/${id}`)
}

// payload: { title, source_id, parties: [names], obligations: [{description, due_date}] }
export function createContract(payload) {
  return api('/contracts', { method: 'POST', body: payload })
}

export function addParty(contractId, name) {
  return api(`/contracts/${contractId}/parties`, {
    method: 'POST',
    body: { name },
  })
}

// payload: { description, due_date }
export function addObligation(contractId, payload) {
  return api(`/contracts/${contractId}/obligations`, {
    method: 'POST',
    body: payload,
  })
}

// Multipart upload of a PDF/Word file; returns the new DocumentVersion row.
export function uploadContractFile(contractId, file) {
  const form = new FormData()
  form.append('file', file)
  return api(`/contracts/${contractId}/upload`, { method: 'POST', body: form })
}

// Approver/admin decision on a draft obligation: 'approved' or 'rejected'.
export function updateObligationStatus(obligationId, status) {
  return api(`/obligations/${obligationId}/status`, {
    method: 'POST',
    body: { status },
  })
}
