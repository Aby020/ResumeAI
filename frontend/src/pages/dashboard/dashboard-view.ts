/**
 * Thin view-model over the `/api/dashboard/` payload.
 *
 * Keeps the derivation one place (and unit-testable) so components can reason
 * about "what is true right now" instead of re-filtering arrays. Everything
 * here is computed from real API fields — no invented metrics.
 */

import type { Dashboard, RecentResume } from '../../types/models'

export interface DashboardView {
  /** The user's total uploads (from the API). */
  total: number
  /** API aggregates across all analyses. */
  averageAts: number
  highestAts: number
  bestJobMatch: number
  /** The newest uploads (up to five), newest first — as returned. */
  recent: RecentResume[]
  /**
   * The recent uploads that carry a meaningful ATS score (>0). A pending
   * upload always reports 0, so this is the honest "analyzed" subset.
   */
  analyzed: RecentResume[]
  /** Newest analyzed resume, or null. */
  latestAnalyzed: RecentResume | null
  /** Newest upload of any kind, or null. */
  latestUpload: RecentResume | null
  /** True when nothing has been uploaded yet (drives the empty workspace). */
  isEmpty: boolean
  /** True when uploads exist but none has a score yet. */
  isAwaiting: boolean
  /** Primary ATS mark — the latest analyzed score, or null while awaiting. */
  currentScore: number | null
}

export function analyzeDashboard(data: Dashboard): DashboardView {
  const recent = data.recent_resumes
  const analyzed = recent.filter((r) => r.ats_score > 0)
  const latestAnalyzed = analyzed[0] ?? null
  const latestUpload = recent[0] ?? null
  const isEmpty = data.total_resumes === 0
  const isAwaiting = !isEmpty && analyzed.length === 0

  return {
    total: data.total_resumes,
    averageAts: data.average_ats,
    highestAts: data.highest_ats,
    bestJobMatch: data.best_job_match,
    recent,
    analyzed,
    latestAnalyzed,
    latestUpload,
    isEmpty,
    isAwaiting,
    currentScore: latestAnalyzed ? latestAnalyzed.ats_score : null,
  }
}