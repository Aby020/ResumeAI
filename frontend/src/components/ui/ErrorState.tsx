import { Button } from './Button'
import { cn } from '../../lib/utils/cn'

interface ErrorStateProps {
  /** Short, human heading, e.g. "Couldn't load your analysis". */
  title: string
  /** Supporting detail — the API message, a hint, etc. */
  description?: string
  /** When present, show a retry button that calls this. */
  onRetry?: () => void
  className?: string
}

/** Centered error state with an optional retry action. */
export function ErrorState({
  title,
  description,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 py-16 text-center',
        className,
      )}
      role="alert"
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-danger-soft text-danger">
        <svg
          className="h-5 w-5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <path d="M12 9v4m0 4h.01" />
          <circle cx="12" cy="12" r="9" />
        </svg>
      </div>
      <div>
        <p className="font-medium text-ink">{title}</p>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} className="mt-1">
          Try again
        </Button>
      )}
    </div>
  )
}