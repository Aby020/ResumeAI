import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { Container } from '../shared/Container'
import { Button } from '../ui/Button'
import { ThemeToggle } from '../ui/ThemeToggle'

interface PageShellProps {
  children: ReactNode
}

/**
 * Application shell for authenticated pages — a slim sticky header (brand,
 * theme toggle, auth actions) over a themed <main>. Deliberately minimal:
 * real navigation comes when the app pages are designed.
 */
export function PageShell({ children }: PageShellProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleSignOut(): Promise<void> {
    await logout()
    navigate('/')
  }

  return (
    <div className="flex min-h-dvh flex-col bg-bg">
      <header className="sticky top-0 z-40 border-b border-line bg-bg/85 backdrop-blur-sm">
        <Container className="flex h-14 items-center justify-between gap-4">
          <Link
            to="/"
            className="font-display text-base font-semibold tracking-tight text-ink"
          >
            Resume<span className="text-primary">AI</span>
          </Link>

          <div className="flex items-center gap-1">
            <ThemeToggle />
            {user ? (
              <Button variant="ghost" size="sm" onClick={handleSignOut}>
                Sign out
              </Button>
            ) : (
              <Link
                to="/sign-in"
                className="inline-flex h-8 items-center rounded-md px-3 text-sm font-medium text-text transition-colors duration-base hover:bg-surface-3 hover:text-text"
              >
                Sign in
              </Link>
            )}
          </div>
        </Container>
      </header>

      <main className="flex-1">
        <Container className="py-8">{children}</Container>
      </main>
    </div>
  )
}