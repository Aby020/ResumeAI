import { motion } from 'motion/react'
import { ResumeAILogo } from '../shared/ResumeAILogo'
import { fadeUp } from '../../motion/variants'

/**
 * The hero's right-hand résumé visual — a stylized document treatment in the
 * existing ResumeAI logo/document language, plus a short editorial quote.
 *
 * On large screens the document panel and quote sit side by side with a
 * vertical border divider; on mobile they stack vertically with a top border.
 *
 * Deliberately decorative: the skeleton "text lines" are abstract hairlines,
 * never fake data, so the block reads as product identity rather than a
 * fabricated reading of the user's resume.
 */
export function HeroVisual() {
  return (
    <motion.aside variants={fadeUp} initial="hidden" animate="visible">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-stretch lg:gap-0">
        {/* Stylized résumé document — left portion */}
        <div className="flex-1 border border-line bg-surface px-8 py-10 sm:px-10">
          <div className="mx-auto w-fit">
            <ResumeAILogo size={72} className="text-ink" />
          </div>
          <div className="mx-auto mt-8 w-44 max-w-full space-y-3" aria-hidden="true">
            <span className="block h-1.5 w-full rounded-full bg-primary/60" />
            <span className="block h-1.5 w-3/4 rounded-full bg-surface-3" />
            <span className="block h-1.5 w-5/6 rounded-full bg-surface-3" />
            <span className="block h-1.5 w-2/3 rounded-full bg-surface-3" />
          </div>
        </div>

        {/* Quote — right portion, vertical divider on wide screens, horizontal on mobile */}
        <div className="flex flex-col justify-center border-t border-line pt-5 lg:w-[42%] lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
          <p className="font-display text-lg font-bold leading-snug tracking-tight text-ink">
            &ldquo;A stronger resume opens more doors.&rdquo;
          </p>
          <hr className="mt-4 w-8 border-t-2 border-primary" aria-hidden="true" />
          <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.25em] text-primary">
            Same you. A brighter tomorrow.
          </p>
        </div>
      </div>
    </motion.aside>
  )
}
