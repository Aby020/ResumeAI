/**
 * Small display-formatting helpers. Date parsing is lenient on purpose —
 * Django returns ISO-8601 ("2026-09-01T12:00:00Z"); a malformed value should
 * degrade to the raw string instead of throwing.
 */

const EMPTY = '—'

/** Parse an ISO-8601 string to a Date (or null on garbage input). */
export function parseIsoDate(value: string | null | undefined): Date | null {
  if (!value) return null
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

/** Format an ISO-8601 datetime to a short locale date, e.g. "Sep 1, 2026". */
export function formatDate(value: string | null | undefined): string {
  const date = parseIsoDate(value)
  if (!date) return EMPTY
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date)
}

/** Format an ISO-8601 datetime with time, e.g. "Sep 1, 2026, 2:30 PM". */
export function formatDateTime(value: string | null | undefined): string {
  const date = parseIsoDate(value)
  if (!date) return EMPTY
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

/** Format a numeric score, or an em dash when absent/invalid. */
export function formatScore(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return EMPTY
  return String(Math.round(value))
}

/** Format a 0–100 score as a percentage label (no fraction). */
export function formatPercent(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return EMPTY
  return `${Math.round(value)}%`
}