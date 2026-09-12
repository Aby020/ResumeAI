import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { WorkspaceShell } from '../../components/workspace/WorkspaceShell'
import { WorkspaceHeader } from '../../components/workspace/WorkspaceHeader'
import { Panel } from '../../components/ui/Panel'
import { SectionLabel } from '../../components/ui/SectionLabel'
import { Button } from '../../components/ui/Button'
import { useAuth } from '../../contexts/AuthContext'
import { useTheme, type ThemePreference } from '../../contexts/ThemeContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { updateProfile } from '../../lib/api/auth'
import { ApiError } from '../../types/api-error'
import { formatDate } from '../../lib/utils/format'
import { cn } from '../../lib/utils/cn'
import { motion } from 'motion/react'
import { fadeUp } from '../../motion/variants'

type SectionKey = 'information' | 'account' | 'preferences' | 'security'

const SECTIONS: { key: SectionKey; label: string }[] = [
  { key: 'information', label: 'Profile information' },
  { key: 'account', label: 'Account' },
  { key: 'preferences', label: 'Preferences' },
  { key: 'security', label: 'Security' },
]

const THEME_OPTIONS: { value: ThemePreference; label: string; hint: string }[] = [
  { value: 'light', label: 'Light', hint: 'Warm paper surfaces' },
  { value: 'dark', label: 'Dark', hint: 'Deep ink workspace' },
  { value: 'system', label: 'System', hint: 'Follows your device' },
]

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const inputBase =
  'h-11 w-full rounded-md border border-line bg-surface-2 px-3.5 text-sm text-text placeholder:text-muted/70 ' +
  'transition-[border-color,box-shadow,background-color] duration-base ease-out ' +
  'focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-60'

type FieldErrors = Record<string, string | string[]>

function fieldMessage(errors: FieldErrors, field: string): string {
  const value = errors[field]
  if (Array.isArray(value)) return value[0] ?? ''
  return value ?? ''
}

/** Initials for the identity chip — "Ada Lovelace" → "AL". */
function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  const first = parts[0][0] ?? ''
  const last = parts[parts.length - 1][0] ?? ''
  return (first + last).toUpperCase()
}

function Field({
  id,
  label,
  error,
  children,
}: {
  id: string
  label: string
  error?: string
  children: ReactNode
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-text-soft">
        {label}
      </label>
      {children}
      {error !== undefined && error !== '' && (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  )
}

function InfoRow({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="flex flex-col gap-1 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
      <dt className="shrink-0 font-mono text-[10px] uppercase tracking-[0.15em] text-muted sm:w-40">
        {label}
      </dt>
      <dd className="text-sm font-medium text-ink">
        {value}
        {note && <span className="ml-2 text-xs font-normal text-muted">{note}</span>}
      </dd>
    </div>
  )
}

/**
 * Profile &amp; settings — a clean account workspace, not another analytics
 * dashboard. Every field comes from the real profile API: only `first_name`,
 * `last_name` and `email` are editable (the serializer's contract); username
 * and member-since are read-only. Security shows honest account facts and
 * sign out — no invented controls, since no password-change endpoint exists.
 * Theme preferences drive the existing shared theme system.
 */
export function ProfilePage() {
  useDocumentTitle('Profile')
  const { user, setUser, logout } = useAuth()
  const navigate = useNavigate()
  const { preference, setPreference } = useTheme()

  const [section, setSection] = useState<SectionKey>('information')

  // ProfilePage only mounts inside ProtectedRoute, so `user` is present at
  // first render — the form initializes straight from it (no sync effect).
  const [firstName, setFirstName] = useState(user?.first_name ?? '')
  const [lastName, setLastName] = useState(user?.last_name ?? '')
  const [email, setEmail] = useState(user?.email ?? '')
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState('')

  const savedTimer = useRef<number | null>(null)
  useEffect(
    () => () => {
      if (savedTimer.current !== null) window.clearTimeout(savedTimer.current)
    },
    [],
  )

  if (!user) return null

  const displayName = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()
  const identityName = displayName || user.username

  async function handleSave(): Promise<void> {
    const nextErrors: FieldErrors = {}
    if (!EMAIL_RE.test(email.trim())) {
      nextErrors.email = ['Enter a valid email address.']
    }
    setFieldErrors(nextErrors)
    setFormError('')
    if (Object.keys(nextErrors).length > 0) {
      setSaveState('error')
      return
    }

    setSaveState('saving')
    try {
      const updated = await updateProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
      })
      setUser(updated)
      setSaveState('saved')
      if (savedTimer.current !== null) window.clearTimeout(savedTimer.current)
      savedTimer.current = window.setTimeout(() => setSaveState('idle'), 2500)
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.hasFieldErrors()) {
          setFieldErrors(error.fieldErrors ?? {})
        } else {
          setFormError(error.message)
        }
      } else {
        setFormError("We couldn't save your profile right now.")
      }
      setSaveState('error')
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault()
    void handleSave()
  }

  async function handleSignOut(): Promise<void> {
    await logout()
    navigate('/')
  }

  const renderSection = (): ReactNode => {
    switch (section) {
      case 'account':
        return (
          <Panel header={<SectionLabel>Account</SectionLabel>}>
            <dl className="divide-y divide-line">
              <InfoRow label="Username" value={user.username} note="— used to sign in" />
              <InfoRow label="Email" value={user.email} />
              <InfoRow
                label="Member since"
                value={formatDate(user.date_joined ?? null)}
              />
            </dl>
            <div className="border-t border-line px-6 py-4">
              <p className="text-xs leading-relaxed text-muted">
                Username is a read-only identity for your account and can&rsquo;t be changed
                here.
              </p>
            </div>
          </Panel>
        )

      case 'preferences':
        return (
          <Panel header={<SectionLabel>Appearance &amp; preferences</SectionLabel>}>
            <div className="p-6 lg:p-7">
              <p className="text-sm font-medium text-ink">Theme</p>
              <p className="mt-1 text-sm leading-relaxed text-muted">
                Choose how the workspace looks. System follows your device settings and
                updates live.
              </p>
              <div className="mt-4 grid gap-2 sm:grid-cols-3" role="group" aria-label="Theme preference">
                {THEME_OPTIONS.map((option) => {
                  const active = preference === option.value
                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setPreference(option.value)}
                      aria-pressed={active}
                      className={cn(
                        'rounded-md border px-4 py-3 text-left transition-colors duration-base focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
                        active
                          ? 'border-primary bg-primary-faint'
                          : 'border-line bg-surface-2 hover:border-line-strong',
                      )}
                    >
                      <span
                        className={cn(
                          'block text-sm font-medium',
                          active ? 'text-primary' : 'text-ink',
                        )}
                      >
                        {option.label}
                      </span>
                      <span className="mt-1 block text-xs text-muted">{option.hint}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          </Panel>
        )

      case 'security':
        return (
          <Panel header={<SectionLabel>Security</SectionLabel>}>
            <div className="space-y-6 p-6 lg:p-7">
              <p className="text-sm text-text-soft">
                Signed in as <span className="font-medium text-ink">{user.email}</span>.
              </p>
              <ul className="space-y-3 border-t border-line pt-5">
                {[
                  'Passwords are stored as a secure hash, never in plain text.',
                  'Sessions use JWT access and refresh tokens that keep you signed in across the workspace.',
                  'Profile fields are updated through the authenticated profile API only.',
                ].map((fact) => (
                  <li key={fact} className="flex items-start gap-3 text-sm leading-relaxed text-text">
                    <span
                      aria-hidden="true"
                      className="mt-1.5 h-2 w-2 shrink-0 rotate-45 bg-primary"
                    />
                    <span className="min-w-0">{fact}</span>
                  </li>
                ))}
              </ul>
              <div className="border-t border-line pt-5">
                <p className="text-xs leading-relaxed text-muted">
                  Changing your password directly isn&rsquo;t available through the current
                  API — it&rsquo;s managed by sign-in and account creation.
                </p>
              </div>
              <div className="border-t border-line pt-5">
                <Button variant="secondary" onClick={() => void handleSignOut()}>
                  Sign out of this workspace
                </Button>
              </div>
            </div>
          </Panel>
        )

      default:
        return (
          <Panel header={<SectionLabel>Profile information</SectionLabel>}>
            <div className="space-y-6 p-6 lg:p-7">
              <div className="flex items-center gap-4">
                <span
                  aria-hidden="true"
                  className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-on-primary"
                >
                  {initials(identityName)}
                </span>
                <div className="min-w-0">
                  <p className="font-display text-lg font-bold tracking-tight text-ink">
                    {identityName}
                  </p>
                  <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
                    {user.username}
                  </p>
                </div>
              </div>

              <form noValidate onSubmit={handleSubmit} className="grid gap-5 sm:grid-cols-2">
                <Field
                  id="profile-first-name"
                  label="First name"
                  error={fieldMessage(fieldErrors, 'first_name')}
                >
                  <input
                    id="profile-first-name"
                    name="first_name"
                    type="text"
                    value={firstName}
                    onChange={(event) => setFirstName(event.target.value)}
                    className={cn(
                      inputBase,
                      fieldMessage(fieldErrors, 'first_name') !== '' &&
                        'border-danger focus:border-danger focus:ring-danger/25',
                    )}
                  />
                </Field>

                <Field
                  id="profile-last-name"
                  label="Last name"
                  error={fieldMessage(fieldErrors, 'last_name')}
                >
                  <input
                    id="profile-last-name"
                    name="last_name"
                    type="text"
                    value={lastName}
                    onChange={(event) => setLastName(event.target.value)}
                    className={cn(
                      inputBase,
                      fieldMessage(fieldErrors, 'last_name') !== '' &&
                        'border-danger focus:border-danger focus:ring-danger/25',
                    )}
                  />
                </Field>

                <div className="sm:col-span-2">
                  <Field id="profile-email" label="Email" error={fieldMessage(fieldErrors, 'email')}>
                    <input
                      id="profile-email"
                      name="email"
                      type="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      className={cn(
                        inputBase,
                        fieldMessage(fieldErrors, 'email') !== '' &&
                          'border-danger focus:border-danger focus:ring-danger/25',
                      )}
                    />
                  </Field>
                </div>

                <div className="flex flex-col gap-3 sm:col-span-2 sm:flex-row sm:items-center sm:justify-between">
                  {formError !== '' && (
                    <p role="alert" className="text-sm text-danger">
                      {formError}
                    </p>
                  )}
                  {saveState === 'saved' && (
                    <p role="status" className="text-sm font-medium text-success">
                      <span aria-hidden="true">✓ </span>Changes saved
                    </p>
                  )}
                  <div className="sm:ml-auto">
                    <Button type="submit" loading={saveState === 'saving'} disabled={saveState === 'saving'}>
                      {saveState === 'saving' ? 'Saving…' : 'Save changes'}
                    </Button>
                  </div>
                </div>
              </form>
            </div>
          </Panel>
        )
    }
  }

  return (
    <WorkspaceShell>
      <WorkspaceHeader
        eyebrow="Account"
        title="Profile &amp; settings"
        subtitle="Manage your identity, appearance and account security — one clean workspace."
      />

      <div className="mt-8 grid gap-6 lg:grid-cols-12">
        {/* Section navigation */}
        <nav aria-label="Profile sections" className="lg:col-span-3">
          <div className="flex gap-1 overflow-x-auto border border-line bg-surface p-2 lg:flex-col lg:overflow-visible">
            {SECTIONS.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setSection(item.key)}
                aria-current={section === item.key ? 'page' : undefined}
                className={cn(
                  'shrink-0 whitespace-nowrap rounded-md px-3 py-2.5 text-sm font-medium transition-colors duration-base',
                  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
                  section === item.key
                    ? 'bg-primary-faint text-primary'
                    : 'text-text-soft hover:bg-surface-3 hover:text-ink',
                )}
              >
                {item.label}
              </button>
            ))}
            <div className="mt-1 shrink-0 border-t border-line pt-1 lg:mt-2">
              <button
                type="button"
                onClick={() => void handleSignOut()}
                className={cn(
                  'w-full whitespace-nowrap rounded-md px-3 py-2.5 text-left text-sm font-medium transition-colors duration-base',
                  'text-text hover:bg-surface-3 hover:text-danger',
                )}
              >
                Sign out
              </button>
            </div>
          </div>
        </nav>

        {/* Active section */}
        <motion.div
          key={section}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="min-w-0 lg:col-span-9"
        >
          {renderSection()}
        </motion.div>
      </div>
    </WorkspaceShell>
  )
}