import { motion } from 'motion/react'

const MATCHING_SKILLS = ['Product Strategy', 'UX Research', 'Prototyping', 'Interaction Design']
const MISSING_SKILLS = ['Data Analysis', 'Design Systems']

/**
 * The hero's product visualization — a realistic ResumeAI analysis preview.
 *
 * Recreates the analysis panel look (window chrome, score tiles, linear bars,
 * skill chips, AI suggestion) so the product is demonstrated rather than
 * described. All figures are illustrative example data.
 */
export function ProductCard() {
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-surface shadow-lg">
      {/* Window chrome */}
      <div className="flex items-center justify-between border-b border-line bg-surface-2 px-4 py-3">
        <div className="flex items-center gap-1.5" aria-hidden="true">
          <span className="h-2.5 w-2.5 rounded-full bg-line-strong" />
          <span className="h-2.5 w-2.5 rounded-full bg-line" />
          <span className="h-2.5 w-2.5 rounded-full bg-line" />
        </div>
        <span className="font-mono text-[11px] uppercase tracking-wider text-muted">
          Resume Analysis
        </span>
        <span className="text-xs font-medium text-primary">View full report ↗</span>
      </div>

      <div className="space-y-5 p-5">
        {/* Resume identity */}
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-display text-base font-bold text-ink">Product Designer Resume</p>
            <p className="mt-0.5 font-mono text-xs text-muted">
              product-designer-resume.pdf · 1 page
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded border border-primary/30 bg-primary-faint px-2 py-1 text-[11px] font-medium text-primary">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden="true" />
            Ready
          </span>
        </div>

        {/* Score tiles */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg border border-line bg-surface-2 p-3.5">
            <p className="text-xs font-medium uppercase tracking-wide text-muted">ATS Readiness</p>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="font-display text-3xl font-bold tabular-nums text-ink">87</span>
              <span className="text-xs text-muted">/100</span>
            </div>
            <div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-surface-3">
              <motion.div
                className="h-full rounded-full bg-score-good"
                initial={{ width: 0 }}
                whileInView={{ width: '87%' }}
                viewport={{ once: true, amount: 0.4 }}
                transition={{ duration: 0.6, ease: 'easeOut', delay: 0.15 }}
              />
            </div>
          </div>
          <div className="rounded-lg border border-line bg-surface-2 p-3.5">
            <p className="text-xs font-medium uppercase tracking-wide text-muted">Job Match</p>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="font-display text-3xl font-bold tabular-nums text-primary">82</span>
              <span className="text-xs text-muted">/100</span>
            </div>
            <div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-surface-3">
              <motion.div
                className="h-full rounded-full bg-primary"
                initial={{ width: 0 }}
                whileInView={{ width: '82%' }}
                viewport={{ once: true, amount: 0.4 }}
                transition={{ duration: 0.6, ease: 'easeOut', delay: 0.25 }}
              />
            </div>
          </div>
        </div>

        {/* Skill split */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <p className="text-xs font-semibold text-success">Matching skills</p>
            <ul className="mt-2 flex flex-wrap gap-1.5">
              {MATCHING_SKILLS.map((skill) => (
                <li
                  key={skill}
                  className="rounded border border-success/30 bg-success-soft px-2 py-1 text-xs text-success"
                >
                  {skill}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold text-danger">Missing skills</p>
            <ul className="mt-2 flex flex-wrap gap-1.5">
              {MISSING_SKILLS.map((skill) => (
                <li
                  key={skill}
                  className="rounded border border-danger/30 bg-danger-soft px-2 py-1 text-xs text-danger"
                >
                  {skill}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* AI suggestion */}
        <div className="rounded-lg border border-line bg-primary-faint p-3.5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-primary">
            AI Suggestion
          </p>
          <p className="mt-1 text-sm leading-relaxed text-text">
            Quantify impact under{' '}
            <span className="font-medium text-ink">Product Strategy</span> — add metrics to your
            top two achievements. Estimated gain:{' '}
            <span className="font-medium text-ink">+6 ATS</span>.
          </p>
        </div>

        {/* Revision history */}
        <div className="flex items-center justify-between border-t border-line pt-3">
          <p className="text-[11px] font-medium uppercase tracking-wider text-muted">
            Revision history
          </p>
          <p className="font-mono text-[11px] text-muted">v1 → v4 · +25 pts</p>
        </div>
      </div>
    </div>
  )
}