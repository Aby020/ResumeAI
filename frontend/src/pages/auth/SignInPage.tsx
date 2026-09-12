import { useRef, useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { AuthLayout } from '../../components/auth/AuthLayout'
import { AuthVisual } from '../../components/auth/AuthVisual'
import { AuthField } from '../../components/auth/AuthField'
import { PasswordField } from '../../components/auth/PasswordField'
import { Button } from '../../components/ui/Button'
import { ApiError } from '../../types/api-error'

/**
 * Premium sign-in page. Fields live on the left with the product visual on the
 * right; the form calls the real auth API (never fake authentication). On
 * success the user is sent back to the page that redirected them here (the
 * async flow records `state.from`), or to the dashboard by default.
 */
export function SignInPage() {
  useDocumentTitle('Sign in')
  const { user, isLoading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  // Set right before the post-login navigate() so the "already signed in"
  // <Navigate> below doesn't fire and override the destination the visitor
  // was originally headed for (both would race in the same commit otherwise).
  const justLoggedIn = useRef(false)

  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Already authenticated — don't drag signed-in users back through the flow.
  // (Ref read is intentional: it prevents Navigate from racing the post-login
  // imperative navigate() in the same commit.)
  // eslint-disable-next-line react/refs
  if (!isLoading && user && !justLoggedIn.current) {
    return <Navigate to="/dashboard" replace />
  }

  // One field accepts an email *or* a username — the backend's login
  // serializer resolves either (EmailOrUsernameTokenObtainPairSerializer).
  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    setFormError(null)
    setFieldErrors({})

    const trimmed = identifier.trim()
    if (!trimmed) {
      setFieldErrors((prev) => ({ ...prev, username: 'Enter your email or username.' }))
      return
    }
    if (!password) {
      setFieldErrors((prev) => ({ ...prev, password: 'Enter your password.' }))
      return
    }

    setSubmitting(true)
    try {
      await login({ username: trimmed, password })
      justLoggedIn.current = true
      navigate(from, { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.hasFieldErrors()) {
          const next: Record<string, string> = {}
          for (const [key, message] of Object.entries(err.fieldErrors ?? {})) {
            next[key] = Array.isArray(message) ? message[0] : message
          }
          setFieldErrors(next)
        } else {
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
        Continue your analysis
      </h1>
      <p className="mt-2.5 text-sm leading-relaxed text-text-soft">
        Your resume scores, insights and recommended edits are exactly where you left them.
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
          label="Email or username"
          name="username"
          type="text"
          value={identifier}
          onChange={(event) => setIdentifier(event.target.value)}
          error={fieldErrors.username}
          placeholder="you@company.com"
          autoComplete="username"
          disabled={submitting}
        />
        <PasswordField
          label="Password"
          name="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={fieldErrors.password}
          placeholder="••••••••"
          autoComplete="current-password"
          disabled={submitting}
        />
        <Button type="submit" variant="primary" size="lg" fullWidth loading={submitting}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>

      <p className="mt-6 text-sm text-text-soft">
        New to ResumeAI?{' '}
        <Link
          to="/sign-up"
          className="font-medium text-primary transition-colors duration-base hover:text-primary-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        >
          Create an account
        </Link>
      </p>
    </AuthLayout>
  )
}