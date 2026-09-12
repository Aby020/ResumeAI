import type { ReactNode } from 'react'
import { motion } from 'motion/react'
import { fadeUp } from '../../motion/variants'

interface WorkspaceHeaderProps {
  /** Small mono eyebrow above the title, e.g. "Career intelligence". */
  eyebrow?: string
  /** The page title (rendered as an <h1>). */
  title: ReactNode
  /** One-line supporting copy under the title. */
  subtitle?: ReactNode
  /** Right-aligned primary actions (e.g. an "Analyze resume" link). */
  actions?: ReactNode
}

/**
 * Editorial page header for workspace pages — eyebrow · display title ·
 * supporting line · right-aligned actions. Shared by dashboard pages so the
 * header rhythm stays consistent across the workspace.
 */
export function WorkspaceHeader({
  eyebrow,
  title,
  subtitle,
  actions,
}: WorkspaceHeaderProps) {
  return (
    <motion.header variants={fadeUp} initial="hidden" animate="visible">
      {eyebrow && (
        <p className="flex items-center gap-3 font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary">
          <span aria-hidden="true" className="h-px w-6 bg-primary" />
          {eyebrow}
        </p>
      )}
      <div className="mt-3 flex flex-wrap items-end justify-between gap-x-6 gap-y-4">
        <h1 className="font-display text-2xl font-bold leading-[1.15] tracking-tight text-ink sm:text-3xl">
          {title}
        </h1>
        {actions && <div className="flex shrink-0 items-center gap-3">{actions}</div>}
      </div>
      {subtitle && (
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-text-soft sm:text-base">
          {subtitle}
        </p>
      )}
    </motion.header>
  )
}