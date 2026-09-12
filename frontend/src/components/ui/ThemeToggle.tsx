import type { ReactNode } from 'react'
import { useTheme, type ThemePreference } from '../../contexts/ThemeContext'

const ORDER: ThemePreference[] = ['light', 'dark', 'system']

/** Next preference after the current one (light → dark → system → light). */
function nextPreference(current: ThemePreference): ThemePreference {
  const idx = ORDER.indexOf(current)
  return ORDER[(idx + 1) % ORDER.length]
}

function SunIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4m11.4-11.4 1.4-1.4" />
    </svg>
  )
}

function MoonIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
    </svg>
  )
}

function SystemIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="2" y="3" width="20" height="14" rx="2" />
      <path d="M8 21h8m-4-4v4" />
    </svg>
  )
}

const ICONS: Record<ThemePreference, (props: { className?: string }) => ReactNode> = {
  light: (props) => <SunIcon {...props} />,
  dark: (props) => <MoonIcon {...props} />,
  system: (props) => <SystemIcon {...props} />,
}

const LABELS: Record<ThemePreference, string> = {
  light: 'Light',
  dark: 'Dark',
  system: 'System',
}

/**
 * Cycles light → dark → system. The icon always shows the *active preference*,
 * and the title explains what the next click will do.
 */
export function ThemeToggle() {
  const { preference, setPreference } = useTheme()
  const next = nextPreference(preference)
  const Icon = ICONS[preference]

  return (
    <button
      type="button"
      className="inline-flex h-9 w-9 items-center justify-center rounded-md text-text-soft hover:bg-surface-3 hover:text-text transition-colors duration-base"
      onClick={() => setPreference(next)}
      title={`Theme: ${LABELS[preference]}. Click to switch to ${LABELS[next]}.`}
      aria-label={`Theme: ${LABELS[preference]}. Click to switch to ${LABELS[next]}.`}
    >
      <Icon className="h-[18px] w-[18px]" />
    </button>
  )
}