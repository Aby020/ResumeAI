import { motion } from 'motion/react'
import { scoreTier, toneFill, toneText } from '../../lib/utils/score'
import { cn } from '../../lib/utils/cn'

interface SignalSpectrumProps {
  /** Current signal value (0–100), or null while awaiting a score. */
  score: number | null
  /**
   * `full` (default) renders the standalone product panel with its own
   * heading and tier legend. `compact` drops the heading and legend so the
   * spectrum can live inside a card that owns its label (the signal row).
   */
  variant?: 'full' | 'compact'
  className?: string
}

const TIERS = [
  { name: 'Excellent', tone: 'excellent', min: 90 },
  { name: 'Strong', tone: 'good', min: 75 },
  { name: 'Solid', tone: 'moderate', min: 60 },
  { name: 'Developing', tone: 'weak', min: 40 },
] as const

/** Scale tick positions (percent) where tier hairlines are drawn. */
const TIER_TICKS = [40, 60, 75, 90]

/**
 * The workspace's signature product visualization — a horizontal career
 * signal spectrum. The current ATS value lands on a 0–100 scale with tier
 * boundaries, so "where my resume sits" reads at a glance. Always driven by
 * the real score; an awaiting state keeps the spectrum honest.
 */
export function SignalSpectrum({
  score,
  variant = 'full',
  className,
}: SignalSpectrumProps) {
  const clamped = score === null ? null : Math.min(100, Math.max(0, score))
  const tier = score === null ? null : scoreTier(score)
  const markerLeft = clamped === null ? 0 : Math.min(96, Math.max(4, clamped))
  const fillWidth = clamped === null ? '0%' : `${clamped}%`

  const track = (
    <div className="relative mt-8">
        {/* Marker chip */}
        {score !== null && clamped !== null && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.5 }}
            transition={{ duration: 0.35, ease: 'easeOut', delay: 0.4 }}
            className="absolute -top-5 -translate-x-1/2"
            style={{ left: `${markerLeft}%` }}
            aria-hidden="true"
          >
            <div className="flex flex-col items-center gap-1">
              <span
                className={cn(
                  'rounded-md border border-line bg-surface px-2.5 py-1 font-display text-lg font-bold tabular-nums shadow-sm',
                  tier && toneText[tier.tone],
                )}
              >
                {clamped}
              </span>
              <span className="h-2 w-px bg-line-strong" />
            </div>
          </motion.div>
        )}

        {/* Track */}
        <div className="relative">
          <div
            className="h-1.5 w-full overflow-visible rounded-full bg-surface-3"
            role="img"
            aria-label={
              score === null
                ? 'Career signal spectrum, no score yet'
                : `Career signal spectrum, current score ${score} out of 100, ${tier?.label}`
            }
          >
            <motion.div
              className={cn('h-full rounded-full', score !== null && toneFill[tier!.tone])}
              initial={{ width: 0 }}
              whileInView={{ width: fillWidth }}
              viewport={{ once: true, amount: 0.5 }}
              transition={{ duration: 0.7, ease: 'easeOut', delay: 0.15 }}
              aria-hidden="true"
            />
          </div>

          {/* Tier boundary hairlines */}
          {TIER_TICKS.map((mark) => (
            <span
              key={mark}
              aria-hidden="true"
              className="absolute top-1/2 hidden h-3.5 w-px -translate-y-1/2 bg-line-strong sm:block"
              style={{ left: `${mark}%` }}
            />
          ))}

          {/* Scale labels */}
          <div className="mt-2 flex items-center justify-between font-mono text-[10px] uppercase tracking-wider text-muted" aria-hidden="true">
            <span>0</span>
            <span className="hidden sm:inline">25</span>
            <span>50</span>
            <span className="hidden sm:inline">75</span>
            <span>100</span>
          </div>
        </div>
      </div>
    )

  if (variant === 'compact') {
    return <div className={className}>{track}</div>
  }

  return (
    <section
      className={className}
      aria-labelledby="spectrum-heading"
      aria-describedby={score === null ? undefined : 'spectrum-summary'}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2
          id="spectrum-heading"
          className="flex items-center gap-3 font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary"
        >
          <span aria-hidden="true" className="h-px w-6 bg-primary" />
          Career signal spectrum
        </h2>
        <p id="spectrum-summary" className="font-mono text-xs text-muted">
          {score === null ? 'Waiting on your first score' : `Now · ${score}/100 · ${tier?.label}`}
        </p>
      </div>

      {track}

      {/* Tier legend */}
      <ul className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-line pt-4">
        {TIERS.map((t) => (
          <li key={t.name} className="flex items-center gap-2">
            <span aria-hidden="true" className={cn('h-1.5 w-1.5 rounded-full', toneFill[t.tone])} />
            <span className="text-xs font-medium text-text-soft">
              {t.name}
              <span className="ml-1 font-mono text-[10px] text-muted">≥{t.min}</span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}