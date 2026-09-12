/**
 * Theme context — light / dark / system.
 *
 * Persists to the same `resumeAI.theme` key the Django templates use
 * (static/js/theme-init.js), so a toggle here is honored by the Django app
 * and vice-versa. The index.html bootstrap script applies `data-theme` before
 * React mounts to prevent a flash of unstyled content; this provider keeps it
 * in sync and reacts to OS `prefers-color-scheme` changes when "system".
 */

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useLocalStorage } from '../hooks/useLocalStorage'

export type ThemePreference = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

const THEME_STORAGE_KEY = 'resumeAI.theme'
/** Stored values the Django bootstrap script understands. */
const PREF_TO_STORED: Record<ThemePreference, string> = {
  light: 'light',
  dark: 'dark',
  system: 'system',
}

interface ThemeContextValue {
  /** The user's chosen preference — never the resolved OS value. */
  preference: ThemePreference
  /** What has actually been applied to the document. */
  theme: ResolvedTheme
  setPreference: (next: ThemePreference) => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

function systemPrefersDark(): boolean {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches
  )
}

function readStoredPreference(): ThemePreference {
  try {
    const raw = window.localStorage.getItem(THEME_STORAGE_KEY)
    if (raw === 'light' || raw === 'dark' || raw === 'system') return raw
  } catch {
    /* fall through to default */
  }
  return 'system'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useLocalStorage<ThemePreference>(
    THEME_STORAGE_KEY,
    readStoredPreference(),
  )

  // System-level dark preference; kept in state so we re-render on changes.
  const [systemDark, setSystemDark] = useState<boolean>(systemPrefersDark)

  const resolved: ResolvedTheme =
    preference === 'system' ? (systemDark ? 'dark' : 'light') : preference

  useEffect(() => {
    const mql = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = (event: MediaQueryListEvent): void =>
      setSystemDark(event.matches)
    if (typeof mql.addEventListener === 'function') {
      mql.addEventListener('change', onChange)
      return () => mql.removeEventListener('change', onChange)
    }
    mql.addListener(onChange)
    return () => mql.removeListener(onChange)
  }, [])

  // Apply the resolved theme to the document root. Reflects the same
  // attribute the Django bootstrap script set pre-hydration.
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolved)
    document.documentElement.style.colorScheme = resolved
  }, [resolved])

  // Keep the stored value in the Django-compatible shape.
  useEffect(() => {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, PREF_TO_STORED[preference])
    } catch {
      /* storage unavailable */
    }
  }, [preference])

  const value = useMemo<ThemeContextValue>(
    () => ({ preference, theme: resolved, setPreference: setPreferenceState }),
    [preference, resolved, setPreferenceState],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    throw new Error('useTheme must be used within a <ThemeProvider>')
  }
  return ctx
}