import { motion } from 'motion/react'
import { Link } from 'react-router-dom'
import { formatDate } from '../../lib/utils/format'
import type { DashboardView } from '../../pages/dashboard/dashboard-view'
import { staggerContainer, staggerChild } from '../../motion/variants'
import { SignalBand } from './SignalBand'
import { SignalSpectrum } from './SignalSpectrum'
import { cn } from '../../lib/utils/cn'

interface CareerSignalProps {
  view: DashboardView
}

/** Shared card recipe for the signal row — subtle borders, no rounding. */
const cardClass = 'border border-line bg-surface p-6 lg:p-7'

/** Small zigzag wave icon before the signal card heading — matches reference. */
function SignalIcon() {
  return (
    <svg viewBox="0 0 20 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3.5 shrink-0" aria-hidden="true">
      <path d="M1 7h3l2-4 2 8 2-4 2 4 2-4 2 4h3" />
    </svg>
  )
}

/**
 * The primary signal row — three equal cards answering "how strong is my
 * resume" (ATS), "how well does it match" (job match) and "where do I sit"
 * (the spectrum). Always real API values with an honest placeholder while an
 * analysis is pending; never a fabricated score.
 */
export function CareerSignal({ view }: CareerSignalProps) {
  const { latestAnalyzed, latestUpload, currentScore, bestJobMatch } = view
  const hasAnyMatch = view.analyzed.length > 0 && bestJobMatch > 0

  const atsDetail = latestAnalyzed
    ? `${latestAnalyzed.title} · ${formatDate(latestAnalyzed.uploaded_at)}`
    : latestUpload
      ? 'Your latest upload is on file — its score appears once analyzed.'
      : 'Upload your resume to get your first ATS score.'

  const matchDetail = hasAnyMatch
    ? `Best match across ${view.analyzed.length} analyzed ${view.analyzed.length === 1 ? 'resume' : 'resumes'}`
    : 'Analyze with a job description to measure how well your resume fits a target role.'

  return (
    <motion.section
      variants={staggerContainer}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
      className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      {/* ATS signal */}
      <motion.div variants={staggerChild} className={cardClass}>
        <h3 className="flex items-center gap-2 font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary">
          <SignalIcon />
          ATS signal
        </h3>
        <div className="mt-4">
          <SignalBand
            label="How hiring systems read your resume"
            score={currentScore}
            size="lg"
            detail={atsDetail}
          />
        </div>
        {!latestAnalyzed && latestUpload && (
          <Link
            to={`/analysis/${latestUpload.id}`}
            className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-primary transition-colors duration-base hover:text-primary-strong"
          >
            Open latest upload
            <span aria-hidden="true">→</span>
          </Link>
        )}
      </motion.div>

      {/* Job-match signal */}
      <motion.div variants={staggerChild} className={cardClass}>
        <h3 className="flex items-center gap-2 font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary">
          <SignalIcon />
          Job match
        </h3>
        <div className="mt-4">
          <SignalBand
            label="Target alignment"
            score={hasAnyMatch ? bestJobMatch : null}
            size="md"
            detail={matchDetail}
          />
        </div>
      </motion.div>

      {/* Career signal spectrum — heading text varies by state */}
      <motion.div
        variants={staggerChild}
        className={cn(cardClass, 'sm:col-span-2 lg:col-span-1')}
      >
        <h3 className="flex items-center gap-2 font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary">
          <SignalIcon />
          {currentScore ? 'Career signal spectrum' : 'Your first score lands here'}
        </h3>
        <SignalSpectrum score={currentScore} variant="compact" />
      </motion.div>
    </motion.section>
  )
}
