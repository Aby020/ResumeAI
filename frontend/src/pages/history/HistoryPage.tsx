import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { WorkspaceShell } from '../../components/workspace/WorkspaceShell'
import { WorkspaceHeader } from '../../components/workspace/WorkspaceHeader'
import { Panel } from '../../components/ui/Panel'
import { SectionLabel } from '../../components/ui/SectionLabel'
import { LoadingState } from '../../components/ui/LoadingState'
import { ErrorState } from '../../components/ui/ErrorState'
import { buttonClasses } from '../../components/ui/Button'
import { ResumeAILogo } from '../../components/shared/ResumeAILogo'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { listHistory } from '../../lib/api/history'
import { deleteResume } from '../../lib/api/resumes'
import { ApiError } from '../../types/api-error'
import { ConfirmDialog } from '../../components/ui/ConfirmDialog'
import type { HistoryItem } from '../../types/models'
import { formatDate } from '../../lib/utils/format'
import { scoreTier, toneFill, toneText } from '../../lib/utils/score'
import { cn } from '../../lib/utils/cn'
import { motion } from 'motion/react'
import { fadeUp } from '../../motion/variants'

type LoadState = 'loading' | 'error' | 'ready'
type StatusFilter = 'all' | 'analyzed' | 'pending'
type SortKey = 'newest' | 'ats' | 'match'

const PAGE_SIZE = 8
const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'All statuses' },
  { value: 'analyzed', label: 'Analyzed' },
  { value: 'pending', label: 'Awaiting analysis' },
]
const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'newest', label: 'Newest first' },
  { value: 'ats', label: 'Highest ATS score' },
  { value: 'match', label: 'Highest job match' },
]

/** Select arrow chevron. */
function ChevronIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  )
}

const selectClasses =
  'h-9 appearance-none rounded-md border border-line bg-surface pl-3 pr-9 text-sm font-medium text-text ' +
  'transition-colors duration-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30'

function StatusBadge({ status }: { status: 'analyzed' | 'pending' }) {
  if (status === 'analyzed') {
    return (
      <span className="rounded-md bg-success-soft px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-success">
        Analyzed
      </span>
    )
  }
  return (
    <span className="rounded-md bg-surface-3 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted">
      Awaiting analysis
    </span>
  )
}

/** Scannable numeric score cell (ATS or job match) with a thin linear track. */
function ScoreCell({ label, value }: { label: string; value: number | null }) {
  const hasValue = value !== null && value > 0
  const tier = scoreTier(hasValue ? value : 0)
  return (
    <span className="flex w-14 flex-col items-end gap-1">
      <span
        className={cn(
          'font-mono text-sm font-semibold tabular-nums',
          hasValue ? toneText[tier.tone] : 'text-muted',
        )}
      >
        {hasValue ? value : '—'}
      </span>
      <span className="text-[10px] uppercase tracking-wider text-muted">{label}</span>
      <span className="h-0.5 w-full overflow-hidden rounded-full bg-surface-3" aria-hidden="true">
        <span
          className={cn('block h-full rounded-full', hasValue && toneFill[tier.tone])}
          style={{ width: hasValue ? `${value}%` : '0%' }}
        />
      </span>
    </span>
  )
}

/** The career progression line — only renders real, ascending analyzed scores. */
function ProgressionPanel({ progression }: { progression: HistoryItem[] }) {
  if (progression.length >= 2) {
    return (
      <Panel header={<SectionLabel>Your career signal progression</SectionLabel>}>
        <div className="overflow-x-auto p-6 lg:p-7">
          <ol className="flex items-stretch gap-6 sm:gap-12">
            {progression.map((item, i) => (
              <li key={item.resume_id} className="flex min-w-[96px] flex-col">
                <div className="mb-3 flex items-center" aria-hidden="true">
                  <span
                    className={cn(
                      'h-2 w-2 shrink-0 rounded-full',
                      i === progression.length - 1 ? 'bg-primary' : 'bg-line-strong',
                    )}
                  />
                  {i < progression.length - 1 && (
                    <span className="mx-1 h-px w-10 shrink-0 bg-line-strong sm:w-14" />
                  )}
                </div>
                <span
                  className={cn(
                    'font-display text-2xl font-bold tabular-nums leading-none text-ink',
                    i === progression.length - 1 && 'text-primary',
                  )}
                >
                  {item.ats_score}
                </span>
                <span className="mt-1.5 text-xs text-muted">
                  {formatDate(item.analyzed_date)}
                </span>
                <Link
                  to={`/analysis/${item.resume_id}`}
                  className="mt-2 text-xs font-medium text-primary transition-colors duration-base hover:text-primary-strong"
                >
                  View <span aria-hidden="true">→</span>
                </Link>
              </li>
            ))}
          </ol>
        </div>
      </Panel>
    )
  }

  return (
    <Panel header={<SectionLabel>Your career signal progression</SectionLabel>}>
      <div className="p-6 lg:p-7">
        <p className="font-display text-lg font-semibold text-ink">
          Your improvement line starts with a second analysis
        </p>
        <p className="mt-1 max-w-xl text-sm leading-relaxed text-muted">
          Re-upload an improved version after your next review and ResumeAI will trace
          your ATS scores here — a clear record of career signal growth across versions.
        </p>
        <div className="mt-6 flex items-center gap-1.5" aria-hidden="true">
          {[0, 1, 2, 3].map((i) => (
            <span key={i} className="h-px w-10 bg-line" />
          ))}
          <span className="h-2 w-2 rounded-full bg-line-strong" />
          <span className="h-2 w-2 rounded-full bg-surface-3" />
        </div>
      </div>
    </Panel>
  )
}

/** Premium empty state — the workspace starting point, never an error. */
function EmptyHistory({ hasItems, onClear }: { hasItems: boolean; onClear?: () => void }) {
  if (hasItems) {
    return (
      <Panel>
        <div className="flex flex-col items-center gap-4 px-6 py-14 text-center">
          <p className="font-display text-lg font-semibold text-ink">
            No analyses match your filters
          </p>
          {onClear && (
            <button
              type="button"
              onClick={onClear}
              className="text-sm font-medium text-primary transition-colors duration-base hover:text-primary-strong"
            >
              Clear search &amp; filters
            </button>
          )}
        </div>
      </Panel>
    )
  }

  return (
    <motion.section
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className="border border-line bg-surface"
    >
      <div className="flex flex-col items-center gap-6 px-6 py-16 text-center lg:py-20">
        <ResumeAILogo size={56} className="text-ink" />
        <div>
          <p className="font-display text-xl font-bold tracking-tight text-ink">
            No analyses yet
          </p>
          <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted">
            Your history is where every resume version and its scores come together.
            Upload your first resume to begin your career signal line.
          </p>
        </div>
        <Link to="/upload" className={buttonClasses('primary', 'lg')}>
          Analyze your resume
          <span aria-hidden="true">→</span>
        </Link>
      </div>
    </motion.section>
  )
}

/**
 * Resume history — a career improvement timeline/workspace, not a generic
 * database table. Every row, score, status and progression point is real
 * `/api/history/` output; search, filter and sort are lightweight local
 * controls over that data. An early user sees an intentional starting state —
 * never fabricated history.
 */
export function HistoryPage() {
  useDocumentTitle('History')

  const [items, setItems] = useState<HistoryItem[] | null>(null)
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [errorMessage, setErrorMessage] = useState('')
  const [attempt, setAttempt] = useState(0)

  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [sortKey, setSortKey] = useState<SortKey>('newest')
  const [page, setPage] = useState(1)

  // Delete flow — the row being confirmed, the in-flight flag, and any failure
  // message (kept inside the dialog so a failed delete can be retried).
  const [pendingDelete, setPendingDelete] = useState<HistoryItem | null>(null)
  const [deleteBusy, setDeleteBusy] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  useEffect(() => {
    let active = true
    async function run(): Promise<void> {
      setLoadState('loading')
      setErrorMessage('')
      try {
        const history = await listHistory()
        if (!active) return
        setItems(history)
        setLoadState('ready')
      } catch (error) {
        if (!active) return
        const message =
          error instanceof ApiError && error.message
            ? error.message
            : "We couldn't load your analysis history right now."
        setErrorMessage(message)
        setLoadState('error')
      }
    }
    void run()
    return () => {
      active = false
    }
  }, [attempt])

  // Real, chronological progression (oldest first). Pending uploads can't
  // join the line — a score of 0 is never charted.
  const progression = useMemo(() => {
    const analyzed = (items ?? []).filter(
      (item) => item.status === 'analyzed' && item.analyzed_date !== null,
    )
    return [...analyzed].sort(
      (a, b) => (a.analyzed_date ?? '').localeCompare(b.analyzed_date ?? ''),
    )
  }, [items])

  // Search / filter / sort over the real list.
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    const matches = (items ?? []).filter((item) => {
      const inStatus =
        statusFilter === 'all' ||
        (statusFilter === 'analyzed' ? item.status === 'analyzed' : item.status === 'pending')
      const inQuery = normalized === '' || item.title.toLowerCase().includes(normalized)
      return inStatus && inQuery
    })

    switch (sortKey) {
      case 'ats':
        return [...matches].sort((a, b) => b.ats_score - a.ats_score)
      case 'match':
        return [...matches].sort(
          (a, b) => (b.job_match_score ?? 0) - (a.job_match_score ?? 0),
        )
      default:
        return [...matches].sort(
          (a, b) => (b.analyzed_date ?? '').localeCompare(a.analyzed_date ?? ''),
        )
    }
  }, [items, query, statusFilter, sortKey])

  const total = filtered.length
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const safePage = Math.min(Math.max(1, page), pages)
  const pageItems = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)
  const rangeStart = total === 0 ? 0 : (safePage - 1) * PAGE_SIZE + 1
  const rangeEnd = Math.min(safePage * PAGE_SIZE, total)

  function resetPage(): void {
    setPage(1)
  }

  /**
   * Confirmed deletion of the row in `pendingDelete`. The hard delete
   * (database row + stored PDF/job image + analysis) happens server-side in
   * `DELETE /api/resumes/<id>/` (ownership-scoped — a foreign id is a 404).
   * On success the row is dropped from local state so the list, progression
   * line, filters and pagination refresh immediately. On failure the dialog
   * stays open with the error so the user can retry or cancel; nothing is ever
   * removed locally without a server-confirmed 2xx.
   */
  async function confirmDelete(): Promise<void> {
    if (!pendingDelete) return
    setDeleteBusy(true)
    setDeleteError('')
    try {
      await deleteResume(pendingDelete.resume_id)
      setItems((current) =>
        (current ?? []).filter((item) => item.resume_id !== pendingDelete.resume_id),
      )
      setPendingDelete(null)
    } catch (error) {
      setDeleteError(
        error instanceof ApiError && error.message
          ? error.message
          : "We couldn't delete this resume. Please try again.",
      )
    } finally {
      setDeleteBusy(false)
    }
  }

  let content: ReactNode

  if (loadState === 'loading') {
    content = <LoadingState label="Reading your analysis history…" className="min-h-[60vh]" />
  } else if (loadState === 'error' || !items) {
    content = (
      <ErrorState
        title="Couldn't load your history"
        description={errorMessage}
        onRetry={() => setAttempt((attempt) => attempt + 1)}
      />
    )
  } else if (items.length === 0) {
    content = <EmptyHistory hasItems={false} />
  } else {
    content = (
      <div className="space-y-8">
        <motion.section variants={fadeUp} initial="hidden" animate="visible">
          <ProgressionPanel progression={progression} />
        </motion.section>

        {/* Lightweight search / filter / sort */}
        <motion.section
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          aria-label="Search and filter analyses"
          className="flex flex-col gap-3 sm:flex-row sm:items-center"
        >
          <div className="relative min-w-0 flex-1">
            <span
              aria-hidden="true"
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
            </span>
            <input
              type="search"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value)
                resetPage()
              }}
              placeholder="Search by resume title…"
              aria-label="Search analyses by title"
              className="h-9 w-full rounded-md border border-line bg-surface pl-9 pr-3 text-sm text-text placeholder:text-muted/70 transition-colors duration-base focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <label htmlFor="history-status" className="sr-only">Status</label>
              <select
                id="history-status"
                value={statusFilter}
                onChange={(event) => {
                  setStatusFilter(event.target.value as StatusFilter)
                  resetPage()
                }}
                className={selectClasses}
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <ChevronIcon />
            </div>
            <div className="relative">
              <label htmlFor="history-sort" className="sr-only">Sort</label>
              <select
                id="history-sort"
                value={sortKey}
                onChange={(event) => {
                  setSortKey(event.target.value as SortKey)
                  resetPage()
                }}
                className={selectClasses}
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <ChevronIcon />
            </div>
          </div>
        </motion.section>

        {/* Analysis list — editorial rows */}
        <motion.section variants={fadeUp} initial="hidden" animate="visible">
          <Panel>
            {pageItems.length === 0 ? (
              <EmptyHistory
                hasItems
                onClear={() => {
                  setQuery('')
                  setStatusFilter('all')
                  setSortKey('newest')
                  resetPage()
                }}
              />
            ) : (
              <>
                <ul className="divide-y divide-line">
                  {pageItems.map((item) => {
                    const analyzed = item.status === 'analyzed'
                    const match =
                      item.job_match_score !== null && item.job_match_score > 0
                        ? item.job_match_score
                        : null
                    return (
                      <li key={item.resume_id}>
                        <div className="flex items-center gap-3">
                          <Link
                            to={`/analysis/${item.resume_id}`}
                            aria-label={`Open analysis for ${item.title}${
                              analyzed
                                ? `, ATS score ${item.ats_score}`
                                : ', awaiting analysis'
                            }`}
                            className="flex min-w-0 flex-1 items-center gap-3 px-6 py-4 transition-colors duration-base hover:bg-surface-2"
                          >
                            <span aria-hidden="true" className="shrink-0 text-ink/70">
                              <ResumeAILogo size={18} />
                            </span>

                            <div className="min-w-0 flex-1">
                              <p className="truncate text-sm font-medium text-ink">
                                {item.title}
                              </p>
                              <div className="mt-1 flex flex-wrap items-center gap-2">
                                <span className="text-xs text-muted">
                                  {formatDate(item.analyzed_date)}
                                </span>
                                <StatusBadge status={item.status} />
                              </div>
                            </div>

                            <div className="flex shrink-0 items-center gap-5">
                              <ScoreCell label="ATS" value={analyzed ? item.ats_score : null} />
                              <ScoreCell label="Match" value={match} />
                            </div>
                          </Link>

                          {/* Delete — a sibling of the row Link (never nested
                              inside an interactive element), so it stays a
                              first-class, keyboard-focusable action. The
                              danger tone only appears on hover/focus so rows
                              stay calm until the user intends the action. */}
                          <button
                            type="button"
                            onClick={() => {
                              setDeleteError('')
                              setPendingDelete(item)
                            }}
                            aria-label={`Delete ${item.title}`}
                            title="Delete this analysis"
                            className="mr-4 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-muted transition-colors duration-base hover:bg-danger-soft hover:text-danger focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-danger"
                          >
                            <svg
                              aria-hidden="true"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              className="h-4 w-4"
                            >
                              <path d="M3 6h18" />
                              <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                              <path d="M10 11v6" />
                              <path d="M14 11v6" />
                            </svg>
                          </button>
                        </div>
                      </li>
                    )
                  })}
                </ul>

                {/* Pagination */}
                {total > PAGE_SIZE && (
                  <div className="flex flex-col justify-between gap-3 border-t border-line px-6 py-4 sm:flex-row sm:items-center">
                    <p className="text-xs text-muted">
                      Showing {rangeStart}–{rangeEnd} of {total}
                    </p>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setPage(Math.max(1, safePage - 1))}
                        disabled={safePage === 1}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-line text-text-soft transition-colors duration-base hover:bg-surface-3 disabled:opacity-40"
                        aria-label="Previous page"
                      >
                        ←
                      </button>
                      <span className="px-1 font-mono text-xs tabular-nums text-muted">
                        {safePage} / {pages}
                      </span>
                      <button
                        type="button"
                        onClick={() => setPage(Math.min(pages, safePage + 1))}
                        disabled={safePage === pages}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-line text-text-soft transition-colors duration-base hover:bg-surface-3 disabled:opacity-40"
                        aria-label="Next page"
                      >
                        →
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </Panel>
        </motion.section>
      </div>
    )
  }

  return (
    <>
      <WorkspaceShell>
        <WorkspaceHeader
          eyebrow="Career history"
          title="Analysis history"
          subtitle="Every resume version you've analyzed — its ATS score, job match and how your career signal has grown across versions."
          actions={
            <Link to="/upload" className={buttonClasses('primary', 'md')}>
              Analyze new resume
              <span aria-hidden="true">→</span>
            </Link>
          }
        />
        <div className="mt-8">{content}</div>
      </WorkspaceShell>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete this analysis?"
        description={
          pendingDelete && (
            <>
              <p>
                <span className="font-medium text-ink">{pendingDelete.title}</span>, its uploaded
                PDF, ATS analysis and any AI recommendations will be permanently
                removed.
              </p>
              <p className="mt-2 font-medium">This can't be undone.</p>
            </>
          )
        }
        confirmLabel="Delete analysis"
        cancelLabel="Keep it"
        busy={deleteBusy}
        error={deleteError}
        onConfirm={() => void confirmDelete()}
        onCancel={() => setPendingDelete(null)}
      />
    </>
  )
}