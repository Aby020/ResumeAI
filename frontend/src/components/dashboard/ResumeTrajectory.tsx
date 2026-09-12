import { motion } from 'motion/react'
import { formatDate } from '../../lib/utils/format'
import { scoreTier, toneFill } from '../../lib/utils/score'
import { staggerContainer, staggerChild } from '../../motion/variants'
import { cn } from '../../lib/utils/cn'
import type { DashboardView } from '../../pages/dashboard/dashboard-view'

interface ResumeTrajectoryProps {
  view: DashboardView
  className?: string
}

/**
 * Resume evolution — the user's score trajectory across their most recent
 * analyzed resumes. A refined horizontal "62 ─ 71 ─ 78" line: each real score
 * is a node on a hairline rail, newest emphasized. Nothing is fabricated —
 * with fewer than two scored resumes this degrades to an honest single-point
 * or empty state, and the sr-only table is the accessible data equivalent.
 */
export function ResumeTrajectory({ view, className }: ResumeTrajectoryProps) {
  const { analyzed } = view
  const chrono = [...analyzed].reverse()
  const first = chrono.length >= 2 ? chrono[0].ats_score : null
  const last = chrono.length >= 2 ? chrono[chrono.length - 1].ats_score : null
  const trend = first !== null && last !== null ? last - first : null

  let content

  if (chrono.length >= 2) {
    content = (
      <div className="relative">
        {/* Connecting rail */}
        <span
          aria-hidden="true"
          className="absolute left-0 right-0 top-[2.375rem] h-px bg-line-strong"
        />
        <motion.ol
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          className="relative flex items-start justify-between"
        >
          {chrono.map((r, i) => {
            const lastPoint = i === chrono.length - 1
            const tier = scoreTier(r.ats_score)
            return (
              <motion.li
                key={r.id}
                variants={staggerChild}
                className="flex flex-1 flex-col items-center"
              >
                <span
                  className={cn(
                    'h-7 font-display text-lg font-bold tabular-nums leading-none tracking-tight',
                    lastPoint ? 'text-primary' : 'text-ink',
                  )}
                >
                  {r.ats_score}
                </span>
                <span className="mt-1 flex h-3 items-center justify-center" aria-hidden="true">
                  <span
                    className={cn(
                      'rounded-full',
                      toneFill[tier.tone],
                      lastPoint
                        ? 'h-3.5 w-3.5 ring-4 ring-primary/15'
                        : 'h-3 w-3',
                    )}
                  />
                </span>
                <span className="mt-2 hidden whitespace-nowrap font-mono text-[11px] uppercase tracking-wider text-muted sm:block">
                  {formatDate(r.uploaded_at)}
                </span>
              </motion.li>
            )
          })}
        </motion.ol>

        {/* Accessible data equivalent */}
        <table className="sr-only">
          <caption>ATS score across your most recent analyzed resumes</caption>
          <thead>
            <tr>
              <th scope="col">Resume</th>
              <th scope="col">Date</th>
              <th scope="col">ATS score</th>
            </tr>
          </thead>
          <tbody>
            {chrono.map((r) => (
              <tr key={r.id}>
                <td>{r.title}</td>
                <td>{formatDate(r.uploaded_at)}</td>
                <td>{r.ats_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  } else if (chrono.length === 1) {
    const only = chrono[0]
    content = (
      <div className="flex items-center gap-6 border border-line bg-surface p-6">
        <span className="font-display text-5xl font-bold tabular-nums leading-none text-primary">
          {only.ats_score}
        </span>
        <div>
          <p className="font-mono text-xs font-medium uppercase tracking-[0.2em] text-muted">
            First score on record
          </p>
          <p className="mt-1.5 text-sm text-text-soft">
            {only.title} · {formatDate(only.uploaded_at)}
          </p>
        </div>
      </div>
    )
  } else {
    content = (
      <div className="border border-line bg-surface p-6">
        <p className="text-sm text-muted">
          Your trajectory draws itself here as analyses complete — scores
          appear the moment a resume is evaluated.
        </p>
      </div>
    )
  }

  return (
    <section className={className} aria-labelledby="trajectory-heading">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <h2
          id="trajectory-heading"
          className="flex items-center gap-3 font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary"
        >
          <span aria-hidden="true" className="h-px w-6 bg-primary" />
          Resume evolution
        </h2>
        {trend !== null && (
          <p className="font-mono text-xs text-muted">
            <span className={cn(trend >= 0 ? 'text-success' : 'text-danger')}>
              {trend >= 0 ? '+' : ''}
              {trend}
            </span>{' '}
            points over your last {chrono.length} analyzed resumes
          </p>
        )}
      </div>
      <p className="mt-2 text-sm leading-relaxed text-text-soft">
        ATS score across your most recent analyzed resumes.
      </p>
      <div className="mt-6">{content}</div>
    </section>
  )
}