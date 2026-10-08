import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

import { api, clearToken, getToken, setToken } from './api'

const AuthContext = createContext(null)

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => getToken())
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(() => getToken() != null)

  const logout = useCallback(() => {
    clearToken()
    setTokenState(null)
    setUser(null)
  }, [])

  // api.js already clears the token on any 401; this drops the user state too.
  useEffect(() => {
    const onUnauthorized = () => {
      setTokenState(null)
      setUser(null)
    }
    window.addEventListener('auth:unauthorized', onUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', onUnauthorized)
  }, [])

  // Startup: if a token exists, ask the backend who we are.
  useEffect(() => {
    if (!getToken()) {
      return
    }
    let cancelled = false
    api('/auth/me')
      .then((me) => {
        if (!cancelled) setUser(me)
      })
      .catch(() => {
        // 401 is handled by the event above; other errors leave user null.
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await api('/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    setToken(data.access_token)
    setTokenState(data.access_token)
    const me = await api('/auth/me')
    setUser(me)
    return me
  }, [])

  const signup = useCallback(
    async (payload) => {
      await api('/auth/signup', { method: 'POST', body: payload })
      // Account created — sign in right away.
      return login(payload.email, payload.password)
    },
    [login],
  )

  const refreshUser = useCallback(async () => {
    const me = await api('/auth/me')
    setUser(me)
    return me
  }, [])

  const value = useMemo(
    () => ({ token, user, loading, login, signup, logout, refreshUser }),
    [token, user, loading, login, signup, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
