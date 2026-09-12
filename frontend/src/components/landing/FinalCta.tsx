import { motion } from 'motion/react'
import { Link } from 'react-router-dom'
import { Container } from '../shared/Container'
import { fadeUp } from '../../motion/variants'

/**
 * Final CTA — a deep teal band that is visually distinct from the page's
 * paper surfaces. Inverse palette comes free from the tokens: on-primary is
 * near-white on light and near-black-teal on dark, so the band adapts.
 */
export function FinalCta() {
  return (
    <section aria-labelledby="final-cta-heading" className="border-b border-line">
      <div className="relative overflow-hidden bg-primary">
        {/* Decorative beams */}
        <div aria-hidden="true" className="pointer-events-none absolute inset-0">
          <div className="absolute inset-x-0 top-[-40%] mx-auto h-[160%] w-[85%] rounded-[100%] bg-on-primary/5 blur-3xl" />
          <div className="absolute -bottom-1/3 -left-1/4 h-3/4 w-3/4 rounded-full bg-primary-strong/50 blur-3xl" />
          <div className="absolute -bottom-1/3 -right-1/4 h-3/4 w-3/4 rounded-full bg-primary-strong/50 blur-3xl" />
        </div>

        <Container className="relative py-20 text-center sm:py-24">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
          >
            <p className="font-mono text-xs font-medium uppercase tracking-[0.2em] text-on-primary/70">
              Resume analytics · ATS · Job matching
            </p>
            <h2
              id="final-cta-heading"
              className="mx-auto mt-5 max-w-2xl font-display text-3xl font-bold leading-tight tracking-tight text-on-primary sm:text-4xl lg:text-5xl"
            >
              Make your next application your best one.
            </h2>
            <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-on-primary/80 sm:text-lg">
              Analyze your resume for free. See your ATS score, find the exact gaps, and turn them
              into edits — in minutes, not days.
            </p>
            <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/sign-up"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-on-primary px-6 text-base font-medium text-primary transition-colors duration-base hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-on-primary"
              >
                Analyze my resume
                <span aria-hidden="true">→</span>
              </Link>
              <Link
                to="/sign-in"
                className="inline-flex h-12 items-center justify-center rounded-md border border-on-primary/40 px-6 text-base font-medium text-on-primary transition-colors duration-base hover:bg-on-primary/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-on-primary"
              >
                Sign in
              </Link>
            </div>
          </motion.div>
        </Container>
      </div>
    </section>
  )
}