import { motion } from 'motion/react'
import { Container } from '../shared/Container'
import { SectionHeader } from './SectionHeader'
import { fadeUp } from '../../motion/variants'
import { cn } from '../../lib/utils/cn'

const VERSIONS = [
  { version: 'v1', label: 'Imported resume', score: 62, delta: null },
  { version: 'v2', label: 'Keywords aligned', score: 71, delta: '+9' },
  { version: 'v3', label: 'Impact quantified', score: 78, delta: '+7' },
  { version: 'v4', label: 'Structure & bullets', score: 87, delta: '+9' },
]

/**
 * Progress section — how scores improve across iterative edits. A version
 * history card of four revisions. Clearly labelled illustrative, so it reads
 * as an example trajectory rather than a claims-based statistic.
 */
export function Progress() {
  return (
    <section id="progress" className="scroll-mt-16 border-b border-line bg-bg">
      <Container className="py-16 sm:py-24 lg:py-28">
        <SectionHeader
          align="center"
          eyebrow="Track your progress"
          title="Every revision gets you closer."
          description="ResumeAI keeps a history of each version of your resume and shows how your scores change as you apply its suggestions."
        />

        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          className="mx-auto mt-12 max-w-3xl rounded-lg border border-line bg-surface p-6 shadow-md sm:p-8"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs font-medium uppercase tracking-wider text-muted">
              Resume score history
            </p>
            <span className="rounded-full border border-line bg-surface-2 px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-text-soft">
              Illustrative example
            </span>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-4">
            {VERSIONS.map((v) => (
              <div key={v.version} className="rounded-md border border-line bg-surface-2 p-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs uppercase tracking-wider text-muted">
                    {v.version}
                  </span>
                  {v.delta && (
                    <span className="font-mono text-[11px] font-medium text-success">{v.delta}</span>
                  )}
                </div>
                <p className="mt-2 font-display text-3xl font-bold tabular-nums text-ink">
                  {v.score}
                  <span className="ml-1 font-mono text-xs font-normal text-muted">/100</span>
                </p>
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-3">
                  <motion.div
                    className={cn('h-full rounded-full', v.score >= 80 ? 'bg-score-excellent' : 'bg-score-good')}
                    initial={{ width: 0 }}
                    whileInView={{ width: `${v.score}%` }}
                    viewport={{ once: true, amount: 0.4 }}
                    transition={{ duration: 0.6, ease: 'easeOut' }}
                  />
                </div>
                <p className="mt-3 text-xs text-text-soft">{v.label}</p>
              </div>
            ))}
          </div>

          <p className="mt-6 text-xs leading-relaxed text-muted">
            This chart is an illustrative example of an improvement path — the scores shown are
            not real user statistics. You will get real scores for your own resume.
          </p>
        </motion.div>
      </Container>
    </section>
  )
}