/**
 * Auth context — the single source of truth for "who is logged in".
 *
 * On mount it hydrates from stored tokens (fetching /auth/me/), and exposes
 * login / register / logout. `register` follows the API contract: register
 * returns a bare User (no tokens), so it logs the new user in afterwards.
 */

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  fetchCurrentUser,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
} from '../lib/api/auth'
import { tokenStorage } from '../lib/api/token-storage'
import type { LoginPayload, RegisterPayload, User } from '../types/models'

interface AuthContextValue {
  /** The logged-in user, or null while unauthenticated. */
  user: User | null
  /** True while the initial token-hydration check runs. */
  isLoading: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
  /** Replace the current user (e.g. after a successful profile update). */
  setUser: (user: User | null) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  // Hydrate from stored tokens on first mount.
  useEffect(() => {
    let active = true

    async function hydrate(): Promise<void> {
      if (!tokenStorage.getAccessToken()) {
        if (active) setIsLoading(false)
        return
      }
      try {
        const me = await fetchCurrentUser()
        if (active) setUser(me)
      } catch {
        // Token expired / invalid — drop the stored tokens.
        tokenStorage.clear()
      } finally {
        if (active) setIsLoading(false)
      }
    }

    void hydrate()
    return () => {
      active = false
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      async login(payload: LoginPayload): Promise<void> {
        await apiLogin(payload)
        const me = await fetchCurrentUser()
        setUser(me)
      },
      async register(payload: RegisterPayload): Promise<void> {
        await apiRegister(payload)
        await apiLogin({ username: payload.username, password: payload.password })
        const me = await fetchCurrentUser()
        setUser(me)
      },
      async logout(): Promise<void> {
        await apiLogout()
        setUser(null)
      },
      setUser,
    }),
    [user, isLoading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an <AuthProvider>')
  }
  return ctx
}