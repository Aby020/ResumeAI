import type { ReactNode } from 'react'
import { cn } from '../../lib/utils/cn'

interface SectionLabelProps {
  children: ReactNode
  className?: string
  /** When set, the label is an accessible heading with this id. */
  id?: string
}

/**
 * Mono uppercase eyebrow with a short teal hairline — the shared section
 * label used across workspace pages so every header reads consistently
 * (dashboard, upload, analysis, history, profile).
 */
export function SectionLabel({ children, className, id }: SectionLabelProps) {
  return (
    <h2
      id={id}
      className={cn(
        'flex items-center gap-3 font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary',
        className,
      )}
    >
      <span aria-hidden="true" className="h-px w-6 bg-primary" />
      {children}
    </h2>
  )
}