import type { AiExplanation } from '../../types/models'
import { Panel } from '../ui/Panel'
import { SectionLabel } from '../ui/SectionLabel'
import { cn } from '../../lib/utils/cn'

interface RecommendationsSectionProps {
  /** Deterministic engine recommendations (always present after analysis). */
  recommendations: string[]
  /** Optional cached AI explanation payload (when the AI service is enabled). */
  ai: AiExplanation | null
}

const PRIORITY_TONE: Record<AiExplanation['items'][number]['priority'], string> = {
  high: 'bg-danger-soft text-danger',
  medium: 'bg-warning-soft text-warning',
  low: 'bg-surface-3 text-text-soft',
}

/** "0" → "01" — the numbered-priority style the recommendations read in. */
function numbered(index: number): string {
  return String(index + 1).padStart(2, '0')
}

/**
 * AI recommendations — the first-class, numbered, priority-ordered section of
 * the analysis page. The layout is designed ahead of the coming AI provider
 * work so longer generated content (wording, skill, summary and bullet
 * suggestions) lands without breaking. What renders today is only real API
 * output: the engine's `recommendations` and, when present, the cached
 * `ai_explanation`.
 */
export function RecommendationsSection({
  recommendations,
  ai,
}: RecommendationsSectionProps) {
  const aiCount = ai?.items.length ?? 0
  const total = aiCount + recommendations.length

  return (
    <Panel
      header={
        <div className="flex flex-wrap items-center justify-between gap-3">
          <SectionLabel>AI recommendations</SectionLabel>
          {total > 0 && (
            <span className="font-mono text-[10px] uppercase tracking-wider text-muted">
              01 — Highest priority first
            </span>
          )}
        </div>
      }
    >
      {total === 0 ? (
        <div className="p-6 lg:p-7">
          <p className="text-sm leading-relaxed text-muted">
            Recommendations from your analysis will appear here.
          </p>
        </div>
      ) : (
        <div>
          {ai && (
            <>
              {ai.summary.trim() !== '' && (
                <p className="border-b border-line px-6 py-4 text-sm leading-relaxed text-text-soft">
                  {ai.summary}
                </p>
              )}
              <ol className="divide-y divide-line">
                {ai.items.map((item, i) => (
                  <li
                    key={`${item.category}-${i}`}
                    className="flex gap-5 px-6 py-5"
                  >
                    <span
                      aria-hidden="true"
                      className="shrink-0 font-mono text-sm font-semibold tabular-nums text-primary"
                    >
                      {numbered(i)}
                    </span>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={cn(
                            'rounded-md px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider',
                            PRIORITY_TONE[item.priority],
                          )}
                        >
                          {item.priority} priority
                        </span>
                        {item.category !== '' && (
                          <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted">
                            {item.category}
                          </span>
                        )}
                      </div>
                      <p className="mt-2 text-sm font-medium text-ink">{item.finding}</p>
                      {item.plain_language !== '' && (
                        <p className="mt-1 text-sm leading-relaxed text-text-soft">
                          {item.plain_language}
                        </p>
                      )}
                      {item.action !== '' && (
                        <p className="mt-2 text-sm text-primary">
                          <span className="font-medium">Suggested action: </span>
                          {item.action}
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            </>
          )}

          {recommendations.length > 0 && (
            <ol className="divide-y divide-line">
              {recommendations.map((recommendation, i) => (
                <li key={i} className="flex gap-5 px-6 py-5">
                  <span
                    aria-hidden="true"
                    className="shrink-0 font-mono text-sm font-semibold tabular-nums text-primary"
                  >
                    {numbered(aiCount + i)}
                  </span>
                  <p className="min-w-0 text-sm leading-relaxed text-text">
                    {recommendation}
                  </p>
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
    </Panel>
  )
}