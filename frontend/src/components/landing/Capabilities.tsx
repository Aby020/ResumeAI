import type { ReactNode } from 'react'
import { motion } from 'motion/react'
import { Container } from '../shared/Container'
import { SectionHeader } from './SectionHeader'
import { staggerContainer, staggerChild } from '../../motion/variants'
import { cn } from '../../lib/utils/cn'

const ATS_CHECKS = [
  { label: 'Section order & headings', ok: true, status: 'Pass' },
  { label: 'ATS-safe formatting', ok: true, status: 'Pass' },
  { label: 'Action verbs & metrics', ok: true, status: 'Pass' },
  { label: 'Keyword density', ok: false, status: 'Light' },
  { label: 'Scannable one-page layout', ok: true, status: 'Pass' },
]

const PRODUCT_REWRITES = [
  { before: 'Worked on onboarding flows', after: 'Cut onboarding completion time by 38%' },
  { before: 'Helped ship platform features', after: 'Shipped 14 features with a 3-engineer team' },
]

const HISTORY_SCORES = [62, 71, 78, 87]

function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div
      variants={staggerChild}
      className={cn('rounded-lg border border-line bg-surface p-6 shadow-sm', className)}
    >
      {children}
    </motion.div>
  )
}

function Meta({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div>
      <span className="font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary">
        {number}
      </span>
      <h3 className="mt-2 font-display text-xl font-bold tracking-tight text-ink sm:text-2xl">
        {title}
      </h3>
      <p className="mt-3 text-sm leading-relaxed text-text-soft">{description}</p>
    </div>
  )
}

function CheckIcon() {
  return (
    <svg className="h-3 w-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 8.5 6.5 12 13 4.5" />
    </svg>
  )
}

function WarnIcon() {
  return (
    <svg className="h-3 w-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <path d="M8 3v5" />
      <path d="M8 11.5h.01" />
    </svg>
  )
}

/**
 * Capability section. Deliberately NOT five identical cards: a wide lead card
 * (ATS analysis) followed by two pair rows, each with its own small product
 * fragment so every capability reads differently.
 */
export function Capabilities() {
  return (
    <section id="capabilities" className="scroll-mt-16 border-b border-line bg-surface-2">
      <Container className="py-16 sm:py-24 lg:py-28">
        <SectionHeader
          eyebrow="Capabilities"
          title="Everything your resume needs to get to yes."
          description="Five focused capabilities — scoring, matching, and the edits that move both."
        />

        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.15 }}
          className="mt-14 space-y-5"
        >
          {/* 01 — ATS Analysis (wide lead) */}
          <Panel className="grid gap-8 md:grid-cols-[1.1fr_1fr] md:items-center">
            <Meta
              number="01"
              title="ATS Analysis"
              description="ResumeAI reads your resume the way ATS software does — structure, formatting and keyword placement — before a recruiter ever sees it."
            />
            <div className="rounded-lg border border-line bg-surface-2 p-5">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                Screening checks
              </p>
              <ul className="mt-2 divide-y divide-line">
                {ATS_CHECKS.map((item) => (
                  <li key={item.label} className="flex items-center justify-between gap-3 py-2.5">
                    <span className="font-mono text-xs text-text-soft">{item.label}</span>
                    <span
                      className={cn(
                        'inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] font-semibold',
                        item.ok ? 'bg-success-soft text-success' : 'bg-warning-soft text-warning',
                      )}
                    >
                      {item.ok ? <CheckIcon /> : <WarnIcon />}
                      {item.status}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </Panel>

          {/* 02 + 03 — matching and skill analysis */}
          <div className="grid gap-5 md:grid-cols-2">
            <Panel>
              <div className="flex h-full flex-col">
                <Meta
                  number="02"
                  title="Job Matching"
                  description="Paste any job description and get a match score across skills, experience and required keywords — with the specific gaps called out."
                />
                <div className="mt-6 flex items-baseline gap-1">
                  <span className="font-display text-3xl font-bold tabular-nums text-ink">82</span>
                  <span className="text-xs text-muted">/100</span>
                </div>
                <p className="mt-1 text-xs text-text-soft">matches this role</p>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-3">
                  <motion.div
                    className="h-full rounded-full bg-primary"
                    initial={{ width: 0 }}
                    whileInView={{ width: '82%' }}
                    viewport={{ once: true, amount: 0.4 }}
                    transition={{ duration: 0.55, ease: 'easeOut' }}
                  />
                </div>
                <p className="mt-4 text-xs text-text-soft">
                  <span className="font-medium text-primary">Strong fit</span> — 4 of 5 required
                  responsibilities present.
                </p>
              </div>
            </Panel>

            <Panel>
              <div className="flex h-full flex-col">
                <Meta
                  number="03"
                  title="Skill Analysis"
                  description="Every required skill is checked against your resume, so it's obvious what to add and what's already covered."
                />
                <div className="mt-6 space-y-3">
                  {[
                    { label: 'Matching skills', value: '12', tone: 'bg-score-good', pct: 75 },
                    { label: 'Missing skills', value: '4', tone: 'bg-score-poor', pct: 25 },
                  ].map((row) => (
                    <div key={row.label}>
                      <div className="flex items-baseline justify-between gap-3">
                        <span className="text-sm font-medium text-text">{row.label}</span>
                        <span className="font-mono text-xs tabular-nums text-muted">{row.value}</span>
                      </div>
                      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-3">
                        <motion.div
                          className={cn('h-full rounded-full', row.tone)}
                          initial={{ width: 0 }}
                          whileInView={{ width: `${row.pct}%` }}
                          viewport={{ once: true, amount: 0.4 }}
                          transition={{ duration: 0.55, ease: 'easeOut' }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-xs text-text-soft">75% of required skills covered — one gap to close.</p>
              </div>
            </Panel>
          </div>

          {/* 04 + 05 — improvements and history */}
          <div className="grid gap-5 md:grid-cols-2">
            <Panel>
              <Meta
                number="04"
                title="Resume Improvements"
                description="Plain-language suggestions with copy-ready rewrites for the sections holding your score back."
              />
              <ul className="mt-6 space-y-2.5">
                {PRODUCT_REWRITES.map((item) => (
                  <li
                    key={item.after}
                    className="rounded-md border border-line bg-surface-2 px-3 py-2.5"
                  >
                    <p className="text-xs text-muted line-through">{item.before}</p>
                    <p className="mt-1 text-sm font-medium text-ink">{item.after}</p>
                  </li>
                ))}
              </ul>
            </Panel>

            <Panel>
              <Meta
                number="05"
                title="Progress & History"
                description="Watch your score rise across versions and keep a full history of what changed and why."
              />
              <div className="mt-6" aria-label="Score rising from 62 to 87 across four versions">
                <div className="flex items-end gap-3" style={{ height: '96px' }}>
                  {HISTORY_SCORES.map((score, i) => (
                    <div key={score} className="flex h-full flex-1 flex-col justify-end gap-1.5">
                      <span className="text-center font-display text-sm font-bold tabular-nums text-primary">
                        {score}
                      </span>
                      <motion.div
                        className={cn('rounded-t', i === 3 ? 'bg-primary' : 'bg-primary/40')}
                        initial={{ height: 8 }}
                        whileInView={{ height: `${score * 0.78}px` }}
                        viewport={{ once: true, amount: 0.4 }}
                        transition={{ duration: 0.5, ease: 'easeOut', delay: i * 0.08 }}
                      />
                      <span className="text-center font-mono text-[10px] text-muted">v{i + 1}</span>
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-xs text-text-soft">Every revision is measured and kept — improvement becomes visible, not guessed.</p>
              </div>
            </Panel>
          </div>
        </motion.div>
      </Container>
    </section>
  )
}