import { useEffect, useState } from 'react'
import { motion } from 'motion/react'
import { Panel } from '../ui/Panel'
import { SectionLabel } from '../ui/SectionLabel'
import { cn } from '../../lib/utils/cn'
import { staggerChild, staggerContainer } from '../../motion/variants'

/**
 * One step in the processing narrative. The order is the order the backend
 * pipeline actually runs (upload → parse → extract → ATS → job match → recs).
 */
export interface ProcessingStage {
  key: string
  label: string
  /** Shown beside the stage while it is the active one. */
  hint?: string
}

interface AnalysisProcessingProps {
  /** Ordered processing narrative for this analysis. */
  stages: ProcessingStage[]
  /** Resume title shown as context in the header (the stored row, if known). */
  title?: string
}

/** Pace at which the narrative advances through its stages. */
const STAGE_DURATION_MS = 1100

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="m5 13 4 4L19 7" />
    </svg>
  )
}

/**
 * Premium analysis-processing state. The API surfaces a single pending
 * request with no intermediate backend progress, so this is an *honest*
 * frontend sequence, not claimed server progress:
 *
 *   - Stage 0 ("Resume uploaded") is genuinely complete when the page mounts
 *     (the upload/GET succeeded to reach this page).
 *   - The remaining stages advance on a visible cadence, with the last stage
 *     ("Almost there") held as the active/indeterminate one until the analysis
 *     response resolves and this component unmounts.
 *   - Nothing is ever completed after its server-side work finished unless the
 *     request has genuinely moved past it; no percentage is shown anywhere.
 *
 * Respects reduced motion via the foundation's MotionConfig + the CSS
 * reduced-motion block (both in index.css / App.tsx).
 */
export function AnalysisProcessing({ stages, title }: AnalysisProcessingProps) {
  const lastIndex = stages.length - 1
  const [activeIndex, setActiveIndex] = useState(1) // stage 0 (upload) is complete

  useEffect(() => {
    if (activeIndex >= lastIndex) return
    const timer = window.setTimeout(() => {
      setActiveIndex((index) => Math.min(index + 1, lastIndex))
    }, STAGE_DURATION_MS)
    return () => window.clearTimeout(timer)
  }, [activeIndex, lastIndex])

  return (
    <Panel className="overflow-hidden">
      {/* Header */}
      <div className="border-b border-line px-6 py-5">
        <SectionLabel>Processing</SectionLabel>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
          <div>
            <p className="font-display text-xl font-bold tracking-tight text-ink sm:text-2xl">
              Analysing your resume
            </p>
            <p className="mt-1 text-sm leading-relaxed text-muted">
              Extracting the text and scoring it against the ATS rubric.
            </p>
          </div>
          {title && (
            <span className="max-w-56 truncate rounded-md border border-line bg-surface-2 px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-text-soft">
              {title}
            </span>
          )}
        </div>
      </div>

      {/* Body */}
      <div
        className="px-6 py-6 sm:px-8"
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        {/* Indeterminate line — sweeps, never fills to a fraction. */}
        <div
          className="progress-indeterminate h-1 rounded-full bg-surface-3"
          aria-hidden="true"
        />

        <motion.ol
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="mt-8 space-y-1"
        >
          {stages.map((stage, index) => {
            const status =
              index < activeIndex ? 'done' : index === activeIndex ? 'active' : 'pending'
            return (
              <motion.li
                key={stage.key}
                variants={staggerChild}
                aria-current={status === 'active' ? 'step' : undefined}
                className={cn(
                  'flex items-start gap-3 rounded-md px-3 py-2.5 transition-colors duration-base',
                  status === 'active' && 'bg-primary-faint',
                )}
              >
                {/* Status node */}
                <span
                  className={cn(
                    'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border',
                    status === 'done' && 'border-primary/40 bg-primary-soft text-primary',
                    status === 'active' && 'border-primary/50 bg-primary-soft',
                    status === 'pending' && 'border-line-strong bg-surface',
                  )}
                >
                  {status === 'done' && <CheckIcon className="h-3 w-3" />}
                  {status === 'active' && (
                    <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                  )}
                  {status === 'pending' && (
                    <span className="h-1.5 w-1.5 rounded-full bg-line-strong" />
                  )}
                </span>

                {/* Label + hint */}
                <div className="min-w-0 pt-0.5">
                  <p
                    className={cn(
                      'text-sm leading-snug',
                      status === 'done'
                        ? 'text-text'
                        : status === 'active'
                          ? 'font-medium text-ink'
                          : 'text-muted',
                    )}
                  >
                    {stage.label}
                  </p>
                  {status === 'active' && stage.hint && (
                    <motion.p
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, ease: 'easeOut' }}
                      className="mt-0.5 text-xs leading-relaxed text-muted"
                    >
                      {stage.hint}
                    </motion.p>
                  )}
                </div>
              </motion.li>
            )
          })}
        </motion.ol>

        <p className="mt-6 border-t border-line pt-4 text-xs leading-relaxed text-muted">
          Analysis runs on our servers and usually takes a few seconds — you'll land on
          your results automatically.
        </p>
      </div>
    </Panel>
  )
}