/**
 * Shared API contract types — strict mirrors of the Django REST API responses.
 * Keep these aligned with the serializers in account_manager/, resume/ and
 * dashboard/ (see the per-file notes).
 */

/** `GET /api/auth/me/`, login/register, and profile responses */
export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  /** ISO-8601 datetime, e.g. "2026-09-01T12:00:00Z" */
  date_joined: string
}

/** `POST /api/auth/login/` — SimpleJWT token pair */
export interface AuthTokens {
  access: string
  refresh: string
}

/** `POST /api/auth/token/refresh/` */
export interface TokenRefreshResponse {
  access: string
}

/** Register payload — mirrors RegisterSerializer fields */
export interface RegisterPayload {
  first_name: string
  username: string
  email: string
  password: string
  confirm_password: string
}

/** Login payload — accepts a username *or* email in the `username` field */
export interface LoginPayload {
  username: string
  password: string
}

/** Allowed keys someone may PATCH via `PATCH /api/profile/` */
export interface ProfileUpdatePayload {
  email?: string
  first_name?: string
  last_name?: string
}

/** A resume row from `GET /api/resumes/` (list + detail) */
export interface Resume {
  id: number
  title: string
  /** URL to the stored file */
  file: string
  /** ISO-8601 datetime */
  uploaded_at: string
  is_deleted: boolean
  ats_score: number | null
  job_match_score: number | null
  analyzed_at: string | null
}

/** Multipart upload payload for `POST /api/resumes/` */
export interface ResumeCreatePayload {
  title: string
  file: File
  job_description?: string
  job_image?: File
}

/** One row from `GET /api/history/` */
export interface HistoryItem {
  resume_id: number
  title: string
  ats_score: number
  job_match_score: number | null
  analyzed_date: string | null
  status: 'analyzed' | 'pending'
}

/** One ATS category row: `{ "<Category>": { score, max } }` */
export interface AtsCategory {
  score: number
  max: number
}

/** `ats_breakdown` in the analysis payload — category name → score/max */
export type AtsBreakdown = Record<string, AtsCategory>

/** `job_match_details` in the analysis payload */
export interface JobMatchDetails {
  match_confidence: number | null
  missing_required_skills: string[]
  missing_preferred_skills: string[]
  missing_experience: string[]
  missing_certifications: string[]
  missing_technologies: string[]
  resume_strengths: string[]
  resume_weaknesses: string[]
  suggestions: string[]
  recommendations: string[]
}

/** One item of the cached AIExplanation payload (resume.ai.schemas.ExplanationItem) */
export interface AiExplanationItem {
  category: string
  finding: string
  plain_language: string
  action: string
  priority: 'high' | 'medium' | 'low'
}

/** Cached AIExplanation payload (resume.ai.schemas.AIExplanation) */
export interface AiExplanation {
  items: AiExplanationItem[]
  summary: string
}

/** One item of the cached AIRewrite payload (resume.ai.schemas.RewriteSuggestion) */
export interface AiRewriteSuggestion {
  section: string
  original: string
  rewritten: string
  target_finding: string
  rationale: string
}

/** Cached AIRewrite payload (resume.ai.schemas.AIRewrite) */
export interface AiRewrite {
  suggestions: AiRewriteSuggestion[]
  note: string
}

/** `GET /api/resumes/<pk>/analysis/` — full analysis payload */
export interface ResumeAnalysis {
  resume_id: number
  ats_score: number
  ats_grade: string | null
  ats_breakdown: AtsBreakdown
  strengths: string[]
  improvement_areas: string[]
  recommendations: string[]
  detected_skills: string[]
  job_match_score: number | null
  job_description: string
  matching_skills: string[]
  missing_skills: string[]
  extra_skills: string[]
  job_match_details: JobMatchDetails
  ai_explanation: AiExplanation | null
  ai_rewrite: AiRewrite | null
  /** ISO-8601 datetime */
  analyzed_at: string
}

/** One row of `recent_resumes` in the dashboard payload */
export interface RecentResume {
  id: number
  title: string
  uploaded_at: string
  ats_score: number
  job_match_score: number | null
}

/** `GET /api/dashboard/` — summary metrics */
export interface Dashboard {
  total_resumes: number
  average_ats: number
  highest_ats: number
  best_job_match: number
  recent_resumes: RecentResume[]
}