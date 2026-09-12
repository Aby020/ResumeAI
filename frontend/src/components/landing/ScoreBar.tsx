import { motion } from 'motion/react'
import { cn } from '../../lib/utils/cn'

export type ScoreTone = 'good' | 'moderate' | 'weak'

const toneClasses: Record<ScoreTone, string> = {
  good: 'bg-score-good',
  moderate: 'bg-score-moderate',
  weak: 'bg-score-poor',
}

interface ScoreBarProps {
  /** Optional category name. When omitted, renders bar-only (for score tiles). */
  label?: string
  /** Score on the 0–100 scale. The bar fills to this percentage. */
  score: number
  tone?: ScoreTone
  /** Stagger delay (seconds) so a group of bars fills in sequence. */
  delay?: number
  className?: string
}

/**
 * The core ResumeAI data visualization: a slim linear score bar.
 *
 * Linear bars (not rings) are the house style — they read as precise and
 * "system-like". The score is always rendered as text beside the bar, so the
 * value never depends on color or fill alone.
 */
export function ScoreBar({ label, score, tone = 'good', delay = 0, className }: ScoreBarProps) {
  const width = `${Math.min(100, Math.max(0, score))}%`
  return (
    <div className={className}>
      {label && (
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-sm font-medium text-text">{label}</span>
          <span className="font-mono text-xs tabular-nums text-muted">{score}/100</span>
        </div>
      )}
      <div className={cn('h-1.5 overflow-hidden rounded-full bg-surface-3', label && 'mt-1.5')}>
        <motion.div
          className={cn('h-full rounded-full', toneClasses[tone])}
          initial={{ width: 0 }}
          whileInView={{ width }}
          viewport={{ once: true, amount: 0.4 }}
          transition={{ duration: 0.55, ease: 'easeOut', delay }}
          aria-hidden="true"
        />
      </div>
    </div>
  )
}