import { motion } from 'motion/react'
import { Link } from 'react-router-dom'
import { formatDate } from '../../lib/utils/format'
import { staggerContainer, staggerChild } from '../../motion/variants'
import { cn } from '../../lib/utils/cn'
import { ResumeAILogo } from '../shared/ResumeAILogo'
import type { DashboardView } from '../../pages/dashboard/dashboard-view'

interface RecentAnalysesProps {
  view: DashboardView
  className?: string
}

/**
 * Recent analyses — an editorial list card, not a table. Each row carries the
 * résumé title, date, ATS signal and job-match score when present and resolves
 * to `/analysis/:id`. Pending uploads (`ats_score === 0`) read as "awaiting
 * analysis" — never as a fabricated zero. With no uploads yet the card holds
 * an honest empty line so the workspace keeps its composition.
 */
export function RecentAnalyses({ view, className }: RecentAnalysesProps) {
  const { recent, total } = view

  return (
    <section
      className={cn('flex flex-col border border-line bg-surface', className)}
      aria-labelledby="recent-heading"
    >
      <div className="flex items-baseline justify-between gap-6 border-b border-line px-6 py-5">
        <h2
          id="recent-heading"
          className="font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary"
        >
          Recent analyses
        </h2>
        {total > 0 && (
          <Link
            to="/history"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-text-soft transition-colors duration-base hover:text-ink"
          >
            View all
            <span aria-hidden="true">→</span>
          </Link>
        )}
      </div>

      {recent.length === 0 ? (
        <div className="flex flex-1 items-center px-6 py-8">
          <p className="text-sm leading-relaxed text-muted">
            No analyses yet — your recent uploads will appear here.
          </p>
        </div>
      ) : (
        <motion.ol
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          className="flex-1"
        >
          {recent.map((r, i) => {
            const analyzed = r.ats_score > 0
            const match = r.job_match_score !== null && r.job_match_score > 0
              ? r.job_match_score
              : null

            return (
              <motion.li
                key={r.id}
                variants={staggerChild}
                className={cn(i > 0 && 'border-t border-line')}
              >
                <Link
                  to={`/analysis/${r.id}`}
                  aria-label={`Open analysis for ${r.title}${
                    analyzed ? `, ATS score ${r.ats_score}` : ', awaiting analysis'
                  }`}
                  className="group flex items-center gap-3 px-6 py-4 transition-colors duration-base hover:bg-surface-2"
                >
                  <span aria-hidden="true" className="shrink-0 text-ink/70">
                    <ResumeAILogo size={18} />
                  </span>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink">{r.title}</p>
                    <p className="mt-0.5 text-xs text-muted">
                      {formatDate(r.uploaded_at)}
                      {!analyzed && ' · awaiting analysis'}
                    </p>
                  </div>

                  <div className="flex shrink-0 items-center gap-4">
                    <span className="flex flex-col items-end">
                      <span
                        className={cn(
                          'font-mono text-sm tabular-nums',
                          analyzed ? 'text-ink' : 'text-muted',
                        )}
                      >
                        {analyzed ? r.ats_score : '—'}
                      </span>
                      <span className="text-[10px] uppercase tracking-wider text-muted">ats</span>
                    </span>
                    <span className="hidden flex-col items-end sm:flex">
                      <span
                        className={cn(
                          'font-mono text-sm tabular-nums',
                          match !== null ? 'text-ink' : 'text-muted',
                        )}
                      >
                        {match ?? '—'}
                      </span>
                      <span className="text-[10px] uppercase tracking-wider text-muted">match</span>
                    </span>
                    <span
                      aria-hidden="true"
                      className="text-text-soft transition-transform duration-base group-hover:translate-x-0.5"
                    >
                      →
                    </span>
                  </div>
                </Link>
              </motion.li>
            )
          })}
        </motion.ol>
      )}
    </section>
  )
}