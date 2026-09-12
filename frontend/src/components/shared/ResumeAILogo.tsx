import { cn } from '../../lib/utils/cn'

interface ResumeAILogoProps {
  /** Icon size in pixels. */
  size?: number
  /** Show the "ResumeAI" wordmark beside the icon. */
  showWordmark?: boolean
  className?: string
}

/**
 * Reusable ResumeAI brand mark — a refined document icon representing a
 * resume, paired with the wordmark. The icon uses `currentColor` for theme
 * adaptability and `var(--primary)` for the career-teal accent, so it stays
 * visually correct in both light and dark themes.
 *
 * The document shape features a clean paper silhouette with a subtle corner
 * fold and three horizontal lines — the top one teal, representing a resume
 * section heading — giving it a distinctive "resume" identity that reads at
 * small sizes.
 */
export function ResumeAILogo({
  size = 32,
  showWordmark = false,
  className,
}: ResumeAILogoProps) {
  const icon = (
    <svg
      viewBox="0 0 20 26"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={Math.round(size * 1.3)}
      aria-hidden="true"
      className="shrink-0"
    >
      {/* Paper body — tall rounded rect with a folded top-right corner */}
      <path
        d="M2 0h8.5L18 7.5v16.5c0 1.1-.9 2-2 2H2c-1.1 0-2-.9-2-2V2c0-1.1.9-2 2-2z"
        fill="currentColor"
        opacity="0.08"
      />
      <path
        d="M2 0h8.5L18 7.5v16.5c0 1.1-.9 2-2 2H2c-1.1 0-2-.9-2-2V2c0-1.1.9-2 2-2z"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeOpacity="0.25"
      />

      {/* Corner fold crease */}
      <path
        d="M10.5 0v5.5c0 1.1.9 2 2 2H18"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeOpacity="0.15"
      />

      {/* Resume text lines — top one is teal (section heading) */}
      <rect x="3.5" y="11" width="7" height="1.5" rx="0.75" fill="var(--primary, #0f766e)" />
      <rect x="3.5" y="14.5" width="11" height="1" rx="0.5" fill="currentColor" opacity="0.18" />
      <rect x="3.5" y="17.5" width="9" height="1" rx="0.5" fill="currentColor" opacity="0.18" />
      <rect x="3.5" y="20.5" width="11" height="1" rx="0.5" fill="currentColor" opacity="0.18" />
    </svg>
  )

  if (!showWordmark) {
    return <span className={cn('inline-flex', className)}>{icon}</span>
  }

  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      {icon}
      <span className="font-display text-lg font-bold tracking-tight text-ink">
        Resume<span className="text-primary">AI</span>
      </span>
    </span>
  )
}
