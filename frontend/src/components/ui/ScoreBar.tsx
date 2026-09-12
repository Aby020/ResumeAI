import { motion } from 'motion/react'
import { cn } from '../../lib/utils/cn'
import { scoreTier, toneFill, toneText } from '../../lib/utils/score'

interface ScoreBarProps {
  /** Category label, e.g. "Contact & Links". */
  label: string
  /** Current score on the category scale. */
  score: number
  /** The scale the score sits on; defaults to 100. */
  max?: number
  /** Optional caption under the track. */
  detail?: string
  className?: string
}

/**
 * Compact horizontal score bar for per-category values (the ATS rubric and
 * history rows). Linear bars, never rings, are the house style; the value and
 * tier always render as text so the reading never depends on color alone.
 */
export function ScoreBar({ label, score, max = 100, detail, className }: ScoreBarProps) {
  const percent = max > 0 ? (score / max) * 100 : 0
  const clamped = Math.min(100, Math.max(0, percent))
  const tier = scoreTier(clamped)
  const width = `${clamped}%`

  return (
    <div className={cn('min-w-0', className)}>
      <div className="flex items-baseline justify-between gap-3">
        <p className="truncate text-sm font-medium text-text">{label}</p>
        <div className="flex shrink-0 items-baseline gap-2">
          <span
            className={cn('font-mono text-xs uppercase tracking-wider', toneText[tier.tone])}
          >
            {tier.label}
          </span>
          <span className="font-mono text-sm tabular-nums text-ink">
            {score}
            {max !== 100 && <span className="text-muted">/{max}</span>}
          </span>
        </div>
      </div>
      <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-surface-3" aria-hidden="true">
        <motion.div
          className={cn('h-full rounded-full', toneFill[tier.tone])}
          initial={{ width: 0 }}
          whileInView={{ width }}
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
      {detail && <p className="mt-1 text-xs leading-relaxed text-muted">{detail}</p>}
    </div>
  )
}