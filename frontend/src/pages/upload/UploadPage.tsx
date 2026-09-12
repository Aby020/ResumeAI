import { useRef, useState, type ChangeEvent, type DragEvent, type KeyboardEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { WorkspaceShell } from '../../components/workspace/WorkspaceShell'
import { WorkspaceHeader } from '../../components/workspace/WorkspaceHeader'
import { Panel } from '../../components/ui/Panel'
import { SectionLabel } from '../../components/ui/SectionLabel'
import { Button, buttonClasses } from '../../components/ui/Button'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { createResume } from '../../lib/api/resumes'
import { ApiError } from '../../types/api-error'
import { cn } from '../../lib/utils/cn'
import { motion } from 'motion/react'
import { fadeUp } from '../../motion/variants'

const ACCEPTED = 'application/pdf,.pdf'

/** A resume is a PDF — name or MIME check, forgiving of mislabeled uploads. */
function isPdf(file: File): boolean {
  return file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf'
}

/** Byte size as "214 KB" / "1.4 MB". */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

type UploadPhase = 'idle' | 'dragging' | 'selected' | 'invalid' | 'submitting'

/**
 * Upload & analyse — the ResumeAI workflow entry.
 *
 * Resume (PDF) + optional job description → Analyse. Every state is driven by
 * real application state: file selection and validation happen client-side,
 * the "uploading" state is the live `POST /api/resumes/` call, and analysis
 * finishes on the analysis page (its GET runs the pipeline — no fake progress
 * bars, no invented delays). Job-match is only ever enabled by an actual
 * job description.
 */
export function UploadPage() {
  useDocumentTitle('Upload')
  const navigate = useNavigate()

  const inputRef = useRef<HTMLInputElement>(null)

  const [phase, setPhase] = useState<UploadPhase>('idle')
  const [file, setFile] = useState<File | null>(null)
  const [invalidMessage, setInvalidMessage] = useState<string | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [submitError, setSubmitError] = useState<string | null>(null)

  const jdCharacters = jobDescription.length
  const jobMatchEnabled = jdCharacters > 0

  // ── File picking ─────────────────────────────────────────────────────

  function acceptFile(next: File): void {
    if (!isPdf(next)) {
      setInvalidMessage(
        'Only PDF files are supported. Please choose a PDF version of your resume.',
      )
      setPhase('invalid')
      return
    }
    setInvalidMessage(null)
    setSubmitError(null)
    setFile(next)
    setPhase('selected')
  }

  function openPicker(): void {
    inputRef.current?.click()
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>): void {
    const picked = event.target.files?.[0]
    if (picked) acceptFile(picked)
    // Reset so re-selecting the same file still fires change.
    event.target.value = ''
  }

  // Drag & drop ──────────────────────────────────────────────────────────

  function handleDragOver(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault()
    setPhase((current) => (current === 'invalid' ? current : 'dragging'))
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>): void {
    // Only exit the drop state when the pointer actually leaves the zone.
    if (event.currentTarget.contains(event.relatedTarget as Node)) return
    setPhase((current) => (current === 'invalid' ? current : file ? 'selected' : 'idle'))
  }

  function handleDrop(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault()
    const dropped = event.dataTransfer.files?.[0]
    if (dropped) {
      acceptFile(dropped)
    } else {
      setPhase(file ? 'selected' : 'idle')
    }
  }

  function handleZoneKey(event: KeyboardEvent<HTMLDivElement>): void {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openPicker()
    }
  }

  // ── Submission ───────────────────────────────────────────────────────

  async function handleAnalyze(): Promise<void> {
    if (!file || phase === 'submitting') return
    setSubmitError(null)
    setPhase('submitting')
    try {
      const title = file.name.replace(/\.pdf$/i, '').trim() || 'My resume'
      const resume = await createResume({
        title,
        file,
        job_description: jobDescription.trim() === '' ? undefined : jobDescription.trim(),
      })
      // Tell the analysis page whether a job description was supplied so its
      // processing narrative can honestly include (or omit) the job-compat step.
      navigate(`/analysis/${resume.id}`, {
        state: { jobDescriptionPresent: jobMatchEnabled },
      })
    } catch (error) {
      setPhase('selected')
      setSubmitError(
        error instanceof ApiError
          ? error.message
          : "We couldn't upload your resume right now. Please try again.",
      )
    }
  }

  const locked = phase === 'submitting'

  // ── Dropzone visual states ───────────────────────────────────────────

  const dragging = phase === 'dragging'

  const zone = (
    <div
      role="button"
      tabIndex={0}
      aria-label={
        file
          ? `Resume selected: ${file.name}. Press Enter to replace it.`
          : 'Choose a resume PDF. Drag and drop your file here, or activate to browse.'
      }
      onClick={() => !locked && openPicker()}
      onKeyDown={handleZoneKey}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        'flex min-h-56 cursor-pointer flex-col items-center justify-center gap-3 px-6 py-10 text-center',
        'border-2 border-dashed transition-colors duration-base focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
        dragging
          ? 'border-primary bg-primary-faint'
          : phase === 'invalid'
            ? 'border-danger bg-danger-soft/40'
            : 'border-line-strong bg-surface-2 hover:border-primary/60 hover:bg-surface',
        locked && 'pointer-events-none opacity-70',
      )}
    >
      {phase === 'invalid' ? (
        <>
          <span aria-hidden="true" className="text-danger">
            <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M12 9v4m0 4h.01" />
              <circle cx="12" cy="12" r="8.5" />
            </svg>
          </span>
          <p role="alert" className="max-w-sm text-sm font-medium text-danger">
            {invalidMessage}
          </p>
          <span className={buttonClasses('secondary', 'sm')}>Choose another file</span>
          <p className="text-xs text-muted">PDF files only.</p>
        </>
      ) : phase === 'selected' && file ? (
        <div className="flex w-full max-w-md flex-col items-center gap-4" role="status">
          <div className="flex w-full items-center gap-4 border border-line bg-surface p-4 text-left">
            <span aria-hidden="true" className="shrink-0 text-primary">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="h-7 w-7">
                <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
                <path d="M14 3v5h5" />
              </svg>
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-ink">{file.name}</p>
              <p className="mt-0.5 text-xs text-muted">{formatFileSize(file.size)}</p>
            </div>
            <span className="shrink-0 rounded-md bg-primary-soft px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-primary">
              PDF
            </span>
          </div>
          <div className="flex items-center gap-5">
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation()
                openPicker()
              }}
              className="text-sm font-medium text-primary transition-colors duration-base hover:text-primary-strong"
            >
              Replace file
            </button>
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation()
                setFile(null)
                setInvalidMessage(null)
                setSubmitError(null)
                setPhase('idle')
              }}
              className="text-sm font-medium text-text-soft transition-colors duration-base hover:text-danger"
            >
              Remove
            </button>
          </div>
        </div>
      ) : (
        <>
          <span aria-hidden="true" className="text-primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="h-9 w-9">
              <path d="M12 16V4m0 0 3.5 3.5M12 4 8.5 7.5" />
              <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
            </svg>
          </span>
          <p className="font-display text-base font-semibold text-ink">Drag &amp; drop your resume</p>
          <p className="max-w-xs text-sm leading-relaxed text-muted">
            Upload a PDF and ResumeAI will extract the text and score how ATS systems and
            recruiters read it.
          </p>
          <span className={buttonClasses('secondary', 'sm')}>Browse files</span>
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted">PDF only</p>
        </>
      )}
    </div>
  )

  return (
    <WorkspaceShell>
      <div className="space-y-8">
        <WorkspaceHeader
          eyebrow="Upload &amp; analyse"
          title="Upload a resume"
          subtitle="Add your resume, optionally pair it with a job description, and ResumeAI will show how ATS systems and recruiters read it — plus the precise edits that move the number."
        />

        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="grid gap-6 lg:grid-cols-12"
        >
          {/* Resume upload */}
          <div className="lg:col-span-7">
            <Panel
              header={
                <SectionLabel id="upload-resume-heading">Resume document</SectionLabel>
              }
              className="overflow-hidden"
            >
              {zone}
            </Panel>
          </div>

          {/* Optional job description */}
          <div className="lg:col-span-5">
            <Panel
              header={
                <div className="flex items-center justify-between gap-3">
                  <SectionLabel id="upload-jd-heading">
                    Job description · Optional
                  </SectionLabel>
                  {jobMatchEnabled && (
                    <span className="rounded-md bg-primary-soft px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-primary">
                      Job match enabled
                    </span>
                  )}
                </div>
              }
            >
              <div className="p-6">
                <label htmlFor="job-description" className="sr-only">
                  Job description
                </label>
                <textarea
                  id="job-description"
                  value={jobDescription}
                  onChange={(event) => setJobDescription(event.target.value)}
                  disabled={locked}
                  name="job_description"
                  rows={7}
                  placeholder="Paste the job description you're targeting…"
                  className={cn(
                    'min-h-40 w-full resize-y rounded-md border border-line bg-surface-2 px-3.5 py-2.5',
                    'text-sm leading-relaxed text-text placeholder:text-muted/70',
                    'transition-[border-color,box-shadow,background-color] duration-base ease-out',
                    'focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30',
                    'disabled:cursor-not-allowed disabled:opacity-60',
                  )}
                />
                <div className="mt-2 flex flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-xs leading-relaxed text-muted">
                    Adding a job description unlocks Job Match — how well your resume fits the
                    target role.
                  </p>
                  <p className="shrink-0 font-mono text-[10px] uppercase tracking-wider text-muted">
                    {jobDescription.length.toLocaleString()} characters
                  </p>
                </div>
              </div>
            </Panel>
          </div>
        </motion.div>

        {/* Analyse CTA */}
        <motion.section
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          aria-label="Analyse your resume"
          className="flex flex-col gap-4 border border-line bg-surface p-6 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="min-w-0">
            <p className="text-sm font-medium text-ink">
              {file
                ? `Ready to analyse${jobMatchEnabled ? ' and match' : ''}: ${file.name}`
                : 'Add a resume to begin'}
            </p>
            <p className="mt-1 text-xs leading-relaxed text-muted">
              {file
                ? jobMatchEnabled
                  ? 'Job match will be calculated against the provided description.'
                  : "Analyse without a job description for an ATS score. Add one to unlock job match."
                : 'You need a PDF resume to start the analysis.'}
            </p>
          </div>
          <Button
            size="lg"
            loading={phase === 'submitting'}
            disabled={!file}
            onClick={() => void handleAnalyze()}
            className="shrink-0"
          >
            {phase === 'submitting' ? 'Uploading…' : 'Analyze resume'}
            {phase !== 'submitting' && <span aria-hidden="true">→</span>}
          </Button>
        </motion.section>

        {submitError && (
          <p
            role="alert"
            className="rounded-md border border-danger/40 bg-danger-soft px-4 py-3 text-sm text-danger"
          >
            {submitError}
          </p>
        )}

        {/* What happens next */}
        <motion.section
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          aria-labelledby="what-happens-next-heading"
          className="border border-line bg-surface"
        >
          <div className="border-b border-line px-6 py-4">
            <SectionLabel id="what-happens-next-heading">What happens next</SectionLabel>
          </div>
          <ol className="grid gap-8 p-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                step: '01',
                title: 'Resume is analyzed',
                copy: 'The PDF text is extracted and its structure reviewed.',
              },
              {
                step: '02',
                title: 'ATS compatibility is calculated',
                copy: 'Scored 0–100 against the ATS rubric, category by category.',
              },
              {
                step: '03',
                title: 'Job match is calculated',
                copy: 'When a job description exists, your fit against the target role.',
              },
              {
                step: '04',
                title: 'Recommendations are generated',
                copy: 'Prioritized, actionable edits to move your score.',
              },
            ].map((item) => (
              <li key={item.step} className="flex flex-col">
                <span
                  aria-hidden="true"
                  className="font-mono text-lg font-semibold tabular-nums text-primary"
                >
                  {item.step}
                </span>
                <h3 className="mt-3 text-sm font-semibold text-ink">{item.title}</h3>
                <p className="mt-1.5 text-xs leading-relaxed text-muted">{item.copy}</p>
              </li>
            ))}
          </ol>
        </motion.section>

        {/* Hidden picker */}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          className="sr-only"
          aria-hidden="true"
          tabIndex={-1}
          onChange={handleInputChange}
        />
      </div>
    </WorkspaceShell>
  )
}