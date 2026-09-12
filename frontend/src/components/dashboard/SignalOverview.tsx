import { motion } from 'motion/react'
import { fadeUp } from '../../motion/variants'
import { cn } from '../../lib/utils/cn'
import type { DashboardView } from '../../pages/dashboard/dashboard-view'

interface SignalOverviewProps {
  view: DashboardView
  className?: string
}

interface Row {
  label: string
  value: string | number
  caption: string
  muted?: boolean
}

/**
 * The "resume health" reading. The dashboard API exposes aggregate values
 * (average / peak / best match / uploads) — not per-skill health dimensions —
 * so this panel presents exactly those, as a lab-like readout rather than
 * five invented cards. Every figure is a real aggregate from the API.
 */
export function SignalOverview({ view, className }: SignalOverviewProps) {
  const rows: Row[] = [
    {
      label: 'Average ATS',
      value: view.averageAts,
      caption: 'across all your analyses',
    },
    {
      label: 'Peak ATS',
      value: view.highestAts,
      caption: 'your strongest single analysis',
    },
    {
      label: 'Best job match',
      value: view.bestJobMatch > 0 ? view.bestJobMatch : '—',
      caption: view.bestJobMatch > 0 ? 'against a target description' : 'no job comparison yet',
      muted: view.bestJobMatch === 0,
    },
    {
      label: 'Resumes on file',
      value: view.total,
      caption: view.total === 1 ? 'upload' : 'uploads',
    },
  ]

  return (
    <section className={className} aria-labelledby="overview-heading">
      <h2
        id="overview-heading"
        className="flex items-center gap-3 font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary"
      >
        <span aria-hidden="true" className="h-px w-6 bg-primary" />
        Signal overview
      </h2>
      <p className="mt-2 text-sm leading-relaxed text-text-soft">
        How your resume reads, in aggregate.
      </p>

      <motion.div
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        className="mt-6 border border-line bg-surface px-6"
      >
        {rows.map((row, i) => (
          <div
            key={row.label}
            className={cn('flex items-center justify-between gap-6 py-5', i > 0 && 'border-t border-line')}
          >
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-muted">{row.label}</p>
              <p className="mt-1 text-xs text-text-soft">{row.caption}</p>
            </div>
            <span
              className={cn(
                'font-display text-3xl font-bold tabular-nums tracking-tight',
                row.muted ? 'text-muted' : 'text-ink',
              )}
            >
              {row.value}
            </span>
          </div>
        ))}
      </motion.div>

      <p className="mt-3 text-xs leading-relaxed text-muted">
        These figures come straight from your analysis history — nothing estimated.
      </p>
    </section>
  )
}