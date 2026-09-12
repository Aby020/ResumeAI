import { useEffect, useState, type ReactNode } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { WorkspaceShell } from '../../components/workspace/WorkspaceShell'
import { WorkspaceHeader } from '../../components/workspace/WorkspaceHeader'
import { Panel } from '../../components/ui/Panel'
import { SectionLabel } from '../../components/ui/SectionLabel'
import { ErrorState } from '../../components/ui/ErrorState'
import { buttonClasses } from '../../components/ui/Button'
import { SignalBand } from '../../components/dashboard/SignalBand'
import { AnalysisProcessing, type ProcessingStage } from '../../components/analysis/AnalysisProcessing'
import { AtsBreakdown } from '../../components/analysis/AtsBreakdown'
import { SkillsAnalysis } from '../../components/analysis/SkillsAnalysis'
import { RecommendationsSection } from '../../components/analysis/RecommendationsSection'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { getAnalysis, getResume } from '../../lib/api/resumes'
import { ApiError } from '../../types/api-error'
import type { Resume, ResumeAnalysis } from '../../types/models'
import { formatDate, formatDateTime } from '../../lib/utils/format'
import { motion } from 'motion/react'
import { fadeUp, staggerChild, staggerContainer } from '../../motion/variants'

type LoadState = 'loading' | 'error' | 'ready'

function CheckIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="mt-0.5 h-4 w-4 shrink-0 text-success"
    >
      <path d="m5 13 4 4L19 7" />
    </svg>
  )
}

function EmptyLine({ text }: { text: string }) {
  return (
    <div className="px-6 py-8">
      <p className="text-sm text-muted">{text}</p>
    </div>
  )
}

/** Detected-skills evidence chips. */
function SkillChips({ skills }: { skills: string[] }) {
  if (skills.length === 0) {
    return <p className="text-sm text-muted">No skills were detected.</p>
  }
  return (
    <ul className="flex flex-wrap gap-1.5" aria-label="Skills detected in your resume">
      {skills.map((skill) => (
        <li
          key={skill}
          className="rounded-md border border-line-strong bg-surface-2 px-2 py-1 text-xs font-medium text-text-soft"
        >
          {skill}
        </li>
      ))}
    </ul>
  )
}

/**
 * Resume analysis — the flagship ResumeAI page. It pairs the stored resume
 * row with the full analysis payload (`GET /api/resumes/:id/` + `…/analysis/`),
 * so every number, strength, skill and recommendation is real API output.
 * First visit to a fresh upload runs the analysis pipeline server-side — the
 * loading state is that real work, not a fake delay.
 */
export function AnalysisPage() {
  useDocumentTitle('Analysis')
  const { id } = useParams<{ id: string }>()
  const location = useLocation()

  const [resume, setResume] = useState<Resume | null>(null)
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null)
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [errorMessage, setErrorMessage] = useState('')
  const [attempt, setAttempt] = useState(0)

  const parsed = Number(id)
  const validId = Number.isInteger(parsed) && parsed > 0

  // The upload flow carries whether a job description was supplied, so the
  // processing narrative can honestly include (or omit) the job-compatibility
  // stage. Unknown (deep link / history) → omit: never claim a job check that
  // the page can't confirm ran with a target role.
  const jobDescriptionPresent =
    (location.state as { jobDescriptionPresent?: boolean } | null)?.jobDescriptionPresent ??
    false

  // The exact order the backend pipeline runs. "Checking job compatibility"
  // only appears when a real job description exists for this analysis.
  const processingStages: ProcessingStage[] = [
    { key: 'uploaded', label: 'Resume uploaded' },
    {
      key: 'reading',
      label: 'Reading document',
      hint: 'Opening your PDF and locating its text layer.',
    },
    {
      key: 'extracting',
      label: 'Extracting resume content',
      hint: 'Pulling sections, skills, dates and contact details.',
    },
    {
      key: 'ats',
      label: 'Running ATS analysis',
      hint: 'Scoring across all ten rubric categories.',
    },
    ...(jobDescriptionPresent
      ? [
          {
            key: 'job-match',
            label: 'Checking job compatibility',
            hint: 'Matching your resume against the target role.',
          },
        ]
      : []),
    {
      key: 'recommendations',
      label: 'Preparing recommendations',
      hint: 'Building prioritized, actionable edits.',
    },
    { key: 'almost', label: 'Almost there', hint: 'Finalizing your analysis.' },
  ]

  useEffect(() => {
    if (!validId) return
    let active = true
    async function run(): Promise<void> {
      try {
        // Phase 1: the stored resume (a fast DB read that never runs the
        // pipeline) so the processing header can name the document.
        const storedResume = await getResume(parsed)
        if (!active) return
        setResume(storedResume)

        // Phase 2: the analysis — a cache HIT returns instantly; a cache MISS
        // runs the full pipeline server-side while the processing state is on
        // screen. That in-flight request is the real work the state describes.
        const storedAnalysis = await getAnalysis(parsed)
        if (!active) return
        setAnalysis(storedAnalysis)
        setLoadState('ready')
      } catch (error) {
        if (!active) return
        const message =
          error instanceof ApiError && error.message
            ? error.message
            : "We couldn't load this analysis right now."
        setErrorMessage(message)
        setLoadState('error')
      }
    }
    void run()
    return () => {
      active = false
    }
  }, [validId, parsed, attempt])

  const hasJobContext = Boolean(analysis?.job_description?.trim())
  const matchAvailable =
    hasJobContext && analysis !== null && (analysis.job_match_score ?? 0) > 0
  const analyzedAt = analysis?.analyzed_at ?? resume?.uploaded_at ?? null
  const grade = analysis?.ats_grade ?? null
  const breakdownCount = analysis ? Object.keys(analysis.ats_breakdown).length : 0

  let content: ReactNode

  if (!validId) {
    content = (
      <ErrorState
        title="Couldn't find that analysis"
        description="This link points to an analysis that may have been removed."
      />
    )
  } else if (loadState === 'loading') {
    content = (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="min-h-[60vh]"
      >
        <AnalysisProcessing stages={processingStages} title={resume?.title} />
      </motion.div>
    )
  } else if (loadState === 'error' || !analysis || !resume) {
    content = (
      <ErrorState
        title="Couldn't load this analysis"
        description={errorMessage}
        onRetry={() => {
          setLoadState('loading')
          setErrorMessage('')
          setAttempt((attempt) => attempt + 1)
        }}
      />
    )
  } else {
    content = (
      <div className="space-y-8">
        <motion.section
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid gap-6 lg:grid-cols-5"
        >
          {/* ATS score */}
          <motion.div variants={staggerChild} className="lg:col-span-3">
            <Panel header={<SectionLabel>ATS score</SectionLabel>}>
              <div className="p-6 lg:p-7">
                <SignalBand
                  label="How ATS systems read your resume"
                  score={analysis.ats_score}
                  size="lg"
                  detail={
                    grade
                      ? `Grade ${grade} · scored across ${breakdownCount} rubric categories`
                      : `Scored across ${breakdownCount} rubric categories`
                  }
                />
              </div>
            </Panel>
          </motion.div>

          {/* Job match — real score or an honest unavailable state */}
          <motion.div variants={staggerChild} className="lg:col-span-2">
            <Panel header={<SectionLabel>Job match</SectionLabel>}>
              {matchAvailable ? (
                <div className="p-6 lg:p-7">
                  <SignalBand
                    label="Target alignment"
                    score={analysis.job_match_score}
                    size="md"
                    detail={`${analysis.matching_skills.length} matching skills · ${analysis.missing_skills.length} missing`}
                  />
                </div>
              ) : (
                <div className="flex h-full flex-col p-6 lg:p-7">
                  <p className="font-mono text-xs uppercase tracking-wider text-muted">
                    Job match unavailable
                  </p>
                  <p className="mt-3 font-display text-xl font-bold leading-snug tracking-tight text-ink">
                    No job description was supplied
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-text-soft">
                    A job match score is only calculated against a target role. Upload the
                    same resume with a job description to measure how well it fits.
                  </p>
                  <Link
                    to="/upload"
                    className={buttonClasses('secondary', 'sm', 'mt-5 self-start')}
                  >
                    Upload with a job description
                    <span aria-hidden="true">→</span>
                  </Link>
                </div>
              )}
            </Panel>
          </motion.div>
        </motion.section>

        {/* Strengths · improvement areas */}
        <motion.section
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="grid gap-6 lg:grid-cols-2"
        >
          <Panel header={<SectionLabel>Strengths</SectionLabel>}>
            {analysis.strengths.length > 0 ? (
              <ul className="divide-y divide-line">
                {analysis.strengths.map((strength, i) => (
                  <li key={i} className="flex gap-3 px-6 py-4">
                    <CheckIcon />
                    <span className="min-w-0 text-sm leading-relaxed text-text">
                      {strength}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyLine text="Strengths from your analysis will appear here." />
            )}
          </Panel>

          <Panel header={<SectionLabel>Improvement areas</SectionLabel>}>
            {analysis.improvement_areas.length > 0 ? (
              <ul className="divide-y divide-line">
                {analysis.improvement_areas.map((item, i) => (
                  <li key={i} className="flex gap-3 px-6 py-4">
                    <span
                      aria-hidden="true"
                      className="mt-1.5 h-2 w-2 shrink-0 rotate-45 bg-warning/70"
                    />
                    <span className="min-w-0 text-sm leading-relaxed text-text">
                      {item}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyLine text="Actionable improvements from your analysis will appear here." />
            )}
          </Panel>
        </motion.section>

        <motion.section variants={fadeUp} initial="hidden" animate="visible">
          <AtsBreakdown breakdown={analysis.ats_breakdown} />
        </motion.section>

        <motion.section variants={fadeUp} initial="hidden" animate="visible">
          <SkillsAnalysis
            hasJobContext={hasJobContext}
            matchingSkills={analysis.matching_skills}
            missingSkills={analysis.missing_skills}
            extraSkills={analysis.extra_skills}
            jobMatchDetails={analysis.job_match_details}
          />
        </motion.section>

        <motion.section variants={fadeUp} initial="hidden" animate="visible">
          <RecommendationsSection
            recommendations={analysis.recommendations}
            ai={analysis.ai_explanation}
          />
        </motion.section>

        {/* Evidence — the real basis, never a fabricated preview */}
        <motion.section variants={fadeUp} initial="hidden" animate="visible">
          <Panel header={<SectionLabel>Basis of this analysis</SectionLabel>}>
            <dl className="grid gap-x-8 gap-y-5 p-6 sm:grid-cols-2 lg:p-7">
              <div>
                <dt className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted">
                  Resume
                </dt>
                <dd className="mt-1 text-sm font-medium text-ink">{resume.title}</dd>
              </div>
              <div>
                <dt className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted">
                  Analysed
                </dt>
                <dd className="mt-1 text-sm text-text-soft">
                  {formatDateTime(analyzedAt)}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted">
                  Skills detected in your resume
                </dt>
                <dd className="mt-2">
                  <SkillChips skills={analysis.detected_skills} />
                </dd>
              </div>
            </dl>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-6 py-4">
              {resume.file && (
                <a
                  href={resume.file}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-medium text-primary transition-colors duration-base hover:text-primary-strong"
                >
                  Open the uploaded PDF
                  <span aria-hidden="true"> &nearr;</span>
                </a>
              )}
              <p className="text-xs text-muted">
                Recommendations are derived from the extracted text of your uploaded PDF.
              </p>
            </div>
          </Panel>
        </motion.section>

        {/* Actions */}
        <motion.nav
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          aria-label="Analysis actions"
          className="flex flex-wrap items-center gap-3 border border-line bg-surface p-6"
        >
          <span className="mr-1 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
            Continue
          </span>
          <Link to="/upload" className={buttonClasses('primary', 'md')}>
            Analyze a new version
            <span aria-hidden="true">→</span>
          </Link>
          {!hasJobContext && (
            <Link to="/upload" className={buttonClasses('secondary', 'md')}>
              Upload with a job description
            </Link>
          )}
          <Link to="/history" className={buttonClasses('secondary', 'md')}>
            View history
          </Link>
        </motion.nav>
      </div>
    )
  }

  return (
    <WorkspaceShell>
      {loadState === 'ready' && (
        <div className="mb-6">
          <Link
            to="/history"
            className="text-sm font-medium text-text-soft transition-colors duration-base hover:text-ink"
          >
            <span aria-hidden="true">←</span> Analysis history
          </Link>
        </div>
      )}
      <WorkspaceHeader
        eyebrow="Analysis"
        title={resume?.title ?? 'Resume analysis'}
        subtitle={
          <span className="font-mono text-xs uppercase tracking-wider text-muted">
            {formatDate(analyzedAt)}
            {grade && <span className="ml-2 text-primary">Grade · {grade}</span>}
          </span>
        }
        actions={
          <Link to="/upload" className={buttonClasses('secondary', 'sm')}>
            Analyze new
          </Link>
        }
      />
      <div className="mt-8">{content}</div>
    </WorkspaceShell>
  )
}