import { Spinner } from './Button'
import { cn } from '../../lib/utils/cn'

interface LoadingStateProps {
  /** Optional label under the spinner. */
  label?: string
  className?: string
}

/** Centered loading state for async sections and full-page fetches. */
export function LoadingState({ label = 'Loading…', className }: LoadingStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 py-16 text-muted',
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <Spinner className="h-6 w-6 text-primary" />
      <p className="text-sm">{label}</p>
    </div>
  )
}