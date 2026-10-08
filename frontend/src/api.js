// Central fetch wrapper for the ContractOps backend (http://localhost:8000).
// - Attaches Authorization: Bearer <token> when a token is stored
// - Parses JSON responses
// - Turns FastAPI error payloads (detail string or validation list) into
//   readable Error objects that also carry .status and .data

export const API_URL = 'http://localhost:8000'
const TOKEN_KEY = 'contractops_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

function extractMessage(status, data) {
  if (data && typeof data.detail === 'string') {
    return data.detail
  }
  if (data && Array.isArray(data.detail)) {
    return data.detail
      .map((issue) => `${issue.loc?.join('.')}: ${issue.msg}`)
      .join('; ')
  }
  return `Request failed with status ${status}`
}

export async function api(path, { method = 'GET', body } = {}) {
  const headers = {}
  const token = getToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  const text = await response.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = null
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      // Token missing, invalid or expired: drop it and tell the app to log out.
      clearToken()
      window.dispatchEvent(new Event('auth:unauthorized'))
    }
    const error = new Error(extractMessage(response.status, data))
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}
