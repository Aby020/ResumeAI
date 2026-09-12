import { motion } from 'motion/react'
import { Link } from 'react-router-dom'
import { buttonClasses } from '../ui/Button'
import { fadeUp } from '../../motion/variants'
import type { DashboardView } from '../../pages/dashboard/dashboard-view'

interface NextBestActionProps {
  view: DashboardView
}

/**
 * The one contextual call to action the state actually supports — never an
 * invented recommendation. Three honest states: nothing uploaded yet, an
 * upload awaiting analysis, or a scored resume to review. The full-width
 * primary CTA always leads somewhere real.
 */
export function NextBestAction({ view }: NextBestActionProps) {
  const { latestAnalyzed, isEmpty } = view

  let headline: string
  let body: string
  let primary: { to: string; label: string }
  let secondary: { to: string; label: string }

  if (isEmpty) {
    headline = 'Start with your first upload'
    body =
      'Upload your resume and ResumeAI will score how ATS systems and recruiters read it — then show you the precise edits that move the number.'
    primary = { to: '/upload', label: 'Upload your resume' }
    secondary = { to: '/history', label: 'See your uploads' }
  } else if (latestAnalyzed) {
    headline = 'Take your latest score further'
    body = `See the findings behind ${latestAnalyzed.title} and push the next version past ${latestAnalyzed.ats_score}/100.`
    primary = { to: `/analysis/${latestAnalyzed.id}`, label: 'Review your latest analysis' }
    secondary = { to: '/upload', label: 'Analyze a new version' }
  } else {
    headline = 'Your first real score starts with an analysis'
    body =
      'An upload is on file — analyze it now to see how ATS systems and recruiters read your resume.'
    primary = { to: '/upload', label: 'Analyze a new resume' }
    secondary = { to: '/history', label: 'See your uploads' }
  }

  return (
    <motion.section
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.4 }}
      className="flex flex-col border border-line bg-surface p-6"
      aria-labelledby="next-best-action-heading"
    >
      <h3
        className="font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary"
      >
        Next best action
      </h3>

      <span
        aria-hidden="true"
        className="mt-4 inline-flex h-10 w-10 items-center justify-center text-primary"
      >
        <svg
          viewBox="0 0 24 24"
          fill="currentColor"
          className="h-10 w-10"
        >
          <path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z" />
        </svg>
      </span>

      <h2
        id="next-best-action-heading"
        className="mt-4 font-display text-xl font-bold leading-snug tracking-tight text-ink"
      >
        {headline}
      </h2>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-text-soft">{body}</p>

      <div className="mt-6 flex flex-col gap-3">
        <Link to={primary.to} className={buttonClasses('primary', 'lg', 'w-full')}>
          {primary.label}
          <span aria-hidden="true">→</span>
        </Link>
        <Link
          to={secondary.to}
          className="inline-flex items-center justify-center gap-1.5 text-sm font-medium text-text-soft transition-colors duration-base hover:text-ink"
        >
          {secondary.label}
        </Link>
      </div>
    </motion.section>
  )
}
