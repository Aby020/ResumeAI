/**
 * Score tiers — the single source of truth that maps a 0–100 score (ATS or
 * job match) to a label and a Tailwind tone. Used by every score
 * visualization so hero bands, the spectrum and result rows stay consistent.
 *
 * Tier boundaries:
 *   ≥90 Excellent · 75–89 Strong · 60–74 Solid · 40–59 Developing · <40 Needs work
 */

export type ScoreTone = 'excellent' | 'good' | 'moderate' | 'weak' | 'poor'

export interface ScoreTier {
  /** Human label, e.g. "Strong". */
  label: string
  tone: ScoreTone
}

const TIERS: ReadonlyArray<{ min: number; label: string; tone: ScoreTone }> = [
  { min: 90, label: 'Excellent', tone: 'excellent' },
  { min: 75, label: 'Strong', tone: 'good' },
  { min: 60, label: 'Solid', tone: 'moderate' },
  { min: 40, label: 'Developing', tone: 'weak' },
  { min: 0, label: 'Needs work', tone: 'poor' },
]

/** Resolve the tier for a 0–100 score (clamped; never throws). */
export function scoreTier(score: number): ScoreTier {
  const clamped = Math.min(100, Math.max(0, Math.round(score)))
  const tier = TIERS.find((t) => clamped >= t.min) ?? TIERS[TIERS.length - 1]
  return { label: tier.label, tone: tier.tone }
}

/** Tailwind classes per tone. Static strings so Tailwind v4 keeps them. */
export const toneText: Record<ScoreTone, string> = {
  excellent: 'text-score-excellent',
  good: 'text-score-good',
  moderate: 'text-score-moderate',
  weak: 'text-score-weak',
  poor: 'text-score-poor',
}

export const toneFill: Record<ScoreTone, string> = {
  excellent: 'bg-score-excellent',
  good: 'bg-score-good',
  moderate: 'bg-score-moderate',
  weak: 'bg-score-weak',
  poor: 'bg-score-poor',
}

export const toneSoft: Record<ScoreTone, string> = {
  excellent: 'bg-score-excellent-soft',
  good: 'bg-score-good-soft',
  moderate: 'bg-score-moderate-soft',
  weak: 'bg-score-weak-soft',
  poor: 'bg-score-poor-soft',
}