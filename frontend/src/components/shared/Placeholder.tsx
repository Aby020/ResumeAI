import type { ReactNode } from 'react'
import { motion } from 'motion/react'
import { fadeUp } from '../../motion/variants'

interface PlaceholderProps {
  title: string
  description: string
  children?: ReactNode
}

/**
 * Generic body for pages that are scaffolded but not yet designed. Rendered
 * inside PageShell; the card surface keeps placeholders from looking like a
 * bare "coming soon" page while the real layouts are being built.
 */
export function Placeholder({ title, description, children }: PlaceholderProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeUp}
      className="mx-auto flex max-w-xl flex-col items-center gap-4 rounded-lg border border-line bg-surface px-8 py-14 text-center shadow-sm"
    >
      <p className="font-display text-lg font-semibold text-ink">{title}</p>
      <p className="text-sm text-muted">{description}</p>
      {children && <div className="mt-2">{children}</div>}
    </motion.div>
  )
}