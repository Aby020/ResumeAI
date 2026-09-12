import { useState, useCallback, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ThemeToggle } from '../ui/ThemeToggle'
import { buttonClasses } from '../ui/Button'
import { Container } from '../shared/Container'
import { ResumeAILogo } from '../shared/ResumeAILogo'

const NAV_LINKS = [
  { label: 'Features', href: '#capabilities' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Insights', href: '#insights' },
]

export function LandingNav() {
  const [mobileOpen, setMobileOpen] = useState(false)

  const close = useCallback(() => setMobileOpen(false), [])

  // Close on Escape
  useEffect(() => {
    if (!mobileOpen) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') close()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [mobileOpen, close])

  // Close on route-hash link click
  function handleNavClick() {
    close()
  }

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/85 backdrop-blur-sm">
      <Container className="flex h-16 items-center justify-between gap-4">
        {/* Brand */}
        <Link to="/" aria-label="ResumeAI home">
          <ResumeAILogo size={28} showWordmark />
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-8 md:flex" aria-label="Main">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-text-soft transition-colors duration-base hover:text-ink"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Desktop actions */}
        <div className="hidden items-center gap-2 md:flex">
          <ThemeToggle />
          <Link
            to="/sign-in"
            className="inline-flex h-9 items-center rounded-md px-3.5 text-sm font-medium text-text transition-colors duration-base hover:bg-surface-3"
          >
            Sign In
          </Link>
          <Link to="/sign-up" className={buttonClasses('primary', 'sm')}>
            Get Started
          </Link>
        </div>

        {/* Mobile: theme toggle + hamburger */}
        <div className="flex items-center gap-1 md:hidden">
          <ThemeToggle />
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-md text-text-soft transition-colors duration-base hover:bg-surface-3 hover:text-text"
            onClick={() => setMobileOpen((o) => !o)}
            aria-expanded={mobileOpen}
            aria-controls="mobile-nav"
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
      </Container>

      {/* Mobile panel */}
      {mobileOpen && (
        <div
          id="mobile-nav"
          className="border-t border-line bg-bg md:hidden"
          role="navigation"
          aria-label="Mobile"
        >
          <Container className="flex flex-col gap-1 py-4">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={handleNavClick}
                className="rounded-md px-3 py-2.5 text-sm font-medium text-text transition-colors duration-base hover:bg-surface-3"
              >
                {link.label}
              </a>
            ))}
            <div className="my-2 border-t border-line" />
            <Link
              to="/sign-in"
              onClick={handleNavClick}
              className="rounded-md px-3 py-2.5 text-sm font-medium text-text transition-colors duration-base hover:bg-surface-3"
            >
              Sign In
            </Link>
            <Link
              to="/sign-up"
              onClick={handleNavClick}
              className={buttonClasses('primary', 'sm', 'mt-1')}
            >
              Get Started
            </Link>
          </Container>
        </div>
      )}
    </header>
  )
}