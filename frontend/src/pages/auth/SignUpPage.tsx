import { useRef, useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { AuthLayout } from '../../components/auth/AuthLayout'
import { AuthVisual } from '../../components/auth/AuthVisual'
import { AuthField } from '../../components/auth/AuthField'
import { PasswordField } from '../../components/auth/PasswordField'
import { Button } from '../../components/ui/Button'
import { ApiError } from '../../types/api-error'
import { cn } from '../../lib/utils/cn'

/**
 * Mirrors the backend's password complexity checks (account_manager
 * RegisterSerializer) so users get instant feedback. Frontend checks are
 * supplementary only — the API remains the authority.
 */
const [SPECIAL_RE, UPPER_RE, LOWER_RE, NUMBER_RE] = [
  /[!@#$%^&*(),.?":{}|<>]/,
  /[A-Z]/,
  /[a-z]/,
  /\d/,
]

// Django's default username rule: letters, digits, and @/./+/-/_ only.
const USERNAME_RE = /^[\w.@+-]+$/

const REQUIREMENTS = [
  { id: 'length', label: 'At least 8 characters', check: (v: string) => v.length >= 8 },
  { id: 'upper', label: 'One uppercase letter', check: (v: string) => UPPER_RE.test(v) },
  { id: 'lower', label: 'One lowercase letter', check: (v: string) => LOWER_RE.test(v) },
  { id: 'number', label: 'One number', check: (v: string) => NUMBER_RE.test(v) },
  { id: 'special', label: 'One special character', check: (v: string) => SPECIAL_RE.test(v) },
]

function readFieldError(error: ApiError, field: string): string | undefined {
  const messages = error.fieldErrors?.[field]
  if (!messages) return undefined
  return Array.isArray(messages) ? messages[0] : messages
}

function collectFieldErrors(error: ApiError): Record<string, string> {
  const next: Record<string, string> = {}
  for (const [key, message] of Object.entries(error.fieldErrors ?? {})) {
    if (key !== 'non_field_errors') {
      next[key] = Array.isArray(message) ? message[0] : message
    }
  }
  return next
}

/**
 * Premium sign-up page. The form mirrors the registration API (first name,
 * username, email, password, confirm password) and calls the real endpoint —
 * AuthContext.register logs the new user in immediately afterwards, so a
 * successful sign-up lands on the dashboard.
 */
export function SignUpPage() {
  useDocumentTitle('Create account')
  const { user, isLoading, register } = useAuth()
  const navigate = useNavigate()

  const [firstName, setFirstName] = useState('')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Guard the Navigator: after a successful register the auth context already
  // logs the user in, so refuse the "already signed in" redirect once we're
  // about to navigate ourselves (avoids racing the destination).
  const justRegistered = useRef(false)

  // Already authenticated — signed-in users don't need to register again.
  // (Ref read is intentional: it prevents Navigate from racing the
  // post-register imperative navigate() in the same commit.)
  // eslint-disable-next-line react/refs
  if (!isLoading && user && !justRegistered.current) {
    return <Navigate to="/dashboard" replace />
  }

  const metRequirements = password
    ? REQUIREMENTS.filter((req) => req.check(password))
    : []
  const passwordsMatch = password.length > 0 && password === confirmPassword
  const showMatchWarning = confirmPassword.length > 0 && !passwordsMatch

  function validateField(name: string, value: string): string | undefined {
    switch (name) {
      case 'username':
        if (!value.trim()) return 'Choose a username.'
        if (!USERNAME_RE.test(value)) {
          return 'Letters, numbers, and @ . + - _ only.'
        }
        return undefined
      case 'email':
        if (!value.trim()) return 'Enter your email address.'
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())) {
          return 'Enter a valid email address.'
        }
        return undefined
      default:
        return undefined
    }
  }

  function handleBlur(name: string, value: string): void {
    setFieldErrors((prev) => {
      const msg = validateField(name, value)
      const next = { ...prev }
      if (msg) next[name] = msg
      else delete next[name]
      return next
    })
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    setFormError(null)

    const next: Record<string, string> = {}
    const u = username.trim()
    const e = email.trim()

    const usernameError = validateField('username', u)
    const emailError = validateField('email', e)
    if (usernameError) next.username = usernameError
    if (emailError) next.email = emailError

    if (!password) {
      next.password = 'Choose a password.'
    } else if (metRequirements.length < REQUIREMENTS.length) {
      next.password = 'Meet all password requirements below.'
    }
    if (confirmPassword !== password) {
      next.confirmPassword = 'Passwords must match.'
    }

    setFieldErrors(next)
    if (Object.keys(next).length > 0) return

    setSubmitting(true)
    try {
      await register({
        first_name: firstName.trim(),
        username: u,
        email: e,
        password,
        confirm_password: confirmPassword,
      })
      justRegistered.current = true
      navigate('/dashboard', { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        const field = collectFieldErrors(err)
        const confirmed = readFieldError(err, 'confirm_password')
        if (confirmed) field.confirmPassword = confirmed
        setFieldErrors(field)
        if (!err.hasFieldErrors() || Object.keys(field).length === 0) {
          setFormError(err.message)
        }
      } else {
        setFormError('Something went wrong. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout visual={<AuthVisual />}>
      <h1 className="font-display text-3xl font-bold leading-tight tracking-tight text-ink">
        Start building a resume that gets read
      </h1>
      <p className="mt-2.5 text-sm leading-relaxed text-text-soft">
        Analyze your resume, match it against the jobs you want and uncover the
        strengths and gaps that move the score.
      </p>

      {formError && (
        <div
          role="alert"
          className="mt-6 rounded-md border border-danger/40 bg-danger-soft px-4 py-3 text-sm font-medium text-danger"
        >
          {formError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-7 space-y-5" noValidate>
        <AuthField
          label="First name"
          name="first_name"
          type="text"
          value={firstName}
          onChange={(event) => setFirstName(event.target.value)}
          placeholder="Dana"
          autoComplete="given-name"
          disabled={submitting}
        />
        <AuthField
          label="Username"
          name="username"
          type="text"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          onBlur={() => handleBlur('username', username)}
          error={fieldErrors.username}
          placeholder="dana.whitfield"
          autoComplete="username"
          disabled={submitting}
        />
        <AuthField
          label="Email"
          name="email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          onBlur={() => handleBlur('email', email)}
          error={fieldErrors.email}
          placeholder="you@company.com"
          autoComplete="email"
          disabled={submitting}
        />

        <div>
          <PasswordField
            label="Password"
            name="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            error={fieldErrors.password}
            placeholder="Create a password"
            autoComplete="new-password"
            disabled={submitting}
          />
          <PasswordRequirements
            password={password}
            metCount={metRequirements.length}
          />
        </div>

        <PasswordField
          label="Confirm password"
          name="confirm_password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          error={showMatchWarning ? 'Passwords must match.' : fieldErrors.confirmPassword}
          placeholder="Repeat your password"
          autoComplete="new-password"
          disabled={submitting}
        />

        <Button type="submit" variant="primary" size="lg" fullWidth loading={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </Button>
      </form>

      <p className="mt-6 text-sm text-text-soft">
        Already have an account?{' '}
        <Link
          to="/sign-in"
          className="font-medium text-primary transition-colors duration-base hover:text-primary-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        >
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}

function PasswordRequirements({
  password,
  metCount,
}: {
  password: string
  metCount: number
}) {
  if (!password) return null

  return (
    <div className="mt-2.5 rounded-md border border-line bg-surface-2 px-3.5 py-3">
      <p className="text-[11px] font-medium uppercase tracking-wider text-muted">
        Password requirements
        <span className="ml-1.5 font-mono normal-case tracking-normal text-primary">
          {metCount}/{REQUIREMENTS.length}
        </span>
      </p>
      <ul className="mt-2 grid gap-1.5 sm:grid-cols-2">
        {REQUIREMENTS.map((req) => {
          const met = req.check(password)
          return (
            <li
              key={req.id}
              className={cn(
                'flex items-center gap-2 text-sm transition-colors duration-base',
                met ? 'text-success' : 'text-text-soft',
              )}
            >
              <CheckIcon checked={met} />
              {req.label}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function CheckIcon({ checked }: { checked: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        'inline-grid h-4 w-4 shrink-0 place-items-center rounded-full border',
        checked
          ? 'border-success/40 bg-success-soft'
          : 'border-line-strong bg-surface',
      )}
    >
      <svg
        className={cn('h-2.5 w-2.5', checked ? 'text-success' : 'text-transparent')}
        viewBox="0 0 12 12"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M2 6.5 4.5 9 10 3.5" />
      </svg>
    </span>
  )
}

