import { Link } from 'react-router-dom'
import { Container } from '../shared/Container'

const PRODUCT_LINKS = [
  { label: 'Features', href: '#capabilities' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Insights', href: '#insights' },
  { label: 'Progress', href: '#progress' },
]

const ACCOUNT_LINKS = [
  { label: 'Sign In', to: '/sign-in' },
  { label: 'Get Started', to: '/sign-up' },
  { label: 'Dashboard', to: '/dashboard' },
]

export function LandingFooter() {
  return (
    <footer className="bg-surface-2">
      <Container className="py-14">
        <div className="grid gap-10 md:grid-cols-[1.5fr_1fr_1fr]">
          {/* Brand */}
          <div className="max-w-xs">
            <Link to="/" className="inline-flex items-center gap-2.5">
              <span className="inline-grid h-8 w-8 place-items-center rounded-md bg-primary text-on-primary text-sm font-bold">
                R
              </span>
              <span className="font-display text-lg font-bold tracking-tight text-ink">
                Resume<span className="text-primary">AI</span>
              </span>
            </Link>
            <p className="mt-4 text-sm leading-relaxed text-text-soft">
              Career intelligence for your resume — ATS scoring, job matching and AI-assisted
              improvements that turn every application into a stronger one.
            </p>
          </div>

          {/* Product */}
          <nav aria-label="Product">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">Product</h3>
            <ul className="mt-4 space-y-2.5">
              {PRODUCT_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-text-soft transition-colors duration-base hover:text-ink"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          {/* Account */}
          <nav aria-label="Account">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">Account</h3>
            <ul className="mt-4 space-y-2.5">
              {ACCOUNT_LINKS.map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-sm text-text-soft transition-colors duration-base hover:text-ink"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="mt-12 flex flex-col gap-2 border-t border-line pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-muted">© 2026 ResumeAI. All rights reserved.</p>
          <p className="text-xs text-muted">Built for people building careers, one resume at a time.</p>
        </div>
      </Container>
    </footer>
  )
}