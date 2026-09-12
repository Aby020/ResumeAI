import { Link } from 'react-router-dom'

/**
 * Workspace shortcuts — a compact full-width action strip. Each action is a
 * quiet icon + title + supporting line (never a large card), with a brand
 * tagline anchored to the right on wide screens.
 */

function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
      <path d="M12 15V4m0 0 3.5 3.5M12 4 8.5 7.5" />
      <path d="M4 20h16" />
    </svg>
  )
}

function HistoryIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </svg>
  )
}

function ProfileIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 19.5c1.3-3.6 3.9-5.5 7-5.5s5.7 1.9 7 5.5" />
    </svg>
  )
}

const ACTIONS = [
  { label: 'Upload resume', note: 'Score your next version', to: '/upload', Icon: UploadIcon },
  { label: 'View history', note: 'Every analysis at a glance', to: '/history', Icon: HistoryIcon },
  { label: 'Edit profile', note: 'Keep your details current', to: '/profile', Icon: ProfileIcon },
]

export function QuickActions() {
  return (
    <div className="border-t border-line pt-6">
      <h2 className="font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary">
        Quick actions
      </h2>
      <div className="mt-4 flex flex-col justify-between gap-6 lg:flex-row lg:items-center">
        <nav
          className="flex flex-col gap-x-10 gap-y-5 sm:flex-row sm:flex-wrap"
          aria-label="Quick actions"
        >
          {ACTIONS.map(({ label, note, to, Icon }) => (
            <Link
              key={to}
              to={to}
              className="group inline-flex items-center gap-3 text-text transition-colors duration-base hover:text-ink"
            >
              <span
                aria-hidden="true"
                className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-line bg-surface text-text-soft transition-colors duration-base group-hover:border-primary group-hover:text-primary"
              >
                <Icon />
              </span>
              <span>
                <span className="block text-sm font-medium">{label}</span>
                <span className="mt-0.5 block text-xs text-muted">{note}</span>
              </span>
            </Link>
          ))}
        </nav>
        <div className="shrink-0 text-right">
          <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted">
            Better resumes. Brighter opportunities.
          </p>
          <p className="mt-1 font-display text-sm font-semibold text-ink">
            ResumeAI
          </p>
        </div>
      </div>
    </div>
  )
}
