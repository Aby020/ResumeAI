import { motion } from 'motion/react'
import { useCountUp } from '../../hooks/useCountUp'
import { scoreTier, toneFill, toneText } from '../../lib/utils/score'
import { cn } from '../../lib/utils/cn'

interface SignalBandProps {
  /** Short label, e.g. "ATS — how systems read your resume". */
  label: string
  /** Score on the 0–100 scale; null renders an "Awaiting" state. */
  score: number | null
  /** Supporting caption under the track (e.g. the latest analysis). */
  detail?: string
  /** Number size. Larger for the primary signal, compact for secondary. */
  size?: 'lg' | 'md'
  className?: string
}

/**
 * The primary horizontal signal visualization: a descriptor, a large
 * count-up number and a linear track that fills to the score. Linear bars
 * (never rings) are the house style — the value is always text as well, so
 * the reading never depends on color or fill alone.
 */
export function SignalBand({
  label,
  score,
  detail,
  size = 'lg',
  className,
}: SignalBandProps) {
  const tier = scoreTier(score ?? 0)
  const animated = useCountUp(score ?? 0, { duration: 0.75 })
  const hasScore = score !== null
  const width = hasScore ? `${Math.min(100, Math.max(0, score))}%` : '0%'

  return (
    <div className={className}>
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-sm font-medium text-text">{label}</p>
        <p className={cn('font-mono text-xs uppercase tracking-wider', hasScore ? toneText[tier.tone] : 'text-muted')}>
          {hasScore ? tier.label : 'Awaiting'}
        </p>
      </div>

      <div className="mt-2 flex items-baseline gap-1.5">
        <span
          className={cn(
            'font-display font-bold tabular-nums leading-none tracking-tight text-ink',
            size === 'lg' ? 'text-4xl lg:text-5xl' : 'text-3xl',
          )}
        >
          {hasScore ? animated : '—'}
        </span>
        <span className="text-sm text-muted">/100</span>
      </div>

      <div className="mt-4" aria-hidden="true">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-3">
          <motion.div
            className={cn('h-full rounded-full', hasScore && toneFill[tier.tone])}
            initial={{ width: 0 }}
            whileInView={{ width }}
            viewport={{ once: true, amount: 0.5 }}
            transition={{ duration: 0.6, ease: 'easeOut', delay: 0.15 }}
          />
        </div>
      </div>

      {detail && <p className="mt-2.5 text-xs leading-relaxed text-muted">{detail}</p>}
    </div>
  )
}