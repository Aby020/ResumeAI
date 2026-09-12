import type { ReactNode } from 'react'
import { cn } from '../../lib/utils/cn'

interface PanelProps {
  children: ReactNode
  className?: string
  /** Optional top bar (split by its own border-b). */
  header?: ReactNode
  /** Semantic/anchoring id, e.g. to pair with an aria-labelledby label. */
  id?: string
}

/**
 * Restrained bordered surface — the shared workspace "panel" recipe
 * (`border-line · bg-surface`). Every content block on the workspace pages
 * uses it so cards, lists and forms read as one system.
 */
export function Panel({ children, className, header, id }: PanelProps) {
  return (
    <section id={id} className={cn('border border-line bg-surface', className)}>
      {header !== undefined && (
        <div className="border-b border-line px-6 py-4">{header}</div>
      )}
      {children}
    </section>
  )
}