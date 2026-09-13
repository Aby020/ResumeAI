import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { ThemeToggle } from '../ui/ThemeToggle'
import { ResumeAILogo } from '../shared/ResumeAILogo'
import { cn } from '../../lib/utils/cn'

/**
 * Workspace navigation — the authenticatd product bar. A refined top rail
 * (brand · contextual links · theme · user) rather than a permanent sidebar:
 * the workspace reads as a product, not an admin console. On small screens
 * the links collapse into a slide-down panel.
 */

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Overview' },
  { to: '/upload', label: 'Upload resume' },
  { to: '/history', label: 'History' },
  { to: '/profile', label: 'Profile' },
]

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return cn(
    'relative inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors duration-base',
    isActive ? 'text-ink' : 'text-text-soft hover:text-ink',
  )
}

/** Initials for the avatar chip — "Ada Lovelace" → "AL". */
function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  const first = parts[0][0] ?? ''
  const last = parts[parts.length - 1][0] ?? ''
  return (first + last).toUpperCase()
}

export function WorkspaceNav() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const displayName = user?.first_name?.trim() || user?.username || ''

  async function handleSignOut(): Promise<void> {
    // Navigate to the public landing FIRST, then log out. Plain navigate() is
    // wrapped in startTransition, so the "/" commit is deferred — logout's
    // user-state flip would then re-render the still-mounted protected route
    // with user null and let ProtectedRoute's /sign-in redirect replace the
    // pending navigation. flushSync commits the landing before the session
    // clears, so the guard never sees a signed-out user on a protected route.
    navigate('/', { replace: true, flushSync: true })
    await logout()
  }

  // Close the user menu on outside click or Escape.
  useEffect(() => {
    if (!menuOpen) return
    function onPointerDown(e: PointerEvent): void {
      if (!menuRef.current?.contains(e.target as Node)) setMenuOpen(false)
    }
    function onKey(e: KeyboardEvent): void {
      if (e.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [menuOpen])

  // Close the mobile panel on Escape too.
  useEffect(() => {
    if (!mobileOpen) return
    function onKey(e: KeyboardEvent): void {
      if (e.key === 'Escape') setMobileOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [mobileOpen])

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/90 backdrop-blur-sm">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link to="/dashboard" aria-label="ResumeAI — back to your overview">
          <ResumeAILogo size={26} showWordmark />
        </Link>

        {/* Desktop nav */}
        <nav
          className="hidden items-center gap-1 md:flex"
          aria-label="Workspace"
        >
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} className={navLinkClass}>
              {({ isActive }) => (
                <>
                  {item.label}
                  {isActive && (
                    <span
                      aria-hidden="true"
                      className="absolute -bottom-[3px] left-1/2 h-0.5 w-5 -translate-x-1/2 rounded-full bg-primary"
                    />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Desktop actions */}
        <div className="hidden items-center gap-2 md:flex">
          <ThemeToggle />
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              className="inline-flex h-9 items-center gap-2 rounded-md border border-line bg-surface px-2 text-sm font-medium text-text transition-colors duration-base hover:border-line-strong hover:bg-surface-2"
              onClick={() => setMenuOpen((o) => !o)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
            >
              <span
                aria-hidden="true"
                className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-semibold text-on-primary"
              >
                {initials(displayName)}
              </span>
              <span className="hidden max-w-28 truncate sm:inline">{displayName}</span>
              <svg
                aria-hidden="true"
                className={cn(
                  'h-3.5 w-3.5 text-muted transition-transform duration-base',
                  menuOpen && 'rotate-180',
                )}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="m6 9 6 6 6-6" />
              </svg>
            </button>
            {menuOpen && (
              <div
                role="menu"
                aria-label="Account"
                className="absolute right-0 top-11 w-56 overflow-hidden rounded-lg border border-line bg-surface shadow-md"
              >
                <div className="border-b border-line px-4 py-3">
                  <p className="truncate text-sm font-medium text-ink">{displayName}</p>
                  {user?.email && (
                    <p className="mt-0.5 truncate text-xs text-muted">{user.email}</p>
                  )}
                </div>
                <div className="p-1.5">
                  <NavLink
                    to="/profile"
                    role="menuitem"
                    onClick={() => setMenuOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        'block rounded-md px-3 py-2 text-sm font-medium transition-colors duration-base hover:bg-surface-3',
                        isActive ? 'text-primary' : 'text-text',
                      )
                    }
                  >
                    Your profile
                  </NavLink>
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => void handleSignOut()}
                    className="block w-full rounded-md px-3 py-2 text-left text-sm font-medium text-text transition-colors duration-base hover:bg-surface-3"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Mobile: theme toggle + menu */}
        <div className="flex items-center gap-1 md:hidden">
          <ThemeToggle />
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-md text-text-soft transition-colors duration-base hover:bg-surface-3 hover:text-text"
            onClick={() => setMobileOpen((o) => !o)}
            aria-expanded={mobileOpen}
            aria-controls="workspace-mobile-nav"
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileOpen ? (
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            ) : (
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile panel */}
      {mobileOpen && (
        <div
          id="workspace-mobile-nav"
          className="border-t border-line bg-bg md:hidden"
          role="navigation"
          aria-label="Workspace"
        >
          <div className="mx-auto w-full max-w-7xl px-4 py-3 sm:px-6">
            <nav className="flex flex-col gap-0.5" aria-label="Workspace">
              {NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      'rounded-md px-3 py-2.5 text-sm font-medium transition-colors duration-base',
                      isActive
                        ? 'bg-primary-faint text-primary'
                        : 'text-text hover:bg-surface-3',
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
            <div className="my-2 border-t border-line" />
            <button
              type="button"
              onClick={() => {
                setMobileOpen(false)
                void handleSignOut()
              }}
              className="w-full rounded-md px-3 py-2.5 text-left text-sm font-medium text-text transition-colors duration-base hover:bg-surface-3"
            >
              Sign out
            </button>
          </div>
        </div>
      )}
    </header>
  )
}