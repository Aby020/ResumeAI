import { motion } from 'motion/react'
import { staggerChild, staggerContainer } from '../../motion/variants'

const STEPS = [
  {
    index: '01',
    title: 'Upload your resume',
    note: 'PDF or DOCX — whatever you send to a recruiter today.',
  },
  {
    index: '02',
    title: 'Get your ATS & job-match score',
    note: 'How ATS systems and recruiters read it, out of 100.',
  },
  {
    index: '03',
    title: 'Apply the exact edits that move it',
    note: 'Prioritized, actionable fixes — not generic advice.',
  },
]

/**
 * "Three steps to your first score" — refined numbered rows, not feature
 * cards. Still the first-time guidance, reused verbatim once a user has
 * analyses so the workspace keeps its rhythm across the journey.
 *
 * A thin vertical line connects the numbered circles (matching the reference
 * composition) instead of horizontal border separators.
 */
export function ThreeStepGuide() {
  return (
    <section
      className="border border-line bg-surface p-6"
      aria-labelledby="steps-heading"
    >
      <h2
        id="steps-heading"
        className="font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary"
      >
        Three steps to your first score
      </h2>

      <motion.ol
        variants={staggerContainer}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        className="relative mt-3 space-y-2"
      >
        {/* Thin vertical connecting line through the center of all numbered circles */}
        <span
          aria-hidden="true"
          className="absolute left-[15px] top-[18px] bottom-[18px] w-px bg-line"
        />

        {STEPS.map((step) => (
          <motion.li key={step.index} variants={staggerChild}>
            <div className="flex items-start gap-4 py-4">
              <span
                aria-hidden="true"
                className="relative z-10 mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-primary font-mono text-xs font-medium text-primary bg-surface"
              >
                {step.index}
              </span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-ink">{step.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-muted">{step.note}</p>
              </div>
            </div>
          </motion.li>
        ))}
      </motion.ol>
    </section>
  )
}
