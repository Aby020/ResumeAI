/**
 * JWT storage. Tokens live in localStorage (same-origin only; the access
 * token is short-lived at 15 min and the refresh token 7 days). Every read
 * is wrapped in try/catch because localStorage can throw in private/limited
 * browsing modes — in that case the app runs unauthenticated and clears.
 */

const ACCESS_KEY = 'resumeAI.access_token'
const REFRESH_KEY = 'resumeAI.refresh_token'

function read(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    /* storage unavailable — session is memory-only until it is cleared */
  }
}

function remove(key: string): void {
  try {
    window.localStorage.removeItem(key)
  } catch {
    /* ignore */
  }
}

export const tokenStorage = {
  getAccessToken(): string | null {
    return read(ACCESS_KEY)
  },
  getRefreshToken(): string | null {
    return read(REFRESH_KEY)
  },
  setAccessToken(token: string): void {
    write(ACCESS_KEY, token)
  },
  setRefreshToken(token: string): void {
    write(REFRESH_KEY, token)
  },
  setTokens(access: string, refresh: string): void {
    write(ACCESS_KEY, access)
    write(REFRESH_KEY, refresh)
  },
  clear(): void {
    remove(ACCESS_KEY)
    remove(REFRESH_KEY)
  },
}