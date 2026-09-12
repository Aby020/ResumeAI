import { motion } from 'motion/react'
import { Container } from '../shared/Container'
import { SectionHeader } from './SectionHeader'
import { ScoreBar } from './ScoreBar'
import { fadeUp, staggerContainer, staggerChild } from '../../motion/variants'

const INSIGHTS = [
  {
    title: 'Strengths',
    body: 'Know what is already working, so you stop polishing the strong parts.',
  },
  {
    title: 'Improvement areas',
    body: 'Prioritized gaps that move the number — not generic advice.',
  },
  {
    title: 'Matching & missing skills',
    body: 'Every requirement in the job description, checked against your resume.',
  },
  {
    title: 'ATS breakdown',
    body: 'Structure, skills, experience, keywords and formatting — each scored and explained.',
  },
  {
    title: 'Job match insights',
    body: 'How your profile compares to the role, and where to close the gap.',
  },
  {
    title: 'Actionable recommendations',
    body: 'Copy-ready edits you can apply immediately.',
  },
]

/**
 * Insights section. Left: a report-style UI fragment that mirrors a real
 * analysis (score index + ATS breakdown + highlight callout). Right: what the
 * user actually learns, as a compact two-column list.
 */
export function Insights() {
  return (
    <section id="insights" className="scroll-mt-16 border-b border-line bg-surface-2">
      <Container className="py-16 sm:py-24 lg:py-28">
        <div className="grid items-start gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Visual column */}
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            className="order-2 lg:order-1"
          >
            <div className="mx-auto max-w-md rounded-lg border border-line bg-surface shadow-md">
              {/* Report header */}
              <div className="flex items-center justify-between border-b border-line px-5 py-4">
                <div>
                  <p className="font-display text-base font-bold text-ink">Dana Whitfield</p>
                  <p className="mt-0.5 font-mono text-xs text-muted">Product Designer · Analysis #4</p>
                </div>
                <span className="rounded border border-success/30 bg-success-soft px-2 py-1 text-[11px] font-medium text-success">
                  Ready for review
                </span>
              </div>

              <div className="space-y-4 p-5">
                <ScoreBar label="ATS readiness" score={87} />
                <ScoreBar label="Job match" score={82} delay={0.08} />

                <div className="border-t border-line pt-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                    ATS breakdown
                  </p>
                  <div className="mt-3 space-y-2.5">
                    <ScoreBar label="Structure" score={92} />
                    <ScoreBar label="Skills" score={88} delay={0.05} />
                    <ScoreBar label="Experience" score={85} delay={0.1} />
                    <ScoreBar label="Keywords" score={74} tone="moderate" delay={0.15} />
                    <ScoreBar label="Formatting" score={96} delay={0.2} />
                  </div>
                </div>

                {/* Highlight callout */}
                <div className="rounded-md border-l-2 border-warning bg-warning-soft px-4 py-3">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-warning">
                    Job match insight
                  </p>
                  <p className="mt-1 text-sm leading-relaxed text-text">
                    The role emphasizes Data Analysis — your resume mentions it twice but never
                    shows impact. Add one metric to close the match.
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Copy column */}
          <div className="order-1 lg:order-2">
            <SectionHeader
              eyebrow="Detailed insights"
              title="A score is only useful when you know why."
              description="Every number comes with a plain-language explanation and the specific edit that moves it."
            />
            <motion.ul
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.15 }}
              className="mt-10 grid gap-x-8 gap-y-6 sm:grid-cols-2"
            >
              {INSIGHTS.map((item) => (
                <motion.li key={item.title} variants={staggerChild} className="flex gap-3">
                  <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  <div>
                    <h3 className="text-sm font-semibold text-ink">{item.title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-text-soft">{item.body}</p>
                  </div>
                </motion.li>
              ))}
            </motion.ul>
          </div>
        </div>
      </Container>
    </section>
  )
}