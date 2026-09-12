import { motion } from 'motion/react'

/**
 * The product-facing panel on the authentication pages' right half (desktop
 * only). A compact, restrained preview of ResumeAI's career intelligence —
 * score tiles, a skill-split and a suggestion — so authentication visually
 * connects to the product. All figures are illustrative example data.
 *
 * Panel entrance uses the same short fade-and-rise language as the landing
 * page and respects the global reduced-motion switch (MotionConfig).
 */
export function AuthVisual() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: 'easeOut', delay: 0.15 }}
      className="w-full max-w-md"
    >
      <p className="font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary">
        Resume intelligence
      </p>

      <div className="mt-5 overflow-hidden rounded-lg border border-line bg-surface shadow-md">
        {/* Panel header */}
        <div className="flex items-center justify-between border-b border-line bg-surface-2 px-5 py-3.5">
          <p className="font-display text-sm font-bold text-ink">Your resume, scored</p>
          <span className="inline-flex items-center gap-1.5 rounded border border-primary/30 bg-primary-faint px-2 py-0.5 text-[11px] font-medium text-primary">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden="true" />
            Live analysis
          </span>
        </div>

        <div className="space-y-5 p-5">
          {/* Score tiles */}
          <div className="grid grid-cols-2 gap-3">
            <ScoreTile label="ATS readiness" score={87} tone="good" delay={0.3} />
            <ScoreTile label="Job match" score={82} tone="good" delay={0.4} />
          </div>

          {/* Skill split */}
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wider text-muted">
              Skill analysis
            </p>
            <div className="mt-2.5 space-y-2">
              <SkillRow
                label="Matched requirements"
                progress={86}
                className="text-success"
                barClassName="bg-success"
              />
              <SkillRow
                label="Missing from resume"
                progress={32}
                className="text-warning"
                barClassName="bg-warning"
              />
            </div>
          </div>

          {/* Suggestion */}
          <div className="rounded-md border-l-2 border-primary bg-primary-faint px-4 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-primary">
              Suggested edit
            </p>
            <p className="mt-1 text-sm leading-relaxed text-text">
              Quantify two achievements under{' '}
              <span className="font-medium text-ink">Product Strategy</span> to move the score.
            </p>
          </div>
        </div>
      </div>

      <p className="mt-4 flex items-center gap-2 text-xs text-muted">
        <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden="true" />
        Every score comes with the specific edit that improves it.
      </p>
    </motion.div>
  )
}

function ScoreTile({
  label,
  score,
  tone,
  delay,
}: {
  label: string
  score: number
  tone: 'good' | 'moderate' | 'weak'
  delay: number
}) {
  const barClass =
    tone === 'good' ? 'bg-score-good' : tone === 'moderate' ? 'bg-score-moderate' : 'bg-score-poor'
  return (
    <div className="rounded-md border border-line bg-surface-2 p-3.5">
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted">{label}</p>
      <div className="mt-1 flex items-baseline gap-1">
        <span className="font-display text-2xl font-bold tabular-nums text-ink">{score}</span>
        <span className="text-xs text-muted">/100</span>
      </div>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-surface-3">
        <motion.div
          className={barClass}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.6, ease: 'easeOut', delay }}
          aria-hidden="true"
        />
      </div>
    </div>
  )
}

function SkillRow({
  label,
  progress,
  className,
  barClassName,
}: {
  label: string
  progress: number
  className: string
  barClassName: string
}) {
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className={className}>{label}</span>
        <span className="font-mono tabular-nums text-muted">{progress}%</span>
      </div>
      <div className="mt-1 h-1 overflow-hidden rounded-full bg-surface-3">
        <motion.div
          className={barClassName}
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.55, ease: 'easeOut', delay: 0.55 }}
          aria-hidden="true"
        />
      </div>
    </div>
  )
}