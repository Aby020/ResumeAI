import { motion } from 'motion/react'
import { fadeUp } from '../../motion/variants'
import { cn } from '../../lib/utils/cn'

interface SectionHeaderProps {
  eyebrow: string
  title: string
  description?: string
  align?: 'left' | 'center'
  className?: string
}

/**
 * Editorial section header: a mono eyebrow with a hairline rule, a display
 * headline, and optional supporting copy. Shared by every landing section so
 * the vertical rhythm stays consistent.
 */
export function SectionHeader({
  eyebrow,
  title,
  description,
  align = 'left',
  className,
}: SectionHeaderProps) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
      className={cn('max-w-2xl', align === 'center' && 'mx-auto text-center', className)}
    >
      <p className="flex items-center gap-3 font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary">
        <span aria-hidden="true" className="h-px w-6 bg-primary" />
        {eyebrow}
      </p>
      <h2 className="mt-4 font-display text-3xl font-bold leading-tight tracking-tight text-ink sm:text-4xl">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-base leading-relaxed text-text-soft sm:text-lg">{description}</p>
      )}
    </motion.div>
  )
}