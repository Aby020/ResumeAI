import { Link } from 'react-router-dom'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { buttonClasses } from '../components/ui/Button'

export function NotFoundPage() {
  useDocumentTitle('Page not found')

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 bg-bg px-4 text-center">
      <p className="font-display text-6xl font-semibold text-primary">404</p>
      <h1 className="font-display text-xl font-semibold text-ink">
        This page doesn&apos;t exist
      </h1>
      <p className="max-w-sm text-sm text-muted">
        The link may be broken, or the page may have moved.
      </p>
      <Link to="/" className={buttonClasses('secondary', 'sm')}>
        Back to home
      </Link>
    </div>
  )
}