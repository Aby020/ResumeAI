import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { ThemeToggle } from '../ui/ThemeToggle'
import { ResumeAILogo } from '../shared/ResumeAILogo'
import { fadeUp } from '../../motion/variants'

interface AuthLayoutProps {
  /** The form content: heading, fields, CTA, secondary nav. */
  children: ReactNode
  /** The product visual shown on the right half (desktop only). */
  visual?: ReactNode
}

/**
 * Two-part authentication frame. On desktop the form takes the left half and a
 * product visual the right; on mobile the whole page collapses to the form in
 * a comfortable single column. The brand mark sits above the form (not in a
 * centered card), keeping the page airy and editorial rather than
 * "login-box" — in line with the landing page's premium, career-focused tone.
 */
export function AuthLayout({ children, visual }: AuthLayoutProps) {
  return (
    <div className="relative flex min-h-dvh flex-col bg-bg lg:flex-row lg:overflow-hidden">
      {/* Theme toggle — floating top-right */}
      <div className="absolute right-4 top-4 z-20 sm:right-6">
        <ThemeToggle />
      </div>

      {/* Left / primary — the form column */}
      <main className="flex flex-1 flex-col items-stretch justify-center px-5 py-16 sm:px-10 lg:px-16 xl:px-24">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="mx-auto w-full max-w-sm"
        >
          <Link to="/" className="inline-flex" aria-label="ResumeAI home">
            <ResumeAILogo size={34} showWordmark />
          </Link>
          <div className="mt-8">{children}</div>
        </motion.div>
      </main>

      {/* Right / supporting — product visual (desktop only) */}
      {visual && (
        <aside
          aria-hidden="true"
          className="hidden items-center justify-center border-l border-line bg-surface-2 px-12 lg:flex xl:px-20"
        >
          {visual}
        </aside>
      )}
    </div>
  )
}